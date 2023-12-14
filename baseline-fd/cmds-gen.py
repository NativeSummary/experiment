#!/usr/bin/python3
import json
import os,shutil,sys

script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
parent_dir = os.path.dirname(script_dir)
sys.path.insert(1, parent_dir)

from util_funcs import match_unix_time, match_in_file

TIMEOUT = 7200.0

fdroid_dataset_path = '/home/user/ns/dataset/fd-filter'
fdroid_out_dataset_path = '/home/user/ns/experiment/baseline-fd/fdroid-results'

malradar_dataset_path = '/home/user/ns/dataset/malradar-filter'
malradar_out_dataset_path = '/home/user/ns/experiment/baseline-fd/malradar-results'

nfbe_dataset_path = '/home/user/ns/dataset/nfbe'
nfbe_out_dataset_path = '/home/user/ns/experiment/baseline-fd/nfbe-results'

nfbe_dataset_path = '/home/user/ns/dataset/nfbe'
nfbe_out_dataset_path = '/home/user/ns/experiment/baseline-fd/nfbe-results'

nfbe_repacked_dataset_path = '/home/user/ns/dataset/nfbe-repacked'
nfbe_repacked_out_dataset_path = '/home/user/ns/experiment/baseline-fd/nfbe-repacked-results'

nfb_repacked_dataset_path = '/home/user/ns/dataset/nfb-repacked'
nfb_repacked_out_dataset_path = '/home/user/ns/experiment/baseline-fd/nfb-repacked-results'

jucifybench_repacked_dataset_path = '/home/user/ns/dataset/jucifybench-repacked'
jucifybench_repacked_out_dataset_path = '/home/user/ns/experiment/baseline-fd/jucifybench-repacked-results'

fdroid_repacked_dataset_path = '/home/user/ns/dataset/fdroid-repacked'
fdroid_repacked_out_dataset_path = '/home/user/ns/experiment/baseline-fd/fdroid-repacked-results'

malradar_repacked_dataset_path = '/home/user/ns/dataset/malradar-repacked'
malradar_repacked_out_dataset_path = '/home/user/ns/experiment/baseline-fd/malradar-repacked-results'

intersect_dataset_path = '/home/user/ns/dataset/intersect'
intersect_out_dataset_path = '/home/user/ns/experiment/baseline-fd/intersect-results'


target = 'none'
dataset_path = None
out_dataset_path = None
is_repacked = None


def set_target(target_):
    global target
    global dataset_path
    global out_dataset_path
    global is_repacked
    target = target_
    is_repacked = target.endswith("repacked")
    print(f"current target: {target}", file=sys.stderr)

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
    else:
        dataset_path = None
        out_dataset_path = None


    
def_ss_file = '/home/user/ns/experiment/baseline-fd/ss_taintbench.txt'

def main():
    files = []
    for file in os.listdir(dataset_path):
        fpath = os.path.join(dataset_path, file)
        if not file.endswith('.apk'):
            continue
        # if not (file < '3'):
        #     continue
        if is_repacked:
            if not os.path.exists(fpath + '.sources-sinks.txt'):
                exit(-1)
            ss_file = fpath + '.sources-sinks.txt'
        else:
            ss_file = def_ss_file
        files.append((fpath, ss_file))
    files.sort(key=lambda x:x[0])
    if not os.path.exists(out_dataset_path):
        os.makedirs(out_dataset_path, exist_ok=True)
    for fpath, ss_file in files:
        analyze_one(fpath, ss_file)

def already_running(apk_name):
    return os.system(f"pgrep -f [{apk_name[0]}]{apk_name[1:]}") == 0

def done_running(out_path, apk_path):
    xml_name = os.path.basename(apk_path) #type: str
    xml_name = xml_name.removesuffix('.apk')+'.xml'
    if os.path.exists(os.path.join(out_path, xml_name)):
        return True
    else:
        try:
            runned_time = match_unix_time(out_path)
        except IndexError:
            print(f'failed to get wall clock time for {out_path}', file=sys.stderr)
            return False
        except FileNotFoundError:
            return False
        if runned_time >= 7190:
            print(f"Timed out: {out_path}", file=sys.stderr)
            return True
        elif match_in_file(r'The data flow analysis has failed', os.path.join(out_path, 'stderr.txt')):
            print(f"errored: {runned_time}", file=sys.stderr)
            # shutil.rmtree(out_path)
            return True
        elif match_in_file(r'Command terminated by signal', os.path.join(out_path, 'stderr.txt')):
            print(f"terminated: {runned_time}", file=sys.stderr)
            return True
        else:
            print(f"not timed out:{runned_time}", file=sys.stderr)
            return False


def analyze_one(fpath, ss_file):
    fname = os.path.basename(fpath)
    out_path = os.path.join(out_dataset_path, fname)
    if done_running(out_path, fpath):
        print(f"skip {fname}.", file=sys.stderr)
        return
    if already_running(fname):
        print(f"already_running {fname}.", file=sys.stderr)
        return
    # if os.path.exists(out_path):
    #     shutil.rmtree(out_path)
    os.makedirs(out_path, exist_ok=True)
    # ss_file = convert_ss_file(out_path, ss_file)
    # config_file = gen_run_config(fpath, out_path, ss_file)
    print(f"analyzing: {os.path.basename(fpath)}", file=sys.stderr)
    run_tool(out_path, fpath, ss_file)

redir_output_template = '{} | tee {}'
# https://github.com/systemd/systemd/issues/3744
limit_cmd_template = 'systemd-run --scope --same-dir --collect -p MemoryMax=32G -p CPUQuota=100% bash -c "{}"' #  --wait
time_cmd_template = '/usr/bin/time -v /usr/bin/timeout --kill-after=60s 2h {} 1> {} 2> {}' #  4h
# cpulimit_cmd_template = 'cpulimit -l 2000 -- {}'
# limit_cmd_template = 'cpulimit -l 2000 -- /usr/bin/time -v {}'
tool_cmd_template = '/usr/lib/jvm/java-17-openjdk-amd64/bin/java -jar /home/user/ns/tools/flowdroid-2.10/soot-infoflow-cmd-jar-with-dependencies.jar -pa CONTEXTSENSITIVE -pr PRECISE -ps -sf CONTEXTFLOWSENSITIVE --maxthreadnum 1 --mergedexfiles -s {} -p /home/user/ns/tools/platforms -o {} -a {}'
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
    set_target('fdroid-repacked')
    main()
    set_target('malradar-repacked')
    main()
    print(f"{' '.join(sys.argv)} | sudo xargs -0 -I CMD --max-procs=1 bash -c CMD", file=sys.stderr)
    # sudo pkill -f 
