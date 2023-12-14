
# multiprocessing docker runner


import json
import os,sys
import shutil
import time
from multiprocessing import Process, Queue
import subprocess,signal

script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
sys.path.insert(1, script_dir)


## Usage
# docker_run_cmd_template = 'docker run -i --name {} {}' # .format(container_name, run_cmd_suffix)
# 1. Each container should have unique name
# 

def call_it(instance, name, args=(), kwargs=None):
    "indirect caller for instance methods and multiprocessing"
    if kwargs is None:
        kwargs = {}
    return getattr(instance, name)(*args, **kwargs)


class RunInfo:
    def __init__(self, container_name, run_cmd_suffix, TIMEOUT, stdout_file_path_prefix=None, before_run_hook=lambda:None, after_run_hook=lambda:None) -> None:
        self.container_name = container_name
        self.run_cmd_suffix = run_cmd_suffix
        self.stdout_file_path_prefix = stdout_file_path_prefix
        self.TIMEOUT = TIMEOUT
        self.before_run_hook = before_run_hook
        self.after_run_hook = after_run_hook

class DockerRunner:
    def __init__(self, base_path, brand) -> None:
        self.brand = brand
        self.progress_filename = "DockerRunner.progress"
        self.base_path = base_path
        self.GLOBAL_STATE = {
            'stats': dict() # 从文件名映射到一个Tuple，依次是分析时间，返回值
        }
        self.restore_progress()

    def get_stats(self):
        return self.GLOBAL_STATE['stats']

    def restore_progress(self):
        import os
        import pickle
        prog_file = os.path.join(self.base_path, self.progress_filename)
        if os.path.exists(prog_file):
            with open(prog_file, "rb") as f:
                self.GLOBAL_STATE = pickle.load(f)

    def backup_progress(self):
        import os
        import pickle
        prog_file = os.path.join(self.base_path, self.progress_filename)
        with open(prog_file, "wb") as f:
            pickle.dump(self.GLOBAL_STATE, f)

    def set_exc_hook(self):
        import sys
        def my_except_hook(exctype, value, traceback):
            if issubclass(exctype, KeyboardInterrupt):
                self.finalize()
            sys.__excepthook__(exctype, value, traceback)
        sys.excepthook = my_except_hook

    # 输出现有结果
    def finalize(self):
        # 可以添加自定义打印代码，把想要的进度打印为json
        progress_json = os.path.join(self.base_path, f"{self.progress_filename}.json")
        with open(progress_json, 'w') as f:
            json.dump(self.GLOBAL_STATE['stats'], f, indent=4)
        self.backup_progress()


    def mp_run(self, args_list: list[RunInfo], process_count):
        start = time.time()
        # 启动docker monitor
        mon_proc = subprocess.Popen(["python3", f"{script_dir}/docker_mem_monitor.py"], cwd=self.base_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        queues = [None for i in range(process_count)]
        processes = [None for i in range(process_count)]
        try:
            for i in range(process_count):
                if len(args_list) > 0:
                    queues[i] = Queue()
                    processes[i] = self.create_process(queues[i], args_list.pop(0))
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
                            self.handle_result(result)
                        if len(args_list) > 0:
                            queues[i] = Queue()
                            # create_and_start_subprocess(args, queue: Queue)
                            processes[i] = self.create_process(queues[i], args_list.pop(0))
                        else:
                            processes[i] = None
                            queues[i] = None
                        break
                else:
                    time.sleep(1)
        # except KeyboardInterrupt:
        #     # 如果遇到异常，则终止所有进程并finalize
        #     for i in range(process_count):
        #         process = processes[i] #type: Process
        #         if process != None:
        #             # TODO how to terminate
        #             process.terminate()
        finally:
            self.finalize()
        mon_proc.send_signal(signal.SIGINT)
        mon_proc.wait()
        dura = time.time() - start
        print(f'all dockers spent {dura}s')

    # ===========用户编写的部分 ========== TODO

    # https://stackoverflow.com/a/10217089
    # 返回一个已经启动的进程
    def create_process(self, queue, run_info):
        process = Process(target=call_it, args=(self, 'docker_daemon_wrapper', (queue, run_info)))
        process.start()
        return process

    # suffix里可以包含--rm选项，防止占用过多空间
    
    # 先用docker run命令启动，同时捕获输入输出
    # 超时的时候用docker stop命令杀掉。
    # stdout_file_path_prefix为标准输出文件前缀，会在后面加上.stdout.txt和.stderr.txt
    def docker_daemon(self, queue, container_name, run_cmd_suffix, stdout_file_path_prefix=None, timeout=None):
        docker_run_cmd_template = 'docker run -i --name {} {}' # .format(container_name, run_cmd_suffix)
        cmd = docker_run_cmd_template.format(container_name, run_cmd_suffix)
        print(repr(cmd))
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
            subprocess.run(f"docker kill {container_name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            duration = timeout
        except KeyboardInterrupt:
            print(f"docker kill {container_name}")
            subprocess.run(f"docker kill {container_name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            raise
        finally:
            if stdout_file_path_prefix:
                stdout_file.close()
                stderr_file.close()
        return container_name, duration, proc.poll()

    def handle_result(self, result):
        self.GLOBAL_STATE['stats'][result[0]] = result[1:]

    # docker run -v $apk_path:/apk -v $result_folder:/out ns
    def docker_daemon_wrapper(self, queue, run_info: RunInfo):
        run_info.before_run_hook()
        ret = self.docker_daemon(queue, run_info.container_name, run_info.run_cmd_suffix, run_info.stdout_file_path_prefix, run_info.TIMEOUT)
        queue.put(ret) # 返回值传回父进程，再保存
        run_info.after_run_hook()

# 负责攒参数，然后传给mp_run
# def main(self, process_count):
#     file_paths = []
#     for file in os.listdir(dataset_path):
#         if not file.endswith('.apk'):
#             continue
#         fpath = os.path.join(dataset_path, file)
#         # 保存进度
#         # 存在已保存的结果，且结果文件夹未被删除才跳过
#         if self.container_name_template.format(file) in GLOBAL_STATE['stats'] and os.path.exists(os.path.join(out_dataset_path, file)):
#             continue
#         file_paths.append(fpath)
#     file_paths.sort()
#     if not os.path.exists(out_dataset_path):
#         os.makedirs(out_dataset_path, exist_ok=True)
#     self.mp_run(file_paths, process_count, out_dataset_path)

if __name__ == '__main__':
    # main(1)
    pass
    
