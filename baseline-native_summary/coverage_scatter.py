#!/usr/bin/python3
import os,sys

script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
parent_dir = os.path.dirname(script_dir)
sys.path.insert(1, parent_dir)

from util_funcs import load_json, match_in_file



opt_base = '/home/user/ns/experiment/baseline-native_summary/optcompare-results'
noopt_base = '/home/user/ns/experiment/baseline-native_summary/nooptcompare-results'
ju_base = '/home/user/ns/experiment/baseline-jucify/coverage-results'
def main():
    datapoints_opt = []
    datapoints_noopt = []
    datapoints_jucify = []
    for file in os.listdir(opt_base):
        if not file.endswith('.apk'):
            continue
        fp_opt = os.path.join(opt_base, file)
        fp_noopt = os.path.join(noopt_base, file)
        fp_ju = os.path.join(ju_base, file)
        if not os.path.exists(fp_noopt):
            print(f'error: apk no noopt: {fp_noopt}')
            continue
        if not os.path.exists(fp_ju):
            print(f'error: apk no juciy: {fp_ju}')
            continue
        for so in os.listdir(fp_opt):
            if not so.endswith('.so'):
                continue
            sofp_opt = os.path.join(fp_opt, so)
            sofp_noopt = os.path.join(fp_noopt, so)
            if not os.path.exists(fp_noopt):
                print(f'error: so no noopt: {fp_noopt}')
                continue
            try:
                perf_opt = load_json(f'{sofp_opt}.perf.json')
            except FileNotFoundError:
                print(f'failed for {sofp_opt}')
                continue
            try:
                perf_noopt = load_json(f'{sofp_noopt}.perf.json')
            except FileNotFoundError:
                print(f'failed for {sofp_noopt}')
                continue
            func_map = perf_opt["function_address_ranges"]

            for func_stat in perf_opt["functions"]:
                # scatter plot for two version.
                func_stat_noopt = find_func_stat(perf_noopt['functions'], func_stat['binary_address'])
                func_cov = stats_get_coverage(func_stat)
                func_cov_noopt = stats_get_coverage(func_stat_noopt)
                time_s = func_stat['time_ms'] / 1000
                time_s_noopt = func_stat_noopt['time_ms'] / 1000
                datapoints_opt.append((time_s, func_cov))
                datapoints_noopt.append((time_s_noopt, func_cov_noopt))
                # scatter data for angr
            
            # jucify coverage
            arch = match_in_file(r'Selected arch is (.*)$', f'{fp_opt}/pre_analysis.log')[0]
            assert arch in ['arm64-v8a', 'armeabi-v7a', 'armeabi']
            is_32 = arch != 'arm64-v8a'
            perfpath_ju = f'{fp_ju}/{file.removesuffix(".apk")}_result/{so}.cov.json'
            try:
                perf_ju = load_json(perfpath_ju) # type: dict
            except FileNotFoundError:
                print(f'jucify not found: {perfpath_ju}')
                continue
            if len(perf_ju) == 0:
                print(f'jucify no coverage: {perfpath_ju}')
                continue
            for func, stat in perf_ju.items():
                time_s_jucify = stat['time']
                func_cov_ju = calc_func_coverage_jucify(stat['coverage'], func_map, is_32)
                datapoints_jucify.append((time_s_jucify, func_cov_ju))

    import matplotlib.pyplot as plt
    # plt.scatter(*zip(*datapoints_opt), s=1)
    # plt.scatter(*zip(*datapoints_noopt), s=1)
    plt.scatter(*zip(*datapoints_jucify), s=1)
    plt.savefig('func_coverage_scatter.pdf', bbox_inches='tight')


# covered_addrs_static = []
# covered_addrs_opt = []
# covered_addrs_noopt = []
# covered_addrs_jucify = []
# covered_funcs_static = []
# covered_funcs_opt = []
# covered_funcs_noopt = []
# covered_funcs_jucify = []

def find_func_stat(stats, entry_addr):
    for func_stat in stats:
        if func_stat["binary_address"] == entry_addr:
            return func_stat


def stats_get_coverage(func_stat):
    covs = func_stat['detailed_per_function_coverage']
    percents = []
    for i in covs:
        if covs[i]['percentage'] < 0:
            continue
        percents.append(covs[i]['percentage'])
        assert covs[i]['percentage'] >= 0
    return sum(percents)


def calc_func_coverage_jucify(cov, func_map, is_32):
    covered_func = set()
    for addr in cov:
        f = get_func(func_map, addr, is_32)
        if f is None:
            continue
        covered_func.add(f)
    return len(covered_func)

GHIDRA_BASE_32 = 0x10000
GHIDRA_BASE_64 = 0x100000
ANGR_BASE = 0x400000
def get_func(func_map, addr, is_32):
    adjusted_addr = addr - ANGR_BASE
    if is_32:
        adjusted_addr += GHIDRA_BASE_32
    else:
        adjusted_addr += GHIDRA_BASE_64
    for func_entry, body_range in func_map.items():
        low, high = body_range[0]
        if adjusted_addr > low and adjusted_addr < high:
            return func_entry
        

if __name__ == '__main__':
    main()
