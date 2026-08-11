import time
import json
import os
import psutil
import win32gui
import win32process
import sys
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.categories import KEYWORDS, HARD_MAP, FRIENDLY_NAMES, BG_PATTERN_LIST, FORCE_TRACK_PROCESSES

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

USAGE_FILE = os.path.join(DATA_DIR, 'usage_stats.json')
INTERVAL = 10
BG_INTERVAL = 30

def load_usage():
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_usage(data):
    with open(USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_tracking_info(raw_name):
    display_name = FRIENDLY_NAMES.get(raw_name, raw_name)
    if raw_name in HARD_MAP:
        category = HARD_MAP[raw_name]
    else:
        category = '其他'
        exe_lower = raw_name.lower()
        for cat, keywords in KEYWORDS.items():
            for kw in keywords:
                if kw in exe_lower:
                    category = cat
                    break
            if category != '其他':
                break
    return display_name, category

def run_tracker():
    stats = load_usage()
    print(f"✅ 追踪器已启动！数据将保存在 data/usage_stats.json")
    last_bg_scan = 0
    try:
        while True:
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            if today_str not in stats:
                stats[today_str] = {}

            # ======= 前台监控 =======
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                p = psutil.Process(pid)
                raw_name = p.name()
                display_name, category = get_tracking_info(raw_name)
                if display_name not in stats[today_str]:
                    stats[today_str][display_name] = {'fg': 0, 'bg': 0, 'hidden': 0, 'category': category, 'titles': {}}
                stats[today_str][display_name]['fg'] += INTERVAL
                if window_title:
                    if window_title not in stats[today_str][display_name]['titles']:
                        stats[today_str][display_name]['titles'][window_title] = 0
                    stats[today_str][display_name]['titles'][window_title] += INTERVAL
            except:
                pass

            # ======= 后台监控 =======
            if time.time() - last_bg_scan > BG_INTERVAL:
                found_apps = {}
                for proc in psutil.process_iter(['name', 'pid', 'cpu_percent']):
                    try:
                        raw_name = proc.info['name']
                        name_lower = raw_name.lower()
                        is_valid = False
                        for pattern in BG_PATTERN_LIST:
                            if pattern in name_lower:
                                is_valid = True
                                break
                        if raw_name in FORCE_TRACK_PROCESSES:
                            is_valid = True
                        if not is_valid:
                            continue
                        if proc.info['cpu_percent'] < 0.5 and raw_name not in FORCE_TRACK_PROCESSES:
                            continue
                        if 'mumu' in name_lower:
                            key_name = 'MuMu_Group'
                        else:
                            key_name = raw_name
                        if key_name not in found_apps:
                            found_apps[key_name] = 0
                        found_apps[key_name] += 1
                    except:
                        continue
                if found_apps:
                    share_seconds = BG_INTERVAL / len(found_apps)
                    for key_name in found_apps.keys():
                        if key_name == 'MuMu_Group':
                            display_name, category = '游戏 (MuMu模拟器)', '游戏'
                        else:
                            display_name, category = get_tracking_info(key_name)
                        if display_name not in stats[today_str]:
                            stats[today_str][display_name] = {'fg': 0, 'bg': 0, 'hidden': 0, 'category': category, 'titles': {}}
                        stats[today_str][display_name]['bg'] += share_seconds
                last_bg_scan = time.time()

            if int(time.time()) % 60 < INTERVAL:
                save_usage(stats)
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\n⏹️ 停止追踪，数据已保存！")

if __name__ == "__main__":
    run_tracker()