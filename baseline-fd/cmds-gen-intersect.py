
import json
import os,shutil,sys,pickle

import mem_time_collector

TIMEOUT = 7200.0

fdroid_dataset_path = '/home/user/ns/dataset/fd-filter'
fdroid_out_dataset_path = '/home/user/ns/experiment/baseline-fd/intersect-fdroid-results'

malradar_dataset_path = '/home/user/ns/dataset/malradar-filter'
malradar_out_dataset_path = '/home/user/ns/experiment/baseline-fd/intersect-malradar-results'

# nfbe_dataset_path = '/home/user/ns/dataset/nfbe'
# nfbe_out_dataset_path = '/home/user/ns/experiment/baseline-fd/nfbe-results'

# nfbe_dataset_path = '/home/user/ns/dataset/nfbe'
# nfbe_out_dataset_path = '/home/user/ns/experiment/baseline-fd/nfbe-results'

# nfbe_repacked_dataset_path = '/home/user/ns/dataset/nfbe-repacked'
# nfbe_repacked_out_dataset_path = '/home/user/ns/experiment/baseline-fd/nfbe-repacked-results'

# nfb_repacked_dataset_path = '/home/user/ns/dataset/nfb-repacked'
# nfb_repacked_out_dataset_path = '/home/user/ns/experiment/baseline-fd/nfb-repacked-results'

# jucifybench_repacked_dataset_path = '/home/user/ns/dataset/jucifybench-repacked'
# jucifybench_repacked_out_dataset_path = '/home/user/ns/experiment/baseline-fd/jucifybench-repacked-results'

fdroid_repacked_dataset_path = '/home/user/ns/dataset/fdroid-repacked'
fdroid_repacked_out_dataset_path = '/home/user/ns/experiment/baseline-fd/intersect-fdroid-repacked-results'

malradar_repacked_dataset_path = '/home/user/ns/dataset/malradar-repacked'
malradar_repacked_out_dataset_path = '/home/user/ns/experiment/baseline-fd/intersect-malradar-repacked-results'

intersect_dataset_path = '/home/user/ns/dataset/intersect'
intersect_out_dataset_path = '/home/user/ns/experiment/baseline-fd/intersect-results'

# intersect_repacked_dataset_path = None
# intersect_repacked_out_dataset_path = '/home/user/ns/experiment/baseline-fd/intersect-repacked-results'


# command_template = 'docker run --cpus=1 --mem=128G --rm -v $RES_DIR:/root/apps/ nativesummary/jnsaf:3.2.1 /root/apps/$1'


dataset_path = None
out_dataset_path = None
is_repacked = None

def set_dataset_paths(target):
    global dataset_path
    global out_dataset_path
    global is_repacked
    print(f"current target: {target}", file=sys.stderr)
    is_repacked = target.endswith("repacked")
    if target == 'fdroid':
        dataset_path = fdroid_dataset_path
        out_dataset_path = fdroid_out_dataset_path
    elif target == 'malradar':
        dataset_path = malradar_dataset_path
        out_dataset_path = malradar_out_dataset_path
    elif target == 'nfbe':
        dataset_path = nfbe_dataset_path
        out_dataset_path = nfbe_out_dataset_path
    elif target == 'nfbe-repacked':
        dataset_path = nfbe_repacked_dataset_path
        out_dataset_path = nfbe_repacked_out_dataset_path
    elif target == 'nfb-repacked':
        dataset_path = nfb_repacked_dataset_path
        out_dataset_path = nfb_repacked_out_dataset_path
    elif target == 'jucifybench-repacked':
        dataset_path = jucifybench_repacked_dataset_path
        out_dataset_path = jucifybench_repacked_out_dataset_path
    elif target == 'fdroid-repacked':
        dataset_path = fdroid_repacked_dataset_path
        out_dataset_path = fdroid_repacked_out_dataset_path
    elif target == 'malradar-repacked':
        dataset_path = malradar_repacked_dataset_path
        out_dataset_path = malradar_repacked_out_dataset_path
    elif target == 'intersect':
        dataset_path = intersect_dataset_path
        out_dataset_path = intersect_out_dataset_path
    elif target == 'intersect-repacked':
        dataset_path = intersect_repacked_dataset_path
        out_dataset_path = intersect_repacked_out_dataset_path
    else:
        raise RuntimeError(f'unknown target {target}')
        dataset_path = None
        out_dataset_path = None



# def_ss_file = '/home/user/ns/experiment/baseline-fd/ss.txt'

# 分析成功的交集
# with open('../manual-audit/intersec-2.pickel', "rb") as f:
#     intersec = pickle.load(f) #type: set

