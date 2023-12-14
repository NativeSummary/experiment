
import json
import os
import shutil
import time


fd_dataset_path = '/home/user/ns/dataset/fd-filter'
fd_out_dataset_path = '/home/user/ns/experiment/baseline-native_summary/fdroid-results'

malradar_dataset_path = '/home/user/ns/dataset/malradar-filter'
malradar_out_dataset_path = '/home/user/ns/experiment/baseline-native_summary/malradar-results'

# command_template = 'docker run --cpus=1 --mem=128G --rm -v $RES_DIR:/root/apps/ nativesummary/jnsaf:3.2.1 /root/apps/$1'

target = 'malradar'
print(f"current target: {target}")

if target == 'fdroid':
    dataset_path = fd_dataset_path
    out_dataset_path = fd_out_dataset_path
elif target == 'malradar':
    dataset_path = malradar_dataset_path
    out_dataset_path = malradar_out_dataset_path
else:
    dataset_path = None
    out_dataset_path = None


def main():
    # print(f'GLOBAL_STATE {GLOBAL_STATE}')
    file_paths = []
    for file in os.listdir(out_dataset_path):
        fpath = os.path.join(dataset_path, file)
        flow_log = os.path.join(fpath, f'{file}.flow.log')
        

if __name__ == '__main__':
    exit(0) # TODO this script is not useable
    start = time.time()
    main()
    dura = time.time() - start
    print(f'analysis spent {dura}s')
