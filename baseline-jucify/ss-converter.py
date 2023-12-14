
orig_ss = "/home/user/ns/experiment/baseline-fd/ss_taintbench.txt"

with open(orig_ss, 'r') as f:
    ss = f.readlines()

results = []
for line in ss:
    line = line.strip()
    if line.startswith("%") and '->' in line:
        continue
    if '->' in line:
        line = '|'.join(reversed(line.split('->', 1))).strip()
    # print(repr(line))
    line = line.replace('_SOURCE_', 'SOURCE')
    line = line.replace('_SINK_', 'SINK')
    results.append(line)

print('\n'.join(results))
