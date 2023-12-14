import pickle,os,sys

file_path = os.path.realpath(__file__)
elem = 'experiment'
module_path = file_path[:file_path.rfind(elem)+len(elem)]
sys.path.insert(1, module_path)


if __name__ == '__main__':
    with open('mem_time_info.pickel', "rb") as f:
        r = pickle.load(f)

    with open('code_sizes.pickel', "rb") as f:
        cs = pickle.load(f)

    with open('intersec.pickel', "rb") as f:
        intersec = pickle.load(f)

# with open('./manual-audit/intersec-2.pickel', "rb") as f:
#     intersec2 = pickle.load(f)

def code_size(target, name):
    return cs[target][name]



series = ['jucify', 'flowdroid', 'jnsaf', 'ns']
colors = ["red", "green", "black", "orange"]
# series = ['flowdroid', 'ns']
# colors = ["green", 'orange']
targets = ['malradar', 'fdroid']




def plot_time_intersec():
    xs = []
    ys = []
    colors_axis = []
    for color, serie in zip(colors, series):
        for target, apk in intersec:
            time, mem, taint = r[serie][(target, apk)]
            cs = code_size(target, apk)
            if (time > 1500): continue # 限制范围，等效于放大
            if cs > 0.4*10**8: continue
            xs.append(cs)
            ys.append(time)
            colors_axis.append(color)
    import matplotlib.pyplot as plt
    plt.scatter(xs, ys, c=colors_axis, s=1)
    plt.savefig('time-scatter.pdf', bbox_inches='tight')

# #success apps in paper
def success_counter():
    total_apk_count = 0
    fd_success_count = 0
    jucify_success_count = 0
    jnsaf_success_count = 0
    ns_success_count = 0
    jucify_star_success_count = 0
    
    for target in targets:
        for apk in cs[target]:
            total_apk_count += 1
            try:
                time1, mem1, taint1 = r['flowdroid'][(target, apk)]
                fd_success_count += 1
            except KeyError:
                pass
            try:
                time1, mem1, taint1 = r['jucify'][(target, apk)]
                jucify_success_count += 1
            except KeyError:
                pass
            try:
                time1, mem1, taint1 = r['jucify*'][(target, apk)]
                jucify_star_success_count += 1
            except KeyError:
                pass
            try:
                time1, mem1, taint1 = r['jnsaf'][(target, apk)]
                jnsaf_success_count += 1
            except KeyError:
                pass
            try:
                time1, mem1, taint1 = r['ns'][(target, apk)]
                ns_success_count += 1
            except KeyError:
                pass
    print(f'total: {total_apk_count}, ')
    print(f'flowdroid: {fd_success_count}, jnsaf: {jnsaf_success_count}, jucify: {jucify_success_count}')
    print(f'ns: {ns_success_count} jucify_star: {jucify_star_success_count}')

def average(lst):
    return sum(lst) / len(lst)

import collections
def average_mem_times(range_set=None, assert_exist=False):
    if assert_exist:
        print(f'in {len(range_set)} apps:')
    tools = ['flowdroid', 'jucify', 'jnsaf', 'ns']
    mems = collections.defaultdict(lambda:[])
    times = collections.defaultdict(lambda:[])
    max_time = collections.defaultdict(lambda:0)
    max_mem = collections.defaultdict(lambda:0)
    for target in cs:
        for apk in cs[target]:
            key = (target, apk)
            if range_set is not None and key not in range_set: continue
            for tool in tools:
                try:
                    time1, mem1, taint1 = r[tool][key]
                except KeyError:
                    if assert_exist: raise
                    continue
                times[tool].append(time1)
                mems[tool].append(mem1)
                if time1 > max_time[tool]:
                    max_time[tool] = time1
                if mem1 > max_mem[tool]:
                    max_mem[tool] = mem1
    for tool in tools:
        print(f'{tool} avg time: {average(times[tool])} avg mem: {average(mems[tool])} max: {max_time[tool]},{max_mem[tool]}')
    return dict(times), dict(mems)

def plot_box(data, fname, xlabel="Time (s)", labels = ['flowdroid', 'jucify', 'jnsaf', 'ns'], scale = 1):
    import seaborn as sns
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    sns.set_theme(style="whitegrid")
    plt.figure(constrained_layout=True, figsize=(5,2)) # 
    plot = sns.boxplot(data=[[i*scale for i in l] for l in data.values()], orient='h', width=0.4, boxprops={'facecolor':'none'})
    plot.set_xscale("log")
    plot.set_xlabel(xlabel)
    # plot.get_figure().tight_layout()
    plot.set_yticks(range(len(labels)), labels=labels)
    plot.margins(0.05)
    # plot.xaxis.get_major_locator().set_params(subs='all')
    # print (plot.xaxis.get_major_formatter())
    plot.xaxis.set_major_formatter(ticker.LogFormatter())
    plot.get_figure().savefig(fname)


def plot2box_fix(data1, data2, seqs, fname, xlabel="Time (s)", labels = ['FD', 'Jucify', 'JN-SAF', 'NS/FD'], scale = 1):
    '''
    changed: https://stackoverflow.com/questions/67335075/logformatter-with-sparse-tick-labels-and-no-scientific-notation
    '''
    import seaborn as sns
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    import matplotlib.patheffects as path_effects
    import statistics

    data1_ = data1
    data2_ = data2
    if type(data1) is dict:
        data1 = [data1[i] for i in seqs]
    if type(data2) is dict:
        data2 = [data2[i] for i in seqs]
    # sns.set_theme(style="whitegrid")
    fig = plt.figure(2, constrained_layout=True) # , figsize=(5,len(labels))
    # fig.set_size_inches(5,len(labels))
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["figure.figsize"] = (5,len(labels))
    f, axes = plt.subplots(2, 1, constrained_layout=True, sharex='col')
    axes[0].set_title('On 271 apps (intersection of successful apps)', fontsize=12.0)
    axes[0].xaxis.set_tick_params(which='both', labelbottom=True)
    # plot = sns.boxplot(data=[[i*scale for i in l] for l in data1], orient='h', width=0.4, boxprops={'facecolor':'none'}, ax=axes[0])
    plot1_data = [[i*scale for i in l] for l in data1]
    plot = sns.boxplot(data=plot1_data, orient='h', width=0.7, ax=axes[0]) # boxprops={'facecolor':'none'}
    plot.set_xscale("log")
    # plot.set_xlabel(xlabel)
    # plot.get_figure().tight_layout()
    plot.set_yticks(range(len(labels)), labels=labels, fontsize=12.0)
    plot.margins(0.05)
    # plot.xaxis.get_major_locator().set_params(subs='all')
    # print (plot.xaxis.get_major_formatter())
    # plot.set_title("In 271 apps in the intersection")
    plot.xaxis.set_major_formatter(ticker.LogFormatter())
    
    for data, ytick in zip(plot1_data, plot.get_yticks()):
        text_offset = 0
        text = plot.text(statistics.median(data) + text_offset, ytick, f"{statistics.median(data):.2f}", 
                verticalalignment='center', ha='center', size='9',color='w',weight='bold')
        text.set_path_effects([
            path_effects.Stroke(linewidth=2, foreground='black'),
            path_effects.Normal(),
        ])
    
    axes[1].set_title('On all successful apps of each tool', fontsize=13.0)
    plot2_data = [[i*scale for i in l] for l in data2]
    plot = sns.boxplot(data=plot2_data, orient='h', width=0.7, ax=axes[1])
    plot.set_xscale("log")
    plot.set_xlabel(xlabel)
    # plot.get_figure().tight_layout()
    plot.set_yticks(range(len(labels)), labels=[label+"" for label in labels], fontsize=12.0)
    plot.margins(0.05)
    # plot.xaxis.get_major_locator().set_params(subs='all')
    # print (plot.xaxis.get_major_formatter())
    # plot.set_title("In all apps")
    plot.xaxis.set_major_formatter(ticker.LogFormatter())

    for data, ytick in zip(plot2_data, plot.get_yticks()):
        text_offset = 0
        text = plot.text(statistics.median(data) + text_offset, ytick, f"{statistics.median(data):.2f}", 
                verticalalignment='center', ha='center', size='9',color='w',weight='bold')
        text.set_path_effects([
            path_effects.Stroke(linewidth=2, foreground='black'),
            path_effects.Normal(),
        ])

    plot.get_figure().savefig(fname)


def plot2box(data1, data2, fname, xlabel="Time (s)", labels = ['FD', 'Jucify', 'JN-SAF', 'NS/FD'], scale = 1):
    '''
    changed: https://stackoverflow.com/questions/67335075/logformatter-with-sparse-tick-labels-and-no-scientific-notation
    '''
    data1_ = data1
    data2_ = data2
    if type(data1) is dict:
        raise RuntimeError()
    if type(data2) is dict:
        raise RuntimeError()
    import seaborn as sns
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    # sns.set_theme(style="whitegrid")
    fig = plt.figure(2, constrained_layout=True) # , figsize=(5,len(labels))
    # fig.set_size_inches(5,len(labels))
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["figure.figsize"] = (5,len(labels))
    f, axes = plt.subplots(2, 1, constrained_layout=True, sharex='col')
    axes[0].set_title('On 271 apps (intersection of successful apps)', fontsize=10.0)
    axes[0].xaxis.set_tick_params(which='both', labelbottom=True)
    # plot = sns.boxplot(data=[[i*scale for i in l] for l in data1], orient='h', width=0.4, boxprops={'facecolor':'none'}, ax=axes[0])
    plot = sns.boxplot(data=[[i*scale for i in l] for l in data1], orient='h', width=0.7, ax=axes[0]) # boxprops={'facecolor':'none'}
    plot.set_xscale("log")
    # plot.set_xlabel(xlabel)
    # plot.get_figure().tight_layout()
    plot.set_yticks(range(len(labels)), labels=labels)
    plot.margins(0.05)
    # plot.xaxis.get_major_locator().set_params(subs='all')
    # print (plot.xaxis.get_major_formatter())
    # plot.set_title("In 271 apps in the intersection")
    plot.xaxis.set_major_formatter(ticker.LogFormatter())
    axes[1].set_title('On all successful apps of each tool', fontsize=10.0)
    plot = sns.boxplot(data=[[i*scale for i in l] for l in data2], orient='h', width=0.7, ax=axes[1])
    plot.set_xscale("log")
    plot.set_xlabel(xlabel)
    # plot.get_figure().tight_layout()
    plot.set_yticks(range(len(labels)), labels=[label+"" for label in labels])
    plot.margins(0.05)
    # plot.xaxis.get_major_locator().set_params(subs='all')
    # print (plot.xaxis.get_major_formatter())
    # plot.set_title("In all apps")
    plot.xaxis.set_major_formatter(ticker.LogFormatter())
    plot.get_figure().savefig(fname)


