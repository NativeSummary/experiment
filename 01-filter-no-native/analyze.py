
# 多进程运行框架


import json
import os
import shutil
import time
from collections import defaultdict
from multiprocessing import Process, Queue

from native_summary.pre_analysis.__main__ import apk_pre_analysis


# 全局配置
analyse_dex=True
fd_dataset_path = '/home/user/ns/dataset/fdroid'
fd_out_dataset_path = '/home/user/ns/dataset/fd-filter'

malradar_dataset_path = '/home/user/ns/dataset/malradar'
malradar_out_dataset_path = '/home/user/ns/dataset/malradar-filter'

target = 'fdroid'
print(f"current target: {target}")

if target == 'fdroid':
    dataset_path = fd_dataset_path
    out_dataset_path = fd_out_dataset_path
elif target == 'malradar':
    dataset_path = malradar_dataset_path
    out_dataset_path = malradar_out_dataset_path
else:
    dataset_path = None
    out_dataset_path = None

# 跑的东西的相关名称，出现在进度文件名等处。
BRAND = 'filter_dataset'

PROGRESS_FILENAME = f"{BRAND}.progress"
# 全局状态，通过pickel实现持久化
GLOBAL_STATE = {
        'progress': set(), # filenames that finished analyzing
        'arch_count': dict(),
        'stats': dict() # 从文件名映射到一个Tuple，依次是
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
    # progress_json = os.path.join(path, f"{PROGRESS_FILENAME}.json")
    # with open(progress_json, 'w') as f:
    #     json.dump(GLOBAL_STATE, f, indent=4)
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
                processes[i] = run_one(args_list.pop(0), queues[i])
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
                        processes[i] = run_one(args_list.pop(0), queues[i])
                    else:
                        processes[i] = None
                        queues[i] = None
                    break
            else:
                time.sleep(3)
    except KeyboardInterrupt:
        # 如果遇到异常，则终止所有进程并finalize
        for i in range(process_count):
            process = processes[i] #type: Process
            if process != None:
                process.terminate()
    finally:
        finalize(out_path)

# ===========用户编写的部分 ==========

# 返回一个已经启动的进程
def run_one(arg, queue):
    process = Process(target=filter_one, args=(arg, queue))
    process.start()
    return process

def handle_result(result):
    GLOBAL_STATE['stats'][result[0]] = result[2:]
    ac = GLOBAL_STATE['arch_count']
    # default to 0
    if result[1] not in ac:
        ac[result[1]] = 0
    ac[result[1]] += 1

# 负责攒参数，然后传给mp_run
def main(process_count):
    print(f'GLOBAL_STATE {GLOBAL_STATE}')
    filter_one_args = []
    for file in os.listdir(dataset_path):
        fpath = os.path.join(dataset_path, file)
        # 保存进度
        if fpath in GLOBAL_STATE['stats']:
            continue
        filter_one_args.append(fpath)
    filter_one_args.sort()
    mp_run(filter_one_args, process_count, out_dataset_path)

def filter_one(file_path, queue: Queue):
    filename = os.path.basename(file_path)
    print(f'analyzing {filename}')
    apk, dex, arch_selected, so_stat, tags = apk_pre_analysis(file_path, analyse_dex)
    is_flutter = tags['is_flutter']
    has_supported_so = tags['has_so']
    has_java_sym = tags['has_javasym']
    has_java_native_method = len(dex.native_methods) > 0 if analyse_dex else None
    if (not is_flutter) and has_supported_so and has_java_sym:
        shutil.copy(file_path, out_dataset_path)
    queue.put((file_path, arch_selected, is_flutter, has_java_sym, has_java_native_method))
    return is_flutter, has_java_sym, has_java_native_method

if __name__ == '__main__':
    start = time.time()
    restore_progress(out_dataset_path)
    main(70)
    dura = time.time() - start
    print(f'analysis spent {dura}s')
