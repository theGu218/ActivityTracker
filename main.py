import sys
import os
import subprocess
import threading
import time


# ========== 核心修改：一启动就在后台悄悄运行 tracker ==========
def start_tracker_daemon():
    python_exe = sys.executable
    tracker_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "tracker.py")

    if os.path.exists(tracker_path):
        base_dir = os.path.dirname(python_exe)
        pythonw = os.path.join(base_dir, "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = python_exe

        subprocess.Popen([pythonw, tracker_path], shell=False, creationflags=subprocess.CREATE_NO_WINDOW)
        print("🟢 后台追踪器已唤醒 (静默运行)")


threading.Thread(target=start_tracker_daemon, daemon=True).start()
# ============================================================

import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = os.path.join("data", "usage_stats.json")
STARTUP_DIR = os.path.join(os.environ['USERPROFILE'], "AppData", "Roaming", "Microsoft", "Windows", "Start Menu",
                           "Programs", "Startup")


class ActivityTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("电脑活动监控 - 控制中心")
        self.root.geometry("1000x780")

        style = ttk.Style()
        style.theme_use('clam')

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.data_tab = tk.Frame(self.notebook)
        self.notebook.add(self.data_tab, text=" 📊 使用记录 ")
        self.settings_tab = tk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text=" ⚙️ 设置与更新日志 ")

        self.setup_data_tab()
        self.setup_settings_tab()

    def setup_data_tab(self):
        top_frame = tk.Frame(self.data_tab)
        top_frame.pack(pady=10)
        self.mode_var = tk.StringVar(value="今天")
        tk.Label(top_frame, text="📅 选择时间段：", font=("微软雅黑", 12)).pack(side=tk.LEFT, padx=10)
        for mode in ["今天", "本周", "累计至今"]:
            tk.Radiobutton(top_frame, text=mode, variable=self.mode_var, value=mode, command=self.refresh_data).pack(
                side=tk.LEFT, padx=5)
        self.content_frame = tk.Frame(self.data_tab)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.refresh_data()

    def get_data(self, raw_data, dates):
        apps = {}
        for day in dates:
            if day in raw_data:
                for app, info in raw_data[day].items():
                    if app not in apps:
                        apps[app] = {'category': info.get('category', '其他'), 'fg': 0, 'bg': 0, 'hidden': 0}
                    apps[app]['fg'] += info.get('fg', 0)
                    apps[app]['bg'] += info.get('bg', 0)
                    apps[app]['hidden'] += info.get('hidden', 0)
        return apps

    def refresh_data(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if not os.path.exists(DATA_FILE):
            tk.Label(self.content_frame, text="⏳ 正在等待数据生成... (后台追踪器已启动)", font=("微软雅黑", 14)).pack(
                pady=50)
            self.root.after(1000, self.refresh_data)
            return

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except:
            tk.Label(self.content_frame, text="数据文件损坏，正在重新生成...", font=("微软雅黑", 14)).pack(pady=50)
            self.root.after(1000, self.refresh_data)
            return

        today = datetime.date.today().strftime("%Y-%m-%d")
        week_dates = [
            (datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday() - i)).strftime("%Y-%m-%d")
            for i in range(7)]

        mode = self.mode_var.get()
        target_dates = [today] if mode == "今天" else (week_dates if mode == "本周" else sorted(raw_data.keys()))
        apps_data = self.get_data(raw_data, target_dates)

        if not apps_data:
            tk.Label(self.content_frame, text="📅 该时间段暂无数据，请稍等几分钟...", font=("微软雅黑", 14)).pack(pady=50)
            return

        rows = []
        category_totals = {}
        for app, info in apps_data.items():
            fg_h = round(info['fg'] / 3600, 2)
            bg_h = round(info['bg'] / 3600, 2)
            hidden_h = round(info['hidden'] / 3600, 2)
            total_h = round(fg_h + bg_h + hidden_h, 2)
            category = info['category']
            rows.append([app, category, fg_h, bg_h, hidden_h, total_h])
            category_totals[category] = category_totals.get(category, 0) + total_h

        rows.sort(key=lambda x: x[5], reverse=True)
        columns = ("应用", "分类", "🟢前台", "🟡最小化", "🔴托盘", "📈 总用时")
        tree = ttk.Treeview(self.content_frame, columns=columns, show='headings', height=12)
        for c in columns:
            tree.heading(c, text=c)
            tree.column(c, width=140, anchor='center')
        for row in rows[:25]:
            tree.insert("", tk.END, values=row)
        tree.pack(fill=tk.X, expand=False, pady=(0, 15))

        chart_frame = tk.Frame(self.content_frame)
        chart_frame.pack(fill=tk.BOTH, expand=True)
        try:
            cat_names = list(category_totals.keys())
            cat_values = list(category_totals.values())
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.barh(cat_names, cat_values, color=['#FF6B6B', '#4ECDC4', '#FFE66D', '#A8E6CF'])
            ax.set_title(f"各类别总时长分布 ({mode})")
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            plt.close(fig)
        except Exception:
            pass

    # ================== 重新添加开机自启功能 ==================
    def check_autostart(self):
        lnk_path = os.path.join(STARTUP_DIR, "ActivityTracker.lnk")
        return os.path.exists(lnk_path)

    def toggle_autostart(self):
        is_enable = self.autostart_var.get()
        app_path = sys.executable if getattr(sys, 'frozen', False) else __file__
        lnk_path = os.path.join(STARTUP_DIR, "ActivityTracker.lnk")

        if is_enable:
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(lnk_path)
                shortcut.TargetPath = app_path
                # 关键：自启动时携带隐藏参数，防止开机弹窗界面！
                shortcut.Arguments = "--service"
                shortcut.WorkingDirectory = os.path.dirname(app_path)
                shortcut.Save()
            except Exception:
                self.autostart_var.set(False)
        else:
            if os.path.exists(lnk_path):
                os.remove(lnk_path)

    def setup_settings_tab(self):
        frame = tk.Frame(self.settings_tab, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # 1. 开机自启
        self.autostart_var = tk.BooleanVar(value=self.check_autostart())
        tk.Label(frame, text="⚡ 开机自动启动 (静默记录)", font=("微软雅黑", 14)).pack(anchor='w', pady=10)
        chk = tk.Checkbutton(frame, text="启用开机自启", variable=self.autostart_var, command=self.toggle_autostart)
        chk.pack(anchor='w')

        # 2. 日志板块
        tk.Label(frame, text="📜 版本更新日志", font=("微软雅黑", 14)).pack(anchor='w', pady=(20, 5))

        # ✅ 这里必须先创建 log_txt 组件，放到页面上，再往里面写内容！
        log_txt = scrolledtext.ScrolledText(frame, height=20, font=("微软雅黑", 10))
        log_txt.pack(fill=tk.BOTH, expand=True)

        # ================= 调试修改区 =================
        # 判断当前是 源码运行 还是 exe 打包运行
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)  # 如果是 exe，找 exe 所在目录
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))  # 如果是 py，找 py 所在目录

        changelog_file = os.path.join(base_dir, "changelog.md")

        # 现在 log_txt 已经存在了，可以放心插入了
        log_txt.insert(tk.END, f"📁 程序正在查找的路径：\n{changelog_file}\n\n")

        if os.path.exists(changelog_file):
            log_txt.insert(tk.END, "✅ 找到文件！正在加载内容...\n\n")
            try:
                with open(changelog_file, "r", encoding="utf-8") as f:
                    log_txt.insert(tk.END, f.read())
                log_txt.insert(tk.END, "\n\n=== 读取完毕 ===")
            except Exception as e:
                log_txt.insert(tk.END, f"❌ 读取文件时发生错误：\n{e}")
        else:
            log_txt.insert(tk.END, "❌ 找不到日志文件！\n")
            log_txt.insert(tk.END, f"👉 请确保 `changelog.md` 和 `ActivityTracker.exe` 放在同一个文件夹里。")
        # =======================================================

        log_txt.config(state='disabled')


if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = ActivityTrackerApp(root)
    root.mainloop()