def plot2box_jnitime(data1, data2, title1, title2, fname, xlabel="Time (s)", labels1 = ['FD', 'Jucify', 'JN-SAF', 'NS/FD'], labels2 = ['FD', 'Jucify', 'JN-SAF', 'NS/FD'], scale = 1):
    '''
    changed: https://stackoverflow.com/questions/67335075/logformatter-with-sparse-tick-labels-and-no-scientific-notation
    '''
    data1_ = data1
    data2_ = data2
    if type(data1) is dict:
        raise RuntimeError()
    if type(data2) is dict:
        raise RuntimeError()
    import seaborn as sns
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    import matplotlib.patheffects as path_effects
    import statistics
    # sns.set_theme(style="whitegrid")
    fig = plt.figure(2, constrained_layout=True) # , figsize=(5,len(labels))
    # fig.set_size_inches(5,len(labels))
    plt.rcParams["figure.figsize"] = (5,max(len(labels1), len(labels2)))
    plt.rcParams["font.family"] = "Times New Roman"
    f, axes = plt.subplots(2, 1, constrained_layout=True, sharex='col')
    axes[0].set_title(title1, fontsize=12.0)
    axes[0].xaxis.set_tick_params(which='both', labelbottom=True)
    # plot = sns.boxplot(data=[[i*scale for i in l] for l in data1], orient='h', width=0.4, boxprops={'facecolor':'none'}, ax=axes[0])
    plot1_data = [[i*scale for i in l] for l in data1]
    plot = sns.boxplot(data=plot1_data, orient='h', width=0.7, ax=axes[0]) # boxprops={'facecolor':'none'}
    plot.set_xscale("log")
    # plot.set_xlabel(xlabel)
    # plot.get_figure().tight_layout()
    plot.set_yticks(range(len(labels1)), labels=labels1, fontsize=12.0)
    plot.margins(0.05)
    # plot.xaxis.get_major_locator().set_params(subs='all')
    # print (plot.xaxis.get_major_formatter())
    # plot.set_title("In 271 apps in the intersection")
    plot.xaxis.set_major_formatter(ticker.LogFormatter())
    
    
    for data, ytick in zip(plot1_data, plot.get_yticks()):
        text_offset = 0
        text = plot.text(statistics.median(data) + text_offset, ytick, f"{statistics.median(data):.2f}", 
                verticalalignment='center', ha='center', size='9',color='w',weight='bold')
        text.set_path_effects([
            path_effects.Stroke(linewidth=2, foreground='black'),
            path_effects.Normal(),
        ])

    axes[1].set_title(title2, fontsize=12.0)
    plot2_data = [[i*scale for i in l] for l in data2]
    plot = sns.boxplot(data=plot2_data, orient='h', width=0.7, ax=axes[1])
    plot.set_xscale("log")
    plot.set_xlabel(xlabel)
    # plot.get_figure().tight_layout()
    plot.set_yticks(range(len(labels2)), labels=[label+"" for label in labels2], fontsize=12.0)
    plot.margins(0.05)
    # plot.xaxis.get_major_locator().set_params(subs='all')
    # print (plot.xaxis.get_major_formatter())
    # plot.set_title("In all apps")
    plot.xaxis.set_major_formatter(ticker.LogFormatter())


    for data, ytick in zip(plot2_data, plot.get_yticks()):
        text_offset = 0
        text = plot.text(statistics.median(data) + text_offset, ytick, f"{statistics.median(data):.2f}", 
                verticalalignment='center', ha='center', size='9',color='w',weight='bold')
        text.set_path_effects([
            path_effects.Stroke(linewidth=2, foreground='black'),
            path_effects.Normal(),
        ])

    plot.get_figure().savefig(fname)


'''
flowdroid avg time: 343.7562761506273 avg mem: 1960963610.8786612
jucify avg time: 922.3868334027263 avg mem: 6126224307.922592
jnsaf avg time: 272.04450500075535 avg mem: 6239796606.212365
ns avg time: 1365.3815378359782 avg mem: 2081101437.5661764
=======intersec========
in 271 apps:
flowdroid avg time: 76.26830258302587 avg mem: 1092957047.9704797
jucify avg time: 600.607295094381 avg mem: 5894569612.062731
jnsaf avg time: 249.20496305768341 avg mem: 6085069250.564575
ns avg time: 540.691053013819 avg mem: 1219489136.7601476
'''
'''
flowdroid avg time: 1730.091308691308 avg mem: 4003011730.26973
jucify avg time: 922.3868334027263 avg mem: 6126224307.922592
jnsaf avg time: 272.04450500075535 avg mem: 6239796606.212365
ns avg time: 1523.6468347144346 avg mem: 3878598490.441003
=======intersec========
in 271 apps:
flowdroid avg time: 101.41734317343173 avg mem: 1723968103.3210332
jucify avg time: 600.607295094381 avg mem: 5894569612.062731
jnsaf avg time: 249.20496305768341 avg mem: 6085069250.564575
ns avg time: 645.8124183274724 avg mem: 2074940703.1697416
'''

