# 过滤flutter和无so的之后
# 分析每个apk的so文件。

from collections import defaultdict
import json
import os
from zipfile import ZipFile
from native_summary.pre_analysis.__main__ import apk_pre_analysis
from native_summary.pre_analysis.dex_analysis import DexAnalysisCenter, format_method

only_javamethods_in_so_stat = True

dataset_path = 'D:\\~datasets\\repo'
app_count = 0

# APK => 是否为flutter应用，静态成功解析的比例，解析失败的集合，成功解析的集合，解析失败的Native符号，每个so的信息
apk_stat = dict()

# arch count
# 在我的优先arm64的策略下，分析的各种arch的数量。
arch_count = defaultdict(lambda: 0)
no_native_mth_count = 0

# crc count 算了，没必要by crc。还是by name吧。
# crc2name = {}
# crc_count = defaultdict(lambda: 0)

def fdroid_deduplicate(filename_iter):
    # yield last file
    # sepcial case: dev.obfusk.sokobang_1000205001_e3603f6.apk
    # ai.susi_14.apk ai.susi_15.apk ai.susi_16.apk
    prev_prefix = ""
    prev_file = ""
    for file in filename_iter:
        assert file.endswith(".apk")
        ind = file.rfind("_")
        prefix = file[:ind]
        # assert is int
        try:
            num = int(file[ind+1:].rstrip('.apk'))
        except ValueError:
            num = int(file[ind+1:].rstrip('.apk'), 16)
            ind = file.rfind("_", 0, ind)
            prefix = file[:ind]
        if prev_prefix != prefix:
            prev_prefix = prefix
            if len(prev_file) != 0:
                yield prev_file
        prev_file = file
    yield prev_file

def test_main():
    for file in fdroid_deduplicate(os.listdir(dataset_path)):
        print(file)

def main():
    global app_count, no_native_mth_count
    analyse_dex=True
    for file in fdroid_deduplicate(os.listdir(dataset_path)):
        filename = file
        file_path = os.path.join(dataset_path, file)
        if not filename.endswith(".apk"):
            continue

        # limit apk range for debug
        if not filename.startswith("com.morlunk.mumbleclient_73.apk"):
            continue
        
        # if os.path.getsize(file_path) <= 5 * 1024 * 1024:
        #     continue

        print(filename)
        app_count += 1
        apk, dex, arch_selected, so_stat, tags = apk_pre_analysis(file_path, analyse_dex)
        is_flutter = tags['is_flutter']
        # so_stat:
        # so_name -> (checksum, recognized_java_symbols, import, export)

        target_stat = apk_stat
        assert not is_flutter

        arch_count[arch_selected] += 1
        if analyse_dex:
            if len(dex.native_methods) == 0:
                no_native_mth_count += 1

        if only_javamethods_in_so_stat:
            so_stat = {key:(val[0], val[1])  for key, val in so_stat.items()}

        # 是否为flutter应用，静态成功解析的比例，解析失败的Native符号，解析失败的集合，成功解析的集合，每个so的信息
        target_stat[filename] = {}
        target_stat[filename]['selected_arch'] = arch_selected
        if analyse_dex:
            target_stat[filename]['resolve_percentage'] = dex.resolved_percentage()
            target_stat[filename]['failed_native_symbol'] = dex.mappings[DexAnalysisCenter.UNRESOLVED]
            target_stat[filename]['failed_java_mth'] = list(map(format_method, dex.unresolved_java()))
            target_stat[filename]['success_java_mth'] = list(map(format_method, dex.resolved_java()))
        target_stat[filename]['so_stat'] = so_stat


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

# for arch, dic in .items():
#     sorted_list = sorted(dic.items(), key=lambda i:i[1][0], reverse=True)
#     with open(f"ana_{arch}_result.json", 'w') as f:
#         json.dump(sorted_list, f, cls=SetEncoder)

def finalize():
    print(f"Total {app_count} app")
    for arch, count in arch_count.items():
        print(f"arch {arch}\t{count}\t{count / app_count}")
    print("============")
    print(f"no native mth:\t{no_native_mth_count}\t {no_native_mth_count / app_count}")
    
    with open(f"apk_result.json", 'w') as f:
        json.dump(apk_stat, f)


def set_exc_hook():
    import sys
    def my_except_hook(exctype, value, traceback):
        if exctype == KeyboardInterrupt:
            pass
        finalize()
        sys.__excepthook__(exctype, value, traceback)
    sys.excepthook = my_except_hook

if __name__ == '__main__':
    set_exc_hook()
    main()
    finalize()
