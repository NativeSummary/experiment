#!/usr/bin/python3
import sys, pickle, json, pprint
import re
import os
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
# f1 = sys.argv[1]
# f2 = sys.argv[2]


# 分析成功的交集
if __name__ == '__main__':    
    file_path = os.path.realpath(__file__)
    elem = 'experiment'
    module_path = file_path[:file_path.rfind(elem)+len(elem)]
    sys.path.insert(1, module_path)

    from util_funcs import DATABASE_NAME, connect_and_cursor

    connection, cursor = connect_and_cursor(os.path.join(module_path, DATABASE_NAME))


#     with open('intersec.pickel', "rb") as f:
#         intersec = pickle.load(f)
#     with open('mem_time_info.pickel', "rb") as f:
#         r = pickle.load(f)
    with open('/home/user/ns/experiment/manual-audit/native-methods.pickel', "rb") as f:
        native_methods = pickle.load(f)
#     with open('code_sizes.pickel', "rb") as f:
#         code_sizes = pickle.load(f)

ns_path_template = '/home/user/ns/experiment/baseline-fd/{}-repacked-results'
jucify_path_template = '/home/user/ns/experiment/baseline-jucify/{}-results'

def convert_source_or_sink(elem):
    return (elem.attrib['Method'], elem.attrib['Statement'])

def get_set(path):
    root = ET.parse(path).getroot()
    ret = set()
    for result in root.findall('./Results/Result'):
        assert result[0].tag == 'Sink'
        assert result[1].tag == 'Sources'
        sink = convert_source_or_sink(result[0])
        # sources = []
        for sour in result[1]:
            assert sour.tag == 'Source'
            # sources.append(convert_source_or_sink(sour))
            ret.add((sink, convert_source_or_sink(sour)))
    return ret


def get_set_iter(path):
    root = ET.parse(path).getroot()
    for result in root.findall('./Results/Result'):
        assert result[0].tag == 'Sink'
        assert result[1].tag == 'Sources'
        sink = convert_source_or_sink(result[0])
        # sources = []
        for sour in result[1]:
            assert sour.tag == 'Source'
            # sources.append(convert_source_or_sink(sour))
            yield (sink, convert_source_or_sink(sour))


# f2 is baseline
def cmp_set(f1, baseline):
    s1 = get_set(f1)
    s2 = get_set(baseline)
    uni = s1.union(s2)
    new_flow = []
    lost_flow = []
    eq_flow = 0
    for ele in uni:
        if ele in s1 and ele in s2:
            eq_flow += 1  
        elif ele in s1:
            new_flow.append(ele)
            # print(f'new flow: {ele}')
        elif ele in s2:
            lost_flow.append(ele)
            # print(f'lost flow: {ele}')
        else: raise 'error'
    return eq_flow, new_flow, lost_flow


# f2 is baseline
def cmp_set2(s1, baseline):
    if type(s1) is str:
        s1 = get_set(s1)
    if type(baseline) is str:
        s2 = get_set(baseline)
    else: s2 = baseline
    uni = s1.union(s2)
    new_flow = []
    lost_flow = []
    eq_flow = []
    for ele in uni:
        if ele in s1 and ele in s2:
            eq_flow.append(ele)
        elif ele in s1:
            new_flow.append(ele)
            # print(f'new flow: {ele}')
        elif ele in s2:
            lost_flow.append(ele)
            # print(f'lost flow: {ele}')
        else: raise 'error'
    return eq_flow, new_flow, lost_flow



# f2 is baseline
def gen_tag_set(f1, baseline):
    s1 = get_set(f1)
    s2 = get_set(baseline)
    uni = s1.union(s2)
    ret = {}
    for ele in uni:
        if ele in s1 and ele in s2:
            ret[ele] = 'eq'
        elif ele in s1:
            ret[ele] = 'new'
            # print(f'new flow: {ele}')
        elif ele in s2:
            ret[ele] = 'lost'
            # print(f'lost flow: {ele}')
        else: raise 'error'
    return ret

