# ActionLogger

自用的效率与时间管理工具。

## 功能

- 记录应用使用日志
- 每30分钟提醒记录日程表，并提示更新下一30分钟待办事项（分心时提醒用户真正该做的事情）
- 触发黑名单应用时，间歇性提醒用户
  - 专注模式下，若是用户不及时切换，在一定时间后自动杀掉黑名单应用（起到强制打断无意识间分心的作用）

## 环境

- Windows 11 (Windows 10 理论可用，未经测试)
- Python 3.10 (其他版本可能需要修改requirements.txt)
- VirtualEnv
- Visual Studio Code (可选，code.exe需要存在于PATH中，用于快速查看日志文件所在目录)

## 使用

1. 安装依赖

```bash
py -3.10 -m venv .\venv
pip install -r requirements.txt
```

2. 在venv中打包生成二进制

```bash
.\venv\Scripts\Activate.ps1
.\build.bat
```

3. 安装

```bash
.\installer.ps1
```

4. 运行
  
在开始菜单中搜索ActionLogger，点击运行。

5. 修改配置

在安装目录下的blacklist.py中修改黑名单应用列表。列表采用正则表达式匹配，当nproc和title同时匹配时，触发黑名单应用。

示例：

```py
blacklist = [
    # 微信 : nproc = WeChat.exe and title any
    (r"WeChat\.exe", r".*"),
    # 小红书 : nproc = firefox.exe and title contains "小红书"
    (r"firefox\.exe", r".*小红书.*"),
    # 知乎 : nproc = firefox.exe and title contains "知乎"
    (r"firefox\.exe", r".*知乎.*"),
    # QQ : nproc = QQ.exe and title any
    (r"QQ\.exe", r".*"),
    # CS2 : nproc = cs2.exe and title any
    (r"cs2\.exe", r".*"),
]
```

在安装目录下的config.txt中修改日志目录。该文件默认使用UTF-8 with BOM编码。

4. 卸载

```bash
.\uninstaller.ps1
```

## 说明

本项目不对其中内容的正确性以及任何使用后果负责，使用前请仔细阅读代码，了解其功能。

项目产物可能杀死用户的重要工作进程（如浏览器、微信等应用，若是存在于黑名单中），造成数据丢失。

请在充分了解工作机制并确认按需定制黑名单的情况下谨慎使用。
