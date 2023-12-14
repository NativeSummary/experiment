from androguard.misc import AnalyzeAPK
import os,pickle,zipfile

# DATASET = '/home/user/ns/dataset/intersect'
DATASETS = ['/home/user/ns/dataset/fdroid-filter', '/home/user/ns/dataset/malradar-filter']
# DATASET = '/home/user/ns/dataset/fdroid-filter'
# DATASET = '/home/user/ns/dataset/malradar-filter'


tests = [('malradar', '6a40e094dd7b60c78adf21e5afe6bd7b4c8c2669f4fea3c732356d49db156361.apk'), ('malradar', 'cd3c6dabbe4976d1582a91c707cd5bc7eb9666aa22684d3f6430a7714b1a4a2d.apk'), ('malradar', 'bace8fd1076c8fdf587fb10f8b1551d7bef21023fb45c5ab4c397758cd546015.apk'), ('malradar', '28417e850e1b96b2dd8395513699f6ff84aff067b392befc29362d892899078a.apk'), ('malradar', 'b6b3eb4258a662d330c20ac47e6308946e61f04b0b4a484e24ddca50f66b85af.apk'), ('malradar', 'f17f209ad106ea5714c5e31ade26b0abaaee6f2140720d93dd2337cc33cf8162.apk'), ('malradar', '2c30a071cb62e9b685cf35fb9c7e50909b9dfa0de51ddb7b55604e6c8a1ff3fa.apk'), ('malradar', '61aad4bcdd58d4a04a9cd8e573e6131afc356a3c8d86ff861b3de66cec58818f.apk'), ('malradar', 'fd4f9ed49fd486fc76feb6423e2c18056dcd5a8ebf24f447216ca41e46905224.apk'), ('malradar', '2b46cba1e5bae12feaa537af790682f74cdad025a79fb62baf7241569c18f2e8.apk'), ('malradar', '46f5fb6767ff5b60d3adf706f3c51567fdfa2c05ba01c0c6f4078ab98456ae66.apk'), ('malradar', '475a24aed3c912b023052e53eff6bded4029b888c246686388c36d4b49e885ea.apk'), ('malradar', 'cfb28e207958f1d3e280154ee69f54e8f574dae0a33283f7735efd96e06017d8.apk'), ('malradar', 'fefc882ac7428d984b9a4112ba1b53767a111b05f9196fc5e7218b6c16cc796d.apk'), ('malradar', 'c9e826490eb3bac81c95741569da8ca8c51b997660b0e57188ac9647272bb3fc.apk'), ('malradar', '301eba5b8e12405aef837b249623dbc30dc3599a187f9656e08e6dff56e48076.apk'), ('malradar', '021b6aaa963888e542e96c31e8d511c8395d9a48b21f34afc507c800bb1cc529.apk'), ('malradar', 'f4dee02495cb085eb4eda2882b63465c27fceaa13fa3da42b7a6dd808e26ba88.apk'), ('malradar', 'a88b1c01c68f944db550d45c236dcf111ae1b654062aa4fe6c71f6d297a82e6b.apk'), ('malradar', '180b39caa19b771f0b8ceabace55f053d32d65d474181b958d8282dc05df606e.apk'), ('malradar', '96a5235f84c06397806f1786d57a176b4c242ae87622394b4a74db6cfeca41cb.apk'), ('malradar', '3ddcd27fad08fa93ebbfef7bd9bfa1b200d1336ec0f0521dff7999b2ae87217b.apk'), ('malradar', 'e0e4f13d039f9e46c598a1522616f5a0a76594ff51230634919f5574b1d6fd42.apk'), ('malradar', '877d30cc81fdd542b1f1b43c4b38cffebe179a123cbb3afd5d8599b7fa124283.apk'), ('malradar', '73923dce5fffb46feaec39dfbe84b0ab23273b59ab2b6fffe01b86ccb5f33d52.apk'), ('malradar', '44fa10470d180a9548796c65d5ea4c3375827af49764e40f95686054f90fb293.apk'), ('malradar', '15f5f65b46d79291ef005e4268c3e0c785dcffc49da01debb95ab2b3575f4da2.apk'), ('malradar', '9cca3fa6000ee8d1ee875b3c439974f90dcb2f2bb95cbed35a1e0ec0e4b3fe0a.apk'), ('malradar', '2a7acd6073f21ab506f0864fab73c75ee2d0bc23f09ce64bd7aa9f3f4c1c37bc.apk'), ('malradar', 'c8276965d6d071a42708d2fe4091e89824809e54a13a8a51c630366e2856ea5a.apk'), ('malradar', 'cb4e471b7218b691d7c80d58aaa91cdf72256d6759239c274868f2d59266f9ab.apk'), ('malradar', 'e6dfeceb8e00fa6ae500c00f9e1db612c20e95b0719148d4f671d379a56f35d3.apk'), ('malradar', '5edb14dd07d769eceedbbac6c40409f1c5ef2bbf4453060bc737eb63043524ce.apk'), ('malradar', '6c9b88489af394c188c84db00fd4b868f3c7694a8b442197bb39c1e5cc74f643.apk'), ('malradar', 'a018ca84c4b3c25d345d0dd1e41e6f39859cf28aa925a437f80d572a007c9015.apk'), ('malradar', '2016694e540369142dad031966b6f299337bd1c216e4552fca9f683a66d4748c.apk'), ('malradar', '5f02d70133414aad4194ae4b19adc9e5edb3a2d7fe5c8eb729bc7d3a4ded5522.apk'), ('malradar', '3a9b219e9c4daa7de8c83d8386eb4e89b7939649938f1c1ea94008ad3b8b50c1.apk'), ('malradar', '74cb4438e8d6309103e78baad441be64fb86090eb1d82dc11b1ce903ecfcaeda.apk'), ('malradar', 'b108b0057043fae6895492fc6ca13a763a25565cd5fdced599e0d5a9fa362e7f.apk'), ('malradar', 'bd1b1db315ef27481422d71e6464a8475e64884d589cf048301aae06b4c2f970.apk'), ('malradar', '16b0e86933c614f61f9d42f89bed131191563a810422bbdec4790e6107af9503.apk'), ('malradar', '2f6bea9cec431d6d4d17383c217e9853a50fa7eb8dd127dc359116ec83d2025b.apk'), ('malradar', 'd55b1f2f9528cb6f388f7e342b348fc79234b43b51d2346ccbb2528929c2c01c.apk'), ('malradar', '157b006c164dc7aa2688010ac482f7c3ad8a67b928cec310a4484a4008cb173b.apk'), ('malradar', 'efb88dcf5eef49cc584c604e50af560768a92e03add7094ba98f1be9f46b1741.apk'), ('malradar', 'bc1f5c7f0474a3db7950061dba49fcbe1ef1fc4813186b66de6adb371a54d49b.apk'), ('malradar', '39b577b4296f187cf6d73981f9e562b66f37800dfa657c5c2278ce2ca1275beb.apk'), ('malradar', 'e7864e53373011d659ecd7d7eb64e0bab7c071f6ab4feabc1422c61d10188c56.apk'), ('malradar', '4a9875adcd9cb5431de6aa419a488da79c865fabe68c3c9fb8dfd47b5cf77144.apk'), ('malradar', 'f7651838bb43aedef99760fada6c355649d794dbfe41f45393ffe1334c1dcf51.apk'), ('malradar', 'b4c15e5755839210047e203975098570fdd50e6ee21c15e4f579273afa12440d.apk'), ('malradar', '3fa0d7f0953f4c342f4d5f9a6efb63a8e2717f869ac872de706c3bd4a10b9b3a.apk'), ('malradar', '5ed77cd85b395a0b19b3d41d47f50c75da95a3c3d581eb953fdde387e23d1273.apk'), ('malradar', 'b48289d48dd36069e0e93347193824c2b6319fa61660e3a2eb9d6a925775623f.apk'), ('malradar', '58dee279bf34b030d72625c7dfea447e3e844be9f756a09fcabd7a8a665b37cf.apk'), ('malradar', '3dda6eae9ca6483c9f09e2b488cb11d9b19255ce9404634bb85ee4e11d7afe4e.apk'), ('malradar', '592ee450a1050871d1de4f24502287fd43e89ce911438adf7ab8fce8d3ca094c.apk'), ('malradar', '2761889f6565af8d821a6fb91a8cfa75feba75bba6e4ea0295b130e68093373b.apk'), ('malradar', 'ffa9361443c9f9f46149e3ea441dbb1d8876680a4a492efcf602555a309f9865.apk'), ('malradar', '894dff83ace2bc959a1a136ad71001b96049b227e9ddca6f019169f627fcbd33.apk'), ('malradar', 'f02eea20264ae3d8d10ab378bf3a2ba04961e9212ef02f81b2362192cb45a47d.apk'), ('malradar', '081534b29e412564f634115f1a8c858c9d52086a21387c4884db9fe75bac7b35.apk'), ('malradar', 'cb4b3db7eb4599eb4d6cf43ff8bdb43ce270bbf2d77e6783f3fd4828aad37a49.apk'), ('malradar', '3834596ab1de92836c539a475b7035df8e038de9eede848bdfc266ebffae9a49.apk'), ('malradar', '471729e9f09174efdc3d3837f5d533625f980eff06a9b0c06e1414c5574400e4.apk'), ('malradar', '6e8f156a9ff947752ca4ad2dd45155dec045949f1f3750036bf8b1952ecb0a1a.apk'), ('malradar', '7ddaa2aaf485cfe9c5974e4c80c5f0250921823daac1ac241060d8eabb561a16.apk'), ('fdroid', 'com.cleveroad.sample_1.apk'), ('malradar', 'b4989d381a07d09a667c0caa3695f93ea3f6fe8a1901a90110fe04410b804050.apk'), ('malradar', '03c7bb0a03016be77b9f589deb2a2f8902bf884e85328d9b06b94830285b6439.apk'), ('malradar', 'b4665d6aba70e9b08169e55c12b8210eab2e16fcd8184aa599d0baac0fbfee35.apk'), ('malradar', '9f2ae747e0433f8640f328e704336e914d1fd6e1ff4dac66c80fe4641daec901.apk')]