def get_jnsaf_native_flow(flow, apkname, native_methods, filter_set=None):
    ret = collections.defaultdict(lambda:[])
    # print(path)
    nms = native_methods[apkname]
    m = get_set_jnsaf(flow)
    for f, steps in m.items():
        native_parts = []
        for step in steps:
            if contains_native_method_jnsaf(nms, step):
                native_parts.append(step)
        if len(native_parts) != 0:
            ret[f].append(native_parts) 
    return dict(ret)

# 为每个apk的结果，找出里面和native相关的部分。
# map: flow set -> [(native flow xml, native part)]
def get_native_flow(path, apkname, native_methods, filter_set=None):
    ret = collections.defaultdict(lambda:[])
    # print(path)
    nms = native_methods[apkname]
    root = ET.parse(path).getroot()

    for result in root.findall('./Results/Result'):
        assert result[0].tag == 'Sink'
        assert result[1].tag == 'Sources'
        sink = convert_source_or_sink(result[0])
        # sources = []
        for sour in result[1]:
            assert sour.tag == 'Source'
            # sources.append(convert_source_or_sink(sour))
            sspair = (sink, convert_source_or_sink(sour))
            if filter_set is not None:
                if sspair not in filter_set:
                    continue
            native_parts = []
            for pe in sour.findall('./TaintPath/PathElement'):
                call_stmt = pe.attrib['Statement']
                if contains_native_method(nms, call_stmt):
                    native_parts.append(call_stmt)
            if len(native_parts) != 0:
                ret[sspair].append(native_parts) # ET.tostring(sour)
    return dict(ret)

def dot2sig(clz):
    return f"L{clz.replace('.','/')};"

def contains_native_method_jnsaf(nms, step):
    for clz,name,desc,access in nms:
        if dot2sig(clz) in step and f'.{name}' in step:
            return True
    return False

def contains_native_method(nms, stmt):
    for clz,name,desc,access in nms:
        if 'NativeSummary' in stmt:
            return True
        if f'<{clz}' in stmt and f'{name}(' in stmt: # todo
            return True
    return False

# ==============JNSAF==============

def find_match(ind, s):
    if ind == -1: return -1
    assert s[ind] == '{'
    level = 1
    while ind < len(s) and level > 0:
        ind += 1
        if s[ind] == '{': level += 1
        if s[ind] == '}': level -= 1
    return ind

def jnsaf_parse_dict(origs: str):
    s = origs.strip()
    if s[0] == '"':
        assert s[0] == '"' and s[-1] == '"'
        return s[1:-1]
    if s[0] == '{':
        assert s[0] == '{' and s[-1] == '}'
        s = s[1:-1].strip()
        result = []
        while len(s) != 0:
            s = s.strip()
            ind = s.find('{'); endind = find_match(s.find('{'), s)
            if ind == -1 or ind > endind:
                ind = s.find(':'); endind = s.find('\n')
                if ind != -1: ind +=1
                if endind == -1: endind = len(s)-1
            result.append({s[:ind].strip(): jnsaf_parse_dict(s[ind:endind+1])})
            s = s[endind+1:]
            s = s.strip()
        return result
    else:
        raise "wtf"

desc1 = re.compile(r'api_source:.*@signature `(.*)`')
desc2 = re.compile(r'entrypoint_source: Entry@(.*) ')
desc3 = re.compile(r'icc_source:.*@signature `(.*)`')
desc4 = re.compile(r'api_sink:.*@signature `(.*)`')
desc5 = re.compile(r'icc_sink:.*@signature `(.*)`')
def handle_desc(s):
    ret = desc1.search(s)
    if ret is None:
        ret = desc2.search(s)
    if ret is None:
        ret = desc3.search(s)
    if ret is None:
        ret = desc4.search(s)
    if ret is None:
        ret = desc5.search(s)
    if ret is None:
        raise RuntimeError("cannot match desc")
    ret = ret.groups()[0]
    ret = ret.split('.', 1)
    ret2 = ret[1].rsplit(':', 1)
    ret = [ret[0]] + ret2
    clazz, name, sig = ret
    assert clazz.startswith('L') and clazz.endswith(';')
    return (clazz[1:-1].replace('/', '.'), name)

