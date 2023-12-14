

import sys,os,itertools

cwd = os.path.dirname(os.path.realpath(__file__))
prev = cwd[:cwd.rfind('experiment')+len('experiment')]
sys.path.insert(1, prev)

from mem_time_collector import *

with open('../intersec.pickel', "rb") as f:
    intersec = pickle.load(f) #type: set

with open('../code_sizes.pickel', "rb") as f:
    code_sizes = pickle.load(f) #type: set

def match_java_analysis_time(fp):
    path = os.path.join(fp, 'java_analysis.log')
    try:
        return int( match_in_file(r'Repacking spent (.*) ms.$', path)[0] ) / 1000.0
    except:
        raise RuntimeError(f'Cannot get java time: {fp}')

def get_so_times(fp):
    result = {}
    for file in os.listdir(fp):
        if file.endswith('.so.txt'):
            result[file.removesuffix('.txt')] = get_so_time_one(os.path.join(fp, file))
    return result

def get_so_time_one(fp):
    logf = fp.removesuffix('.so.txt')+'.so.log'
    result = {}
    result['total'] = float( read_file(fp) )
    try:
        result['total_script'] = int( match_in_file(r'NativeSummary script execution time: (.*)ms.', logf)[0] ) / 1000.0
    except IndexError:
        result['total_script'] = None
    for time, name in match_in_file(r'Analysis spent (.*) ms for (.*) \(GhidraScript\)', logf):
        result[name] = int(time) / 1000.0
    return result

def average(lst):
    return sum(lst) / len(lst)

