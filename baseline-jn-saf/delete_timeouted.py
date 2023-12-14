import os,sys,re,pickle,shutil

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def load_obj(path):
    with open(path, "rb") as f:
        return pickle.load(f)

def match_in_file(pat, path):
    return re.findall(pat, read_file(path), re.MULTILINE)

def match_timeout(path):
    path = os.path.join(path, 'docker_runner.stderr.txt')
    return len(match_in_file(r'can not finish', path)) > 0


BASE = '/home/user/ns/experiment/baseline-jn-saf'
def collect(target):
    rpath = os.path.join(BASE, f'{target}-results')
    for file in os.listdir(rpath):
        fpath = os.path.join(rpath, file)
        if not file.endswith('.apk'):
            continue
        if match_timeout(fpath):
            print(f"delete: {file}")
            shutil.rmtree(fpath)

if __name__ == '__main__':
    collect('malradar')
