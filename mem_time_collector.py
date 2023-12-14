#!/usr/bin/python3
import os,sys,re,pickle,json

script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)

from util_funcs import *

if __name__ == '__main__':
    connection, cursor = connect_and_cursor(os.path.join(script_dir, DATABASE_NAME))
    cursor.execute(SQL_TOOL_RUN_CREATE)


jucify_datas = {}
jucify_star_datas = {}
fd_datas = {}
jnsaf_datas = {}
ns_datas = {}

from util_funcs import read_file, load_obj, line_match_first, match_in_file, match_unix_time, match_unix_time_mem

def get_time_in_json(brand, path):
    apk_name = os.path.basename(path)
    parent = os.path.dirname(path)
    progress = os.path.join(parent, f'{brand}.progress')
    stats = load_obj(progress)['stats']
    stat = stats[f'{brand}-{apk_name}'] # KeyError
    return stat[0]

def get_mem_in_json(key, path):
    with open(path, "rb") as f:
        state = pickle.load(f)['stats']
        return state[key][0]

FD_BASE = '/home/user/ns/experiment/baseline-fd'
def collect_fd(target):
    rpath = os.path.join(FD_BASE, f'intersect-{target}-results')
    success_count = 0
    err1_count = 0
    sql_data = []
    for file in os.listdir(rpath):
        fpath = os.path.join(rpath, file)
        if not file.endswith('.apk'):
            continue
        is_success = True
        xmlname = file.removesuffix('.apk')+'.xml'
        xmlpath = os.path.join(fpath, xmlname)
        if not os.path.exists(xmlpath): # no result
            # print(f'flowdroid: failed: {file}') # python3 ./mem_time_collector.py | wc -l
            is_success = False; xmlpath = None
        try:
            time = match_unix_time(fpath)
            mem = match_unix_time_mem(fpath)
        except FileNotFoundError:
            print(f"error: {fpath}")
            err1_count += 1
            time, mem = None, None
        fd_datas[(target, file)] = (time, mem, xmlpath)
        sql_data.append(('flowdroid', file, target, is_success, time, mem, xmlpath))
        success_count += 1
    cursor.executemany('INSERT OR REPLACE INTO ToolRunStat (tool_name, apk_name, apk_dataset, is_success, total_time, total_mem, flow_content) values(?,?,?,?,?,?,?);', sql_data)
    connection.commit()
    print(f"fd success_count {success_count} err1_count {err1_count}")

JNSAF_BASE = '/home/user/ns/experiment/baseline-jn-saf'
def collect_jnsaf(target):
    rpath = os.path.join(JNSAF_BASE, f'{target}-results')
    sql_data = []
    for file in os.listdir(rpath):
        fpath = os.path.join(rpath, file)
        if not file.endswith('.apk'):
            continue
        taint_info = get_taint_info_jnsaf(fpath)
        if len(taint_info) > 0:
            taint_info = taint_info[0]
            is_success = True
        else:
            taint_info = None
            is_success = False
            # python3 ./mem_time_collector.py | wc -l
            # print(f'jnsaf: failed: {file}')
        time = get_time_in_json('jn-saf', fpath)
        # python3 ./mem_time_collector.py > jnsaf-malradar.rerun.txt
        try:
            mem = get_mem_in_json(f'jn-saf-{file}', os.path.join(JNSAF_BASE, 'docker_stats.progress'))
        except KeyError:
            print('warn: check mem info in other progress')
            mem = get_mem_in_json(f'jn-saf-{file}', os.path.join(NS_BASE, 'docker_stats.progress'))
            # continue
        sql_data.append(('jnsaf', file, target, is_success, time, mem, taint_info))
        jnsaf_datas[(target,file)] = (time, mem, taint_info)
    cursor.executemany('INSERT OR REPLACE INTO ToolRunStat (tool_name, apk_name, apk_dataset, is_success, total_time, total_mem, flow_content) values(?,?,?,?,?,?,?);', sql_data)
    connection.commit()

def jucify_has_dot_result(path):
    file = os.path.basename(path)
    result_dir = f'{path}/{file.removesuffix(".apk")}_result'
    if os.path.exists(result_dir):
        for file in os.listdir(result_dir):
            if file.endswith('.result'): return True

JUC_BASE = '/home/user/ns/experiment/baseline-jucify'
def collect_jucify(target):
    rpath = os.path.join(JUC_BASE, f'{target}-results')
    sql_data = []
    success_count = 0
    for file in os.listdir(rpath):
        fpath = os.path.join(rpath, file)
        if not file.endswith('.apk'):
            continue
        is_success = True
        xmlpath = os.path.join(fpath, f'{file}.xml')
        if not os.path.exists(xmlpath): # no result
            # print(f'jucify: failed: {file}') # python3 ./mem_time_collector.py | wc -l
            is_success = False; xmlpath = None
        elif not jucify_has_dot_result(fpath):
            is_success = False
        try:
            time = match_unix_time_file(f"{fpath}/docker_runner.stderr.txt")
            mem = match_unix_time_mem_file(f"{fpath}/docker_runner.stderr.txt")
        except FileNotFoundError:
            print(f"error: {fpath}")
            time, mem = None, None
        except IndexError:
            print(f"fatal error: {fpath}")
            time, mem = None, None
        jucify_datas[(target, file)] = (time, mem, xmlpath)
        if is_success: success_count += 1
        sql_data.append(('jucify', file, target, is_success, time, mem, xmlpath))
    print(f'In {len(sql_data)} apps, {success_count} success.')
    cursor.executemany('INSERT OR REPLACE INTO ToolRunStat (tool_name, apk_name, apk_dataset, is_success, total_time, total_mem, flow_content) values(?,?,?,?,?,?,?);', sql_data)
    connection.commit()