def mid(lst):
    return lst[len(lst) // 2]

def average_with_ref(lst):
    return f'{average(lst)}({mid(lst)})'

def calc_averate(range_set=None, assert_exist=False):
    flowdroid_times = []
    ns_flowdroid_times = []
    java_times = []
    total_times = []
    bai_times = []
    ghidra_times = []
    jni_times = []
    mems = []
    flowd_mems = []
    count = 0

    for target in code_sizes:
        for file in code_sizes[target]:
            key = (target, file)
            if range_set is not None and key not in range_set: continue
    # for key in sorted(intersec):
    #     target, file = key
    # for target, file in itertools.chain(zip(itertools.repeat('fdroid'), os.listdir(os.path.join(NS_BASE, f'fdroid-results'))), zip(itertools.repeat('malradar'), os.listdir(os.path.join(NS_BASE, f'malradar-results')))):
    #     key = (target, file)
            fpath_fd = os.path.join(FD_BASE, f'intersect-{target}-results', file)
            fpath_nsfd = os.path.join(FD_BASE, f'intersect-{target}-repacked-results', file)
            xmlname = file.removesuffix('.apk')+'.xml'
            xmlpath = os.path.join(fpath_nsfd, xmlname)
            if not os.path.exists(xmlpath) or file == '18e7754e978423b38408e0d50e0eb815cf917cb7ccd3aea3a9793a39a168a11f.apk': # no result
                # print(f'ns: flowdroid failed: {file}')
                if assert_exist: raise RuntimeError(f'cannot find result for {file}')
                continue
            count += 1
            fpath_ns = os.path.join(NS_BASE, f'{target}-results', file)
            try:
                java_time = match_java_analysis_time(fpath_ns)
            except RuntimeError:
                continue
            java_times.append(java_time)

            total_time = get_time_in_json('ns', fpath_ns)
            total_times.append(total_time)
            
            flowdroid_time = match_unix_time(fpath_fd)
            flowdroid_times.append(flowdroid_time)
            
            ns_flowdroid_time = match_unix_time(fpath_nsfd)
            ns_flowdroid_times.append(ns_flowdroid_time)

            mem = get_mem_in_json(f'ns-{file}', os.path.join(NS_BASE, 'docker_stats.progress'))
            mems.append(mem)
            flowdroid_mem = match_unix_time_mem(fpath_fd)
            flowd_mems.append(flowdroid_mem)
            detailed_time = get_so_times(fpath_ns)
            # print(f'for {key}')
            apk_ghidra_times = []
            for so_name in detailed_time:
                so_detailed_time = detailed_time[so_name]
                if so_detailed_time['total_script'] != None:
                    bai_time = so_detailed_time['total_script']
                    bai_times.append(bai_time)
                else:
                    bai_time = None
                ghidra_time = so_detailed_time['total']
                ghidra_times.append(ghidra_time)
                apk_ghidra_times.append(ghidra_time)
                so_jni_times = []
                for jni in so_detailed_time:
                    if jni == 'total_script': continue
                    if jni == 'total': continue
                    jni_time = so_detailed_time[jni]
                    so_jni_times.append(jni_time)
                    jni_times.append(jni_time)
                if bai_time != None:
                    assert sum(so_jni_times) <= bai_time
                    assert bai_time <= ghidra_time
                # print(f'  for so {so_name}:\n    ghidra_time: {ghidra_time}, bai_time:{bai_time}, all_jni_times: {sum(so_jni_times)}')
            assert sum(apk_ghidra_times) + java_time <= total_time
        # print(f'  total: {total_time}, flowdroid_baseline: {flowdroid_time}, flowdroid: {ns_flowdroid_time}')
        # print(f'  ghidra_times: {sum(apk_ghidra_times)}, java_analysis: {java_time}')
    # return [average(i) for i in [flowdroid_times, ns_flowdroid_times, java_times, ] ]
    print(f'in {count} apps')
    print(f'  total(no fd): {average_with_ref(total_times)}, flowdroid_baseline: {average_with_ref(flowdroid_times)}')
    binary_analysis_t = sum(ghidra_times) / count
    print(f'  total = py_preanalysis: {average(total_times) - (binary_analysis_t) - average(java_times)} binary_analysis: {binary_analysis_t} java_analysis: {average_with_ref(java_times)} flowdroid: {average_with_ref(ns_flowdroid_times)}')
    bai_times_t = sum(bai_times) / count
    print(f'  binary_analysis = ghidra_loading {binary_analysis_t - bai_times_t}, bai_times: {bai_times_t}')
    print(f'  jni_times: {average_with_ref(jni_times)}  ave_so: {len(jni_times) / len(ghidra_times)} avg_mem: {average_with_ref(mems)} avg_fd_mem: {average_with_ref(flowd_mems)}')
    print(f'  (per so): ghidra_times: {average_with_ref(ghidra_times)}, bai_times: {average_with_ref(bai_times)}')

# ======== collect times for each analyzed native method. ================



def main():
    calc_averate()
    print('=====in intersect=======')
    stats = calc_averate(intersec, True)

if __name__ == '__main__':
    main()

'''
  total(no fd): 1035.003970263371, flowdroid_baseline: 324.8406107431935, flowdroid: 329.5091390728483
  binary_analysis: 973.6607582902452 ghidra_times: 495.7680668851417, bai_times: 277.6315046692608, java_analysis: 7.0331184694628455
  jni_times: 19.158730855973957  ave_so: 14.286998875983514 avg_mem: 1188539479.602649 avg_fd_mem: 1951608885.9455483
=====in intersect=======
  total(no fd): 454.81297183300734, flowdroid_baseline: 76.26830258302587, flowdroid: 85.87808118081182
  binary_analysis: 418.55539219493795 ghidra_times: 328.7782935792121, bai_times: 165.4318976608187, java_analysis: 3.408642066420663
  jni_times: 22.499458585858573  ave_so: 7.173913043478261 avg_mem: 790128992.2177122 avg_fd_mem: 1092957047.9704797
'''


# depricated below
'''
intersect:
============
  total: 532.7288209671775, flowdroid_baseline: 196.32374999999993, flowdroid: 359.75916666666626
  ghidra_times: 366.0734342303672, bai_times: 188.91001984126999, java_analysis: 5.155171874999997
  jni_times: 23.4424055944056  ave_so: 7.913043478260869 avg_mem: 852912963.1458334 avg_fd_mem: 3053131604.1666665

all:
============
  total: 1027.9929166079448, flowdroid_baseline: 295.1696826568266, flowdroid: 494.9491291512914
  ghidra_times: 492.77985030674944, bai_times: 274.02046640624985, java_analysis: 7.000030996309971
  jni_times: 18.900871797569536  ave_so: 14.297856336968785 avg_mem: 1184087009.4627306 avg_fd_mem: 3581851672.3247232
'''