# 2023年3月23日 找到JN-SAF能跑出来的相关APK，然后改了那边python代码重跑
from util_funcs import match_in_file_bytes, match_in_file, read_file, match_in_str, read_file_bytes
def jnsaf_find_native():
    result = set()
    gen_summ_counts = 0
    JNBASE = '/home/user/ns/experiment/baseline-jn-saf'
    for ty in ['fdroid', 'malradar']:
        rp = os.path.join(JNBASE,f'{ty}-results')
        for file in os.listdir(rp):
            if not file.endswith('.apk'): continue
            fullp = os.path.join(rp, file, f'{file}.pystderr.log')
            if not os.path.exists(fullp): continue
            matches = match_in_file_bytes(b'Server GenSummary', fullp) # 判断存在Server GenSummary
            if len(matches) <= 0: continue
            gen_summ_counts += len(matches)
            result.add((ty, file))
    # print(result) # {('fdroid', 'teaonly.droideye_8.apk'), ('fdroid', 'is.xyz.omw_40.apk'), ('malradar', '92237bcc0fb7b7e67820f8f1e2f6b643b5b954816bff16186651400027abff16.apk'), ('fdroid', 'io.githubfede0d.planetrider_1.apk'), ('fdroid', 'com.roguetemple.hydroid_1500.apk'), ('fdroid', 'org.navitproject.navit_6382.apk'), ('malradar', '314de858ed8d816213020c71ef78a8c4616bac91a171349b703e44747832fca3.apk'), ('malradar', '5137f72d7fec55b0a6e504a923c95b891410f99ed7ed8b37d8499ae4e5bbc6fe.apk'), ('malradar', '7d3a00c93cbf15df1afab245f9be47feb27c862d51581dadaec50378bee7d5fa.apk'), ('malradar', '8963b16b3002bbeeba934d6bfd5194dc7682cdf916c3da2933f93c19de194aab.apk'), ('malradar', '34660a36d8159c844557d302d6b0c2c9a3980487d9756f52f9cef67d5ef56108.apk'), ('fdroid', 'fr.ubordeaux.math.paridroid_25.apk'), ('fdroid', 'eu.faircode.netguard_2022111001.apk'), ('fdroid', 'ir.hsn6.k2_2.apk'), ('malradar', 'bbc268ca63eeb27e424fec1b3976bab550da304de18e29faff94d9057b1fa25a.apk'), ('fdroid', 'com.reecedunn.espeak_21.apk'), ('fdroid', 'st.wow.git.hrm_3.apk'), ('malradar', 'f2e260c122552cac14d04b50d8ac941678c58fde314f7e625797b8c567f17431.apk'), ('malradar', '43b36c438a3531e42623fbd00f5b57066a4db8048ce8e0ab0b5ecf9eac67aabf.apk'), ('fdroid', 'com.shurik.droidzebra_17.apk'), ('malradar', 'aae8a67645a4030b7c40af90a1c7fec270f2b8c0d736093321a05adeba012409.apk'), ('malradar', '8b0853e3a0e25be0b0601578028cf2ef39830e331e64a88089a2b25b0449d221.apk'), ('fdroid', 'org.mupen64plusae.v3.alpha_87.apk'), ('fdroid', 'de.kromke.andreas.mediascanner_18.apk'), ('malradar', '297cb76d16a1d875240e7495841ff61ee104b6b8c75e3b2db27e8eadae3c73bf.apk'), ('malradar', '7c840433020c33e16e942a39d53c593ce58db680a41955a8a29139cf022be8dd.apk'), ('fdroid', 'com.xenris.liquidwarsos_11.apk'), ('malradar', '04a204adfbe677c3587e26dc31ac008d6c147265a455f216cbe9a441469d4c30.apk'), ('fdroid', 'org.synergy_2.apk'), ('fdroid', 'ru.evgeniy.dpitunnel_13.apk'), ('fdroid', 'org.mattvchandler.a2050_190010009.apk'), ('malradar', '6e995d68c724f121d43ec2ff59bc4e536192360afa3beaec5646f01094f0b745.apk'), ('fdroid', 'trikita.obsqr_16.apk'), ('malradar', 'a76f6948599757e395aa29ab389ef661dd8b16a08deb67dd277471a8b09be30d.apk'), ('malradar', '5a01367d32f64fc1c956fe482bf04767c707159baa21581f1461e03a6a45503d.apk'), ('fdroid', 'ir.hsn6.defendo_8.apk'), ('malradar', '11818e4c330c15835388509481da5beff560b161847364a6857a714f1f8f6d85.apk'), ('fdroid', 'de.spiritcroc.defaultdarktheme_oms_53.apk'), ('malradar', 'ab711252a34081515c25dbf0359ba744662973ea8c984acb9e903d706ae62d44.apk'), ('malradar', '211d8411751a80b57f50699b91c5ca8dd344e4b5ea0ac6f713298ab78a496060.apk'), ('malradar', '47b5308eb059b087763cc5e156325eded042cc82220a8ba3d4ffafd3c5dcb024.apk'), ('malradar', 'ecb6603a8cd1354c9be236a3c3e7bf498576ee71f7c5d0a810cb77e1138139ec.apk'), ('malradar', 'e298ef75b1ab8fca25481b1ce36ad9aee4d5b4fcc113f7b51f23c3a076e857fb.apk'), ('malradar', '08316f05f39965faac3f54c8e48872fe67416bc35b89ee165c1e38a2ee0b8822.apk'), ('malradar', '5769f8e5133688978b2e2e5878f968aaac88a8c8ba9dff39bafe74d04c21b40c.apk'), ('malradar', '3793cdf0ad01d60962aeaf2e2352f7824383a093809334bb6f22511f56cea12a.apk'), ('malradar', 'f51a27163cb0ddd08caa29d865b9f238848118ba2589626af711330481b352df.apk'), ('malradar', '58ed39c6ff742bfe02f7a799651a376e4eb6689684716d8e9c52d2538247db86.apk'), ('malradar', 'c9ad0c5c9e3efcbd96ddd0160654d6c169541b680e448e936963b8ad342da3b9.apk'), ('fdroid', 'aq.metallists.loudbang_47.apk'), ('fdroid', 'org.petero.droidfish_98.apk'), ('fdroid', 'net.tedstein.AndroSS_17.apk'), ('malradar', 'd5b9633a5b0bf99d4f376a632219500874c42deb1e70659a3d3694b11d8ae06c.apk'), ('fdroid', 'com.formfun_1.apk'), ('fdroid', 'idv.markkuo.ambitsync_9.apk'), ('malradar', 'd93dac3ad67afa6ed6e7ec90eeed771b2b6558d92cbe4fae23bfbc7950ebed68.apk'), ('malradar', '95548ceecfcb927bb1b41f7da1c8287244bd0529f9769146eec2dd5321e500aa.apk'), ('fdroid', 'com.emanuelef.remote_capture_61.apk'), ('fdroid', 'com.viper.simplert_2.apk'), ('malradar', '60cfc73feb5404f1cad88221c7f027216d2e24f264338954df921d8aba38cba5.apk'), ('malradar', 'd783d5161fc18ff0e1abe2f48bb9e2e743a85df17368d29d992033701c678e98.apk'), ('malradar', 'b4a8a6b8cd302fe614331d7549ca09b586b0542993d8329d77b65b3cbca3ea37.apk'), ('malradar', '228c01021d917bdc2858b07b21ec9e5103e2b85ae42aabccf933de958639b55c.apk'), ('fdroid', 'com.oF2pks.kalturadeviceinfos_24.apk'), ('fdroid', 'org.servalproject_2371.apk'), ('fdroid', 'io.github.kobuge.games.minilens_2.apk'), ('fdroid', 'troop.com.freedcam_282.apk'), ('malradar', '58be55b3bc11687c63fb15755a317335f881dece298f9aaf5353c4f35423d6c6.apk'), ('fdroid', 'org.echoline.drawterm_2.apk'), ('fdroid', 'org.jschwab.openrecipes_4.apk'), ('malradar', 'b2cade8370255cb10d7183d1c301443c6a2d31e2db579081daa741dcb1c5a8f0.apk'), ('fdroid', 'com.roguetemple.hyperroid_12070.apk'), ('malradar', '54f2aa690954ddfcd72e0915147378dd9a7228954b05c54da3605611b2d5a55e.apk'), ('malradar', '3327c2a0765817e7c2d5787c1889a9dc9abea9593077b8fb217161de499374bf.apk'), ('malradar', '8bb362dda2ccad540026105379a3880c78b502485440aaf3ccdb1272cb63c3d1.apk'), ('fdroid', 'in.p1x.tanks_of_freedom_20.apk'), ('malradar', 'a656eff1c3862fbce28e21e638373a6557e8a3be9a2593ebd2d8a8db44328c8b.apk'), ('fdroid', 'com.philolog.hoplitekeyboard_30.apk'), ('fdroid', 'ir.hsn6.trans_4.apk'), ('fdroid', 'com.atelieryl.wonderdroid_51.apk'), ('fdroid', 'org.vi_server.androidudpbus_1.apk'), ('malradar', '9684b915870cbe07fc75070985ae39d30aeb16db29eb9f3b685d72ac6224252c.apk'), ('malradar', 'a6b8d6663444496d2b55cc07dae01d3b0bf3bb18c796de16950d438fb65babab.apk'), ('fdroid', 'com.Bisha.TI89EmuDonation_1133.apk'), ('fdroid', 'one.librem.tunnel_1000299.apk'), ('fdroid', 'ir.hsn6.tpb_2.apk'), ('fdroid', 'com.zagayevskiy.pacman_2.apk'), ('fdroid', 'com.commonslab.commonslab_3.apk'), ('malradar', 'c9c6207c3eff3eccf15fd77b3d36a314c04b25905fc233184fc728bf9f72b619.apk'), ('malradar', '55dc3888c4ea2c6585c826d3e8c3007a3c4c16c916da704c2b32ec03eb32860b.apk'), ('malradar', '91e1376421e23e3c1ab677207460fe56c032784f8900067af6266bfc0c6ede4e.apk'), ('fdroid', 'br.odb.knights_5.apk'), ('malradar', 'a346ac7b3dec5c8cabb758d73eb0941f427806db6f572c2453c19223ddf55fe4.apk'), ('fdroid', 'org.tilelessmap.app_4.apk'), ('fdroid', 'net.christianbeier.droidvnc_ng_18.apk'), ('malradar', 'a4295a2120fc6b75b6a86a55e8c6b380f0dfede3b9824fe5323e139d3bee6f5c.apk'), ('malradar', '3cd62210ef53bca2b2aef1bd8ced308adfa7187ff3f1837248b22bf9fd81bcda.apk'), ('fdroid', 'org.kwaak3_1.apk'), ('fdroid', 'com.opendoorstudios.ds4droid_463.apk'), ('fdroid', 'im.status.ethereum_2022093016.apk'), ('malradar', '0497b6000a7a23e9e9b97472bc2d3799caf49cbbea1627ad4d87ae6e0b7e2a98.apk'), ('fdroid', 'com.write.Quill_41.apk'), ('malradar', 'b1f70b82aba39865b32d392faba2c3dc9e793d7ec082760b6c7627969083e2fb.apk'), ('malradar', 'a528951fa2a7a51a12f8d5f159b0194342e1330205c03c46c954461057b98ce9.apk'), ('malradar', '9e03bf2b1a57ad4d1be9ad9317499a977025d5167e23b695f942e5961e6e61d7.apk'), ('malradar', 'eadcd88ebe96a7ce3024aeb0a44e010bf311a4274e8d5de00f100f6f2dee02c7.apk'), ('malradar', '37250e02eff4caf36cb0a173f7dc5fc92ca0df8403ab4efd3fed35103ca40671.apk'), ('malradar', 'a5724477db2d9d625f9a2c8de1a0f9ca6558727af243bcbbcb02dd5b884f4ccc.apk'), ('malradar', '6261be516a54d8566348b8305e96f34bdbf4f11620350c5f36f4bc3cb67fc181.apk'), ('malradar', 'f67a613a2b29a7013c94c51b5b0d53555058f06e02ebaeb58c2e8cee035f5a46.apk'), ('malradar', '8a1eb641cc67cd7229bf9cd1a103e3d37a1a6015ff3e9f17680fc759bc619187.apk'), ('malradar', '80bdc09dca8c15f662e183115a4ebf96ad6f79bc2b1a9908d57028add2d0ad84.apk'), ('malradar', 'a5b2d73f904072d4da642105fb2092e12ca115d0f7deeff3dc24dd3c7b9b216c.apk'), ('fdroid', 'org.pipoypipagames.towerjumper_13.apk'), ('fdroid', 'se.leap.bitmaskclient_162000.apk'), ('fdroid', 'me.wenxinwang.pulsedroidrtp_6.apk'), ('fdroid', 'com.annie.dictionary.fork_20210415.apk'), ('malradar', '7127825c01dd0e4da2a3bbacb08e5f2a4104de142cb4ae5181be489e376d4320.apk'), ('fdroid', 'org.ea.sqrl_54.apk'), ('malradar', 'f4da643b2b9a310fdc1cc7a3cbaee83e106a0d654119fddc608a4b587c5552a3.apk'), ('malradar', 'b02e391d8de6dda7d2a78a4f65874cd7b584da7c7cbaab33c795e66902cad342.apk'), ('fdroid', 'io.github.muntashirakon.setedit_7.apk'), ('fdroid', 'ir.hsn6.turo_7.apk'), ('malradar', '3650dd5693ab98fb3cf76d25e4d03e809838d1875d0c8765e9a13d84d6151c9b.apk'), ('fdroid', 'com.amanoteam.unalix_9.apk'), ('malradar', '0477596226794c995305ca7fb80bed3ace168924492bb253861d50df9b7715ea.apk'), ('fdroid', 'com.google.android.sambadocumentsprovider_111.apk'), ('malradar', 'c45e525fd03a1c364a2b8d3973b9588b5cd75e75c0aa4e716d314f565b2e8225.apk'), ('malradar', 'edbebf9213ce1615058d6beadb3c6b2a8f66e20d2c0e82f77899b1ae227929e3.apk'), ('malradar', '49aaed9dec956d345610cc724c0d1fae52ca319b8635f96bfc49ae0421ccfbaa.apk'), ('malradar', 'ed5a3868e942ecf0e319502ab9d5825520d5a6d1455a620b8c9f83c74360935f.apk'), ('fdroid', 'com.unwrappedapps.android.wallpaper.creative_2.apk'), ('fdroid', 'org.eehouse.android.xw4_190.apk'), ('fdroid', 'com.metallic.chiaki_7.apk'), ('malradar', '5cc90679f8b0379fd60da17750c5823852ce2a4a58ee56a6d81aee9fc7efa65a.apk'), ('fdroid', 'com.wireguard.android_492.apk'), ('fdroid', 'org.xapek.andiodine_6.apk'), ('malradar', '2cda870a8e60d4a4457ee3b7ad256f08e1a8a60aa2c5c0f85e2e6876c2ba44f3.apk'), ('malradar', '381620b5fc7c3a2d73e0135c6b4ebd91e117882f804a4794f3a583b3b0c19bc5.apk'), ('malradar', 'f8cf80b0bcc2350a52819f4d2dc56c16e4264f3237fad5101e84a7c089f5b866.apk'), ('fdroid', 'com.googlecode.eyesfree.espeak_7.apk'), ('malradar', 'd8aca3508ee537c0f5b07c6652f2a771c9d7cddd728196669bfcba93b2e5eb2c.apk'), ('malradar', 'e3f77ff093f322e139940b33994c5a57ae010b66668668dc4945142a81bcc049.apk'), ('fdroid', 'org.chickenhook.binderfuzzy_2.apk'), ('malradar', '66b791469abb23d558cb2a28a9e7fe1a7b3863335b21c7ab7ebf37f90e65f4f4.apk'), ('malradar', 'abcf3b1b631f0fa776bf22f1bee8bfc6b95a00b345c103ee82a3d26b466b2dd6.apk'), ('fdroid', 'mn.tck.semitone_4.apk'), ('malradar', '027d81b167c2851caeba3411ac93988fccc5e6a84687842827cea8a1df7c4373.apk'), ('fdroid', 'la.daube.photochiotte_32.apk'), ('fdroid', 'fr.xplod.focal_8.apk'), ('fdroid', 'com.tutpro.baresip.plus_121.apk'), ('malradar', '6466a6f2b3323392cc7d97ef43909cb660d9f8757e816493f7759e83cfc25859.apk'), ('fdroid', 'com.hwloc.lstopo_269.apk'), ('fdroid', 'org.bibledit.android_154.apk'), ('malradar', '2ed77be505cd246ca41bba218d8a5c59ae6049eff2c3b72ca91433ad4fe3b103.apk'), ('fdroid', 'com.github.axet.bookreader_416.apk'), ('malradar', '7fb8106d0e3e4c691049f6dea76a3e50e80e58e857e89d2a6c9c9181df4caa8e.apk'), ('malradar', '203561fe0d21800b08122ee54c164d9e757ac294e6bf1191a4c341c43003f1d8.apk'), ('fdroid', 'org.pipoypipagames.cowsrevenge_9.apk'), ('malradar', '98f3a0e89f6d73ddc51b090d27c221f91875d027e399e7dd90dac3d39a85154b.apk'), ('fdroid', 'org.wikimedia.commons.wikimedia_1.apk'), ('malradar', 'e6cb3997a40bd0690e9264d9216f05d9631b0d78fbd100b5241406fc54ad3e5f.apk'), ('malradar', 'e7c7dd13997a470d8eee79b6f12949d19e5cae9b5dbf0a57694eeaa818e3f8dd.apk'), ('malradar', '4ae73a79a3e8bc0f0595ec2002b108167977677dfaae432f28f37dc88f5122f5.apk'), ('fdroid', 'net.avs234_16.apk'), ('malradar', '30bf493c79824a255f9b56db74a04e711a59257802f215187faffae9c6c2f8dc.apk'), ('malradar', '9d4a4f85f2772e816949467e632b11cf57f1bc877a11aeacd8169bde6ea048c4.apk'), ('fdroid', 'com.jecelyin.editor_39.apk'), ('fdroid', 'is.xyz.omw_nightly_46.apk'), ('malradar', '8104a663df0fd31bec717a3521a1fdfd9ef35aaae657da7de59d44de1167ab54.apk'), ('fdroid', 'jp.sawada.np2android_20130429.apk'), ('malradar', 'ebd0a8043434edac261cb25b94f417188a5c0d62b5dd4033f156b890d150a4c5.apk'), ('malradar', 'b2396341f77b9549f62a0ce8cc7dacf5aa250242ed30ed5051356d819b60abff.apk'), ('fdroid', 'ro.ui.pttdroid_5.apk'), ('malradar', '9ee88892688088bbec7ae42bfdf71a1c8e0bb6914a1d44de66d8b1298c70370f.apk'), ('fdroid', 'com.zaren_14.apk'), ('fdroid', 'cc.kafuu.bilidownload_18.apk'), ('fdroid', 'ch.hsr.eyecam_81.apk'), ('malradar', 'e9801598d27618a1fe6bbcc0e6fc67e5843e65908d219eb7a2a2e2aad832e84d.apk'), ('fdroid', 'sushi.hardcore.droidfs_27.apk'), ('malradar', '0d023600123b17269b7140995f593360e9af2f18f488be6e858e79a28e69825d.apk'), ('malradar', '796b1d610734b36b81dea62239010826f9c95335de5a2aae15d99de56fb69900.apk'), ('fdroid', 'org.emunix.unipatcher_160100.apk'), ('fdroid', 'com.github.metacubex.clash.meta_206001.apk'), ('fdroid', 'eu.domob.anacam_10200.apk'), ('malradar', 'bf2968b7a3ba3687dee6122de538d3d59e062553e77a80d29817f2ff4137f4ea.apk'), ('malradar', '54594edbe9055517da2836199600f682dee07e6b405c6fe4b476627e8d184bfe.apk'), ('malradar', 'bf79785f90c01164437cb19577cbb9c729a277f45d702ed9e2984d0550b3fc2f.apk'), ('malradar', '8cd8c53a8dd17345ddaebed15ca390e20705c84512a27cb9d4eddacda4e6d025.apk'), ('fdroid', 'net.kervala.comicsreader_28.apk'), ('malradar', '6283c5ffb00a8acb0f1e388feb3ff35279b6405b5478a0750eb554588d468674.apk'), ('malradar', '09e39391b0e99f5f6751daa802d9271c08faa0ffa36fa87f20d5d1eecbe03a8f.apk'), ('fdroid', 'de.saschahlusiak.freebloks_122.apk'), ('fdroid', 'org.ghostsinthelab.apps.guilelessbopomofo_71.apk'), ('malradar', '96d4ad62d42f2fc20e90f0ef6c8afbf83831f5f1592b0cd0ab4fdb4a090ef86b.apk'), ('fdroid', 'org.purplei2p.i2pd_2450100.apk'), ('fdroid', 'com.jeffboody.GearsES2eclair_7.apk'), ('malradar', 'ff6ca0e2ccdf44dc78c739b9b94baef1d579ac7f991b52c3f9f505090a5b9d90.apk'), ('fdroid', 'io.github.alketii.mightyknight_1.apk'), ('malradar', '2e9f458a0c63283e7fe79bd8514a8945010265d041a565723884b26a20905a9d.apk'), ('fdroid', 'com.sgr_b2.compass_18.apk'), ('malradar', '65b2fc59c7c570d649c29eb2be1f3ca8bd6cc81f1d208e2da76dbb75fb46fc94.apk'), ('malradar', '005d73e49d96b1d56bd864817ffa7581e7064a4e0571776d4b47394e35ef7819.apk')}
    # print(len(result)) # 203
    # print(gen_summ_counts) # 771

