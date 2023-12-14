#!/bin/bash


TARGET=malradar
# TARGET=fdroid
nl='
'

SS=/home/user/ns/experiment/baseline-fd/ss.txt

if [ -z "${1}" ]; then
    echo no arg. default to $SS
else
    SS=$1
fi


for i in `ls $TARGET-results`; do
    if [[ $i != *.apk ]] ; then
        continue
    fi
    # 没有重打包的apk文件
    if [ ! -e "$TARGET-results/$i/repacked_apks/apk" ]; then
        # echo "$TARGET-results/$i/repacked_apks/apk"
        continue
    fi
    # 没有sinks文件
    if [ ! -e "$TARGET-results/$i/repacked_apks/apk.sinks.txt" ]; then
        echo error: $TARGET-results/$i/repacked_apks has no apk.sinks.txt
        # continue
    fi
    # if [ ! -s "$TARGET-results/$i/repacked_apks/apk.sinks.txt" ]; then
    #     echo empty!: $TARGET-results/$i/repacked_apks/apk.sinks.txt
    #     continue
    # fi
    # echo processing $TARGET-results/$i/repacked_apks/apk.sinks.txt
    # cp $SS $TARGET-results/$i/repacked_apks/sources-sinks.txt
    # cat $TARGET-results/$i/repacked_apks/apk.sinks.txt >> $TARGET-results/$i/repacked_apks/sources-sinks.txt
done


