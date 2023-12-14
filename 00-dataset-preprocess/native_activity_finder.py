from androguard.misc import AnalyzeAPK
import os,pickle,zipfile,lxml

# DATASET = '/home/user/ns/dataset/intersect'
DATASETS = ['/home/user/ns/dataset/fdroid', '/home/user/ns/dataset/malradar']
# DATASET = '/home/user/ns/dataset/fdroid-filter'
# DATASET = '/home/user/ns/dataset/malradar-filter'


def is_native_activity(apk):
    manifest =apk.get_android_manifest_xml() #type:lxml.etree.Element
    for md in manifest.findall('application/activity/meta-data'):
        if 'android.app.lib_name' in md.values():
            return True

na_count = 0

for DATASET in DATASETS:
    for file in os.listdir(DATASET):
        if not file.endswith('.apk'): 
            print(f'{file} is not apk!')
            continue
        apk_path = os.path.join(DATASET, file)
        print(f'current: {file}')
        try:
            apk, dfs, dex = AnalyzeAPK(apk_path)
        except KeyboardInterrupt:
            exit(-1)
        except:
            print(f"error: {file}")
            continue
        if is_native_activity(apk):
            print(f"found!!!!!")
            na_count += 1

# na_count: 27 / 2255 = 1.19%
print(f'na_count: {na_count}')