def jucify_get_edges_analyzed(file):
    funcs_set = set()
    funcs = []
    times = []
    matches = match_in_file_bytes(rb'(Current Function: |Analysis spent: )(.*)\.', file)
    for mat in matches:
        if mat[0].startswith(b'Curr'):
            funcs_set.add(mat[1])
            funcs.append(mat[1])
        elif mat[0].startswith(b'Ana'):
            s = mat[1].removesuffix(b's')
            times.append(float(s))
        else:
            raise RuntimeError()
    # assert 
    return funcs_set, times

# 2023年3月23日 寻找jucify那边新增的调用边。
def jucify_get_edges(range_set=None):
    BASE = '/home/user/ns/experiment/baseline-jucify'
    rfiles = []
    native2javas = 0
    java2natives = 0
    edges_analyzed = 0 # 分析了但是没输出的
    jni_times = []
    for ty in ['fdroid', 'malradar']:
        rp = os.path.join(BASE,f'old-results/{ty}-results')
        for file in os.listdir(rp):
            if range_set is not None and (ty, file) not in range_set: continue
            if not file.endswith('.apk'): continue
            f, t = jucify_get_edges_analyzed(os.path.join(rp, file, f'{file}.native.log'))
            edges_analyzed += len(f); jni_times += t
            # result file
            dir1 = os.path.join(rp, file, f'{file.removesuffix(".apk")}_result')
            if not os.path.exists(dir1): continue
            for rfile in os.listdir(dir1):
                if not rfile.endswith('.result'): continue
                rfile = os.path.join(dir1, rfile)
                rfiles.append(rfile)
                native2java, java2native = parse_jucify_result(rfile)
                native2javas += native2java
                java2natives += java2native
    print(f'Jucify can detect {java2natives} (internal: {len(jni_times)} (success) + {edges_analyzed - len(jni_times)} (fail) = {edges_analyzed}) native methods, and {native2javas} call edges.') # Jucify can detect 2275 native methods, and 130 call edges.
    return jni_times

def jucify_star_get_edges(range_set=None):
    BASE = '/home/user/ns/experiment/baseline-jucify'
    rfiles = []
    native2javas = 0
    java2natives = 0
    edges_analyzed = 0 # 分析了但是没输出的
    jni_times = []
    for ty in ['fdroid', 'malradar']:
        rp = os.path.join(BASE,f'{ty}-results2')
        for file in os.listdir(rp):
            if range_set is not None and (ty, file) not in range_set: continue
            if not file.endswith('.apk'): continue
            f, t = jucify_get_edges_analyzed(os.path.join(rp, file, f'{file}.native.log'))
            edges_analyzed += len(f); jni_times += t
            # result file
            dir1 = os.path.join(rp, file, f'{file.removesuffix(".apk")}_result')
            if not os.path.exists(dir1): continue
            for rfile in os.listdir(dir1):
                if not rfile.endswith('.result'): continue
                rfile = os.path.join(dir1, rfile)
                rfiles.append(rfile)
                native2java, java2native = parse_jucify_result(rfile)
                native2javas += native2java
                java2natives += java2native
    print(f'Jucify* can detect {java2natives} (internal: {len(jni_times)} (success) + {edges_analyzed - len(jni_times)} (fail) = {edges_analyzed}) native methods, and {native2javas} call edges.') # Jucify can detect 2275 native methods, and 130 call edges.
    return jni_times

def parse_jucify_result(p):
    # 乱码，应该是名字解析错了。
    if 'libAK.so.result' in p: # wrong
        return 0,0
    native2java = set()
    java2native = set()
    with open(p, 'r') as f:
        lines = f.readlines()
    for line in lines[1:]:
        line2 = line.split(',')
        if line.count(',') == 10:
            # native2java += 1
            # classname, methodName, sig, callsite symbol
            # native2java.add((line2[5].strip(), line2[6].strip(), line2[7].strip(), line2[9]))
            native2java.add((line2[5].strip(), line2[6].strip(), line2[7].strip()))
        elif line.count(',') == 4:
            # java2native +=1
            # java2native.add(line2[3].strip())
            java2native.add((line2[0].strip(), line2[1].strip(), line2[2].strip()))
        else:
            raise RuntimeError('line not correct')
    return len(native2java), len(java2native)

