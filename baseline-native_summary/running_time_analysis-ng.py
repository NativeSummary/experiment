#!/usr/bin/python3
import os,sys
import sqlite3
import shutil

script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
parent_dir = os.path.dirname(script_dir)
sys.path.insert(1, parent_dir)

from util_funcs import DATABASE_NAME, load_obj, match_in_file, read_file, connect_and_cursor, SQL_TOOL_RUN_CREATE, average, match_unix_time_mem, match_unix_time


connection, cursor = connect_and_cursor(os.path.join(parent_dir, DATABASE_NAME))

cursor.execute(SQL_TOOL_RUN_CREATE)
cursor.execute('''
CREATE TABLE IF NOT EXISTS NSTimeStat (
    id INTEGER PRIMARY KEY,
    apk_name TEXT,
    apk_dataset TEXT,
    target_mode TEXT,
    total_time_without_taint REAL,
    pre_analysis_time REAL,
    ghidra_loading REAL,
    bai_script REAL,
    java_time REAL,
    taint_analysis_time REAL,
    memory_usage REAL,
    CONSTRAINT apk_name_unique UNIQUE (apk_name, target_mode)
);
               ''')

def match_java_analysis_time(fp):
    path = os.path.join(fp, 'java_analysis.log')
    try:
        return int( match_in_file(r'Repacking spent (.*) ms.$', path)[0] ) / 1000.0
    except:
        if (match_in_file(r'StackOverflowError', path)):
            print(f"stackoverflow error")
        elif match_in_file(r'Load semantic summary failed', path):
            print('no summary.')
        elif match_in_file(r'Unexpected inner class annotation element', path):
            print('soot error.')
        elif match_in_file(r'Trying to cast reference type java\.lang\.Object to a primitive', path):
            print('soot error.')
        elif match_in_file(r'StmtSwitch: type of throw argument is not a RefType', path):
            print('soot error.')
        elif match_in_file(r'cannot set active body for phantom class', path):
            print('apk packer.')
        elif match_in_file(r'Attempt to create RefType containing', path):
            print('rm {fp}')
            # shutil.rmtree(fp)
        elif match_in_file(r'Attempt to make a class whose name starts', path):
            print('rm {fp}')
            # shutil.rmtree(fp)
        elif match_in_file(r'Invalid number of arguments', path):
            print('rm {fp}')
            # shutil.rmtree(fp)
        elif match_in_file(r'soot\.RefType cannot be cast to class soot\.ArrayType', path):
            print('rm {fp}')
            # shutil.rmtree(fp)
        else:
            print(f'Cannot get java time: {path}')
        return None


def get_so_times(fp):
    result = {}
    for file in os.listdir(fp):
        if file.endswith('.so.txt'):
            result[file.removesuffix('.txt')] = get_so_time_one(os.path.join(fp, file))
    return result

def get_so_time_one(fp):
    logf = fp.removesuffix('.so.txt')+'.so.log'
    result = {}
    try:
        result['total'] = float( read_file(fp) )
    except IndexError:
        print(f"Cannot find .so.txt for {fp}")
        raise
    try:
        result['total_script'] = int( match_in_file(r'NativeSummary script execution time: (.*)ms.', logf)[0] ) / 1000.0
    except IndexError:
        print(f"Cannot find script exec time for {logf}")
        raise
        result['total_script'] = None
    return result

# 获取main.py打印的各模块时间。
def ns_get_main_times(fp):
    ret = {} # {'pre_analysis': '2.645852565765381', 'binary_analysis': '51.62220287322998', 'java_analysis': '9.488436222076416'}
    path = os.path.join(fp, 'docker_runner.stdout.txt')
    for match in match_in_file(r'(binary_analysis|java_analysis|pre_analysis) took (.*)s\.', path):
        ret[match[0]] = match[1]
    return ret

# 获取main.py打印的总时间。
def ns_get_all_times2(fp):
    path = os.path.join(fp, 'docker_runner.stdout.txt')
    try:
        return float(match_in_file(r'NativeSummary docker script running time: (.*)$', path)[0])
    except (IndexError, FileNotFoundError):
        # print(f'get total time failed for {path}')
        # os.system(f"sudo rm -rf {fp}")
        return None

from collections import defaultdict

