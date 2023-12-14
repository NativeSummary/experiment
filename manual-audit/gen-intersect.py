# 在dataset文件夹生成intersect数据集，重跑flowdroid，得到泄露路径

import pickle,shutil,os


# with open('../intersec.pickel', "rb") as f:
#     intersec = pickle.load(f) #type: set

with open('./intersec-2.pickel', "rb") as f:
    intersec = pickle.load(f) #type: set

out = '/home/user/ns/dataset/intersect'
os.makedirs(out, exist_ok=True)

for ty, app in intersec:
    shutil.copy(f'/home/user/ns/dataset/{ty}/{app}', out)
