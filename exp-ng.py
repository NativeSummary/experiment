import os
import sqlite3
from collections import namedtuple, defaultdict

from util_funcs import *

ToolRunStat = namedtuple('ToolRunStat', ['tool_name', 'apk_info', 'is_success', 'total_time', 'total_mem', 'flow_count', 'flow_content', 'j2n_find_count', 'j2n_success_count', 'n2j_find_count', 'n2j_success_count', 'native_related_flow_count', 'ns_time_info'])
ApkInfo = namedtuple('ApkInfo', ['name', 'dataset', 'code_size'])
NSTimeInfo = namedtuple('NSTimeInfo', ['total_time', 'pre_analysis_time', 'ghidra_loading', 'bai_script', 'java_time', 'taint_analysis_time'])


cursor.execute()