import shutil
# rangeset = Set[Tuple(ty,file)]
def jnsaf_get_edges(range_set=None):
    BASE = '/home/user/ns/experiment/baseline-jn-saf'
    native2javas = 0
    java2natives = 0
    errors = []
    times = []
    for ty in ['fdroid', 'malradar']:
        rp = os.path.join(BASE, f'{ty}-results')
        for file in os.listdir(rp):
            if range_set is not None and (ty, file) not in range_set: continue
    # for ty,file in {('fdroid', 'teaonly.droideye_8.apk'), ('fdroid', 'is.xyz.omw_40.apk'), ('malradar', '92237bcc0fb7b7e67820f8f1e2f6b643b5b954816bff16186651400027abff16.apk'), ('fdroid', 'io.githubfede0d.planetrider_1.apk'), ('fdroid', 'com.roguetemple.hydroid_1500.apk'), ('fdroid', 'org.navitproject.navit_6382.apk'), ('malradar', '314de858ed8d816213020c71ef78a8c4616bac91a171349b703e44747832fca3.apk'), ('malradar', '5137f72d7fec55b0a6e504a923c95b891410f99ed7ed8b37d8499ae4e5bbc6fe.apk'), ('malradar', '7d3a00c93cbf15df1afab245f9be47feb27c862d51581dadaec50378bee7d5fa.apk'), ('malradar', '8963b16b3002bbeeba934d6bfd5194dc7682cdf916c3da2933f93c19de194aab.apk'), ('malradar', '34660a36d8159c844557d302d6b0c2c9a3980487d9756f52f9cef67d5ef56108.apk'), ('fdroid', 'fr.ubordeaux.math.paridroid_25.apk'), ('fdroid', 'eu.faircode.netguard_2022111001.apk'), ('fdroid', 'ir.hsn6.k2_2.apk'), ('malradar', 'bbc268ca63eeb27e424fec1b3976bab550da304de18e29faff94d9057b1fa25a.apk'), ('fdroid', 'com.reecedunn.espeak_21.apk'), ('fdroid', 'st.wow.git.hrm_3.apk'), ('malradar', 'f2e260c122552cac14d04b50d8ac941678c58fde314f7e625797b8c567f17431.apk'), ('malradar', '43b36c438a3531e42623fbd00f5b57066a4db8048ce8e0ab0b5ecf9eac67aabf.apk'), ('fdroid', 'com.shurik.droidzebra_17.apk'), ('malradar', 'aae8a67645a4030b7c40af90a1c7fec270f2b8c0d736093321a05adeba012409.apk'), ('malradar', '8b0853e3a0e25be0b0601578028cf2ef39830e331e64a88089a2b25b0449d221.apk'), ('fdroid', 'org.mupen64plusae.v3.alpha_87.apk'), ('fdroid', 'de.kromke.andreas.mediascanner_18.apk'), ('malradar', '297cb76d16a1d875240e7495841ff61ee104b6b8c75e3b2db27e8eadae3c73bf.apk'), ('malradar', '7c840433020c33e16e942a39d53c593ce58db680a41955a8a29139cf022be8dd.apk'), ('fdroid', 'com.xenris.liquidwarsos_11.apk'), ('malradar', '04a204adfbe677c3587e26dc31ac008d6c147265a455f216cbe9a441469d4c30.apk'), ('fdroid', 'org.synergy_2.apk'), ('fdroid', 'ru.evgeniy.dpitunnel_13.apk'), ('fdroid', 'org.mattvchandler.a2050_190010009.apk'), ('malradar', '6e995d68c724f121d43ec2ff59bc4e536192360afa3beaec5646f01094f0b745.apk'), ('fdroid', 'trikita.obsqr_16.apk'), ('malradar', 'a76f6948599757e395aa29ab389ef661dd8b16a08deb67dd277471a8b09be30d.apk'), ('malradar', '5a01367d32f64fc1c956fe482bf04767c707159baa21581f1461e03a6a45503d.apk'), ('fdroid', 'ir.hsn6.defendo_8.apk'), ('malradar', '11818e4c330c15835388509481da5beff560b161847364a6857a714f1f8f6d85.apk'), ('fdroid', 'de.spiritcroc.defaultdarktheme_oms_53.apk'), ('malradar', 'ab711252a34081515c25dbf0359ba744662973ea8c984acb9e903d706ae62d44.apk'), ('malradar', '211d8411751a80b57f50699b91c5ca8dd344e4b5ea0ac6f713298ab78a496060.apk'), ('malradar', '47b5308eb059b087763cc5e156325eded042cc82220a8ba3d4ffafd3c5dcb024.apk'), ('malradar', 'ecb6603a8cd1354c9be236a3c3e7bf498576ee71f7c5d0a810cb77e1138139ec.apk'), ('malradar', 'e298ef75b1ab8fca25481b1ce36ad9aee4d5b4fcc113f7b51f23c3a076e857fb.apk'), ('malradar', '08316f05f39965faac3f54c8e48872fe67416bc35b89ee165c1e38a2ee0b8822.apk'), ('malradar', '5769f8e5133688978b2e2e5878f968aaac88a8c8ba9dff39bafe74d04c21b40c.apk'), ('malradar', '3793cdf0ad01d60962aeaf2e2352f7824383a093809334bb6f22511f56cea12a.apk'), ('malradar', 'f51a27163cb0ddd08caa29d865b9f238848118ba2589626af711330481b352df.apk'), ('malradar', '58ed39c6ff742bfe02f7a799651a376e4eb6689684716d8e9c52d2538247db86.apk'), ('malradar', 'c9ad0c5c9e3efcbd96ddd0160654d6c169541b680e448e936963b8ad342da3b9.apk'), ('fdroid', 'aq.metallists.loudbang_47.apk'), ('fdroid', 'org.petero.droidfish_98.apk'), ('fdroid', 'net.tedstein.AndroSS_17.apk'), ('malradar', 'd5b9633a5b0bf99d4f376a632219500874c42deb1e70659a3d3694b11d8ae06c.apk'), ('fdroid', 'com.formfun_1.apk'), ('fdroid', 'idv.markkuo.ambitsync_9.apk'), ('malradar', 'd93dac3ad67afa6ed6e7ec90eeed771b2b6558d92cbe4fae23bfbc7950ebed68.apk'), ('malradar', '95548ceecfcb927bb1b41f7da1c8287244bd0529f9769146eec2dd5321e500aa.apk'), ('fdroid', 'com.emanuelef.remote_capture_61.apk'), ('fdroid', 'com.viper.simplert_2.apk'), ('malradar', '60cfc73feb5404f1cad88221c7f027216d2e24f264338954df921d8aba38cba5.apk'), ('malradar', 'd783d5161fc18ff0e1abe2f48bb9e2e743a85df17368d29d992033701c678e98.apk'), ('malradar', 'b4a8a6b8cd302fe614331d7549ca09b586b0542993d8329d77b65b3cbca3ea37.apk'), ('malradar', '228c01021d917bdc2858b07b21ec9e5103e2b85ae42aabccf933de958639b55c.apk'), ('fdroid', 'com.oF2pks.kalturadeviceinfos_24.apk'), ('fdroid', 'org.servalproject_2371.apk'), ('fdroid', 'io.github.kobuge.games.minilens_2.apk'), ('fdroid', 'troop.com.freedcam_282.apk'), ('malradar', '58be55b3bc11687c63fb15755a317335f881dece298f9aaf5353c4f35423d6c6.apk'), ('fdroid', 'org.echoline.drawterm_2.apk'), ('fdroid', 'org.jschwab.openrecipes_4.apk'), ('malradar', 'b2cade8370255cb10d7183d1c301443c6a2d31e2db579081daa741dcb1c5a8f0.apk'), ('fdroid', 'com.roguetemple.hyperroid_12070.apk'), ('malradar', '54f2aa690954ddfcd72e0915147378dd9a7228954b05c54da3605611b2d5a55e.apk'), ('malradar', '3327c2a0765817e7c2d5787c1889a9dc9abea9593077b8fb217161de499374bf.apk'), ('malradar', '8bb362dda2ccad540026105379a3880c78b502485440aaf3ccdb1272cb63c3d1.apk'), ('fdroid', 'in.p1x.tanks_of_freedom_20.apk'), ('malradar', 'a656eff1c3862fbce28e21e638373a6557e8a3be9a2593ebd2d8a8db44328c8b.apk'), ('fdroid', 'com.philolog.hoplitekeyboard_30.apk'), ('fdroid', 'ir.hsn6.trans_4.apk'), ('fdroid', 'com.atelieryl.wonderdroid_51.apk'), ('fdroid', 'org.vi_server.androidudpbus_1.apk'), ('malradar', '9684b915870cbe07fc75070985ae39d30aeb16db29eb9f3b685d72ac6224252c.apk'), ('malradar', 'a6b8d6663444496d2b55cc07dae01d3b0bf3bb18c796de16950d438fb65babab.apk'), ('fdroid', 'com.Bisha.TI89EmuDonation_1133.apk'), ('fdroid', 'one.librem.tunnel_1000299.apk'), ('fdroid', 'ir.hsn6.tpb_2.apk'), ('fdroid', 'com.zagayevskiy.pacman_2.apk'), ('fdroid', 'com.commonslab.commonslab_3.apk'), ('malradar', 'c9c6207c3eff3eccf15fd77b3d36a314c04b25905fc233184fc728bf9f72b619.apk'), ('malradar', '55dc3888c4ea2c6585c826d3e8c3007a3c4c16c916da704c2b32ec03eb32860b.apk'), ('malradar', '91e1376421e23e3c1ab677207460fe56c032784f8900067af6266bfc0c6ede4e.apk'), ('fdroid', 'br.odb.knights_5.apk'), ('malradar', 'a346ac7b3dec5c8cabb758d73eb0941f427806db6f572c2453c19223ddf55fe4.apk'), ('fdroid', 'org.tilelessmap.app_4.apk'), ('fdroid', 'net.christianbeier.droidvnc_ng_18.apk'), ('malradar', 'a4295a2120fc6b75b6a86a55e8c6b380f0dfede3b9824fe5323e139d3bee6f5c.apk'), ('malradar', '3cd62210ef53bca2b2aef1bd8ced308adfa7187ff3f1837248b22bf9fd81bcda.apk'), ('fdroid', 'org.kwaak3_1.apk'), ('fdroid', 'com.opendoorstudios.ds4droid_463.apk'), ('fdroid', 'im.status.ethereum_2022093016.apk'), ('malradar', '0497b6000a7a23e9e9b97472bc2d3799caf49cbbea1627ad4d87ae6e0b7e2a98.apk'), ('fdroid', 'com.write.Quill_41.apk'), ('malradar', 'b1f70b82aba39865b32d392faba2c3dc9e793d7ec082760b6c7627969083e2fb.apk'), ('malradar', 'a528951fa2a7a51a12f8d5f159b0194342e1330205c03c46c954461057b98ce9.apk'), ('malradar', '9e03bf2b1a57ad4d1be9ad9317499a977025d5167e23b695f942e5961e6e61d7.apk'), ('malradar', 'eadcd88ebe96a7ce3024aeb0a44e010bf311a4274e8d5de00f100f6f2dee02c7.apk'), ('malradar', '37250e02eff4caf36cb0a173f7dc5fc92ca0df8403ab4efd3fed35103ca40671.apk'), ('malradar', 'a5724477db2d9d625f9a2c8de1a0f9ca6558727af243bcbbcb02dd5b884f4ccc.apk'), ('malradar', '6261be516a54d8566348b8305e96f34bdbf4f11620350c5f36f4bc3cb67fc181.apk'), ('malradar', 'f67a613a2b29a7013c94c51b5b0d53555058f06e02ebaeb58c2e8cee035f5a46.apk'), ('malradar', '8a1eb641cc67cd7229bf9cd1a103e3d37a1a6015ff3e9f17680fc759bc619187.apk'), ('malradar', '80bdc09dca8c15f662e183115a4ebf96ad6f79bc2b1a9908d57028add2d0ad84.apk'), ('malradar', 'a5b2d73f904072d4da642105fb2092e12ca115d0f7deeff3dc24dd3c7b9b216c.apk'), ('fdroid', 'org.pipoypipagames.towerjumper_13.apk'), ('fdroid', 'se.leap.bitmaskclient_162000.apk'), ('fdroid', 'me.wenxinwang.pulsedroidrtp_6.apk'), ('fdroid', 'com.annie.dictionary.fork_20210415.apk'), ('malradar', '7127825c01dd0e4da2a3bbacb08e5f2a4104de142cb4ae5181be489e376d4320.apk'), ('fdroid', 'org.ea.sqrl_54.apk'), ('malradar', 'f4da643b2b9a310fdc1cc7a3cbaee83e106a0d654119fddc608a4b587c5552a3.apk'), ('malradar', 'b02e391d8de6dda7d2a78a4f65874cd7b584da7c7cbaab33c795e66902cad342.apk'), ('fdroid', 'io.github.muntashirakon.setedit_7.apk'), ('fdroid', 'ir.hsn6.turo_7.apk'), ('malradar', '3650dd5693ab98fb3cf76d25e4d03e809838d1875d0c8765e9a13d84d6151c9b.apk'), ('fdroid', 'com.amanoteam.unalix_9.apk'), ('malradar', '0477596226794c995305ca7fb80bed3ace168924492bb253861d50df9b7715ea.apk'), ('fdroid', 'com.google.android.sambadocumentsprovider_111.apk'), ('malradar', 'c45e525fd03a1c364a2b8d3973b9588b5cd75e75c0aa4e716d314f565b2e8225.apk'), ('malradar', 'edbebf9213ce1615058d6beadb3c6b2a8f66e20d2c0e82f77899b1ae227929e3.apk'), ('malradar', '49aaed9dec956d345610cc724c0d1fae52ca319b8635f96bfc49ae0421ccfbaa.apk'), ('malradar', 'ed5a3868e942ecf0e319502ab9d5825520d5a6d1455a620b8c9f83c74360935f.apk'), ('fdroid', 'com.unwrappedapps.android.wallpaper.creative_2.apk'), ('fdroid', 'org.eehouse.android.xw4_190.apk'), ('fdroid', 'com.metallic.chiaki_7.apk'), ('malradar', '5cc90679f8b0379fd60da17750c5823852ce2a4a58ee56a6d81aee9fc7efa65a.apk'), ('fdroid', 'com.wireguard.android_492.apk'), ('fdroid', 'org.xapek.andiodine_6.apk'), ('malradar', '2cda870a8e60d4a4457ee3b7ad256f08e1a8a60aa2c5c0f85e2e6876c2ba44f3.apk'), ('malradar', '381620b5fc7c3a2d73e0135c6b4ebd91e117882f804a4794f3a583b3b0c19bc5.apk'), ('malradar', 'f8cf80b0bcc2350a52819f4d2dc56c16e4264f3237fad5101e84a7c089f5b866.apk'), ('fdroid', 'com.googlecode.eyesfree.espeak_7.apk'), ('malradar', 'd8aca3508ee537c0f5b07c6652f2a771c9d7cddd728196669bfcba93b2e5eb2c.apk'), ('malradar', 'e3f77ff093f322e139940b33994c5a57ae010b66668668dc4945142a81bcc049.apk'), ('fdroid', 'org.chickenhook.binderfuzzy_2.apk'), ('malradar', '66b791469abb23d558cb2a28a9e7fe1a7b3863335b21c7ab7ebf37f90e65f4f4.apk'), ('malradar', 'abcf3b1b631f0fa776bf22f1bee8bfc6b95a00b345c103ee82a3d26b466b2dd6.apk'), ('fdroid', 'mn.tck.semitone_4.apk'), ('malradar', '027d81b167c2851caeba3411ac93988fccc5e6a84687842827cea8a1df7c4373.apk'), ('fdroid', 'la.daube.photochiotte_32.apk'), ('fdroid', 'fr.xplod.focal_8.apk'), ('fdroid', 'com.tutpro.baresip.plus_121.apk'), ('malradar', '6466a6f2b3323392cc7d97ef43909cb660d9f8757e816493f7759e83cfc25859.apk'), ('fdroid', 'com.hwloc.lstopo_269.apk'), ('fdroid', 'org.bibledit.android_154.apk'), ('malradar', '2ed77be505cd246ca41bba218d8a5c59ae6049eff2c3b72ca91433ad4fe3b103.apk'), ('fdroid', 'com.github.axet.bookreader_416.apk'), ('malradar', '7fb8106d0e3e4c691049f6dea76a3e50e80e58e857e89d2a6c9c9181df4caa8e.apk'), ('malradar', '203561fe0d21800b08122ee54c164d9e757ac294e6bf1191a4c341c43003f1d8.apk'), ('fdroid', 'org.pipoypipagames.cowsrevenge_9.apk'), ('malradar', '98f3a0e89f6d73ddc51b090d27c221f91875d027e399e7dd90dac3d39a85154b.apk'), ('fdroid', 'org.wikimedia.commons.wikimedia_1.apk'), ('malradar', 'e6cb3997a40bd0690e9264d9216f05d9631b0d78fbd100b5241406fc54ad3e5f.apk'), ('malradar', 'e7c7dd13997a470d8eee79b6f12949d19e5cae9b5dbf0a57694eeaa818e3f8dd.apk'), ('malradar', '4ae73a79a3e8bc0f0595ec2002b108167977677dfaae432f28f37dc88f5122f5.apk'), ('fdroid', 'net.avs234_16.apk'), ('malradar', '30bf493c79824a255f9b56db74a04e711a59257802f215187faffae9c6c2f8dc.apk'), ('malradar', '9d4a4f85f2772e816949467e632b11cf57f1bc877a11aeacd8169bde6ea048c4.apk'), ('fdroid', 'com.jecelyin.editor_39.apk'), ('fdroid', 'is.xyz.omw_nightly_46.apk'), ('malradar', '8104a663df0fd31bec717a3521a1fdfd9ef35aaae657da7de59d44de1167ab54.apk'), ('fdroid', 'jp.sawada.np2android_20130429.apk'), ('malradar', 'ebd0a8043434edac261cb25b94f417188a5c0d62b5dd4033f156b890d150a4c5.apk'), ('malradar', 'b2396341f77b9549f62a0ce8cc7dacf5aa250242ed30ed5051356d819b60abff.apk'), ('fdroid', 'ro.ui.pttdroid_5.apk'), ('malradar', '9ee88892688088bbec7ae42bfdf71a1c8e0bb6914a1d44de66d8b1298c70370f.apk'), ('fdroid', 'com.zaren_14.apk'), ('fdroid', 'cc.kafuu.bilidownload_18.apk'), ('fdroid', 'ch.hsr.eyecam_81.apk'), ('malradar', 'e9801598d27618a1fe6bbcc0e6fc67e5843e65908d219eb7a2a2e2aad832e84d.apk'), ('fdroid', 'sushi.hardcore.droidfs_27.apk'), ('malradar', '0d023600123b17269b7140995f593360e9af2f18f488be6e858e79a28e69825d.apk'), ('malradar', '796b1d610734b36b81dea62239010826f9c95335de5a2aae15d99de56fb69900.apk'), ('fdroid', 'org.emunix.unipatcher_160100.apk'), ('fdroid', 'com.github.metacubex.clash.meta_206001.apk'), ('fdroid', 'eu.domob.anacam_10200.apk'), ('malradar', 'bf2968b7a3ba3687dee6122de538d3d59e062553e77a80d29817f2ff4137f4ea.apk'), ('malradar', '54594edbe9055517da2836199600f682dee07e6b405c6fe4b476627e8d184bfe.apk'), ('malradar', 'bf79785f90c01164437cb19577cbb9c729a277f45d702ed9e2984d0550b3fc2f.apk'), ('malradar', '8cd8c53a8dd17345ddaebed15ca390e20705c84512a27cb9d4eddacda4e6d025.apk'), ('fdroid', 'net.kervala.comicsreader_28.apk'), ('malradar', '6283c5ffb00a8acb0f1e388feb3ff35279b6405b5478a0750eb554588d468674.apk'), ('malradar', '09e39391b0e99f5f6751daa802d9271c08faa0ffa36fa87f20d5d1eecbe03a8f.apk'), ('fdroid', 'de.saschahlusiak.freebloks_122.apk'), ('fdroid', 'org.ghostsinthelab.apps.guilelessbopomofo_71.apk'), ('malradar', '96d4ad62d42f2fc20e90f0ef6c8afbf83831f5f1592b0cd0ab4fdb4a090ef86b.apk'), ('fdroid', 'org.purplei2p.i2pd_2450100.apk'), ('fdroid', 'com.jeffboody.GearsES2eclair_7.apk'), ('malradar', 'ff6ca0e2ccdf44dc78c739b9b94baef1d579ac7f991b52c3f9f505090a5b9d90.apk'), ('fdroid', 'io.github.alketii.mightyknight_1.apk'), ('malradar', '2e9f458a0c63283e7fe79bd8514a8945010265d041a565723884b26a20905a9d.apk'), ('fdroid', 'com.sgr_b2.compass_18.apk'), ('malradar', '65b2fc59c7c570d649c29eb2be1f3ca8bd6cc81f1d208e2da76dbb75fb46fc94.apk'), ('malradar', '005d73e49d96b1d56bd864817ffa7581e7064a4e0571776d4b47394e35ef7819.apk')}:
            if not file.endswith('.apk'): continue
            # fullp = os.path.join(BASE, 'results2', file, f'{file}.pystderr.log')
            fullp = os.path.join(rp, file, f'{file}.pystderr.log')
            if not os.path.exists(fullp):
                errors.append(fullp)
                # print('1',end='')
                assert False
                continue
            
            # matches = match_in_file_bytes(b'Server GenSummary', fullp)
            # if len(matches) <= 0:
            #     # print('2',end='')
            #     # shutil.rmtree(os.path.join(BASE, 'results2', file))
            #     errors.append(fullp)
            #     continue
            java2native, native2java, t = parse_jnsaf_edges(fullp)
            java2natives += java2native
            native2javas += native2java
            times += t
    print(f'jnsaf can detect {java2natives} ({len(times)} success) native methods, and {native2javas} call edges. {len(errors)} not invoking native analysis')
    # jnsaf can detect 304 native methods, and 89 call edges.
    # print(errors)
    return times

