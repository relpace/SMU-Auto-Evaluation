# 南方医科大学自动评课脚本
如题，实现南医教务课程自动评价。支持小范围的随机打分。
# 使用方法
## 对于一般Windows用户
># 1.环境配置
>0. 安装Python
>1. 安装Pycharm 
>2. 下载解压项目文件： 项目主页 - Code - Download Zip 
>3. 打开Pycharm 点击 文件 - 打开 - 选择解压的项目文件夹
>4. 弹出“正在创建虚拟环境”窗口，选择确定。等待依赖安装完成
>5. Pycharm侧栏-Python软件包-添加软件包-从磁盘-选择muggle-ocr-1.0.3.tar.gz
>6. 在脚本同一目录下新建名为config.ini的配置文件
>
> 配置文件格式：
>
>     [login]
>     account=你的账号
>     password=你的密码
># 2.定时任务设置
>Win+R 运行
>
>     taskschd.msc
>### 点击 操作 - 创建任务
>触发器选项卡:
> * 按预定计划-每天 时间任意
>
>操作选项卡:
>* 程序或脚本：选择 脚本下载目录\SMU-Auto-Evaluation-Master\.venv\Scripts\python.exe
>* 添加参数: main.py
>* 起始于: 你的目录\SMU-Auto-Evaluation-Master
>
>设置选项卡：
>* 勾选[如果过了计划开始时间，立即启动任务]
>
> # 3.Enjoy


