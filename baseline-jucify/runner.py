#!/usr/bin/python3
# 多进程运行框架


import json
import os,sys
import shutil
import time
from multiprocessing import Process, Queue
import subprocess

## 使用方式
# 1. 

# 全局配置

TIMEOUT = 999999

fd_dataset_path = '/home/user/ns/dataset/fd-filter'
fd_out_dataset_path = '/home/user/ns/experiment/baseline-jucify/fdroid-results'

malradar_dataset_path = '/home/user/ns/dataset/malradar-filter'
malradar_out_dataset_path = '/home/user/ns/experiment/baseline-jucify/malradar-results'

nfb_dataset_path = '/home/user/ns/dataset/nfb'
nfb_out_dataset_path = '/home/user/ns/experiment/baseline-jucify/nfb-results'

nfbe_dataset_path = '/home/user/ns/dataset/nfbe'
nfbe_out_dataset_path = '/home/user/ns/experiment/baseline-jucify/nfbe-results'

coverage_dataset_path = '/home/user/ns/dataset/malradar-filter'
coverage_out_dataset_path = '/home/user/ns/experiment/baseline-jucify/coverage-results'

# command_template = 'docker run --cpus=1 --mem=128G --rm -v $RES_DIR:/root/apps/ nativesummary/jnsaf:3.2.1 /root/apps/$1'

target = 'none'
# print(f"current target: {target}")

def set_dataset_paths(cur_target):
    global target
    global dataset_path
    global out_dataset_path
    target = cur_target
    print(f"current cur_target: {cur_target}", file=sys.stderr)
    if cur_target == 'fdroid':
        dataset_path = fd_dataset_path
        out_dataset_path = fd_out_dataset_path
    elif cur_target == 'malradar':
        dataset_path = malradar_dataset_path
        out_dataset_path = malradar_out_dataset_path
    elif cur_target == 'nfbe':
        dataset_path = nfbe_dataset_path
        out_dataset_path = nfbe_out_dataset_path
    elif cur_target == 'nfb':
        dataset_path = nfb_dataset_path
        out_dataset_path = nfb_out_dataset_path
    elif cur_target == 'coverage':
        dataset_path = coverage_dataset_path
        out_dataset_path = coverage_out_dataset_path
    else:
        raise RuntimeError(f'unknown cur_target {cur_target}')
        dataset_path = None
        out_dataset_path = None

# 跑的东西的相关名称，出现在进度文件名等处。
BRAND = 'jucify'

PROGRESS_FILENAME = f"{BRAND}.progress"
# 全局状态，通过pickel实现持久化
GLOBAL_STATE = {
        'progress': set(), # filenames that finished analyzing
        'stats': dict() # 从文件名映射到一个Tuple，依次是分析时间，返回值
    }


def restore_progress(path):
    import os
    import pickle
    global GLOBAL_STATE
    prog_file = os.path.join(path, PROGRESS_FILENAME)
    if os.path.exists(prog_file):
        with open(prog_file, "rb") as f:
            GLOBAL_STATE = pickle.load(f)
    else:
        GLOBAL_STATE = {
            'progress': set(), # filenames that finished analyzing
            'stats': dict() # 从文件名映射到一个Tuple，依次是分析时间，返回值
        }


def backup_progress(path):
    import os
    import pickle
    prog_file = os.path.join(path, PROGRESS_FILENAME)
    with open(prog_file, "wb") as f:
        pickle.dump(GLOBAL_STATE, f)


def set_exc_hook(path):
    import sys
    def my_except_hook(exctype, value, traceback):
        if issubclass(exctype, KeyboardInterrupt):
            finalize(path)
        sys.__excepthook__(exctype, value, traceback)
    sys.excepthook = my_except_hook


# 输出现有结果
def finalize(path):
    # 可以添加自定义打印代码，把想要的进度打印为json
    progress_json = os.path.join(path, f"{PROGRESS_FILENAME}.json")
    with open(progress_json, 'w') as f:
        json.dump(GLOBAL_STATE['stats'], f, indent=4)
    backup_progress(path)


