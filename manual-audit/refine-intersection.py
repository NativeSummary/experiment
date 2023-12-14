from analyzer import *


# 分析成功的交集
with open('../intersec.pickel', "rb") as f:
    intersec = pickle.load(f) #type: set
def main():
    prev_len = len(intersec)
    for key in sorted(intersec):
        out = generate_audit_folder(*key)
        fd_flow = r['flowdroid'][key][2]
        fd_flow2 = f'/home/user/ns/experiment/baseline-fd/intersect-results/{key[1]}/{key[1].removesuffix(".apk")}.xml'
        empty = False
        try:
            eq_flow, new_flow, lost_flow = cmp_set2(fd_flow, fd_flow2)
            if len(eq_flow) + len(new_flow) + len(lost_flow) == 0:
                empty = True
        except FileNotFoundError:
            if len(get_set(fd_flow)) == 0:
                empty = True
        if empty:
            print(f"empty: {fd_flow}")
            intersec.remove(key)
    with open('./intersec-2.pickel', "wb") as f:
        pickle.dump(intersec ,f)
    print(f"prev len: {prev_len}, current len: {len(intersec)}")

if __name__ == '__main__':
    main()
