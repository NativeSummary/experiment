#!/bin/bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

MR=/home/user/ns/dataset/malradar

run_one() {
    RES_DIR=$SCRIPTPATH/malradar-results/$1
    mkdir -p $RES_DIR
    cp $MR/$1 $RES_DIR/$1
    docker run -i --rm --cpus=1 --memory=32G -v $RES_DIR:/root/apps/ nativesummary/jnsaf:3.2.1 /root/apps/$1
    rm $RES_DIR/$1
}

for filename in /home/user/ns/dataset/malradar/*.apk; do
    run_one `basename $filename`
done