# 把jnsaf的flow转换成(source, sink)的形式，其中source/sink = (类名， 函数名)
def get_set_jnsaf(tool_flow):
    result = {}
    if tool_flow.startswith(': ""\n'):
        # print(fd_flow)
        f = []
    else:
        f = jnsaf_parse_dict(tool_flow)
    # pprint.pprint(f, indent=4)
    
    for path in f:
        # key
        source = path['paths'][0]['source'][1]['desc:']
        pair = handle_desc(source)
        sink = path['paths'][1]['sink'][1]['desc:']
        pair2 = handle_desc(sink)
        # value
        steps = []
        for p in path['paths'][2:]:
            steps.append(p['steps:'])
        result[((pair, pair2))] = steps
    return result

stmt1 = re.compile(r'<(.*):')
stmt2 = re.compile(r' ([a-zA-Z0-9<>]*)\(')
def handle_fd_statement(s):
    clz = stmt1.search(s).groups()[0]
    mth = stmt2.search(s).groups()[0]
    return (clz, mth)

# 把那边flowdroid的set格式转换为上面jnsaf的极简格式。使用regex魔法。
def convert_set_jnsaf(s2):
    result = set()
    for sink, source in s2:
        # 取statement
        source_ = handle_fd_statement(source[1])
        sink_ = handle_fd_statement(sink[1])
        result.add((source_, sink_))
    return result

def cmp_jnsaf(tool_flow, fd_flow):
    s1 = set(get_set_jnsaf(tool_flow).keys())
    s2 = convert_set_jnsaf(get_set(fd_flow))
    # if len(s2) != 0:
    #     print("\n"*5)
    #     print(fd_flow)
    uni = s1.union(s2)
    new_flow = []
    lost_flow = []
    eq_flow = 0
    for ele in uni:
        if ele in s1 and ele in s2:
            eq_flow += 1  
        elif ele in s1:
            new_flow.append(ele)
            # print(f'new flow: {ele}')
        elif ele in s2:
            lost_flow.append(ele)
            # print(f'lost flow: {ele}')
        else: raise 'error'
    return eq_flow, new_flow, lost_flow


# ==============JNSAF end==============

def getTerminationState(path):
    return ET.parse(path).getroot().attrib['TerminationState']

import collections
counts = collections.defaultdict(lambda:0)

# xml -> {new, lost, baseline}
result = {}
def main():
    print(f'{len(intersec)} apps all analyzable')
    for key in intersec:
        fd_flow = r['flowdroid'][key][2]
        fd_flow2 = f'/home/user/ns/experiment/baseline-fd/intersect-{key[0]}-results/{key[1]}/{key[1].removesuffix(".apk")}.xml'
        if not os.path.exists(fd_flow2):
            print(f'fd_flow2 not exist: {key}')
            continue
        fd_flow = fd_flow2

        fd_nfs = get_native_flow(fd_flow, key[1], native_methods)
        counts['native_fd'] += len(fd_nfs)
        for target in ['ns', 'jnsaf', 'jucify']:
            tool_flow = r[target][key][2]
            if target in ['ns','jucify']:
                ns_flow2 = f'/home/user/ns/experiment/baseline-fd/intersect-{key[0]}-repacked-results/{key[1]}/{key[1].removesuffix(".apk")}.xml'
                if target == 'ns' and os.path.exists(ns_flow2):
                    tool_flow = ns_flow2
                tool_nfs = get_native_flow(tool_flow, key[1], native_methods)
                counts[f'native_{target}'] += len(tool_nfs)
            if target != 'jnsaf':
                eq_flow, new_flow, lost_flow = cmp_set(tool_flow, fd_flow)
            else:
                eq_flow, new_flow, lost_flow = cmp_jnsaf(tool_flow, fd_flow)
            result[tool_flow] = {'new': new_flow, 'lost': lost_flow, 'baseline': fd_flow}
            counts[target+' eq'] += eq_flow
            counts[target+' new'] += len(new_flow)
            counts[target+' lost'] += len(lost_flow)
        counts['fd'] += len(get_set(fd_flow))
    print(dict(counts))
    with open('different_flows.json', "w") as f:
        json.dump(result, f, indent=2)