def mp_run(args_list, process_count, out_path):
    from multiprocessing import Process, Queue
    queues = [None for i in range(process_count)]
    processes = [None for i in range(process_count)]
    try:
        for i in range(process_count):
            if len(args_list) > 0:
                queues[i] = Queue()
                # TODO arg
                processes[i] = create_process(args_list.pop(0), queues[i])
        # 轮询是否结束，结束则处理返回值，并启动新的进程
        while processes.count(None) < process_count:
            for i in range(process_count):
                process = processes[i] #type: Process
                queue = queues[i] #type: Queue
                case1 = process != None and (not queue.empty())
                case2 = process != None and not process.is_alive()
                if case1 or case2: 
                    # 任务结束，开始从列表删除当前任务
                    if case1:
                        # 获取Queue返回值
                        # 因此每个函数只能在结束的时候返回一条信息
                        result = queue.get_nowait()
                        handle_result(result)
                    if len(args_list) > 0:
                        queues[i] = Queue()
                        # create_and_start_subprocess(args, queue: Queue)
                        processes[i] = create_process(args_list.pop(0), queues[i])
                    else:
                        processes[i] = None
                        queues[i] = None
                    break
            else:
                time.sleep(3)
    # except KeyboardInterrupt:
    #     # 如果遇到异常，则终止所有进程并finalize
    #     for i in range(process_count):
    #         process = processes[i] #type: Process
    #         if process != None:
    #             # TODO how to terminate
    #             process.terminate()
    finally:
        finalize(out_path)

# ===========用户编写的部分 ==========


# 返回一个已经启动的进程
def create_process(arg, queue):
    process = Process(target=docker_daemon_wrapper, args=(queue, arg))
    process.start()
    return process


# suffix里可以包含--rm选项，防止占用过多空间
docker_run_cmd_template = 'docker run -i --name {} {}' # .format(container_name, run_cmd_suffix)
container_name_template = 'jucify-{}'
# 先用docker run命令启动，同时捕获输入输出
# 超时的时候用docker stop命令杀掉。
# stdout_file_path_prefix为标准输出文件前缀，会在后面加上.stdout.txt和.stderr.txt
def docker_daemon(queue, container_name, run_cmd_suffix, stdout_file_path_prefix=None, timeout=None):
    cmd = docker_run_cmd_template.format(container_name, run_cmd_suffix)
    print(cmd)
    stdout_file, stderr_file = None, None
    if stdout_file_path_prefix:
        os.makedirs(os.path.dirname(stdout_file_path_prefix), exist_ok=True)
        stdout_file = open(stdout_file_path_prefix+'.stdout.txt', 'wb')
        stderr_file = open(stdout_file_path_prefix+'.stderr.txt', 'wb')
    start = time.time()
    proc = subprocess.Popen(cmd, shell=True, stdout=stdout_file, stderr=stderr_file)
    try:
        proc.wait(timeout=timeout)
        duration = time.time() - start
    except subprocess.TimeoutExpired:
        print(f"docker kill {container_name}")
        subprocess.run(f"docker kill {container_name}", shell=True)
        duration = timeout
    except KeyboardInterrupt:
        print(f"docker kill {container_name}")
        subprocess.run(f"docker kill {container_name}", shell=True)
        raise
    finally:
        if stdout_file_path_prefix:
            stdout_file.close()
            stderr_file.close()
    return container_name, duration, proc.poll()

def handle_result(result):
    GLOBAL_STATE['stats'][result[0]] = result[1:]

