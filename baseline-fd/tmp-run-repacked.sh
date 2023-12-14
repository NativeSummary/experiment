#!/bin/bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# TARGET=malradar
# TARGET=fd
# TARGET=nfbe-repacked
TARGET=jucifybench-repacked

run_one() {
    timeout 1800 java -jar /home/user/ns/tools/flowdroid-2.10/soot-infoflow-cmd-jar-with-dependencies.jar -pa CONTEXTSENSITIVE -pr PRECISE -ps -sf CONTEXTFLOWSENSITIVE --dataflowsolver CONTEXTFLOWSENSITIVE --mergedexfiles \
    -s $1.sources-sinks.txt \
    -p /home/user/ns/tools/platforms \
    -o /home/user/ns/experiment/baseline-fd/$TARGET-results \
    -a $1
}

# for filename in /home/user/ns/dataset/$TARGET-filter/*.apk; do
#     run_one $filename
# done
mkdir -p /home/user/ns/experiment/baseline-fd/$TARGET-results
for filename in /home/user/ns/dataset/$TARGET/*.apk; do
    run_one $filename
done
