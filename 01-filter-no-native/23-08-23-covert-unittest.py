# generate base unittest file for pre_analysis module.
# then manually check the unittest result to ensure the resolution is correct
import sys,json,collections

sys.path.append('/home/user/ns/dev/NativeSummary/native_summary_bai')

from pre_analysis.symbol_parser import extract_names, refactored_class_name


result = collections.defaultdict(lambda:[])


def handle_json(path):
    global result
    with open(path, 'r') as f:
        obj = json.load(f)

    for apk, stat in obj.items():
        so_stat = stat["so_stat"]
        for key in so_stat:
            data = so_stat[key][1]
            if data is None:
                continue
            if len(data) > 0:
                res = []
                for sym in data:
                    clz, method, sig = extract_names(sym)
                    refactored_cls_name = refactored_class_name(clz)
                    if sig is not None:
                        res.append([sym, ' '.join((clz, method, sig))])
                    else:
                        res.append([sym, ' '.join((clz, method))])
                result[' '.join((apk, key))] = res

handle_json('/home/user/ns/experiment/01-filter-no-native/apk_result_fdroid.json')
handle_json('/home/user/ns/experiment/01-filter-no-native/apk_result_malradar.json')

with open('/home/user/ns/experiment/01-filter-no-native/unittest1.json', 'w') as f:
    json.dump(dict(result), f, indent=2)
