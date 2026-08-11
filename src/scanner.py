import os
import json
import sys
import win32com.client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.categories import KEYWORDS, HARD_MAP, GENERAL_GARBAGE_PATTERNS

PATHS = [
    os.path.join(os.environ['PROGRAMDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
    os.path.join(os.environ['USERPROFILE'], 'AppData', 'Roaming', 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
    os.path.join(os.environ['USERPROFILE'], 'Desktop')
]

INSTALL_SCAN_PATHS = [
    "D:\\Program Files",
    "D:\\Program Files (x86)",
    "D:\\SteamLibrary",
    "D:\\EpicGames",
    "D:\\Games",
    "C:\\Program Files",
    "C:\\Program Files (x86)"
]

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
OUTPUT_FILE = os.path.join(DATA_DIR, 'software_map.json')


def classify_process(exe_name):
    exe_lower = exe_name.lower()
    if exe_name in HARD_MAP:
        return HARD_MAP[exe_name]
    for category, keywords in KEYWORDS.items():
        for kw in keywords:
            if kw in exe_lower:
                return category
    return '其他'


def scan_shortcuts():
    software_map = {}
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
    except Exception:
        return software_map
    for path in PATHS:
        if not os.path.exists(path): continue
        try:
            for file in os.listdir(path):
                if file.endswith('.lnk'):
                    lnk_path = os.path.join(path, file)
                    try:
                        shortcut = shell.CreateShortCut(lnk_path)
                        target = shortcut.TargetPath
                        if target and target.lower().endswith('.exe'):
                            exe_name = os.path.basename(target)
                            # 1. 快捷方式抓到的，不管名字多怪，都保留（因为这是你主动安装的）
                            app_name = file.replace('.lnk', '')
                            category = classify_process(exe_name)
                            software_map[exe_name] = {
                                'name': app_name,
                                'category': category
                            }
                    except Exception:
                        continue
        except Exception:
            continue
    return software_map


# 🆕 核心升级：通用排雷逻辑
def is_garbage_exe(exe_name):
    """基于文件名判断是否是安装包/服务/更新程序（不看路径，通用性强）"""
    name_lower = exe_name.lower()
    for pattern in GENERAL_GARBAGE_PATTERNS:
        if pattern in name_lower:
            return True
    return False


def scan_install_dirs():
    print("📂 正在深入扫描，已启用【通用启发式排雷】...")
    software_map = {}

    for root_dir in INSTALL_SCAN_PATHS:
        if not os.path.exists(root_dir): continue
        try:
            for dirpath, dirnames, filenames in os.walk(root_dir):
                if dirpath.count(os.sep) - root_dir.count(os.sep) > 4:
                    continue

                for filename in filenames:
                    if filename.lower().endswith('.exe'):
                        exe_name = filename

                        # 2. 如果这个 EXE 名字里包含 update/service/setup 等词，直接跳过
                        if is_garbage_exe(exe_name):
                            continue

                        # 如果已经扫过了，跳过
                        if exe_name in software_map:
                            continue

                        category = classify_process(exe_name)
                        if category == '其他':
                            dir_lower = dirpath.lower()
                            if 'steam' in dir_lower or 'epic' in dir_lower or 'game' in dir_lower or 'gog' in dir_lower:
                                category = '游戏'

                        software_map[exe_name] = {
                            'name': exe_name.replace('.exe', ''),
                            'category': category
                        }
        except Exception:
            continue

    return software_map


def run_scanner():
    print("🚀 开始全自动软件识别扫描...")
    final_map = scan_shortcuts()
    print(f"✅ 快捷方式扫描完成，共识别 {len(final_map)} 个软件。")

    install_map = scan_install_dirs()
    for k, v in install_map.items():
        if k not in final_map:
            final_map[k] = v

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_map, f, ensure_ascii=False, indent=2)

    print(f"🎉 扫描完毕！最终保留 {len(final_map)} 个有效软件映射。")
    print(f"📁 路径: {OUTPUT_FILE}")


if __name__ == "__main__":
    run_scanner()