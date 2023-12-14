#!/bin/bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

TARGET=malradar
TARGET=fd

run_one() {
    timeout 1800 java -jar /home/user/ns/tools/flowdroid-2.10/soot-infoflow-cmd-jar-with-dependencies.jar --timeout 1200 --resulttimeout 1200 --maxthreadnum 64 --mergedexfiles \
    -s $SCRIPTPATH/ss.txt \
    -p /home/user/ns/tools/platforms \
    -o /home/user/ns/experiment/baseline-fd/$TARGET-results \
    -a $1
}

for filename in /home/user/ns/dataset/$TARGET-filter/*.apk; do
    run_one $filename
done

