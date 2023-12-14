from androguard.misc import AnalyzeAPK
import os,pickle,zipfile

# DATASET = '/home/user/ns/dataset/intersect'
DATASETS = ['/home/user/ns/dataset/fdroid-filter', '/home/user/ns/dataset/malradar-filter']
# DATASET = '/home/user/ns/dataset/fdroid-filter'
# DATASET = '/home/user/ns/dataset/malradar-filter'

def format_method(m):
    return (m.get_method().get_class_name().replace("/", ".")[1:-1], m.name, m.descriptor, m.access)

def format_encoded_method(m):
    return (m.get_class_name().replace("/", ".")[1:-1], m.get_name(), m.get_descriptor(), m.get_access_flags_string())


from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat
def get_dfs(_file) -> list[DalvikVMFormat]:
    a =  APK(_file, skip_analysis=True)
    d = []
    for dex in a.get_all_dex():
        df = DalvikVMFormat(dex, using_api=a.get_target_sdk_version())
        d.append(df)
    return d

if os.path.exists('./native-methods.pickel'):
    with open('./native-methods.pickel', "rb") as f:
        result = pickle.load(f)
else:
    result = {}

for DATASET in DATASETS:
    for file in os.listdir(DATASET):
        if file in result:
            print(f'skip {file}')
            continue
        if not file.endswith('.apk'): 
            print(f'{file} is not apk!')
            continue
        print(f'current: {file}')
        apk_path = os.path.join(DATASET, file)
        # try:
        #     apk, dfs, dex = AnalyzeAPK(apk_path)
        # except KeyboardInterrupt:
        #     exit(-1)
        # except:
        #     print(f"error: {file}")
        #     continue
        # native_methods = [m for m in dex.get_methods() if 'native' in m.access]
        # result[file] = []
        # for m in native_methods:
        #     result[file].append(format_method(m))

        dfs = get_dfs(apk_path)
        result[file] = []
        for df in dfs:
            for m in df.get_methods():
                if 'native' in m.get_access_flags_string():
                    result[file].append(format_encoded_method(m))

        with open('./native-methods.pickel', "wb") as f:
            pickle.dump(result ,f)

