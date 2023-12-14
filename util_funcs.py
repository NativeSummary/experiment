# usage:
# file_path = os.path.realpath(__file__)
# elem = 'experiment'
# module_path = file_path[:file_path.rfind(elem)+len(elem)]
# sys.path.insert(1, module_path)

import pickle, re, os,sqlite3,json

## ============ database related ==========

def connect_and_cursor(dbpath):
    con = sqlite3.connect(dbpath)
    cur = con.cursor()
    return con, cur

DATABASE_NAME = 'native_summary.db'
SQL_TOOL_RUN_CREATE = '''
CREATE TABLE IF NOT EXISTS ToolRunStat (
    id INTEGER PRIMARY KEY,
    tool_name TEXT,
    apk_name TEXT,
    apk_dataset TEXT,
    is_success INTEGER,
    total_time REAL,
    total_mem REAL,
    flow_count INTEGER,
    flow_content TEXT,
    j2n_find_count INTEGER,
    j2n_success_count INTEGER,
    n2j_find_count INTEGER,
    n2j_success_count INTEGER,
    native_related_flow_count INTEGER,
    ns_time_info TEXT,
    CONSTRAINT tool_name_unique UNIQUE (tool_name, apk_name)
);'''
# is_success: 1 - success, 0 - failed, 2 - timeout


## ========= match statictics using unix `time` command

# return in seconds
def convert_time(ts) -> float:
    return sum(float(x.strip()) * 60 ** i for i, x in enumerate(reversed(ts.split(':'))))

def match_unix_time(path):
    path = os.path.join(path, 'stderr.txt')
    return convert_time( match_in_file(r'Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): (.*)$', path)[0] )

# return in bytes
def match_unix_time_mem(path):
    path = os.path.join(path, 'stderr.txt')
    return int( match_in_file(r'Maximum resident set size \(kbytes\): (.*)$', path)[0] ) * 1000

def match_unix_time_file(path):
    return convert_time( match_in_file(r'Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): (.*)$', path)[0] )

# return in bytes
def match_unix_time_mem_file(path):
    return int( match_in_file(r'Maximum resident set size \(kbytes\): (.*)$', path)[0] ) * 1000


##========== file operations ==============

def line_match_first(pat, path):
    with open(path, 'r') as f:
        for line in f:
            if ret := re.findall(pat, line):
                return ret

def match_in_file(pat, path):
    return re.findall(pat, read_file(path), re.MULTILINE)

def load_obj(path):
    with open(path, "rb") as f:
        return pickle.load(f)

def load_json(path):
    with open(path, "rb") as f:
        return json.load(f)

def dump_obj(path, data):
    with open(path, "wb") as f:
        pickle.dump(data, f)

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def read_file_bytes(path):
    with open(path, 'rb') as f:
        return f.read()

def load_py_file(path):
    with open(path, 'r') as f:
        return eval(f.read())

def match_in_str(pat, s):
    import re
    return re.findall(pat, s, re.MULTILINE)

def match_in_file(pat, path):
    import re
    return re.findall(pat, read_file(path), re.MULTILINE)

def match_in_file_bytes(pat, path):
    import re
    return re.findall(pat, read_file_bytes(path), re.MULTILINE)

## ======= other ==========

def average(lst):
    return sum(lst) / len(lst)
