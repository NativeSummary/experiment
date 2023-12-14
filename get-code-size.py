import pickle,os

def get_code_size(zf):
    import zipfile
    total = 0
    zf = zipfile.ZipFile(zf)
    for info in zf.infolist():
        name = info.filename.lower()
        if name.endswith('.dex') or name.endswith('.so'):
            total += info.file_size
    return total

FD = '/home/user/ns/dataset/fd-filter'
MALRADAR = '/home/user/ns/dataset/malradar-filter'
full_fd = {i:get_code_size(os.path.join(FD, i)) for i in os.listdir(FD) if i.endswith('.apk')}
full_malradar = {i:get_code_size(os.path.join(MALRADAR, i)) for i in os.listdir(MALRADAR) if i.endswith('.apk')}

with open('code_sizes.pickel', "wb") as f:
    pickle.dump({'malradar':full_malradar, 'fdroid':full_fd}, f)