# compare fd1 with fd2
# 说明flowdroid的不稳定性
def main2():
    total = 0
    for target in code_sizes:
        for apk in code_sizes[target]:
            key = (target, apk)
    # for key in intersec:
            try:
                fd_flow = r['flowdroid'][key][2]
            except KeyError:
                continue
            fd_flow2 = f'/home/user/ns/experiment/baseline-fd/intersect-{key[0]}-results/{key[1]}/{key[1].removesuffix(".apk")}.xml'
            if not os.path.exists(fd_flow2):
                continue
            total += 1
            eq_flow, new_flow, lost_flow = cmp_set(fd_flow2, fd_flow)
            counts['eq'] += eq_flow
            counts['new'] += len(new_flow)
            counts['lost'] += len(lost_flow)
            counts['fd'] += len(get_set(fd_flow))
    print(dict(counts))
    print(f'{total} apps in intersection')

'''
{'eq': 70945, 'new': 11599, 'lost': 27817, 'fd': 98762}
1926 apps in intersection
'''
# for multiprocessing
def count_flow(tool, tool_flow_raw, apk):
    with open('/home/user/ns/experiment/manual-audit/native-methods.pickel', "rb") as f:
        native_methods = pickle.load(f)
    try:
        if tool != 'jnsaf':
            # try:
            tool_nfs = get_native_flow(tool_flow_raw, apk, native_methods)
            # except FileNotFoundError:
            #     continue
            tool_flow = get_set(tool_flow_raw)
        else:
            tool_nfs = get_jnsaf_native_flow(tool_flow_raw, apk, native_methods)
            tool_flow = get_set_jnsaf(tool_flow_raw)
    except ParseError:
        print(f"failed to parse: {tool_flow_raw}")
        return 0, 0, apk
    return len(tool_flow), len(tool_nfs), apk

def search_native_flows_db(tool_name):
    datas = list(cursor.execute("SELECT tool_name, apk_name, flow_content FROM ToolRunStat WHERE is_success != 0 AND flow_content IS NOT NULL AND tool_name = ?", (tool_name,)))
    counts = collections.defaultdict(lambda:0)
    sql_datas = []
    args = []
    for data in list(datas):
        tool, apk, tool_flow_raw = data
        # tool_flow_c, tool_nfs_c = count_flow(tool, tool_flow_raw, apk)
        args.append((tool, tool_flow_raw, apk))
    from multiprocessing.pool import Pool
    with Pool(100) as pool:
        for result in pool.starmap(count_flow, args):
            tool_flow_c, tool_nfs_c, apk = result
            counts[f'{tool}_native'] += tool_nfs_c
            counts[f'{tool}_total'] += tool_flow_c
            counts[f'{tool}_apk'] += 1
            sql_datas.append((tool_flow_c, tool_nfs_c, apk, tool))
    print(dict(counts))
    cursor.executemany("UPDATE ToolRunStat SET flow_count=?, native_related_flow_count=? WHERE apk_name=? AND tool_name=?", sql_datas)
    assert cursor.rowcount > 0
    connection.commit()