# docker run --rm --cpus=1 --memory=32G -v /home/user/ns/tools/platforms:/platforms -v $RES_DIR:/root/apps/ jucify -p /platforms -f /root/apps/$1 -t -c
def docker_daemon_wrapper(queue, fp):
    fname = os.path.basename(fp)
    container_name = container_name_template.format(fname)
    result_dir = os.path.join(out_dataset_path, fname) # -v /home/user/ns/dev/jucify/nativediscloser/jni_interfaces/utils.py:/root/JuCify/nativediscloser/jni_interfaces/utils.py -v /home/user/ns/dev/jucify/target/JuCify-0.1-jar-with-dependencies.jar:/root/JuCify/target/JuCify-0.1-jar-with-dependencies.jar -v /home/user/ns/dev/jucify/scripts/execute_with_limit_time.sh:/root/JuCify/scripts/execute_with_limit_time.sh jucify:fix1
    run_cmd_suffix = f'--rm --cpus=1 --memory=32G -v /home/user/ns/tools/platforms:/platforms -v {result_dir}:/root/apps/ -e JUCIFY_TIMEOUT={JUCIFY_TIMEOUT} -e BINARY_TIMEOUT={BINARY_TIMEOUT} -e WAIT_TIME={WAIT_TIME} jucify -p /platforms -f /root/apps/{fname} -t -c'
    if target == 'coverage':
        run_cmd_suffix = run_cmd_suffix.removesuffix('-t -c') + '-c'
    stdout_file_path_prefix = os.path.join(result_dir, 'docker_runner')
    shutil.rmtree(result_dir, ignore_errors=True)
    os.makedirs(result_dir, exist_ok=True)
    copy_apk = shutil.copy(fp, result_dir)
    copy_apk = os.path.join(result_dir, fname)
    ret = docker_daemon(queue, container_name, run_cmd_suffix, stdout_file_path_prefix, TIMEOUT)
    try:
        os.remove(copy_apk)
    except OSError:
        pass
    queue.put(ret)

def xml_empty_flow(path):
    import xml.etree.ElementTree as ET
    root = ET.parse(path).getroot()
    for result in root.findall('./Results/Result'):
        return False
    return True

def run_success(file):
    if os.path.exists(os.path.join(out_dataset_path, file, f'{file}.xml')):
        if not xml_empty_flow(os.path.join(out_dataset_path, file, f'{file}.xml')):
            return True
    return False

# 负责攒参数，然后传给mp_run
def main(target, process_count):
    set_dataset_paths(target)
    restore_progress(out_dataset_path)
    # print(f'GLOBAL_STATE {GLOBAL_STATE}')
    file_paths = []
    for file in os.listdir(dataset_path):
        if not file.endswith('.apk'):
            continue
        fpath = os.path.join(dataset_path, file)
        # 保存进度
        # 存在已保存的结果，且结果文件夹未被删除才跳过
        if container_name_template.format(file) in GLOBAL_STATE['stats'] and os.path.exists(os.path.join(out_dataset_path, file)):
        # if container_name_template.format(file) in GLOBAL_STATE['stats'] and run_success(file):
            print(f"skipping {file}")
            continue
        file_paths.append(fpath)
    file_paths.sort()
    if not os.path.exists(out_dataset_path):
        os.makedirs(out_dataset_path)
    mp_run(file_paths, process_count, out_dataset_path)

JUCIFY_TIMEOUT = '14400'
BINARY_TIMEOUT = '10800'
WAIT_TIME = '300'

if __name__ == '__main__':
    start = time.time()
    main('fdroid', 19)
    # main('malradar', 30)
    # main('coverage', 30)
    dura = time.time() - start
    print(f'analysis spent {dura}s') # 2023年3月26日 analysis spent 230661.4015533924s

# =======depricated ======

# 有待完善，还没测试
'''
def command_daemon(arg, queue, capture_output_dir=None):
    start = time.time()
    proc = subprocess.run(arg, shell=True)
    ret_code = proc.returncode
    duration = time.time() - start
    queue.put((duration, ret_code))
    return
'''
# 原来是直接支持multiprocessing的Process的。
# 为了支持subprocess的Popen这种的返回值，需要这个包装一下。
'''
class MyProcess:
    def __init__(self, p) -> None:
        self.process = p #type: subprocess.Popen
    def start(self):
        pass
    def is_alive(self) -> bool:
        self.process.poll() is None
    def terminate(self) -> None:
        self.process.kill()

def run_one_example_2(arg, queue):
    p = subprocess.Popen(arg, shell=True)
    process = MyProcess(p)
    process.start()
    return process
'''