NS_BASE = '/home/user/ns/experiment/baseline-native_summary'
def add_dataset(dname, dpath, target=None, dry_run=False):
    global NS_BASE
    # if dname == 'malradar':
    #     NS_BASE = '/home1/user/ns/experiment/baseline-native_summary'
    # else:
    #     NS_BASE = '/home/user/ns/experiment/baseline-native_summary'
    if target is None:
        target = dname
    enable_toolrunstat = False
    if (target == dname) and dname in ['malradar', 'fdroid']:
        enable_toolrunstat = True
    runner_stats = load_obj(f'{NS_BASE}/{dname}-results/DockerRunner.progress')['stats']
    docker_stats = load_obj(f'{NS_BASE}/{dname}-results/docker_stats.progress')['stats']
    failed_count = 0
    failed_count_flowdroid = 0
    failed_count_ns = 0
    timeout_count_ns = 0
    timeout_count_fd = 0
    has_apk_count = 0
    has_xml_count = 0
    status_success_count = 0
    lost_mem = 0
    total_count = 0
    # for ToolRunStat
    sql_data = []
    # sql_failed_data = []
    # sql_timeout_data = []
    # for NSTimeStat
    detailed_time_data = []
    for file in os.listdir(dpath):
        if not file.endswith('.apk'):
            continue
        total_count += 1
        result_path = f'{NS_BASE}/{dname}-results/{file}'
        if not os.path.exists(result_path):
            print(f"not run: {file}")
            assert False
            continue

        # 从docker runner里面获取时间和内存
        total_time_without_taint_docker, ret_val = runner_stats[f'ns-{target}-{file}']
        try:
            mem, cpu = docker_stats[f'ns-{target}-{file}']
        except KeyError:
            mem = None
            lost_mem += 1
            # continue

        # 从docker的main.py里面获取时间
        total_time_without_taint = ns_get_all_times2(result_path)
        if total_time_without_taint is None:
            if total_time_without_taint_docker >= 7200.0:
                # print(f"timeout: {file}")
                timeout_count_ns += 1
                # failed_count += 1
                # continue
            else:
                # sql_failed_data.append(('ns', file, dname, 0))
                print(f'get total time failed ({total_time_without_taint_docker}) for {result_path}/docker_runner.stdout.txt')
                failed_count += 1
                assert False
                # continue

        has_apk = False
        if os.path.exists(f'{result_path}/repacked_apks/apk'):
            has_apk = True
            has_apk_count += 1

        has_xml = False
        # result_path_fd = f'/home/user/ns/experiment/baseline-fd/{target}-repacked-results/{file}'
        # taint_path_fd = f'{result_path_fd}/{file.removesuffix(".apk")}.xml'
        # if os.path.exists(taint_path_fd):
        #     has_xml_count += 1
        #     has_xml = True
        #     assert has_apk

        time_fd, mem_fd = None, None
        if has_xml:
            # assert status == 1
            try:
                time_fd = match_unix_time(result_path_fd)
                mem_fd = match_unix_time_mem(result_path_fd)
            except FileNotFoundError:
                print(f'get flowd time failed: {result_path_fd}')
                assert False
            except IndexError:
                print(f'cannot get time: {result_path_fd}/stderr.txt')
                # failed_count += 1
                assert False
                status = 0
            if time_fd > 7190:
                # assert has_xml == False, f'{result_path_fd}/stderr.txt'
                # print(f'flowdroid timeout: {result_path_fd}/stderr.txt')
                timeout_count_fd += 1
                # failed_count += 1
                # status = 0
            elif not os.path.exists(taint_path_fd):
                failed_count_flowdroid += 1
                if match_in_file(r'IndexOutOfBoundsException', f'{result_path_fd}/stderr.txt'):
                    print("flowd: wide argument error")
                elif match_in_file(r'backward analysis on an empty entry set', f'{result_path_fd}/stderr.txt'):
                    print("backward analysis on an empty entry set")
                else:
                    print(f'flowdroid failed: {result_path_fd}/stderr.txt')
        else:
            taint_path_fd = None

        status = 0
        if has_apk and has_xml:
            status = 1

        # if total_time_without_taint is None: assert time_fd is None
        total_time = None
        max_mem = None
        if status == 1:
            if total_time_without_taint is None:
                failed_count += 1
                status = 0
            elif mem is None:
                failed_count += 1
                status = 0
            else:
                total_time = total_time_without_taint+time_fd
                max_mem = max([mem_fd, mem])
                # if total_time > 7200:
                #     status = 2
        data = ('ns', file, dname, status, total_time, max_mem, taint_path_fd)
        if status == 1:
            status_success_count += 1
            assert None not in data

        sql_data.append(data)
        # 不成功就不统计平均时间。
        if status != 1:
            continue
        # 从main.py的输出里面获取详细时间
        main_times = ns_get_main_times(result_path)
        pre_analysis_time, ghidra_total_time, java_time = main_times['pre_analysis'], main_times['binary_analysis'], main_times['java_analysis']
        pre_analysis_time, ghidra_total_time, java_time = float(pre_analysis_time), float(ghidra_total_time), float(java_time)
        java_time2 = match_java_analysis_time(result_path)
        if java_time2 is None:
            # sql_failed_data.append(('ns', file, dname, 0))
            failed_count += 1
            continue
        # detailed time 包含
        # # total: runner.py写入到txt的总时间
        # # total_script: ns脚本总时间
        # # 还可以分析单个jni时间，暂时没有获取。
        try:
            detailed_time = get_so_times(result_path)
        except (IndexError, FileNotFoundError):
            # sql_failed_data.append(('ns', file, dname, 0))
            print(f'failed to get detailed time: {file}')
            failed_count += 1
            continue
        total_times = []
        script_times = []
        ghidra_load_times = []
        for so_name, so_detailed_time in detailed_time.items():
            script_times.append(so_detailed_time['total_script'])
            total_times.append(so_detailed_time['total'])
            ghidra_load_times.append(so_detailed_time['total'] - so_detailed_time['total_script'])
        # 从ghidra的时间总和到二进制分析的误差。
        diff1 = ghidra_total_time - sum(total_times)
        # 从外部总时间到里面三个时间总和的误差
        diff2 = total_time_without_taint - pre_analysis_time - ghidra_total_time - java_time
        # 外部测量的java时间和里面测量的java时间的误差
        # diff3 = java_time - java_time2
        # print(f"apk: {file}, diff1: {diff1}, diff2: {diff2}")
        assert abs(diff1) + abs(diff2) < 4.7, f'diff: {abs(diff1) + abs(diff2)}'
        # assert not assert_fail
        detailed_time_data.append((file, dname, target, total_time_without_taint, pre_analysis_time, sum(ghidra_load_times), sum(script_times), java_time, time_fd, mem))
    if not dry_run:
        if enable_toolrunstat:
            print(f'updating ToolRunStat...')
            # cursor.executemany('INSERT OR REPLACE INTO ToolRunStat (tool_name, apk_name, apk_dataset, is_success, total_time) values(?,?,?,?,?);', sql_timeout_data)
            cursor.executemany('INSERT OR REPLACE INTO ToolRunStat (tool_name, apk_name, apk_dataset, is_success, total_time, total_mem, flow_content) values(?,?,?,?,?,?,?);', sql_data)
            # cursor.executemany('INSERT OR REPLACE INTO ToolRunStat (tool_name, apk_name, apk_dataset, is_success) values(?,?,?,?);', sql_failed_data)
            connection.commit()
        cursor.executemany('INSERT OR REPLACE INTO NSTimeStat (apk_name, apk_dataset, target_mode, total_time_without_taint, pre_analysis_time, ghidra_loading, bai_script, java_time, taint_analysis_time, memory_usage) values(?,?,?,?,?,?,?,?,?,?);', detailed_time_data)
        connection.commit()
    print(f'in {total_count} apk, has apk {has_apk_count}, has xml {has_xml_count}, status_success_count {status_success_count}')
    print(f'timeout_count_ns: {timeout_count_ns} timeout_count_fd: {timeout_count_fd} failed_count_flowdroid: {failed_count_flowdroid}')
    print(f'failed_count_ns: {failed_count_ns} ')
    print(f'success: {len(detailed_time_data)} failed: {failed_count}, lost_mem {lost_mem}')


