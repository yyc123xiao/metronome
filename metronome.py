"""
节拍器 - 桌面窗口版 (tkinter)
- 独立图形界面，通过电脑声音播放节拍
- 可调节：速度 BPM、声音频率、持续时间
- 支持定时开启、试听、启停控制
"""

import threading
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import winsound


class MetronomeEngine:
    """节拍引擎：后台线程驱动 winsound.Beep，支持定时开启"""

    def __init__(self):
        self.bpm = 100
        self.frequency = 880
        self.duration = 100
        self._stop_event = threading.Event()
        self._thread = None
        self._timer = None
        self.scheduled_time = None  # datetime 或 None

    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def _loop(self):
        interval = 60000.0 / self.bpm  # 每拍间隔 ms
        while not self._stop_event.is_set():
            try:
                winsound.Beep(int(self.frequency), int(self.duration))
            except Exception:
                pass  # 频率超出范围等异常时跳过本拍
            rest = interval - self.duration
            if rest > 0:
                self._stop_event.wait(rest / 1000.0)

    def start(self):
        if self.running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread = None
        self.cancel_schedule()

    def schedule(self, target):
        """定时开启，target 为 datetime；时间已过则返回 False"""
        if self.running:
            return False
        delay = (target - datetime.datetime.now()).total_seconds()
        if delay <= 0:
            return False
        self.scheduled_time = target
        self._timer = threading.Timer(delay, self._fire)
        self._timer.daemon = True
        self._timer.start()
        return True

    def _fire(self):
        self.scheduled_time = None
        self.start()

    def cancel_schedule(self):
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        self.scheduled_time = None


