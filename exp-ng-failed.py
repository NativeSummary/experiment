import os
from collections import namedtuple, defaultdict

from util_funcs import *



# ============ data definition ===========
# https://stackoverflow.com/questions/16377215/how-to-pickle-a-namedtuple-instance-correctly

# wrap constructor
ToolRunStat = namedtuple('ToolRunStat', ['tool_name', 'apk_info', 'is_success', 'total_time', 'total_mem', 'flow_count', 'flow_content', 'j2n_find_count', 'j2n_success_count', 'n2j_find_count', 'n2j_success_count', 'native_related_flow_count', 'ns_time_info'])

ApkInfo = namedtuple('ApkInfo', ['name', 'dataset', 'code_size'])
NSTimeInfo = namedtuple('NSTimeInfo', ['total_time', 'pre_analysis_time', 'ghidra_loading', 'bai_script', 'java_time', 'taint_analysis_time'])

class DatabaseManager:
    # ============ config =============
    DATABASE_FILE_NAME = 'database.pickel'

    def __init__(self, database_path) -> None:
        self.datbase_path = database_path
        # load database
        if os.path.exists(database_path):
            self.database = load_obj(database_path)
        else:
            self.database = {
                'table_tool_run_stat': [],
                'stat_apk_tool_view': {},
                'stat_apk_view': {},
                'stat_tool_view': {},
                # for apk
                'table_apk_info': [],
                'apk_dataset_view': {} # map from dataset name to apkinfo
            }

    def save_database(self):
        dump_obj(self.database_path, self.database)

    def add_apk_dataset(self, dataset_name, dataset_dir):
        if dataset_name in self.database['apk_dataset_view']:
            print(f'add_apk_dataset: skip scanning apk for {dataset_name}')
            return
        result = defaultdict(lambda:[])
        for file in os.listdir(dataset_dir):
            if not file.endswith('.apk'):
                continue
            apk_info = ApkInfo(file, dataset_name, None)
            self.database['table_apk_info'].append(apk_info)
            result[dataset_name].append(apk_info)
        self.database['apk_dataset_view'][dataset_name] = dict(result)

class FlowDroidCollector:
    # setup result_dir
    def __init__(self, apk_info: ApkInfo, is_repacked=False) -> None:
        self.apk_info = apk_info
        base_path = '/home/user/ns/experiment/baseline-fd'
        if is_repacked:
            self.TOOL_NAME = 'flowdroid-repacked'
            self.result_dir = f'{base_path}/{apk_info.dataset}-repacked-results/{apk_info.name}'
        else:
            self.TOOL_NAME = 'flowdroid'
            self.result_dir = f'{base_path}/{apk_info.dataset}-results/{apk_info.name}'
    # constructor for ToolRunStat
    def build(self, apk_info, time, mem, xmlpath) -> ToolRunStat:
        return ToolRunStat(tool_name=self.TOOL_NAME, 
                           apk_info=apk_info, 
                           total_mem=mem, 
                           total_time=time, 
                           is_success=(xmlpath!=None), 
                           flow_content=xmlpath)

    def collect_time_mem(self):
        time, mem = None, None
        try:
            time = match_unix_time(self.result_dir)
            mem = match_unix_time_mem(self.result_dir)
        except FileNotFoundError:
            print(f"collect_time_mem: FileNotFoundError: {self.result_dir}")
        return time, mem

    def collect(self) -> ToolRunStat:
        # memory and time
        time, mem = self.collect_time_mem()
        # flow info
        xmlname = self.apk_info.name.removesuffix('.apk')+'.xml'
        xmlpath = os.path.join(self.result_dir, xmlname)
        if not os.path.exists(xmlpath):
            xmlpath = None
        else:
            pass