def parse_jnsaf_edges(p):
    edges = set()
    mths = []
    for match in match_in_file_bytes(b'CallXXXMethod target signature: (.*)\x1b', p):
        edges.add(match)
    m1 = match_in_file_bytes(rb'Server GenSummary: .*$\ncomponent_name: \"(.*)\"$', p)
    for match in m1:
        mths.append(match)
    matches = match_in_file_bytes(rb'Server GenSummary spent: (.*)s\.', p)
    times = [float(i) for i in matches]
    assert len(m1) == len(match_in_file_bytes(b'Server GenSummary:', p))
    assert abs(len(mths) - len(times)) <= 1
    times_dic = {}
    times_dic.update(zip(mths, times))
    return len(set(mths)), len(edges), list(times_dic.values())

import collections
def ns_get_edges(range_set=None):
    BASE = '/home/user/ns/experiment/baseline-native_summary'
    ps = 0
    cs = 0
    cons = 0
    java2natives = 0
    all_j2n_edges = 0
    times = []
    for ty in ['fdroid', 'malradar']:
        rp = os.path.join(BASE,f'old-{ty}-results')
        for file in os.listdir(rp):
            if range_set is not None and (ty, file) not in range_set: continue
            if not file.endswith('.apk'): continue

            dir = os.path.join(rp, file)
            ana, t = parse_ns_edges_analyzed(dir)
            all_j2n_edges += ana
            times += t
            
            jimp = os.path.join(rp, file, '02-built-bodies.jimple')
            if not os.path.exists(jimp): continue
            m, p, c, con =parse_ns_edges(jimp)
            java2natives += m
            ps += p
            cs += c
            cons += con
    print(f'ns can detect {java2natives}/{all_j2n_edges} native methods, and {cs}+{cons}={cons+cs}/{ps} call edges. {len(times)}') # ns can detect 39682 native methods, and 2273+1071=3344/6348 call edges.
    return times

