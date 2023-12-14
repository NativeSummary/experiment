

输入数据集路径和source sink文件路径。
1. 先创建输出文件夹
2. 把source和sink文件转换过来
3. 创建运行配置
3. 打印运行命令到stdout，stderr提示如何使用xargs批量调用。

无论是repacked，还是baseline都可以这样跑。

```
svn checkout https://github.com/bytedance/appshark/trunk/config
```