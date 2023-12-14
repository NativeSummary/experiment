
import json
import os,shutil,sys


TIMEOUT = 7200.0

fd_dataset_path = '/home/user/ns/dataset/fd-filter'
fd_out_dataset_path = '/home/user/ns/experiment/amandroid/fdroid-results'

malradar_dataset_path = '/home/user/ns/dataset/malradar-filter'
malradar_out_dataset_path = '/home/user/ns/experiment/amandroid/malradar-results'

nfbe_dataset_path = '/home/user/ns/dataset/nfbe'
nfbe_out_dataset_path = '/home/user/ns/experiment/amandroid/nfbe-results'

nfbe_repacked_dataset_path = '/home/user/ns/dataset/nfbe-repacked'
nfbe_repacked_out_dataset_path = '/home/user/ns/experiment/amandroid/nfbe-repacked-results'

nfb_repacked_dataset_path = '/home/user/ns/dataset/nfb-repacked'
nfb_repacked_out_dataset_path = '/home/user/ns/experiment/amandroid/nfb-repacked-results'

jucifybench_repacked_dataset_path = '/home/user/ns/dataset/jucifybench-repacked'
jucifybench_repacked_out_dataset_path = '/home/user/ns/experiment/amandroid/jucifybench-repacked-results'

# command_template = 'docker run --cpus=1 --mem=128G --rm -v $RES_DIR:/root/apps/ nativesummary/jnsaf:3.2.1 /root/apps/$1'

target = 'jucifybench-repacked'
print(f"current target: {target}", file=sys.stderr)

if target == 'fdroid':
    dataset_path = fd_dataset_path
    out_dataset_path = fd_out_dataset_path
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
else:
    dataset_path = None
    out_dataset_path = None


is_repacked = target.endswith("repacked")
# def_ss_file = '/home/user/ns/experiment/baseline-fd/ss.txt'

def main():
    files = []
    for file in os.listdir(dataset_path):
        fpath = os.path.join(dataset_path, file)
        if not file.endswith('.apk'):
            continue
        if is_repacked:
            if not os.path.exists(fpath + '.sources-sinks.txt'):
                exit(-1)
            ss_file = fpath + '.sources-sinks.txt'
        else:
            ss_file = None
        files.append((fpath, ss_file))
    files.sort(key=lambda x:x[0])
    if not os.path.exists(out_dataset_path):
        os.makedirs(out_dataset_path, exist_ok=True)
    for fpath, ss_file in files:
        analyze_one(fpath, ss_file)

def analyze_one(fpath, ss_file):
    fname = os.path.basename(fpath)
    out_path = os.path.join(out_dataset_path, fname)
    if os.path.exists(out_path):
        shutil.rmtree(out_path)
    os.makedirs(out_path, exist_ok=True)
    # ss_file = convert_ss_file(out_path, ss_file)
    # config_file = gen_run_config(fpath, out_path, ss_file)
    run_tool(out_path, fpath)

redir_output_template = '{} | tee {}'
limit_cmd_template = 'systemd-run --scope --same-dir --collect -p MemoryMax=32G -p CPUQuota=100% bash -c "{}"' #  --wait
time_cmd_template = '/usr/bin/time -v /usr/bin/timeout 2h {} 1> {} 2> {}'
# cpulimit_cmd_template = 'cpulimit -l 2000 -- {}'
# limit_cmd_template = 'cpulimit -l 2000 -- /usr/bin/time -v {}'
tool_cmd_template = 'java -jar /home/user/ns/tools/amandroid/argus-saf-3.2.1-SNAPSHOT-assembly.jar taint -o {} {}'
def run_tool(out_path, apk_path):
    stdout_path = os.path.join(out_path, 'stdout.txt')
    stderr_path = os.path.join(out_path, 'stderr.txt')
    # cmds
    tool_cmd = tool_cmd_template.format(out_path, apk_path)
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
