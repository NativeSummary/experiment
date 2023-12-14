
import json
import os,shutil,sys


TIMEOUT = 7200.0

fd_dataset_path = '/home/user/ns/dataset/fd-filter'
fd_out_dataset_path = '/home/user/ns/experiment/appshark/fdroid-results'

malradar_dataset_path = '/home/user/ns/dataset/malradar-filter'
malradar_out_dataset_path = '/home/user/ns/experiment/appshark/malradar-results'

nfbe_dataset_path = '/home/user/ns/dataset/nfbe'
nfbe_out_dataset_path = '/home/user/ns/experiment/appshark/nfbe-results'

nfbe_repacked_dataset_path = '/home/user/ns/dataset/nfbe-repacked'
nfbe_repacked_out_dataset_path = '/home/user/ns/experiment/appshark/nfbe-repacked-results'

nfb_repacked_dataset_path = '/home/user/ns/dataset/nfb-repacked'
nfb_repacked_out_dataset_path = '/home/user/ns/experiment/appshark/nfb-repacked-results'

jucifybench_repacked_dataset_path = '/home/user/ns/dataset/jucifybench-repacked'
jucifybench_repacked_out_dataset_path = '/home/user/ns/experiment/appshark/jucifybench-repacked-results'

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



run_config_template = '''{{
  "apkPath": "{}",
  "out": "{}",
  "rules": "{}",
  "maxPointerAnalyzeTime": 600,
  "configPath": "/home/user/ns/tools/appshark-0.1.2/config",
  "maxThread": 20
}}'''
rule_path = "/home/user/ns/tools/appshark-0.1.2/config/rules"

taint_config_base = '''{
  "native_summary": {
    "SliceMode": true,
    "PrimTypeAsTaint": true,
    "source": {
      "Return": [
        ]
    },
    "traceDepth": 15,
    "desc": {
      "name": "InfoFlow",
      "category": "Common",
      "detail": "no detail.",
      "wiki": "",
      "possibility": "4",
      "model": "middle"
    },
    "sink": {
      "<android.util.Log: * d(*)>": {
        "TaintCheck": [
          "p*"
        ]
      },
      "<android.util.Log: * e(*)>": {
        "TaintCheck": [
          "p*"
        ]
      },
      "<android.util.Log: * i(*)>": {
        "TaintCheck": [
          "p*"
        ]
      },
      "<android.util.Log: * w(*)>": {
        "TaintCheck": [
          "p*"
        ]
      },
      "<android.util.Log: * v(*)>": {
        "TaintCheck": [
          "p*"
        ]
      }
    }
  }
}'''

taint_sink_obj = '''{
    "TaintCheck": [
        "p*"
    ]
}'''

is_repacked = target.endswith("repacked")
def_ss_file = '/home/user/ns/experiment/baseline-fd/ss.txt'

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
            ss_file = def_ss_file
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
    ss_file = convert_ss_file(out_path, ss_file)
    config_file = gen_run_config(fpath, out_path, ss_file)
    run_tool(config_file, out_path)

redir_output_template = '{} | tee {}'
limit_cmd_template = 'systemd-run --quiet --user --scope --same-dir --collect bash -c "{}"' #  --wait
time_cmd_template = '/usr/bin/time -v {} 1> {} 2> {}'
# cpulimit_cmd_template = 'cpulimit -l 2000 -- {}'
# limit_cmd_template = 'cpulimit -l 2000 -- /usr/bin/time -v {}'
tool_cmd_template = 'java -jar /home/user/ns/tools/appshark-0.1.2/AppShark-0.1.2-all.jar {}'
def run_tool(config_file, out_path):
    stdout_path = os.path.join(out_path, 'stdout.txt')
    stderr_path = os.path.join(out_path, 'stderr.txt')
    # cmds
    tool_cmd = tool_cmd_template.format(config_file)
    time_cmd = time_cmd_template.format(tool_cmd, stdout_path, stderr_path)
    limit_cmd = limit_cmd_template.format(time_cmd)
    print(limit_cmd, end='\x00')

def convert_ss_file(out_path, ss_file):
    ss = read_file(ss_file)
    obj = convert_ss(ss)
    os.makedirs(os.path.join(out_path, "taint"))
    out_path = os.path.join(out_path, "taint", "taint_rule.json")
    write_json_file(out_path, obj)
    return out_path

def convert_ss(ss):
    ss = parse_ss(ss.split('\n'))
    base_obj = json.loads(taint_config_base)
    for sig, ty in ss:
        # print(f'{sig} is {ty}',file=sys.stderr)
        if ty == '_SOURCE_':
            base_obj["native_summary"]["source"]["Return"].append(sig)
        elif ty == '_SINK_':
            base_obj["native_summary"]["sink"][sig] = json.loads(taint_sink_obj)
        else:
            print(f'error!: Unknown Type {ty} ( {sig} )',file=sys.stderr)
            raise RuntimeError()
    return base_obj

def parse_ss(lines):
    ret = []
    for line in lines:
        line = line.strip()
        if len(line) == 0:
            continue
        if line.startswith("%"):
            continue
        parts = line.split('->', 1)
        parts = (p.strip() for p in parts)
        ret.append(parts)
    return ret

def gen_run_config(fpath, out_path, ss_file):
    ss_file = os.path.relpath(ss_file, start=rule_path)
    config_str = run_config_template.format(fpath, out_path, ss_file)
    out_path = os.path.join(out_path, "run.json5")
    write_file(out_path, config_str)
    return out_path

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def write_json_file(path, obj):
    with open(path, 'w') as f:
        json.dump(obj, f)

if __name__ == '__main__':
    main()
    print(f"{' '.join(sys.argv)} | xargs -0 -I CMD --max-procs=1 bash -c CMD", file=sys.stderr)
