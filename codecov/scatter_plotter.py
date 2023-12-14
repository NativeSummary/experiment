# 散点图: blocknum -> time
# blocknum -> coverage

import os,json

NS_BASE = '/home/user/ns/experiment/baseline-native_summary'
JUCIFY_BASE = '/home/user/ns/experiment/baseline-jucify/coverage-results'
NS_NOOPT_PATH = os.path.join(NS_BASE, "nooptcompare-results")


def collect_ns(results_path):
    blocknum_map = {} # from (class, method name, signature)

    datapoints = []
    for file in os.listdir(results_path):
        if not file.endswith('.apk'):
            continue
        result_dir = os.path.join(results_path, file)
        for infile in os.listdir(result_dir):
            if not file.endswith('.perf.json'):
                continue
            perf_file = os.path.join(result_dir, infile)
            with open(perf_file, 'r') as f:
                stats = json.load(f)
                for stat in stats['functions']:
                    blocknum_map[(stat['class'], stat['name'], stat['signature'])] = stat['static_coverage']
                    datapoints.append(len(stat['static_coverage']), stat['coverage_percentage'])
    return blocknum_map, datapoints

def collect_jucify(results_path, blocknum_map):
    for file in os.listdir(results_path):
        if not file.endswith('.apk'):
            continue
        result_dir = os.path.join(results_path, file, file.removesuffix('.apk')+'_result')
        for infile in os.listdir(result_dir):
            if not file.endswith('.cov.json'):
                continue
            perf_file = os.path.join(result_dir, infile)
            with open(perf_file, 'r') as f:
                stats = json.load(f)
                for stat in stats['functions']:
                    blocknum_map[(stat['class'], stat['name'], stat['signature'])] = stat['static_coverage']
                    datapoints.append(len(stat['static_coverage']), stat['coverage_percentage'])


def main():
    pass

if __name__ == '__main__':
    main()