def main(target):
    set_dataset_paths(target)
    files = []
    # if target == 'intersect-repacked':
    #     files_to_iter = os.listdir(fdroid_repacked_dataset_path) + os.listdir(malradar_repacked_dataset_path)
    # else:
    files_to_iter = os.listdir(dataset_path)
    for file in files_to_iter:
        fpath = os.path.join(dataset_path, file)
        if not file.endswith('.apk'):
            continue
        # if is_repacked:
        #     if not os.path.exists(fpath + '.sources-sinks.txt'):
        #         exit(-1)
        #     ss_file = fpath + '.sources-sinks.txt'
        # else:
        #     ss_file = def_ss_file
        # ss_file = '/home/user/ns/experiment/baseline-fd/ss.txt'
        ss_file = '/home/user/ns/experiment/baseline-fd/ss_taintbench.txt'
        # if target not in ['fdroid-repacked', 'malradar-repacked', 'intersect']:
        #     print("ERROR: dataset not supported.", file=sys.stderr)
        #     exit(-1)
        # if is_repacked:
        #     prev_target = target.removesuffix('-repacked')
        #     if (prev_target, file) not in intersec:
        #         print(f"skip {file}: not in intersect.", file=sys.stderr)
        #         continue
        files.append((fpath, ss_file))
    files.sort(key=lambda x:x[0])
    if not os.path.exists(out_dataset_path):
        os.makedirs(out_dataset_path, exist_ok=True)
    for fpath, ss_file in files:
        analyze_one(fpath, ss_file)

def done_running(out_path, apk_path):
    xml_name = os.path.basename(apk_path) #type: str
    xml_name = xml_name.removesuffix('.apk')+'.xml'
    if os.path.exists(os.path.join(out_path, xml_name)):
        return True
    try:
        if os.path.exists(os.path.join(out_path, 'stderr.txt')):
            if mem_time_collector.match_unix_time(out_path) >= 3600:
                return True
    except IndexError:
        pass
    return False

def analyze_one(fpath, ss_file):
    fname = os.path.basename(fpath)
    out_path = os.path.join(out_dataset_path, fname)
    if done_running(out_path, fpath):
        print(f"skip {fname}.", file=sys.stderr)
        return
    if os.path.exists(out_path):
        shutil.rmtree(out_path)
    os.makedirs(out_path, exist_ok=True, mode=0o777)
    # 构建ss文件
    ss = shutil.copy(ss_file, out_path)
    if is_repacked:
        additional_ss = f"/home/user/ns/experiment/baseline-native_summary/{target.removesuffix('-repacked')}-results/{os.path.basename(fpath)}/repacked_apks/apk.sinks.txt"
        additional_ss = read_file(additional_ss)
        with open(ss, 'a') as f:
            f.write('\n');f.write(additional_ss)
    # ss_file = convert_ss_file(out_path, ss_file)
    # config_file = gen_run_config(fpath, out_path, ss_file)
    run_tool(out_path, fpath, ss)

redir_output_template = '{} | tee {}'
# https://github.com/systemd/systemd/issues/3744
limit_cmd_template = 'systemd-run --scope --same-dir --collect -p MemoryMax=8G -p CPUQuota=800% bash -c "{}"' #  --wait
# for labcmp server
limit_cmd_template = 'sudo systemd-run --scope --same-dir --collect -p MemoryMax=8G -p CPUQuota=800% --uid=1000 bash -c "{}"' #  --wait #  --no-ask-password 
time_cmd_template = '/usr/bin/time -v /usr/bin/timeout 1h {} 1> {} 2> {}' #  4h
# cpulimit_cmd_template = 'cpulimit -l 2000 -- {}'
# limit_cmd_template = 'cpulimit -l 2000 -- /usr/bin/time -v {}'
tool_cmd_template = 'java -jar /home/user/ns/tools/flowdroid-2.10/soot-infoflow-cmd-jar-with-dependencies.jar --maxthreadnum 1 --mergedexfiles --pathreconstructionmode PRECISE -s {} -p /home/user/ns/tools/platforms -o {} -a {}'
def run_tool(out_path, apk_path, ss_file):
    stdout_path = os.path.join(out_path, 'stdout.txt')
    stderr_path = os.path.join(out_path, 'stderr.txt')
    # cmds
    tool_cmd = tool_cmd_template.format(ss_file, out_path, apk_path)
    # tool_cmd = "sleep 5s"
    time_cmd = time_cmd_template.format(tool_cmd, stdout_path, stderr_path)
    limit_cmd = limit_cmd_template.format(time_cmd)
    print(limit_cmd, end='\x00')

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

if __name__ == '__main__':
    targets = ['fdroid', 'malradar', 'fdroid-repacked', 'malradar-repacked']
    for target in targets:
        main(target)
    print(f"{' '.join(sys.argv)} | sudo xargs -0 -I CMD --max-procs=1 bash -c CMD", file=sys.stderr)
