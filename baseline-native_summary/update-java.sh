#!/bin/bash

TARGET=fdroid

for apk in `ls $TARGET-results`; do
    if [[ $apk != *.apk ]] ; then
        continue
    fi
    result_dir=`realpath $TARGET-results/$apk`
    printf '%s' "docker run -i --cpus=1 --name ns-javaupdate-$apk --rm -v /home/user/ns/dataset/$TARGET-filter/$apk:/apk -v $result_dir:/out ns java /apk /out /root/platforms --out /out/repacked_apks --debug-jimple >$result_dir/java_analysis.log 2>&1"
    printf '\0'
done

# | sudo xargs -0 -I CMD --max-procs=1 bash -c CMD