class NSCollector:
    TOOL_NAME = 'ns'
    BASE_PATH = '/home/user/ns/experiment/baseline-native_summary'
    # map from path to obj
    RUNNER_STATS = {}
    DOCKER_STATS = {}
    def __init__(self, apk_info: ApkInfo, target=None) -> None:
        self.apk_info = apk_info
        base_path = NSCollector.BASE_PATH
        self.result_dir = f'{base_path}/{apk_info.dataset}-results/{apk_info.name}'
        self.init_runner_stat()
        self.init_docker_stat()
        if target is None:
            self.target = apk_info.dataset
        else:
            self.target = target

    def init_runner_stat(self):
        # docker stats
        base_path = self.BASE_PATH
        STATS = self.RUNNER_STATS
        stat_path = f'{base_path}/{self.apk_info.dataset}-results/DockerRunner.progress' # docker_stats.progress
        if stat_path in STATS:
            self.runner_stat = STATS[stat_path]
        else:
            self.runner_stat = load_obj(stat_path)['stats']
            STATS[stat_path] = self.runner_stat

    def init_docker_stat(self):
        # docker stats
        base_path = self.BASE_PATH
        STATS = self.DOCKER_STATS
        stat_path = f'{base_path}/{self.apk_info.dataset}-results/docker_stats.progress' # docker_stats.progress
        if stat_path in STATS:
            self.docker_stat = STATS[stat_path]
        else:
            self.docker_stat = load_obj(stat_path)['stats']
            STATS[stat_path] = self.docker_stat

    def collect_time_mem(self):
        time, ret_val = self.runner_stat[f'ns-{self.target}-{self.apk_info.name}']
        mem, cpu = self.docker_stat[f'ns-{self.target}-{self.apk_info.name}']
        return time, mem

    def collect(self) -> ToolRunStat:
        # flow info
        xmlname = self.apk_info.name.removesuffix('.apk')+'.xml'
        xmlpath = os.path.join(self.result_dir, xmlname)
        if not os.path.exists(xmlpath):
            xmlpath = None
        else:
            pass


class JNSAFCollector:
    BASE_PATH = '/home/user/ns/experiment/baseline-jn-saf'
    # map from path to obj
    RUNNER_STATS = {}
    DOCKER_STATS = {}
    # setup result_dir
    def __init__(self, apk_info: ApkInfo) -> None:
        self.apk_info = apk_info
        base_path = JNSAFCollector.BASE_PATH
        self.TOOL_NAME = 'jnsaf'
        self.result_dir = f'{base_path}/{apk_info.dataset}-results/{apk_info.name}'
        self.init_runner_stat()
        self.init_docker_stat()

    def init_runner_stat(self):
        # docker stats
        base_path = JNSAFCollector.BASE_PATH
        STATS = JNSAFCollector.RUNNER_STATS
        docker_stat_path = f'{base_path}/{self.apk_info.dataset}-results/jn-saf.progress' # docker_stats.progress
        if docker_stat_path in STATS:
            self.runner_stat = STATS[docker_stat_path]
        else:
            self.runner_stat = load_obj(docker_stat_path)['stats']
            STATS[docker_stat_path] = self.runner_stat

    def init_docker_stat(self):
        # docker stats
        base_path = JNSAFCollector.BASE_PATH
        STATS = JNSAFCollector.DOCKER_STATS
        docker_stat_path = f'{base_path}/docker_stats.progress' # docker_stats.progress
        if docker_stat_path in STATS:
            self.docker_stat = STATS[docker_stat_path]
        else:
            self.docker_stat = load_obj(docker_stat_path)['stats']
            STATS[docker_stat_path] = self.docker_stat

    def get_taint_info_jnsaf(self):
        p = os.path.join(self.result_dir, "docker_runner.stdout.txt")
        return re.findall(r'INFO@JNSafService:taint_result(.*)$', read_file(p), re.DOTALL)

    def collect_time_mem(self):
        time, ret_val = self.runner_stat[f'jn-saf-{self.apk_info.name}']
        mem, cpu = self.docker_stat[f'jn-saf-{self.apk_info.name}']
        return time, mem

    def collect(self) -> ToolRunStat:
        fpath = self.result_dir
        taint_info = self.get_taint_info_jnsaf()
        if len(taint_info) > 0:
            taint_info = taint_info[0]
            # # python3 ./mem_time_collector.py > jnsaf-malradar.rerun.txt
            # try:
            #     mem = get_mem_in_json(f'jn-saf-{file}', os.path.join(JNSAF_BASE, 'docker_stats.progress'))
            # except KeyError:
            #     print('warn: check mem info in other progress')
            #     mem = get_mem_in_json(f'jn-saf-{file}', os.path.join(NS_BASE, 'docker_stats.progress'))
            #     continue
            # jnsaf_datas[(target,file)] = (time, mem, taint_info)


class TemplageCollector:
    def __init__(self, result_dir) -> None:
        self.result_dir = result_dir

    def collect(self) -> ToolRunStat:
        pass
