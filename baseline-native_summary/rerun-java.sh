#!/bin/bash



# TARGET=malradar
TARGET=fdroid
# TARGET=nfbe
# TARGET=nfb
# TARGET=jucifybench

function runone() {
    echo java -jar /home/user/ns/dev/NativeSummary/native_summary_java/target/native_summary-1.0-SNAPSHOT.jar $1 $2 /home/user/ns/tools/platforms --out $2/repacked_apks --debug-jimple --debug-type \> $2/java_analysis.log 2\>\&1
}

DATASET=~/ns/dataset/$TARGET-filter

for i in `ls $TARGET-results`; do
    if [[ $i != *.apk ]] ; then
        continue
    fi
    # 没有重打包的apk文件
    if [ ! -e "$TARGET-results/$i/repacked_apks/apk" ]; then
        continue
    fi

    runone "$DATASET/$i" "$TARGET-results/$i"
done
# 