
# 多进程运行框架


import json
import os
import shutil
import time
from multiprocessing import Process, Queue
import subprocess

## 使用方式
# 1. 

# 全局配置

TIMEOUT = 7200.0

fd_dataset_path = '/home/user/ns/dataset/fd-filter'
fd_out_dataset_path = '/home/user/ns/experiment/baseline-native_summary/fdroid-results'

malradar_dataset_path = '/home/user/ns/dataset/malradar-filter'
malradar_out_dataset_path = '/home/user/ns/experiment/baseline-native_summary/malradar-results'

nfb_dataset_path = '/home/user/ns/dataset/nfb'
nfb_out_dataset_path = '/home/user/ns/experiment/baseline-native_summary/nfb-results'

nfbe_dataset_path = '/home/user/ns/dataset/nfbe'
nfbe_out_dataset_path = '/home/user/ns/experiment/baseline-native_summary/nfbe-results'

jucifybench_dataset_path = '/home/user/ns/dataset/jucifybench'
jucifybench_out_dataset_path = '/home/user/ns/experiment/baseline-native_summary/jucifybench-results'

intersec_dataset_path = '/home/user/ns/dataset/intersect'
optcompare_out_dataset_path = '/home/user/ns/experiment/baseline-native_summary/optcompare-results'
nooptcompare_out_dataset_path = '/home/user/ns/experiment/baseline-native_summary/nooptcompare-results'
compare_out_dataset_path = '/home/user/ns/experiment/baseline-native_summary/compare-results'
# command_template = 'docker run --cpus=1 --mem=128G --rm -v $RES_DIR:/root/apps/ nativesummary/jnsaf:3.2.1 /root/apps/$1'

target = 'nooptcompare'
print(f"current target: {target}")

if target == 'fdroid':
    dataset_path = fd_dataset_path
    out_dataset_path = fd_out_dataset_path
elif target == 'malradar':
    dataset_path = malradar_dataset_path
    out_dataset_path = malradar_out_dataset_path
elif target == 'nfbe':
    dataset_path = nfbe_dataset_path
    out_dataset_path = nfbe_out_dataset_path
elif target == 'nfb':
    dataset_path = nfb_dataset_path
    out_dataset_path = nfb_out_dataset_path
elif target == 'jucifybench':
    dataset_path = jucifybench_dataset_path
    out_dataset_path = jucifybench_out_dataset_path
elif target == 'optcompare':
    dataset_path = intersec_dataset_path
    out_dataset_path = optcompare_out_dataset_path
elif target == 'nooptcompare':
    dataset_path = malradar_dataset_path
    out_dataset_path = nooptcompare_out_dataset_path
elif target == 'compare':
    dataset_path = malradar_dataset_path
    out_dataset_path = compare_out_dataset_path
else:
    dataset_path = None
    out_dataset_path = None

# 跑的东西的相关名称，出现在进度文件名等处。
BRAND = 'ns'

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
container_name_template = 'ns-{}'
if target == 'nooptcompare':
    container_name_template = 'ns-noopt-{}'
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
    # proc = None
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

# docker run -v $apk_path:/apk -v $result_folder:/out ns
def docker_daemon_wrapper(queue, fp):
    fname = os.path.basename(fp)
    container_name = container_name_template.format(fname)
    result_dir = os.path.join(out_dataset_path, fname)
    run_cmd_suffix = f'--rm --cpus=1 --memory=32G -v {fp}:/apk -v {result_dir}:/out ns'
    if target == 'compare':
        run_cmd_suffix = "-e GHIDRA_NS_ARGS=@@-noOpt " + run_cmd_suffix
    stdout_file_path_prefix = os.path.join(result_dir, 'docker_runner')
    shutil.rmtree(result_dir, ignore_errors=True)
    os.makedirs(result_dir, exist_ok=True)
    ret = docker_daemon(queue, container_name, run_cmd_suffix, stdout_file_path_prefix, TIMEOUT)
    queue.put(ret)

# 负责攒参数，然后传给mp_run
def main(process_count):
    # print(f'GLOBAL_STATE {GLOBAL_STATE}')
    file_paths = []
    for file in os.listdir(dataset_path):
        if not file.endswith('.apk'):
            continue
        fpath = os.path.join(dataset_path, file)
        # 保存进度
        # 存在已保存的结果，且结果文件夹未被删除才跳过
        if container_name_template.format(file) in GLOBAL_STATE['stats'] and os.path.exists(os.path.join(out_dataset_path, file)):
            continue
        file_paths.append(fpath)
    file_paths.sort()
    if not os.path.exists(out_dataset_path):
        os.makedirs(out_dataset_path, exist_ok=True)
    mp_run(file_paths, process_count, out_dataset_path)

if __name__ == '__main__':
    start = time.time()
    restore_progress(out_dataset_path)
    main(10)
    dura = time.time() - start
    print(f'all dockers spent {dura}s')

