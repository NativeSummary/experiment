
# 方法1是用docker的API，但是每次只能获取单个container，而且每获取一个要卡2秒。所以不太行
# =======方法1 失败===========
# import docker
# try:
#     docker_client = docker.Client
# except AttributeError:
#     docker_client = docker.APIClient

# client = docker_client(base_url='unix://var/run/docker.sock')
# from operator import itemgetter
# ids = map(itemgetter('Id'), client.containers(quiet=True))
# stats = {c: client.stats(c, stream=True) for c in ids}

# import docker
# client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
# for containers in client.containers.list():
#     print(containers.stats(decode=None, stream = False))

# ======方法2 直接解析命令输出==========
# docker stats --no-stream --format '{"name": {{json .Container}}, "mem": {{json .MemUsage}}, "cpu": {{json .CPUPerc}} }'

import json
import subprocess
import os
import time
import pickle
import humanfriendly

# 跑的东西的相关名称，出现在进度文件名等处。
BRAND = 'docker_stats'

PROGRESS_FILENAME = f"{BRAND}.progress"
# 全局状态，通过pickel实现持久化
GLOBAL_STATE = {
        'stats': dict() # 从容器名映射到一个Tuple，依次是最大内存，最大CPU
    }

def restore_progress(path):
    global GLOBAL_STATE
    prog_file = os.path.join(path, PROGRESS_FILENAME)
    if os.path.exists(prog_file):
        print("load previous progress")
        with open(prog_file, "rb") as f:
            GLOBAL_STATE = pickle.load(f)

def backup_progress(path):
    json_file = os.path.join(path, PROGRESS_FILENAME+'.json')
    with open(json_file, "w") as f:
        json.dump(GLOBAL_STATE, f)
    prog_file = os.path.join(path, PROGRESS_FILENAME)
    with open(prog_file, "wb") as f:
        pickle.dump(GLOBAL_STATE, f)

def get_stats():
    lines = subprocess.check_output("docker stats --no-trunc --no-stream --format".split(' ')+['{"name": {{json .Name}}, "mem": {{json .MemUsage}}, "cpu": {{json .CPUPerc}} }'])
    lines = lines.removesuffix(b'\n')
    ret = []
    for line in lines.split(b'\n'):
        stat = json.loads(line)
        ret.append(stat)
    return ret

def get_stats_stream():
    process = subprocess.Popen("docker stats --no-trunc --format".split(' ')+['{"name": {{json .Name}}, "mem": {{json .MemUsage}}, "cpu": {{json .CPUPerc}} }']
                                 , stdout=subprocess.PIPE)
    return process.stdout

def escape(text):
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def docker_monitor_main(base_path='.'):
    restore_progress(base_path)
    try:
        stream = get_stats_stream()
        for line in iter(stream.readline, ""):
            stat = json.loads(escape(line.decode()))
            try:
                handle_stat(stat)
            except Exception:
                print(f"handle failed, stat: {stat}")
                raise
    except KeyboardInterrupt:
        pass
    finally:
        backup_progress(base_path)

def handle_stat(stat):
    name = stat['name']
    mem_str = stat['mem'].split('/')[0].strip()
    cpu_str = stat['cpu'].removesuffix('%')
    if mem_str == '--' or cpu_str == '--':
        return
    mem = humanfriendly.parse_size(mem_str, binary=True)
    cpu = float(cpu_str)
    # print(f'name: {name}, mem: {mem}, cpu: {cpu}')
    state = GLOBAL_STATE['stats']
    if name not in state:
        state[name] = [0, 0.0]
    # 记录最大值
    if mem > state[name][0]:
        print(f'name: {name}, mem: {mem}, cpu: {cpu}')
        state[name][0] = mem
    if cpu > state[name][1]:
        state[name][1] = cpu


if __name__ == '__main__':
    start = time.time()
    docker_monitor_main()
    dura = time.time() - start
    print(f'duration: {dura}s')
