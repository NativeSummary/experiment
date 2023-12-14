import os,sys,re,pickle,json, shutil


def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def match_in_file(pat, path):
    return re.findall(pat, read_file(path), re.MULTILINE)

DO_DELETE = True

NS_BASE = '/home/user/ns/experiment/baseline-native_summary'
# 2023年7月23日 delete nullpointerexception when modeling C++ stdlib external function
def inc_delete_ns(target):
    for file in sorted(os.listdir(os.path.join(NS_BASE, f'{target}-results'))):
        if not file.endswith('.apk'):
            continue
        fpath_ns = os.path.join(NS_BASE, f'{target}-results', file)
        # apk_path = os.path.join(fpath_ns, "repacked_apks", "apk")
        # if os.path.exists(apk_path):
        #     continue
        should_del = False
        for file2 in os.listdir(fpath_ns):
            if not file2.endswith('.so.log'):
                continue
            f2p = os.path.join(fpath_ns, file2)
            if match_in_file(r"decodeParams\(SummaryExporter\.java:116\)",f2p):
                should_del = True
                break
        if should_del:
            print(f"deleting: {fpath_ns}")
            if DO_DELETE:
                shutil.rmtree(fpath_ns)

if __name__ == '__main__':
    inc_delete_ns('malradar')