# change jucify timeouts
def collect_jucify_star(target):
    rpath = os.path.join(JUC_BASE, f'{target}-results2')
    sql_data = []
    # sql_failed_data = []
    for file in os.listdir(rpath):
        fpath = os.path.join(rpath, file)
        if not file.endswith('.apk'):
            continue
        is_success = True
        xmlpath = os.path.join(fpath, f'{file}.xml')
        if not os.path.exists(xmlpath): # no result
            # print(f'jucify: failed: {file}') # python3 ./mem_time_collector.py | wc -l
            # sql_failed_data.append(('jucify*', file, target, 0))
            is_success = False
            xmlpath = None
            # continue
        # try:
        mem = get_mem_in_json(f'jucify-{file}', os.path.join(JUC_BASE, 'new_stats', 'docker_stats.progress'))
        # except KeyError:
        #     mem = get_mem_in_json(f'jucify-{file}', '/home/user/ns/tmp/2023-03-23-change-ss2/jucify/docker_stats.progress')
        time =  get_time_in_json('jucify', fpath)
        jucify_star_datas[(target, file)] = (time, mem, xmlpath)
        sql_data.append(('jucify*', file, target, is_success, time, mem, xmlpath))
    cursor.executemany('INSERT OR REPLACE INTO ToolRunStat (tool_name, apk_name, apk_dataset, is_success, total_time, total_mem, flow_content) values(?,?,?,?,?,?,?);', sql_data)
    connection.commit()


DATASET_BASE = '/home/user/ns/dataset'
NS_BASE = '/home/user/ns/experiment/baseline-native_summary'
def collect_ns(target):
    for file in os.listdir(os.path.join(DATASET_BASE, f'{target}-repacked')):
        if not file.endswith('.apk'):
            continue
        fpath_ns = os.path.join(NS_BASE, f'{target}-results', file)
        fpath_fd = os.path.join(FD_BASE, f'intersect-{target}-repacked-results', file)
        xmlname = file.removesuffix('.apk')+'.xml'
        xmlpath = os.path.join(fpath_fd, xmlname)
        flowdroid_out = os.path.join(fpath_fd, 'stderr.txt')
        if not os.path.exists(xmlpath): # no result
            # print(f'ns: flowdroid failed: {file}')
            continue
        try:
            mem = get_mem_in_json(f'ns-{file}', os.path.join(NS_BASE, 'docker_stats.progress'))
        except KeyError:
            print(f'{file}')
            continue
        flowdroid_mem = match_unix_time_mem(fpath_fd)
        time = get_time_in_json('ns', fpath_ns)
        flowdroid_time = match_unix_time(fpath_fd)
        ns_datas[(target, file)] = (time+flowdroid_time, max(mem,flowdroid_mem), xmlpath)
        # print(target,file)

def table_print():
    files = set(jucify_datas.keys())
    files.update(fd_datas.keys())
    for file in files:
        t1 = fd_datas.get(file, '  ')
        t2 = jucify_datas.get(file, '  ')
        print(f"{file}\tfd: {t1}\tjucify: {t2}")

def get_taint_info_jnsaf(p):
    # p = os.path.join(JNSAF_BASE, f'{target}-results', apkname)
    p = os.path.join(p, "docker_runner.stdout.txt")
    return re.findall(r'INFO@JNSafService:taint_result(.*)$', read_file(p), re.DOTALL)

TARGETS = ['fdroid', 'malradar']
COLLECTORS = [collect_jnsaf, collect_jucify]

def collect_all():
    # collect_fd('fdroid')
    # collect_fd('malradar')
    # collect_jnsaf('fdroid')
    # collect_jnsaf('malradar') # prom
    collect_jucify('fdroid')
    collect_jucify('malradar')
    # collect_jucify_star('fdroid')
    # collect_jucify_star('malradar')

# 
def filter_nms(its):
    ret = set()
    native_methods = load_obj("manual-audit/native-methods.pickel")
    lost = []
    for target, apk in its:
        if len(native_methods[apk]) > 0:
            ret.add((target, apk))
        else:
            lost.append((target, apk))
    print(lost)
    return ret

def dump_result():
    result = { 'jucify': jucify_datas, 'flowdroid': fd_datas,
        'jnsaf': jnsaf_datas, 'ns': ns_datas}
    # with open('mem_time_info.pickel', "wb") as f:
    #     pickle.dump(result, f)
    # with open('mem_time_info.json', 'w') as f:
    #     # json.dump(result, f, indent=4)
    #     import pprint
    #     pp = pprint.PrettyPrinter(indent=4)
    #     f.write(pp.pformat(result))

    its = set(result['ns'].keys())
    for serie in ['jnsaf', 'jucify']:
        its.intersection_update(set(result[serie].keys()))
    its = filter_nms(its) # 2023年3月28日 no native method but jni onload calls useful java methods
    print(f'{len(its)} apps in intersection')
    # with open('intersec.pickel', "wb") as f:
    #     pickle.dump(its, f)

def fix_jucify_star():
    collect_jucify_star('fdroid')
    collect_jucify_star('malradar')
    # input('update existing mem_time_info.pickel?')
    # with open('mem_time_info.pickel', "rb") as f:
    #     r = pickle.load(f)
    # r['jucify*'] = jucify_star_datas
    # with open('mem_time_info.pickel', "wb") as f:
    #     pickle.dump(r, f)

if __name__ == '__main__':
    collect_all()
    connection.close()
