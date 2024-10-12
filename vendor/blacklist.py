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