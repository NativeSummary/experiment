#!/usr/bin/python3
import json
import os,shutil,sys

script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
parent_dir = os.path.dirname(script_dir)
sys.path.insert(1, parent_dir)

# from util_funcs import match_unix_time, match_in_file

def match_in_file(pat, path):
    import re
    return re.findall(pat, read_file(path), re.MULTILINE)

# return in seconds
def convert_time(ts) -> float:
    return sum(float(x.strip()) * 60 ** i for i, x in enumerate(reversed(ts.split(':'))))

def match_unix_time(path):
    path = os.path.join(path, 'stderr.txt')
    return convert_time( match_in_file(r'Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): (.*)$', path)[0] )


TIMEOUT = 7200.0

fdroid_dataset_path = '/home/user/ns2/dataset/fd-filter'
fdroid_out_dataset_path = '/home/user/ns2/experiment/baseline-fd/fdroid-results'

malradar_dataset_path = '/home/user/ns2/dataset/malradar-filter'
malradar_out_dataset_path = '/home/user/ns2/experiment/baseline-fd/malradar-results'

fdroid_repacked_dataset_path = '/home/user/ns2/dataset/fdroid-repacked'
fdroid_repacked_out_dataset_path = '/home/user/ns2/experiment/baseline-fd/fdroid-repacked-results'

malradar_repacked_dataset_path = '/home/user/ns2/dataset/malradar-repacked'
malradar_repacked_out_dataset_path = '/home/user/ns2/experiment/baseline-fd/malradar-repacked-results'


# command_template = 'docker run --cpus=1 --mem=128G --rm -v $RES_DIR:/root/apps/ nativesummary/jnsaf:3.2.1 /root/apps/$1'

target = 'fdroid-repacked'
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


is_repacked = target.endswith("repacked")
def_ss_file = '/home/user/ns2/experiment/baseline-fd/ss_taintbench.txt'

def main():
    files = []
    for file in os.listdir(dataset_path):
        fpath = os.path.join(dataset_path, file)
        if not file.endswith('.apk'):
            continue
        # if not (file < 'c'):
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
    # if os.path.exists(out_path):
    #     shutil.rmtree(out_path)
    os.makedirs(out_path, exist_ok=True)
    # ss_file = convert_ss_file(out_path, ss_file)
    # config_file = gen_run_config(fpath, out_path, ss_file)
    print(f"analyzing: {os.path.basename(fpath)}", file=sys.stderr)
    run_tool(out_path, fpath, ss_file)

redir_output_template = '{} | tee {}'
# https://github.com/systemd/systemd/issues/3744
limit_cmd_template = 'systemd-run --scope --same-dir --collect -p MemoryMax=6G -p CPUQuota=100% bash -c "{}"' #  --wait
time_cmd_template = '/usr/bin/time -v /usr/bin/timeout --kill-after=60s 2h {} 1> {} 2> {}' #  4h
# cpulimit_cmd_template = 'cpulimit -l 2000 -- {}'
# limit_cmd_template = 'cpulimit -l 2000 -- /usr/bin/time -v {}'
tool_cmd_template = '/usr/lib/jvm/java-17-openjdk-amd64/bin/java -jar /home/user/ns2/tools/flowdroid-2.10/soot-infoflow-cmd-jar-with-dependencies.jar --maxthreadnum 1 --mergedexfiles -s {} -p /home/user/ns2/tools/platforms -o {} -a {}'
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
    main()
    print(f"{' '.join(sys.argv)} | sudo xargs -0 -I CMD --max-procs=1 bash -c CMD", file=sys.stderr)
    # sudo pkill -f 
