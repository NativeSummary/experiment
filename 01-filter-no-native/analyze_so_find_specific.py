# 不同arch分开统计
# 统计一个目录下，so按文件名分类计数，统计hash情况（考虑深入研究获取版本号？）同时保留一些APK名字？方便之后找一个解压出来？。
# 或者每种so保留三个APK名字，解压三个出来。

from collections import defaultdict
import json
import os
from typing import OrderedDict
from zipfile import ZipFile
from native_summary.pre_analysis.__main__ import select_abi
from native_summary.pre_analysis.elf_analysis import get_elf_import_export
from androguard.core.bytecodes.axml import AXMLPrinter

PRESERVE_COUNT = 2
dataset_path = r'D:\~datasets\MalDevGenome'


app_count = 0

# arch -> dict(filename -> [count, [(apk_name, arch, java_syms, imp, exp)]])
filename_stat = defaultdict(lambda :[0,[]])


def main():
    global app_count
    for file in os.listdir(dataset_path):
        # filename = os.fsdecode(file)
        filename = file
        file_path = os.path.join(dataset_path, file)
        if not filename.endswith(".apk"):
            continue

        # limit apk range
        # if not filename.startswith("app."):
        #     continue
        print(filename)
        app_count += 1
        apk_zip = ZipFile(file_path)
        arch_selected, is_flutter, has_so = select_abi(apk_zip)
        target_prefix = get_target_prefix(apk_zip)

        for so_info in apk_zip.infolist():
            if so_info.filename.startswith("lib/" + arch_selected) and so_info.filename.endswith(".so"):
                path_parts = so_info.filename.split("/")
                if len(path_parts) != 3: print("Warning: irregular path: " + so_info.filename)
                filename = path_parts[-1]
                # checksum = so_info.CRC

                # update filename stat
                imp, exp = get_elf_import_export(apk_zip.open(so_info), in_memory=True)
                target_sym = []
                if exp is not None:
                    target_sym = [i for i in exp if i.startswith(target_prefix)]
                if len(target_sym) != 0:
                    result = {}
                    result["apk"] = file
                    result["arch"] = arch_selected
                    result["target_syms"] = target_sym
                    filename_stat[filename][1].append(result)

                    filename_stat[filename][0] += 1

def get_package_name(apk_zip: ZipFile):
    with apk_zip.open("AndroidManifest.xml", "r") as fp:
        a = AXMLPrinter(fp.read())
        xml = a.get_xml_obj()
        return xml.get('package')

def get_target_prefix(apk_zip):
    pn = get_package_name(apk_zip)
    parts = pn.split('.')[:2]
    prefix = "Java_"+'_'.join(parts)
    return prefix


def simplify_result(dic):
    del dic["import"]
    del dic["export"]


def finalize():
    print(f"Total {app_count} app")
    
    sorted_list = sorted(filename_stat.items(), key=lambda i:i[1][0], reverse=True)
    with open(f"so_result_full.json", 'w') as f:
        json.dump(OrderedDict(sorted_list), f, sort_keys=False)
    
    simplified_list = []
    for file, val in sorted_list:
        has_java = False
        count, list_ = val
        for occr in list_:
            if len(occr["java_syms"]) != 0:
                has_java = True
            simplify_result(occr)
        if has_java:
            simplified_list.append((file, val))
    with open(f"so_result_onlyjava_simplify.json", 'w') as f:
        json.dump(OrderedDict(simplified_list), f, sort_keys=False)
    

def set_exc_hook():
    import sys
    def my_except_hook(exctype, value, traceback):
        if exctype == KeyboardInterrupt:
            pass
        finalize()
        sys.__excepthook__(exctype, value, traceback)
    sys.excepthook = my_except_hook


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
       if isinstance(obj, set):
          return list(obj)
       return json.JSONEncoder.default(self, obj)

if __name__ == '__main__':
    set_exc_hook()
    main()
    finalize()
