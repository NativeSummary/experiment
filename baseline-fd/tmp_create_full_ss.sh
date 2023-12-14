#!/bin/bash


TARGET=malradar
TARGET=fdroid
nl='
'

SS=/home/user/ns/experiment/baseline-fd/ss.txt

if [ -z "${1}" ]; then
    echo no arg. default to $SS
else
    SS=$1
fi

PREFIX=/home/user/ns/dataset/nfbe-repacked

for i in `ls $PREFIX`; do
    if [[ $i != *.apk ]] ; then
        continue
    fi
    # 没有sinks文件
    if [ ! -e "$PREFIX/$i.sinks.txt" ]; then
        echo error: $TARGET-results/$i/repacked_apks has no apk.sinks.txt
        continue
    fi
    if [ ! -s "$PREFIX/$i.sinks.txt" ]; then
        echo empty!: $PREFIX/$i.sinks.txt
    fi
    echo processing $PREFIX/$i.sinks.txt
    cp $SS $PREFIX/$i.sources-sinks.txt
    cat $PREFIX/$i.sinks.txt >> $PREFIX/$i.sources-sinks.txt
done


