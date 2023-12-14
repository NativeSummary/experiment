#!/bin/bash

TARGET=malradar
# TARGET=fdroid
nl='
'

for i in `ls $TARGET-results`; do
    if [[ $i != *.apk ]] ; then
        continue
    fi
    if [ ! -e "$TARGET-results/$i/repacked_apks" ]; then
        continue
    fi
    if [ -f "$TARGET-results/$i/repacked_apks" ]; then
        echo file $i
        # 旧版代码输出位置修复
        # mv $TARGET-results/$i/repacked_apks $TARGET-results/$i/repacked_apk
        # mkdir $TARGET-results/$i/repacked_apks
        # mv $TARGET-results/$i/repacked_apk $TARGET-results/$i/repacked_apks/apk
    fi
    if [ -d "$TARGET-results/$i/repacked_apks" ]; then
        fname=$(ls -A $TARGET-results/$i/repacked_apks)
        if [ -z "$fname" ]; then
            continue
        fi
        # 文件只有一个，名字为apk
        if [[ "$fname" = "apk" ]]; then
            file=$TARGET-results/$i/repacked_apks/$fname
            echo ok $file
            # 旧版代码sinks文件修复
            # sudo chown -R user:user $TARGET-results/$i/repacked_apks
            # mv $file ${file}.apk
            # zip -d $file.apk 'META-INF/*.SF' 'META-INF/*.RSA'
            # mv $file.apk ${file}
            # java -jar /home/user/ns/SinksGenerator.jar $file
            continue
        fi
        # 文件数量超过一个，即包含换行
        if [[ "$fname" = *"$nl"*  ]]; then
            continue
        fi
        # 旧版代码输出位置修复
        # mv $TARGET-results/$i/repacked_apks/$fname $TARGET-results/$i/repacked_apks/apk
        echo dir $TARGET-results/$i/repacked_apks/$fname
    fi
done