def parse_ns_edges_analyzed(dir):
    times = []
    analyzed = set()
    for f in os.listdir(dir):
        if not f.endswith('.so.log'): continue
        fd = os.path.join(dir, f)
        data = read_file_bytes(fd)
        # 给java_的去重，其他的不去重
        times_lj = {}
        times_l = []
        analyzed_l = set()
        for mat in match_in_str(rb'Analysis spent (.*) ms for (\S*)', data):
            if b'JNI_OnLoad' in mat[1]: continue
            if mat[1].startswith(b'Java_'):
                times_lj[mat[1]] = float(mat[0]) / 1000
            else:
                times_l.append(float(mat[0]) / 1000)
            # 
        for mat in match_in_str(rb'Running solver on (.*) function', data):
            if b'JNI_OnLoad' in mat: continue
            analyzed_l.add(mat)
        assert abs(len(analyzed_l) - len(times_lj) - len(times_l)) <= 1
        times += list(times_lj.values())
        times += times_l
        analyzed.update(analyzed_l)
    return len(analyzed), times

# 
def parse_ns_edges(jimp):
    import re
    jimp = read_file(jimp)
    jimp = re.sub(r'public static .* JNI_OnLoad\(.*\)$\n\s*{[^}]*}', "", jimp) # exclude jni_onload
    mths = match_in_str(r'^ *(.*\))\s*{', jimp)
    mths = set([i for i in mths if 'JNI_OnLoad' not in i and '"' not in i])
    possible_calls = match_in_str(r'^ *((.* = )?(.*))\(.*\);', jimp)
    specialinvokes = [i for i in possible_calls if 'specialinvoke' in i[2]]
    possible_calls = set([i[2] for i in possible_calls if 'NativeSummary' not in i[2] and 'valueOf' not in i[2] and 'toString' not in i[2]])
    calls = match_in_str(r'^ *((.* = )?([a-zA-Z0-9_.$]*))\(.*\);', jimp)
    calls = set([i[2] for i in calls if 'NativeSummary' not in i[2] and 'valueOf' not in i[2] and 'toString' not in i[2]])
    special_calls = match_in_str(r'new (.*);\n\n *specialinvoke .*\.<init>', jimp)
    scc = len(special_calls)
    special_calls = set(special_calls)

    todo_set = possible_calls.difference(calls)
    
    assert len(specialinvokes) == scc

    if len(todo_set) > 0:
        pass
    return len(mths), len(possible_calls), len(calls), len(special_calls)

def average_nms():
    with open('./manual-audit/native-methods.pickel', "rb") as f:
        nms = pickle.load(f)
    lens = []
    for file, nmlist in nms.items():
        lens.append(len(nmlist))
    print(f'total {sum(lens)} native methods, average {average(lens)} per apk')

def get_edges():
    juc_t = jucify_get_edges()
    jnsaf_t = jnsaf_get_edges()
    ns_t = ns_get_edges()
    average_nms()
    print(f"======in intersection({len(intersec)})=====")
    juc_ti = jucify_get_edges(intersec)
    jnsaf_ti = jnsaf_get_edges(intersec)
    ns_ti = ns_get_edges(intersec)
    plot2box([juc_ti, jnsaf_ti, ns_ti], [juc_t, jnsaf_t, ns_t], 'jni_time_box.pdf', labels=['Jucify', 'JN-SAF', 'NS/FD'])
'''
Jucify can detect 2303 native methods, and 130 call edges.
jnsaf can detect 211 native methods, and 85 call edges.
ns can detect 39678 native methods, and 2273+1071=3344/6348 call edges.
total 231137 native methods, average 102.4543439716312 per apk
======in intersection(271)=====
Jucify can detect 0 native methods, and 0 call edges.
jnsaf can detect 43 native methods, and 5 call edges.
ns can detect 1530 native methods, and 479+153=632/1087 call edges.
'''

def find_timeout():
    timeout = 7190.0
    timeouted = {}
    for serie in series:
        for target in targets:
            for apk in cs[target]:
                try:
                    time1, mem1, taint1 = r[serie][(target,apk)]
                    if time1 > timeout:
                        timeouted[(serie, target,apk)] = time1
                except KeyError:
                    pass
                
    print(timeouted)
    print(len(timeouted))

def plot_box_main():
    seq = ['flowdroid', 'jucify', 'jnsaf', 'ns']
    times, mems = average_mem_times()
    times_intersec, mems_intersec = average_mem_times(intersec, True)
    # plot2box(times_intersec, times, 'time_box.pdf')
    # plot2box(mems_intersec, mems, 'mem_box.pdf', 'Mem (GB)', scale=10**-9)
    # plot2box_fix(times_intersec, times, seq, 'time_box.pdf')
    plot2box_fix(mems_intersec, mems, seq, 'mem_box.pdf', 'Mem (GB)', scale=10**-9)
    import pickle
    with open("mem_box.pickel", 'wb') as f:
        pickle.dump((mems_intersec, mems, "memory on intersection apps", "memory on all apps"), f)

def plot_box_main2():
    """
    plot_box_main but no flowdroid (not used)
    """
    seq = ['jucify', 'jnsaf', 'ns']
    times, mems = average_mem_times()
    times.pop('flowdroid'); mems.pop('flowdroid')
    times_intersec, mems_intersec = average_mem_times(intersec, True)
    times_intersec.pop('flowdroid'); mems_intersec.pop('flowdroid')
    plot2box_fix(times_intersec, times, seq, 'time_box3.pdf', labels=['Jucify', 'JN-SAF', 'NS/FD'])
    plot2box_fix(mems_intersec, mems, seq, 'mem_box3.pdf', 'Mem (GB)', scale=10**-9, labels=['Jucify', 'JN-SAF', 'NS/FD'])


# #success apps in paper
def error_counter():
    total_apk_count = 0
    fd_success_count = 0
    jucify_success_count = 0
    jnsaf_success_count = 0
    ns_success_count = 0
    jucify_star_success_count = 0
    
    for target in targets:
        for apk in cs[target]:
            total_apk_count += 1
            try:
                time1, mem1, taint1 = r['flowdroid'][(target, apk)]
                fd_success_count += 1
            except KeyError:
                pass
            try:
                time1, mem1, taint1 = r['jucify'][(target, apk)]
                jucify_success_count += 1
            except KeyError:
                pass
            try:
                time1, mem1, taint1 = r['jucify*'][(target, apk)]
                jucify_star_success_count += 1
            except KeyError:
                pass
            try:
                time1, mem1, taint1 = r['jnsaf'][(target, apk)]
                jnsaf_success_count += 1
            except KeyError:
                pass
            try:
                time1, mem1, taint1 = r['ns'][(target, apk)]
                ns_success_count += 1
            except KeyError:
                print(f"ns fail: {(target, apk)}: /home/user/ns/experiment/baseline-native_summary/{target}-results/{apk}")
                pass
    print(f'total: {total_apk_count}, ')
    print(f'flowdroid: {fd_success_count}, jnsaf: {jnsaf_success_count}, jucify: {jucify_success_count}')
    print(f'ns: {ns_success_count} jucify_star: {jucify_star_success_count}')


JUCIFY_TIMEOUT = 180
def jucify_get_jni_times(file, JUCIFY_TIMEOUT):
    func_time = {}
    matches = match_in_file_bytes(rb'(Current Function: |Analysis spent: |Timeout when analyzing)(.*)\.', file)
    current = None
    state = 'done'
    for ind, mat in enumerate(matches):
        if mat[0].startswith(b'Current'):
            # assert state == 'done'
            state = 'analyzing'
            datas = mat[1].split(b', ')
            class_ = datas[0]
            method_name = datas[1]
            sig = datas[2]
            current = (class_, method_name, sig)
        elif mat[0].startswith(b'Timeout'):
            assert state == 'analyzing' or func_time[current] > (JUCIFY_TIMEOUT - 1)
            state = 'done'
            func_time[current] = JUCIFY_TIMEOUT # jucify timeout
        elif mat[0].startswith(b'Analysis'):
            assert state == 'analyzing'
            state = 'done'
            s = mat[1].removesuffix(b's')
            time_ = float(s)
            func_time[current] = time_
        else:
            raise RuntimeError()
    # assert 
    return func_time

