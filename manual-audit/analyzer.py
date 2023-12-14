
import sys, pickle, json, pprint
import re
import os
import xml.etree.ElementTree as ET
import shutil
import collections
# f1 = sys.argv[1]
# f2 = sys.argv[2]

from flow_compare import *


# 分析成功的交集
with open('./intersec-2.pickel', "rb") as f:
    intersec = pickle.load(f) #type: set
with open('../mem_time_info.pickel', "rb") as f:
    r = pickle.load(f)
with open('./native-methods.pickel', "rb") as f:
    native_methods = pickle.load(f)
with open('../native_flows.obj.py', "rb") as f:
    native_flows = eval(f.read())

ns_path_template = '/home/user/ns/experiment/baseline-fd/{}-repacked-results'
jucify_path_template = '/home/user/ns/experiment/baseline-jucify/{}-results'


def getTerminationState(path):
    return ET.parse(path).getroot().attrib['TerminationState']

def ignore_ghidra_project(dir: str, names: list[str]):
    ret = []
    if dir.endswith('.apk'):
        if 'project' in names:
            ret.append('project')
        if 'repacked_apks' in names:
            ret.append('repacked_apks')
        for n in names:
            if n.endswith('.java_serialize') or n.endswith('.so.txt'):
                ret.append(n)
    return ret
    
audit_out_path = '/home/user/ns/experiment/manual-audit/apps'
def generate_audit_folder(ty, app):
    ret = os.path.join(audit_out_path, app)
    shutil.copytree(f'/home/user/ns/experiment/baseline-native_summary/{ty}-results/{app}', 
                    ret, ignore=ignore_ghidra_project, dirs_exist_ok=True)
    return ret

def xml_empty_flow(path):
    import xml.etree.ElementTree as ET
    root = ET.parse(path).getroot()
    for result in root.findall('./Results/Result'):
        return False
    return True


def assert_same(f1, f2):
    eq_flow, new_flow, lost_flow = cmp_set2(f1, f2)
    if len(eq_flow) + len(new_flow) + len(lost_flow) == 0:
        print(f"empty: {f1}")

    if len(new_flow) != 0 or len(lost_flow) != 0:
        print(f'{len(new_flow)} new, {len(lost_flow)} lost')
    else:
        print("OK")
    # assert len(new_flow) == 0 and len(lost_flow) == 0, f"{f1}\n{f2}\n"


def main():
    for key in native_flows:
        out = generate_audit_folder(*key)

        fd_flow2 = f'/home/user/ns/experiment/baseline-fd/intersect-results/{key[1]}/{key[1].removesuffix(".apk")}.xml'
        ns_flow2 = f'/home/user/ns/experiment/baseline-fd/intersect-{key[0]}-repacked-results/{key[1]}/{key[1].removesuffix(".apk")}.xml'

        try:
            jucify_flow = r['jucify'][key][2]
            if os.path.exists(jucify_flow):
                shutil.copy(jucify_flow, os.path.join(out, 'jucify.xml'))
        except:
            pass

        if os.path.exists(fd_flow2):
            shutil.copy(fd_flow2, os.path.join(out, 'fd.xml'))
        if os.path.exists(ns_flow2):
            shutil.copy(ns_flow2, os.path.join(out, 'ns.xml'))



# xml -> {new, lost, baseline}
result = {}
def main2():
    empty_count = 0
    all_flow_infos = {}
    for key in sorted(intersec):
        if key[0] == 'fdroid': # !!!临时
            continue

        fd_flow = r['flowdroid'][key][2]
        fd_flow2 = f'/home/user/ns/experiment/baseline-fd/intersect-results/{key[1]}/{key[1].removesuffix(".apk")}.xml'
        jucify_flow = r['jucify'][key][2]
        ns_flow = r['ns'][key][2]
        ns_flow2 = f'/home/user/ns/experiment/baseline-fd/intersect-{key[0]}-repacked-results/{key[1]}/{key[1].removesuffix(".apk")}.xml'

        if not os.path.exists(fd_flow2):
            print(f'not exist: {key}')
            continue

        # assert_same(fd_flow, fd_flow2)
        if xml_empty_flow(fd_flow2):
            empty_count += 1;
            print(f'empty: {key}')
            continue

        tagm = gen_tag_set(ns_flow2, fd_flow2)
        tagm_j = gen_tag_set(jucify_flow, fd_flow2)


        native_map_set = get_native_flow(ns_flow2, key[1], native_methods)
        if len(native_map_set) == 0: 
            print(f'no native flow: {key}')
            continue
        print(f'OK: {key}')
        out = generate_audit_folder(*key)

        shutil.copy(fd_flow2, os.path.join(out, 'fd.xml'))
        # # 去掉重复的flow
        # fd_set = get_set(fd_flow)
        # copy_dedup()
        shutil.copy(ns_flow2, os.path.join(out, 'ns.xml'))
        shutil.copy(jucify_flow, os.path.join(out, 'jucify.xml'))

        flow_infos = {}

        for flow in native_map_set:
            # if flow not in native_map_set: continue
            flow_infos[flow] = {'tag':f'ns: {tagm[flow]}, jucify: {tagm_j[flow]}', 'nat_flow':native_map_set[flow]}
        
        all_flow_infos[key] = flow_infos
        with open(os.path.join(out, 'flow_tag.py'), "w") as f:
            # json.dump(flow_infos, f, indent=2)
            pprint.pprint(flow_infos, f, indent=4)
        # exit()

def load_py_file(path):
    with open(path, 'r') as f:
        return eval(f.read())

# generate audit app folder from ns_flow to fd_flow
def main3():
    new_flows = load_py_file('ns_fd_lost_native_flows.obj.py')
    lost_flows = load_py_file('ns_fd_new_native_flows.obj.py')
    apps = set()
    for app, flow in new_flows:
        apps.add(app)
    for app, flow in lost_flows:
        apps.add(app)
    for key in apps:
        out = generate_audit_folder(*key)
        fd_flow2 = f'/home/user/ns/experiment/baseline-fd/intersect-{key[0]}-results/{key[1]}/{key[1].removesuffix(".apk")}.xml'
        ns_flow2 = f'/home/user/ns/experiment/baseline-fd/intersect-{key[0]}-repacked-results/{key[1]}/{key[1].removesuffix(".apk")}.xml'
        
        # try:
        shutil.copy(fd_flow2, os.path.join(out, 'fd.xml'))
        # except:
        # # 去掉重复的flow
        # fd_set = get_set(fd_flow)
        # copy_dedup()
        if os.path.exists(ns_flow2):
            shutil.copy(ns_flow2, os.path.join(out, 'ns.xml'))
        else:
            with open(os.path.join(out, 'ns.xml'), 'w') as f:
                f.write('not exist')

        try:
            jucify_flow = r['jucify'][key][2]
            if os.path.exists(jucify_flow):
                shutil.copy(jucify_flow, os.path.join(out, 'jucify.xml'))
        except KeyError:
            pass

if __name__ == '__main__':
    main3()
