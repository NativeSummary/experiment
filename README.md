# Experiment

## Folder layout

- experiment: (this repo)
- dataset: contains android app datasets to be analyzed.
- tools: contains many other tools
    - flowdroid-2.10/
    - platforms/ from https://github.com/Sable/android-platforms
    - amandroid/argus-saf-3.2.1-SNAPSHOT-assembly.jar
    - appshark-0.1.2

## DataDesign

- ToolRunInfo (namedTuple)
    - tool_name
    - apk_name
    - apk_dataset
    - is_success
    - total_time
    - total_mem
    - flow_count
    - flow_content (for jnsaf: string content, for other tools: path to xml file.)
    - j2n_find_count
    - j2n_success_count
    - n2j_find_count
    - n2j_success_count
    - native_related_flow_count
    - CONSTRAINT tool_name_unique UNIQUE (tool_name, apk_name)

- NSTimeInfo
    - apk_name
    - apk_dataset
    - target_mode
    - total_time_without_taint
    - pre_analysis_time
    - ghidra_loading time
    - bai_script time
    - java_time
    - taint_analysis_time
    - CONSTRAINT apk_name_unique UNIQUE (apk_name, target_mode)

- JNIRunInfo
    - tool_name
    - apk_name
    - so_name
    - entry_addr
    - running_time
    - covered_funcs
    - covered_addrs
    - Coverage
    - CONSTRAINT jni_unique UNIQUE (tool_name, apk_name, so_name, entry_addr)

## Steps

1. ~~use `get-code-size.py` to generate `code_sizes.pickel`(dex bytecode size)~~
1. use `mem_time_collector.py` to collect memory time and is_success info into database.
1. use `running_time_analysis-ng.py` (ng means next generation), to collect time and memory info for nativesummary.
1. use `get-stats.py` to collect j2n n2j edges.
1. use `flow_compare.py` to get `#NativeRelatedFlows` and `#TotalFlows`

get datas:
1. use `running_time_analysis-ng.py` to get average running time of each part of nativesummary
1. use `get-stats.py` `print_stats` to j2n n2j edges ...
1. `plot_box_main` in `get-stats.py` generates `time_box.pdf` and `mem_box.pdf`.
1. ~~`get_edges` in `get-stats.py` generates `jni_time_box.pdf`.~~

### matched output

NaitveSummary
- `Analysis spent (.*) ms for (\S*)`
    - binary analysis: Time spent on each registered jni function.
- `Running solver on (.*) function`
    - binary analysis: the native method analyzed

### other

rm docker container by name
```
docker rm $(docker ps -a --format "{{.Names}}" | grep ns-nooptcompare)
```