from util_funcs import load_json
def ns_get_jni_times(path):
    ret = {}
    timeout_map = {}
    # to_remove = set()
    for file in os.listdir(path):
        if not file.endswith('.perf.json'):
            continue
        fp = os.path.join(path, file)
        json_data = load_json(fp)
        for func in json_data['functions']:
            if func['name'] == 'JNI_OnLoad': continue
            methodname = func['name'].encode()
            signature = func['signature'].replace(' ', '').encode()
            if 'class' not in func:
                # if (methodname, signature) in ret:
                #     to_remove.add((methodname, signature))
                ret[(methodname, signature)] = func['time_ms'] / 1000.0
                timeout_map[(methodname, signature)] = func['is_timeout']
            else: # normal
                classname = func['class'].removeprefix('L').removesuffix(';').replace('/', '.').encode()
                ret[(classname, methodname, signature)] = func['time_ms'] / 1000.0
                timeout_map[(classname, methodname, signature)] = func['is_timeout']
    return ret, timeout_map

from collections import defaultdict
def search_jni_times(filter_time = None):
    import re
    BASE = '/home/user/ns/experiment/baseline-jn-saf'
    pat = re.compile(rb'\[SafSu Analysis\]\n(.*?)Server GenSummary spent: (.*?)s\.', re.MULTILINE|re.DOTALL)
    times = defaultdict(lambda:[]) # map tool -> { (apk, class, method, sig) -> time }
    jucify_error_count = 0
    ns_timeout_count = 0
    for ty in ['fdroid', 'malradar']:
        rp = os.path.join(BASE, f'{ty}-results')
        for file in os.listdir(rp):
            if not file.endswith('.apk'): continue
            # fullp = os.path.join(BASE, 'results2', file, f'{file}.pystderr.log')
            fullp = os.path.join(rp, file, f'{file}.pystderr.log')
            if not os.path.exists(fullp):
                continue
            jucify_error = False
            jucify_times = jucify_get_jni_times(f'/home/user/ns/experiment/baseline-jucify/old-results/{ty}-results/{file}/{file}.native.log', JUCIFY_TIMEOUT)
            # try:
            #     jucify_times2 = jucify_get_jni_times(f'/home/user/ns/experiment/baseline-jucify/{ty}-results/{file}/{file}.native.log')
            # except FileNotFoundError:
            #     jucify_times2 = {}
            if len(jucify_times) == 0:
                # print(f'jucify error: /home/user/ns/experiment/baseline-jucify/old-results/{ty}-results/{file}/{file}.native.log', file=sys.stderr)
                jucify_error = True

            try:
                ns_times, ns_timeout_map = ns_get_jni_times(f'/home/user/ns/experiment/baseline-native_summary/{ty}-results/{file}')
            except FileNotFoundError:
                print(f'ns not run {file}')
                continue
            # try:
            #     ns_times2, ns_timeout_map2 = ns_get_jni_times(f'/home/user/ns/experiment/baseline-native_summary/optcompare-results/{file}')
            # except FileNotFoundError:
            #     ns_times2 = {}
            results = pat.findall(read_file_bytes(fullp))
            for result in results:
                jni_infos, time = result
                time = float(time)
                jni_info = jni_infos.split(b'\n')[0].removesuffix(b'`:').removeprefix(b'`')
                classname = jni_info[:jni_info.find(b'.')]
                classname = classname.removeprefix(b'L').removesuffix(b';').replace(b'/', b'.')
                methodname = jni_info[jni_info.find(b'.')+1:jni_info.find(b':(')]
                paramsig = jni_info[jni_info.find(b':(')+2:jni_info.rfind(b')')]
                ret = jni_info[jni_info.rfind(b')')+1:]
                key = (classname, methodname, b'('+paramsig+b')'+ret)
                
                ns_time = ns_times.get(key, None)
                if ns_time is None:
                    # ns_time = ns_times2.get(key, None)
                    # print(f'cannot find ns: {key}', file=sys.stderr)
                    continue

                jucify_time = jucify_times.get(key, None)
                if jucify_time is None:
                    # jucify_time = jucify_times2[key]
                    # print(f'cannot find jucify: {key}', file=sys.stderr)
                    if jucify_error:
                        jucify_error_count += 1
                    continue
                
                if filter_time is not None:
                    if not (ns_time > filter_time and jucify_time > filter_time and time > filter_time):
                        continue

                if (ns_timeout_map[key]):
                    print(f"ns timeout: {(time, jucify_time, ns_time)}")
                    ns_timeout_count += 1
                
                if jucify_time > 180 or ns_time > 400:
                    print(f"out of scope")
                if jucify_time > 1000 or ns_time > 4000:
                    continue
                times['jnsaf'].append(time)
                times['jucify'].append(jucify_time)
                times['ns'].append(ns_time)
    stats = f'data count {len(times["jnsaf"])}, jucify timout {times["jucify"].count(180)} jucify_error_count {jucify_error_count} ns_timeout_count {ns_timeout_count}'
    print(stats)
    return dict(times), stats


def search_jni_times_jucify(filter_time=None):
    import re
    BASE = '/home/user/ns2/experiment/baseline-jucify/'
    times = defaultdict(lambda:[]) # map tool -> { (apk, class, method, sig) -> time }
    # for ty in ['fdroid', 'malradar']:
    #     rp = os.path.join(BASE, f'{ty}-results')
    ns_timeout_count = 0
    max_apk = None
    for file in os.listdir(f'{BASE}/wait1000-results'):
        if not file.endswith('.apk'): continue
        # fullp = os.path.join(BASE, 'results2', file, f'{file}.pystderr.log')
        # fullp = os.path.join(rp, file, f'{file}.pystderr.log')
        # if not os.path.exists(fullp):
        #     continue
        try:
            jucify_times = jucify_get_jni_times(f'/home/user/ns2/experiment/baseline-jucify/wait1000-results/{file}/{file}.native.log', 1000)
        except FileNotFoundError:
            jucify_times = {}
            # print(f'jucify error: /home/user/ns2/experiment/baseline-jucify/wait1000-results/{file}/{file}.native.log', file=sys.stderr)

        ns_times, ns_timeout_map = ns_get_jni_times(f'/home/user/ns/experiment/baseline-native_summary/compare-results/{file}')
        for key in jucify_times:
            jucify_t = jucify_times[key]
            
            ns_t = ns_times.get(key, None)
            # if ns_t is None:
            #     ns_t = ns_times.get(key[1:], None)
            if ns_t is None:
                # print(f"cannot find ns: {key}")
                continue
            if filter_time is not None:
                if not (jucify_t > filter_time and ns_t > filter_time):
                    continue

            if (ns_timeout_map[key]):
                # print(f"ns timeout: {key}")
                ns_timeout_count += 1
            times['jucify'].append(jucify_t)
            times['ns'].append(ns_t)
            if max_apk is None or file > max_apk:
                max_apk = file
    apk_index = sorted(os.listdir('/home/user/ns2/dataset/malradar-filter')).index(max_apk)
    stats = f'datapoints: {len(times["ns"])} jucify timout {times["jucify"].count(1000)} ns_timeout_count {ns_timeout_count} last_apk {max_apk} apk_index {apk_index}'
    print(stats)
    return dict(times), stats

def draw_jni_time_box_v2():
    times, stats = search_jni_times(1)
    # plot2box([times['jnsaf'], times['jucify'], times['ns']], [times['jnsaf'], times['jucify'], times['ns']], 'tmp_time_box_jucify_timeout.pdf', labels=[ 'JN-SAF', 'Jucify', 'NS/FD'])
    times_ju_ns, stats2 = search_jni_times_jucify(1)
    print('plot1:')
    print(stats)
    # plot2box([times['jucify'], times['ns']], [times['jucify'], times['ns']], 'jucify_ns_time_box_gt1.pdf', labels=['Jucify', 'NS/FD'])
    plot2box_jnitime([times['jnsaf'], times['jucify'], times['ns']], [times_ju_ns['jucify'], times_ju_ns['ns']], 
                     f"On {len(times['jnsaf'])} analyzed native methods of 3 tools", f'On {len(times_ju_ns["jucify"])} analyzed native methods of 2 tools', 
                     'jni_time_box_v2.pdf', labels1=['JN-SAF', 'Jucify', 'NS'], labels2=['Jucify', 'NS'])
    import pickle
    with open("jni_time_box_v2.pickel", 'wb') as f:
        pickle.dump((times, times_ju_ns, stats, stats2), f)

def get_stats_jni_time_box_v2(data_file, scale = 1.0):
    import statistics
    with open(data_file, 'rb') as f:
        times, times_ju_ns, stats, stats2 = pickle.load(f)
    if scale != 1.0:
        for val in times.values():
            val[:] = map(lambda x:x*scale, val)
        for val in times_ju_ns.values():
            val[:] = map(lambda x:x*scale, val)
    print(stats)
    for tool, stats in times.items():
        print(f"for tool {tool}")
        print(f"  min: {min(stats)}")
        print(f"  max: {max(stats)}")
        print(f"  average: {sum(stats) / len(stats)} {statistics.mean(stats)}")
        print(f"  stdev: {statistics.stdev(stats)}")
        print(f"  median: {statistics.median(stats)}")
    print(stats2)
    for tool, stats in times_ju_ns.items():
        print(f"for tool {tool}")
        print(f"  min: {min(stats)}")
        print(f"  max: {max(stats)}")
        print(f"  average: {sum(stats) / len(stats)} {statistics.mean(stats)}")
        print(f"  stdev: {statistics.stdev(stats)}")
        print(f"  median: {statistics.median(stats)}")


if __name__ == '__main__':
    # get_stats_jni_time_box_v2("jni_time_box_v2.pickel")
    # print("===========")
    # get_stats_jni_time_box_v2("mem_box.pickel", 10**-9)

    with open("jni_time_box_v2.pickel", 'rb') as f:
        times, times_ju_ns, stats, stats2 = pickle.load(f)
    timeout_ns = [True if i >= 999 else False for i in times_ju_ns['ns']]
    ns_above_129 = [True if i >= 129.11 else False for i in times_ju_ns['ns']]
    ju_above_129 = [True if i >= 129.11 else False for i in times_ju_ns['jucify']]
    print(f"{len(timeout_ns)} ns timeout {timeout_ns.count(True)} above129 {ns_above_129.count(True)} ju_above_129 {ju_above_129.count(True)}")

    # find_timeout()
    # plot_box_main()

    # success_counter()
    # plot_time_intersec()
    # jnsaf_find_native()
    # get_edges()
    # average_nms()
    # error_counter()

    # success_counter()
    # jucify_star_get_edges()
    # jucify_star_get_edges(intersec)
    # Jucify* can detect 5985 (internal: 24710 (success) + 9191 (fail) = 33901) native methods, and 127 call edges.
    # Jucify* can detect 0 (internal: 790 (success) + 60 (fail) = 850) native methods, and 0 call edges.