def format_method(m):
    return (m.get_method().get_class_name().replace("/", ".")[1:-1], m.name, m.descriptor, m.access)

def format_encoded_method(m):
    return (m.get_class_name().replace("/", ".")[1:-1], m.get_name(), m.get_descriptor(), m.get_access_flags_string())


from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat
def get_dfs(_file) -> list[DalvikVMFormat]:
    a =  APK(_file, skip_analysis=True)
    d = []
    for dex in a.get_all_dex():
        df = DalvikVMFormat(dex, using_api=a.get_target_sdk_version())
        d.append(df)
    return d

dataset_paths = {'fdroid':'/home/user/ns/dataset/fdroid-filter', 'malradar': '/home/user/ns/dataset/malradar-filter'}

def get_native_methods_new(apk_path):
    dfs = get_dfs(apk_path)
    result = []
    for df in dfs:
        for m in df.get_methods():
            if 'native' in m.get_access_flags_string():
                result.append(format_encoded_method(m))
    return result

def get_native_methods_old(apk_path):
    apk, dfs, dex = AnalyzeAPK(apk_path)
    native_methods = [m for m in dex.get_methods() if 'native' in m.access]
    result = []
    for m in native_methods:
        result.append(format_method(m))
    return result

def average(lst):
    return sum(lst) / len(lst)

# 测试两种方法的速度，节约的时间，结果的数量对比
if __name__ == '__main__':
    # for t, f in tests:
    from tqdm import tqdm
    import time
    time_saves = []
    diffcounts = []
    try:
        for t in dataset_paths:
            for f in tqdm(os.listdir(dataset_paths[t])):
                if not f.endswith('.apk'): continue
                apk = os.path.join(dataset_paths[t], f)
                start = time.time()
                nm1 = set(get_native_methods_old(apk))
                t1 = time.time() - start
                start = time.time()
                nm2 = set(get_native_methods_new(apk))
                t2 = time.time() - start
                diffcount = len(nm2.difference(nm1))
                diffcounts.append(diffcount)
                assert len(nm1.difference(nm2)) == 0
                time_saves.append(t1-t2)
    finally:
        print(diffcounts)
        print(time_saves)
        print(f'time_saved: {average(time_saves)}, diffcount: {average(diffcounts)}')