class App(tk.Tk):
    # 配色
    BG = "#f0f4fa"        # 窗口背景
    PRIMARY = "#2a5298"   # 主色
    GREEN = "#11998e"     # 开始按钮
    RED = "#e05555"       # 停止按钮
    ORANGE = "#e6892e"    # 定时按钮
    GRAY = "#8a93a3"      # 次要按钮

    def __init__(self):
        super().__init__()
        self.engine = MetronomeEngine()

        self.title("节拍器 Metronome")
        self.geometry("420x640")
        self.resizable(False, False)
        self.configure(bg=self.BG)

        self._build_ui()
        self._refresh_status()

        # 关闭窗口时清理线程
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- UI 构建 ----------

    def _build_ui(self):
        pad = {"padx": 24, "pady": 4}

        # 标题
        title = tk.Label(self, text="🎵 节拍器", font=("微软雅黑", 20, "bold"),
                         fg=self.PRIMARY, bg=self.BG)
        title.pack(pady=(20, 2))
        sub = tk.Label(self, text="通过电脑声音播放节拍", font=("微软雅黑", 10),
                       fg="#7a8494", bg=self.BG)
        sub.pack(pady=(0, 12))

        # --- 三个参数滑块 ---
        self.bpm_var = tk.IntVar(value=100)
        self.freq_var = tk.IntVar(value=880)
        self.dur_var = tk.IntVar(value=100)

        self._add_slider("速度 (BPM)", self.bpm_var, 40, 240, self._on_param_change)
        self._add_slider("声音频率 (Hz)", self.freq_var, 37, 4000, self._on_param_change)
        self._add_slider("持续时间 (ms)", self.dur_var, 10, 500, self._on_param_change)

        # --- 按钮行 ---
        btn_frame = tk.Frame(self, bg=self.BG)
        btn_frame.pack(padx=24, pady=(14, 6))

        self.start_btn = tk.Button(btn_frame, text="▶ 开始", font=("微软雅黑", 12, "bold"),
                                   bg=self.GREEN, fg="white", activebackground="#0d7d73",
                                   activeforeground="white", relief="flat",
                                   width=9, height=2, cursor="hand2",
                                   command=self._start)
        self.start_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = tk.Button(btn_frame, text="■ 停止", font=("微软雅黑", 12, "bold"),
                                  bg=self.RED, fg="white", activebackground="#c04040",
                                  activeforeground="white", relief="flat",
                                  width=9, height=2, cursor="hand2",
                                  state="disabled", command=self._stop)
        self.stop_btn.pack(side="left", padx=(0, 10))

        preview_btn = tk.Button(btn_frame, text="🔈 试听", font=("微软雅黑", 12, "bold"),
                                bg=self.PRIMARY, fg="white", activebackground="#1e3c72",
                                activeforeground="white", relief="flat",
                                width=9, height=2, cursor="hand2",
                                command=self._preview)
        preview_btn.pack(side="left")

        # --- 分隔线 ---
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24, pady=10)

        # --- 定时开启 ---
        sch_title = tk.Label(self, text="⏰ 定时开启", font=("微软雅黑", 12, "bold"),
                             fg="#333333", bg=self.BG)
        sch_title.pack(anchor="w", **pad)

        sch_row = tk.Frame(self, bg=self.BG)
        sch_row.pack(padx=24, pady=(0, 6))

        tk.Label(sch_row, text="时间", font=("微软雅黑", 10),
                 fg="#555555", bg=self.BG).pack(side="left", padx=(0, 8))

        self.time_entry = tk.Entry(sch_row, font=("Consolas", 12), width=12,
                                   relief="solid", bd=1, justify="center")
        self.time_entry.insert(0, "18:00:00")
        self.time_entry.pack(side="left", padx=(0, 10), ipady=4)

        self.sch_btn = tk.Button(sch_row, text="设定定时", font=("微软雅黑", 10, "bold"),
                                 bg=self.ORANGE, fg="white", activebackground="#c77120",
                                 activeforeground="white", relief="flat",
                                 cursor="hand2", padx=12, pady=4,
                                 command=self._schedule)
        self.sch_btn.pack(side="left", padx=(0, 6))

        self.cancel_btn = tk.Button(sch_row, text="取消定时", font=("微软雅黑", 10, "bold"),
                                    bg=self.GRAY, fg="white", activebackground="#6d7684",
                                    activeforeground="white", relief="flat",
                                    cursor="hand2", padx=12, pady=4,
                                    state="disabled", command=self._cancel_schedule)
        self.cancel_btn.pack(side="left")

        hint = tk.Label(self, text="格式: HH:MM 或 HH:MM:SS，若时间已过则顺延到明天",
                        font=("微软雅黑", 9), fg="#9aa3b0", bg=self.BG)
        hint.pack(anchor="w", padx=24)

        # --- 状态栏 ---
        self.status_label = tk.Label(self, text="状态: 就绪", font=("微软雅黑", 10),
                                     fg="#555555", bg="#e4ebf5", anchor="w",
                                     padx=14, pady=8)
        self.status_label.pack(side="bottom", fill="x")

    def _add_slider(self, label, var, minv, maxv, on_change):
        """添加一行参数滑块：标签 + 值 + 滑块"""
        row = tk.Frame(self, bg=self.BG)
        row.pack(fill="x", padx=24, pady=(8, 0))

        tk.Label(row, text=label, font=("微软雅黑", 11),
                 fg="#333333", bg=self.BG).pack(side="left")

        val_label = tk.Label(row, text=str(var.get()), font=("Consolas", 11, "bold"),
                             fg="white", bg=self.PRIMARY, padx=10, pady=1)
        val_label.pack(side="right")

        slider = ttk.Scale(self, from_=minv, to=maxv, variable=var,
                           command=on_change)
        slider.pack(fill="x", padx=24, pady=(2, 0))

        # 保存值标签引用，便于更新显示
        if not hasattr(self, "_val_labels"):
            self._val_labels = {}
        self._val_labels[label] = val_label

    # ---------- 事件处理 ----------

    def _on_param_change(self, _event=None):
        # 更新数值显示（取整）
        for label, var in (("速度 (BPM)", self.bpm_var),
                           ("声音频率 (Hz)", self.freq_var),
                           ("持续时间 (ms)", self.dur_var)):
            self._val_labels[label].config(text=str(int(var.get())))
        # 运行中实时应用参数
        self.engine.bpm = int(self.bpm_var.get())
        self.engine.frequency = int(self.freq_var.get())
        self.engine.duration = int(self.dur_var.get())

    def _start(self):
        self.engine.bpm = int(self.bpm_var.get())
        self.engine.frequency = int(self.freq_var.get())
        self.engine.duration = int(self.dur_var.get())
        self.engine.start()
        self._refresh_buttons()

    def _stop(self):
        self.engine.stop()
        self._refresh_buttons()

    def _preview(self):
        """播放一声当前设置"""
        freq, dur = int(self.freq_var.get()), int(self.dur_var.get())
        threading.Thread(target=lambda: winsound.Beep(freq, dur), daemon=True).start()

    def _schedule(self):
        text = self.time_entry.get().strip()
        target = self._parse_time(text)
        if target is None:
            messagebox.showerror("时间格式错误", "请输入 HH:MM 或 HH:MM:SS 格式的时间\n例如 18:30 或 18:30:00")
            return
        # 若时间已过今天，顺延到明天
        if target < datetime.datetime.now():
            target += datetime.timedelta(days=1)
        self.engine.bpm = int(self.bpm_var.get())
        self.engine.frequency = int(self.freq_var.get())
        self.engine.duration = int(self.dur_var.get())
        self.engine.schedule(target)
        self._refresh_buttons()

    def _cancel_schedule(self):
        self.engine.cancel_schedule()
        self._refresh_buttons()

    @staticmethod
    def _parse_time(text):
        """解析 HH:MM 或 HH:MM:SS，失败返回 None"""
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                t = datetime.datetime.strptime(text, fmt).time()
                return datetime.datetime.combine(datetime.date.today(), t)
            except ValueError:
                continue
        return None

    # ---------- 状态刷新 ----------

    def _refresh_buttons(self):
        running = self.engine.running
        scheduled = self.engine.scheduled_time is not None
        self.start_btn.config(state="disabled" if running else "normal")
        self.stop_btn.config(state="normal" if running else "disabled")
        self.sch_btn.config(state="disabled" if running or scheduled else "normal")
        self.cancel_btn.config(state="normal" if scheduled else "disabled")

    def _refresh_status(self):
        """每 300ms 刷新状态栏与按钮状态"""
        if self.engine.running:
            e = self.engine
            self.status_label.config(
                text=f"状态: ▶ 播放中  |  {e.bpm} BPM  |  {e.frequency} Hz  |  {e.duration} ms",
                fg=self.GREEN)
        elif self.engine.scheduled_time is not None:
            t = self.engine.scheduled_time.strftime("%Y-%m-%d %H:%M:%S")
            self.status_label.config(text=f"状态: ⏰ 已定时，将于 {t} 自动开启", fg=self.ORANGE)
        else:
            self.status_label.config(text="状态: 就绪", fg="#555555")
        self._refresh_buttons()
        self.after(300, self._refresh_status)

    def _on_close(self):
        self.engine.stop()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
