# 辅助审计代码

from analyzer import *

# new_flows = load_py_file('ns_fd_lost_native_flows.obj.py')
# lost_flows = load_py_file('ns_fd_new_native_flows.obj.py')

def get_ghidra_proj(target, apk):
    return f'/home/user/ns/experiment/baseline-native_summary/{target}-results/{apk}/project/native_summary.gpr'

audited = set()

# target_flows = 'ns_fd_new_native_flows.obj.py'
target_flows = 'ns_fd_lost_native_flows.obj.py'


target_flows = load_py_file(target_flows)

# sudo xauth add $(sudo -u user xauth list $DISPLAY)
for app, flow in target_flows:
    print(app)
    os.system(f'sudo /home/user/ns/tools/ghidra_10.1.2_PUBLIC/ghidraRun {get_ghidra_proj(*app)}')
    input("press any key to continue")