# 单看jucify和ns，找含有native函数的flow
def search_native_flows(tool = 'ns', range_set=None):
    # from tqdm import tqdm
    result_by_flow = {}
    result = {}
    # totals = collections.defaultdict(lambda:0)
    counts = collections.defaultdict(lambda:0)
    for target in code_sizes:
        for apk in tqdm(code_sizes[target]):
            key = (target, apk)
            if range_set is not None and key not in range_set: continue
    # for key in intersec:
            if tool == 'jucify':
                try:
                    tool_flow = r['jucify'][key][2]
                except KeyError:
                    continue
                # counts['jucify'] += 1
            elif tool == 'jucify*':
                try:
                    tool_flow = r['jucify*'][key][2]
                except KeyError:
                    continue
            elif tool == 'ns':
                tool_flow = f'/home/user/ns/experiment/baseline-fd/intersect-{key[0]}-repacked-results/{key[1]}/{key[1].removesuffix(".apk")}.xml'
                if not os.path.exists(tool_flow):
                    continue
                # counts['ns'] += 1
            elif tool == 'fd':
                tool_flow = f'/home/user/ns/experiment/baseline-fd/intersect-{key[0]}-results/{key[1]}/{key[1].removesuffix(".apk")}.xml'
                if not os.path.exists(tool_flow):
                    continue
                # counts['fd'] += 1
            elif tool == 'jnsaf':
                try:
                    tool_flow = r['jnsaf'][key][2]
                except KeyError:
                    continue
            else: raise RuntimeError('not supported')
            if tool != 'jnsaf':
                tool_nfs = get_native_flow(tool_flow, key[1], native_methods)
            else:
                tool_nfs = get_jnsaf_native_flow(tool_flow, key[1], native_methods)
            counts[f'native_{target}'] += len(tool_nfs)
            counts[f'native_total'] += len(tool_nfs)
            counts[f'{tool}_apk'] += 1
            if tool == 'jnsaf':
                counts[f'{tool}_flow'] += len(get_set_jnsaf(tool_flow))
            else:
                counts[f'{tool}_flow'] += len(get_set(tool_flow))
            if len(tool_nfs) != 0:
                # print(tool_flow)
                result[key] = tool_nfs
                for flow in tool_nfs:
                    result_by_flow[(key, flow)] = tool_nfs[flow]
    # pprint_obj('fd_native_flows.obj.py', result)
    print(f'counts: {str(dict(counts))}')
    # print(f'{tool}: {str(dict(totals))}')
    return result_by_flow


def main3():
    print(f'=====fd search native flows=====')
    fd_flows = search_native_flows('fd') # counts: {'native_malradar': 38, 'native_total': 56, 'fd_apk': 1913, 'fd_flow': 1624293, 'native_fdroid': 18}
    print(f'=====ns search native flows=====')
    ns_flows = search_native_flows('ns') # counts: {'native_malradar': 3474, 'native_total': 3798, 'ns_apk': 1360, 'ns_flow': 1203775, 'native_fdroid': 324}
    print(f'=====jucify search native flows=====')
    search_native_flows('jucify') # counts: {'native_malradar': 3, 'native_total': 26, 'jucify_apk': 1111, 'jucify_flow': 718687, 'native_fdroid': 23}
    print(f'=====jucify* search native flows=====')
    search_native_flows('jucify*')
    print(f'=====jnsaf search native flows=====')
    search_native_flows('jnsaf') # counts: {'native_malradar': 5, 'native_total': 11, 'jnsaf_apk': 744, 'jnsaf_flow': 3832, 'native_fdroid': 6}
    print(f'=====comapre native flows=====')
    eq_flow, new_flow, lost_flow = cmp_set2(set(ns_flows.keys()), set(fd_flows.keys()))
    print(f'eq {len(eq_flow)}, new {len(new_flow)}, lost {len(lost_flow)}')
    pprint_obj('ns_fd_lost_native_flows.obj.py', {k:fd_flows[k] for k in lost_flow})
    pprint_obj('ns_fd_new_native_flows.obj.py', {k:ns_flows[k] for k in new_flow})
    pprint_obj('ns_fd_eq_ns_native_flows.obj.py', {k:ns_flows[k] for k in eq_flow})
    pprint_obj('ns_fd_eq_fd_native_flows.obj.py', {k:fd_flows[k] for k in eq_flow})