def get_average_times():
    time_stats = cursor.execute("SELECT total_time_without_taint, pre_analysis_time, ghidra_loading, bai_script, java_time, taint_analysis_time, memory_usage FROM NSTimeStat")
    # transpose
    time_stats = [*zip(*time_stats)]
    headers = ["total_time_without_taint", "pre_analysis_time", "ghidra_loading", "bai_script", "java_time", "taint_analysis_time", "memory_usage"]
    for header, col in zip(headers, time_stats):
        print(f"{header}: {average(col)}")
'''
total_time_without_taint: 1458.163093122809
pre_analysis_time: 37.85515184048563
ghidra_loading: 618.4278630637233
bai_script: 755.2168958333331
java_time: 46.55006769982477
taint_analysis_time: 1791.0050260416672
memory_usage: 1078936937.3802083
'''

INTERSECT_DATASET = '/home/user/ns/dataset/intersect'
MALRADAR_DATASET = '/home/user/ns/dataset/malradar-filter'
FDROID_DATASET = '/home/user/ns/dataset/fdroid-filter'
if __name__ == '__main__':
    dry_run = True
    # add_dataset('malradar', MALRADAR_DATASET, dry_run=dry_run) # 
    add_dataset('fdroid', FDROID_DATASET, dry_run=dry_run) # 

    # get_average_times()
