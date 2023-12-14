#!/usr/bin/python3
import json
import os,sys
import shutil
import time
from multiprocessing import Process, Queue
import subprocess
import functools

script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
parent_dir = os.path.dirname(script_dir)
sys.path.insert(1, parent_dir)

from runner_class import DockerRunner, RunInfo

TIMEOUT = 7200.0

fd_dataset_path = '/home/user/ns/dataset/fd-filter'
fd_out_dataset_path = '/home/user/ns/experiment/baseline-native_summary/fdroid-results'

malradar_dataset_path = '/home/user/ns/dataset/malradar-filter'
malradar_out_dataset_path = '/home1/user/ns/experiment/baseline-native_summary/malradar-results'

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

target = 'none'
container_name_template = f'ns-{target}'+ '-{}'

# print(f"current target: {target}")
def set_dataset_paths(cur_target):
    global target
    global dataset_path
    global out_dataset_path
    global container_name_template
    target = cur_target
    container_name_template = f'ns-{target}'+ '-{}'
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
    # elif target == 'optcompare':
    #     dataset_path = intersec_dataset_path
    #     out_dataset_path = optcompare_out_dataset_path
    # elif target == 'nooptcompare':
    #     dataset_path = malradar_dataset_path
    #     out_dataset_path = nooptcompare_out_dataset_path
    elif target == 'compare':
        dataset_path = fd_dataset_path
        out_dataset_path = compare_out_dataset_path
    else:
        dataset_path = None
        out_dataset_path = None

from mem_time_collector import line_match_first
# 对于函数覆盖率，要从jucify那边获取他的arch，然后我们和它选一样的arch
def get_jucify_arch(apk):
    result_path = os.path.join("/home/user/ns/experiment/baseline-jucify/fdroid-results", apk,"docker_runner.stdout.txt")
    return line_match_first(r"Use shared library \(i\.e\., \.so\) files from lib/(.*)/\[0m", result_path)[0]

# print(get_jucify_arch('2a1015f2bdb55b92cd708fd5979ef6d28c55c5c41ffef42703112124a335b472.apk'))
# ['armeabi']

# 跑的东西的相关名称，出现在进度文件名等处。
BRAND = 'ns'

# if target == 'nooptcompare':
#     container_name_template = 'ns-nooptcompare-{}'
# elif target == 'optcompare':
#     container_name_template = 'ns-optcompare-{}'


def before_run_temp(result_dir):
    shutil.rmtree(result_dir, ignore_errors=True)
    os.makedirs(result_dir, exist_ok=True)

def after_run_temp(result_dir):
    os.system(f'sudo chown user:user -R "{result_dir}" > /dev/null 2> /dev/null')
    os.system(f'sed -i "s/root/user/" {os.path.join(result_dir, "project", "native_summary.rep", "project.prp")} > /dev/null 2> /dev/null')

# 负责攒参数，然后传给mp_run
def main(cur_target, process_count):
    set_dataset_paths(cur_target)
    runner = DockerRunner(out_dataset_path, BRAND)
    # print(f'GLOBAL_STATE {GLOBAL_STATE}')
    file_paths = []
    for file in os.listdir(dataset_path):
        if not file.endswith('.apk'):
            continue
        fpath = os.path.join(dataset_path, file)
        container_name = container_name_template.format(file)
        result_dir = os.path.join(out_dataset_path, file)
        stdout_file_path_prefix = os.path.join(result_dir, 'docker_runner')
        run_cmd_suffix = f' --rm --cpus=1 --memory=32G -v {fpath}:/apk -v {result_dir}:/out ns'
        if target == 'compare':
            run_cmd_suffix  = ' -e GHIDRA_NS_ARGS="@@-timeout 1000" ' + run_cmd_suffix
        if target == 'nooptcompare':
            assert False
            run_cmd_suffix = ' -e GHIDRA_NS_ARGS="@@-noModel -timeout 1000" ' + run_cmd_suffix
        elif target == 'optcompare':
            assert False
            run_cmd_suffix = ' -e GHIDRA_NS_ARGS=@@-noModel ' + run_cmd_suffix

        # if target == 'nooptcompare':
        #     if not (file < '2'):
        #         continue
        if target in ['compare', 'nooptcompare', 'optcompare']:
            try:
                abi = get_jucify_arch(file)
            except FileNotFoundError:
                print(f'error: cannot get jucify arch!')
                continue
            run_cmd_suffix = f" -e NS_SELECT_ARCH={abi} " + run_cmd_suffix
        before_run = functools.partial(before_run_temp, result_dir)
        after_run = functools.partial(after_run_temp, result_dir)

        # 存在已保存的结果，且结果文件夹未被删除才跳过
        if container_name in runner.get_stats() and os.path.exists(result_dir):
            continue
        file_paths.append(RunInfo(container_name, run_cmd_suffix, TIMEOUT, stdout_file_path_prefix, before_run, after_run))
    file_paths.sort(key=lambda x:x.container_name)
    if not os.path.exists(out_dataset_path):
        os.makedirs(out_dataset_path, exist_ok=True)
    runner.mp_run(file_paths, process_count)

if __name__ == '__main__':
    main('fdroid', 60)
    main('malradar', 60)
    # main('optcompare', 75)
    # main('compare', 75)
    pass
