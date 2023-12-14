#!/bin/bash


TARGET=malradar
# TARGET=fdroid
# TARGET=nfbe
# TARGET=nfb
# TARGET=jucifybench


nl='
'

SS=/home/user/ns/experiment/baseline-fd/ss_taintbench.txt

if [ -z "${1}" ]; then
    >&2 echo no arg. default to $SS
else
    SS=$1
fi

OUT_PATH="/home/user/ns/dataset/${TARGET}-repacked"

if [ ! -e "$OUT_PATH" ] ; then
    mkdir -p $OUT_PATH
fi

for i in `ls $TARGET-results`; do
    if [[ $i != *.apk ]] ; then
        continue
    fi
    # 没有重打包的apk文件
    if [ ! -e "$TARGET-results/$i/repacked_apks/apk" ]; then
        # echo rm -rf $TARGET-results/$i
        # rm -rf $TARGET-results/$i
        continue
    fi
    # 没有sinks文件
    if [ ! -e "$TARGET-results/$i/repacked_apks/apk.sinks.txt" ]; then
        >&2 echo error: $TARGET-results/$i/repacked_apks has no apk.sinks.txt
        exit -1
    fi
    # empty是正常的
    # if [ ! -s "$TARGET-results/$i/repacked_apks/apk.sinks.txt" ]; then
    #     >&2 echo empty!: $TARGET-results/$i/repacked_apks/apk.sinks.txt
    # fi
    echo save to $OUT_PATH/$i
    cp $TARGET-results/$i/repacked_apks/apk $OUT_PATH/$i
    cp $SS $OUT_PATH/$i.sources-sinks.txt
    cat $TARGET-results/$i/repacked_apks/apk.sinks.txt >> $OUT_PATH/$i.sources-sinks.txt
done
