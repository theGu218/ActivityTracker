# config/categories.py

FILTER_LIST = ['svchost.exe', 'trustedinstaller.exe']
GENERAL_GARBAGE_PATTERNS = ['setup', 'update', 'install', 'service', 'helper', 'x64']

KEYWORDS = {
    '游戏': ['steam', 'genshin', 'honkai', 'starrail', 'wuthering', 'mumu', 'lol', 'rdr2'],
    '工作': ['pycharm', 'code', 'vscode', 'notepad', 'word', 'excel', 'ppt', 'photoshop'],
    '社交': ['qq', 'wechat', '微信', 'kook'],
    '娱乐': ['cloudmusic', 'qqmusic'],
    '上网': ['chrome', 'firefox', 'edge', 'msedge', 'clash']
}

HARD_MAP = {'MuMuNxMain.exe': '游戏', 'launcher.exe': '游戏'}

FRIENDLY_NAMES = {
    'pycharm64.exe': '写代码 (PyCharm)', 'cloudmusic.exe': '听歌 (网易云)',
    'qq.exe': '聊QQ', 'WeChat.exe': '聊微信', 'msedge.exe': '刷网页 (Edge)',
    'TapTap.exe': '游戏 (TapTap)', 'MuMuNxMain.exe': '游戏 (MuMu模拟器)',
    'steam.exe': '游戏 (Steam)', 'steamwebhelper.exe': '游戏 (Steam)',
    'GenshinImpact.exe': '原神', 'launcher.exe': '米哈游启动器',
    'Steam++.exe': '游戏 (Steam)'
}

# === 核心后台进程模糊匹配词库 ===
BG_PATTERN_LIST = ['mumu', 'qq', 'wechat', 'cloudmusic', 'steam']

# === 🟢 终极兜底：强制追踪白名单（无视 CPU 占用率，只要进程活着就算时间） ===
# 因为现代电脑网易云解码走显卡，CPU 可能一直是 0%，加上这个保证挂机听歌也能被计入！
FORCE_TRACK_PROCESSES = ['cloudmusic.exe']