def main4():
    tools = ['fd', 'jucify', 'jucify*', 'jnsaf', 'ns']
    for tool in tools:
        search_native_flows(tool)
    # print("=====intersection===")
    # for tool in tools:
    #     search_native_flows(tool, intersec)

"""
counts: {'native_malradar': 0, 'native_total': 1, 'fd_apk': 271, 'fd_flow': 46667, 'native_fdroid': 1}
counts: {'native_malradar': 0, 'native_total': 2, 'jucify_apk': 271, 'jucify_flow': 51319, 'native_fdroid': 2}
counts: {'native_malradar': 5, 'native_total': 6, 'jnsaf_apk': 271, 'jnsaf_flow': 2029, 'native_fdroid': 1}
counts: {'native_malradar': 33, 'native_total': 122, 'ns_apk': 271, 'ns_flow': 46950, 'native_fdroid': 89}
"""

from pprint import PrettyPrinter

class NoStringWrappingPrettyPrinter(PrettyPrinter):
    def _format(self, object, *args):
        if isinstance(object, str):
            width = self._width
            self._width = sys.maxsize
            try:
                super()._format(object, *args)
            finally:
                self._width = width
        else:
            super()._format(object, *args)

def pprint_obj(path, obj):
    with open(path, 'w') as f:
        f.write(NoStringWrappingPrettyPrinter().pformat(obj))

# def dump_json(path, obj):
#     with open(path, 'w') as f:
#         json.dump(obj, f, indent=4)

if __name__ == '__main__':
    for tool_name in ['ns']:
        search_native_flows_db(tool_name)
    connection.close()
    # main4()
    # counts: {'native_malradar': 9, 'native_total': 54, 'jucify*_apk': 1283, 'jucify*_flow': 815182, 'native_fdroid': 45}
    # search_native_flows('jucify*', intersec)
    # 
    pass

'''
# target = 'malradar'
# target = 'fd'

fold1 = f'/home/user/ns/experiment/11-fd-repacked/{target}-results'
fold2 = f'/home/user/ns/experiment/baseline-fd/{target}-results'


# 全文件对比
pat = re.compile(r'\s*<PerformanceData>.*</PerformanceData>', re.DOTALL)

def cmp(f1, f2):

    with open(f1, 'r') as f:
        f1_str = f.read()

    with open(f2, 'r') as f:
        f2_str = f.read()

    f1_str = pat.sub('', f1_str)
    f2_str = pat.sub('', f2_str)

    if f1_str == f2_str:
        return True
    else:
        return False

def main1():
    for file in sorted(os.listdir(fold1)):
        path1 = os.path.join(fold1, file)
        path2 = os.path.join(fold2, file)
        if not os.path.exists(path2) or os.stat(path2).st_size == 0:
            counts['exist'] += 1
            # print(f"err: baseline not exist: {file}") # 50
            continue
        if getTerminationState(path2) != 'Success':
            counts['nonSuccess'] += 1
            # print('baseline not success') # 53
            continue

        eq_flow, new_flow, lost_flow = cmp_set(path1, path2)
        if new_flow == 0 and lost_flow == 0:
            counts['same'] += 1
            # print('same') # 54
            continue
        else:
            counts['rest'] += 1
            counts['new_flow'] += new_flow
            counts['lost_flow'] += lost_flow
            counts['eq_flow'] += eq_flow
        # if lost_flow != 0:
        #     print(f'[{file}]: new flow {new_flow}, lost flow {lost_flow}') # 57
    print(dict(counts))
'''