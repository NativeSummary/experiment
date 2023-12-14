FDroid数据集

基于这里的说明 https://f-droid.org/en/docs/Running_a_Mirror/ 下载repo，就是执行：rsync -aHS  --delete --delete-delay --info=progress2 mirrors.tuna.tsinghua.edu.cn::fdroid/repo/ ./repo/
然后里面有好多目录，全是放的APK的介绍，APK文件就在repo目录下。其他的都可以删
导出APK文件列表：ls ./repo | grep \\.apk$ > apklist.txt
而APK的命名有两种情况，https://f-droid.org/docs/Build_Metadata_Reference/#Builds 大部分是APK名字，下划线，然后一个数字代表版本号，有少部分APK会额外带个下划线，加上一个commit，这些很少（VSCode匹配：    .*_[0-9]*.apk$\n   ），可以手动重命名一下。得到归一化后的数据集。然后去重。
既然知道了那个后面的数字是版本号，那我直接删掉旧版本。在上面生成的文件列表里，python直接基于最后一个下划线分割，然后基于前面的去重。基于名字把APK移动到旁边文件夹即可。
