
import sys

# ls ./repo | grep \\.apk$ > apklist.txt
file_list = sys.argv[1]
out_file = sys.argv[2]
print(f'file_list {file_list}')
print(f'out_file {out_file}')

apk2ver = dict()

with open(file_list, 'r') as f:
    for line in f.readlines():
        name, version = line.removesuffix('.apk\n').rsplit('_', 1)
        print(name, version)
        if name in apk2ver:
            apk2ver[name].append(version)
        else:
            apk2ver[name] = [version]
print(apk2ver)

with open(out_file, 'w') as f:
    for apk in apk2ver:
        ver = max(apk2ver[apk])
        f.write(f'{apk}_{ver}.apk\n')

