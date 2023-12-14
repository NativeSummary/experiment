
# 杀掉CPU占用小于1%的jnsaf docker
import json
import subprocess
import os
import time
import pickle
import humanfriendly
import collections


SPARE_TIMES = 100
low_count = collections.defaultdict(lambda:0)

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

def main():
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
        pass
        # backup_progress('.')

def handle_stat(stat):
    name = stat['name']
    if not name.startswith('jn-saf-'):
        return
    mem_str = stat['mem'].split('/')[0].strip()
    cpu_str = stat['cpu'].removesuffix('%')
    if mem_str == '--' or cpu_str == '--':
        return
    mem = humanfriendly.parse_size(mem_str, binary=True)
    cpu = float(cpu_str)
    if cpu < 1:
        print(f'name: {name}, mem: {mem}, cpu: {cpu}')
        low_count[name] += 1
        if low_count[name] > SPARE_TIMES:
            kill_docker(name)
            low_count[name] = 0
    else:
        low_count[name] = 0
    # state = GLOBAL_STATE['stats']
    # if name not in state:
    #     state[name] = [0, 0.0]
    # # 记录最大值
    # if mem > state[name][0]:
    #     print(f'name: {name}, mem: {mem}, cpu: {cpu}')
    #     state[name][0] = mem
    # if cpu > state[name][1]:
    #     state[name][1] = cpu

def kill_docker(name):
    print(f'killing {name}.')
    os.system(f'docker kill {name}')
    time.sleep(1)

if __name__ == '__main__':
    start = time.time()
    # restore_progress('.')
    main()
    dura = time.time() - start
    print(f'duration: {dura}s')
