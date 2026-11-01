from __future__ import annotations

import codecs
import importlib.util
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

APP_NAME = "Instagram Archive"
GITHUB_USER = "ramdanolii14"
GITHUB_REPO = "InstagramDownloader-CLI"
GITHUB_PROFILE_URL = "https://github.com/ramdanolii14"
GITHUB_REPO_URL = "https://github.com/ramdanolii14/InstagramDownloader-CLI"

CATEGORY_OPTIONS = [
    ("Posts", "posts"),
    ("Reels", "reels"),
    ("Photos", "photos"),
    ("Tagged posts", "tagged"),
    ("Reposts", "reposts"),
    ("Stories (active)", "stories"),
    ("Highlights", "highlights"),
    ("Highlight covers", "highlights-covers"),
    ("Profile avatar", "avatar"),
    ("Profile information", "info"),
]

DEFAULT_SETTINGS = {
    "background": "#101827",
    "panel": "#172235",
    "accent": "#8b5cf6",
    "font_scale": 1.0,
    "cookies_path": "",
    "output_path": str(Path.home() / "Documents" / "Instagram Archive"),
}

def app_data_dir() -> Path:
    base = os.environ.get("APPDATA")
    path = Path(base) / "InstagramArchive" if base else Path.home() / ".instagram-archive"
    path.mkdir(parents=True, exist_ok=True)
    return path

def settings_path() -> Path:
    return app_data_dir() / "settings.json"

def load_settings() -> dict:
    settings = DEFAULT_SETTINGS.copy()
    try:
        loaded = json.loads(settings_path().read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            settings.update({k: v for k, v in loaded.items() if k in settings})
    except (OSError, json.JSONDecodeError):
        pass
    return settings

def save_settings(settings: dict) -> None:
    settings_path().write_text(
        json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8"
    )

def normalize_username(value: str) -> str | None:
    value = value.strip()
    if value.startswith("@"):
        value = value[1:]
    if "://" in value:
        match = re.fullmatch(
            r"https?://(?:www\.)?instagram\.com/([A-Za-z0-9._]+)/?/?",
            value,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        value = match.group(1)
    if not re.fullmatch(r"[A-Za-z0-9._]{1,30}", value):
        return None
    return value

def fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "InstagramArchive/1.0 (GitHub: ramdanolii14)",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))

class InstagramArchiveApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.settings = load_settings()
        self.current_page = "home"
        self.process: subprocess.Popen | None = None
        self.worker_thread: threading.Thread | None = None
        self.events: queue.Queue = queue.Queue()
        self.download_started = False
        self.download_active = False
        self.download_stop_event: threading.Event | None = None
        self.download_log_history: list[str] = []
        self.download_metrics = {
            "started_at": None,
            "last_activity": None,
            "current_file": "",
            "current_bytes": 0,
            "current_speed": 0.0,
            "current_percent": None,
            "completed": 0,
            "skipped": 0,
            "failed": 0,
            "phase": "Ready",
        }
        self._last_download_ui_refresh = 0.0
        self.profile_info = None
        self.repo_info = None
        self.install_running = False
        self.install_process: subprocess.Popen | None = None
        self.install_logs: list[str] = []
        self.install_last_error = ""

        self.bg = self.settings["background"]
        self.panel = self.settings["panel"]
        self.accent = self.settings["accent"]
        self.card = self.mix_color(self.bg, self.panel, 0.55)
        self.text = "#edf2ff"
        self.muted = "#a7b3c8"
        self.green = "#2ecc91"
        self.red = "#ff6b75"
        self.yellow = "#f5bd4f"
        self.font_scale = float(self.settings.get("font_scale", 1.0))

        self.root.title("Instagram Archive | by Ramdan Olii")
        self.root.geometry("1120x760")
        self.root.minsize(900, 650)
        self.root.configure(bg=self.bg)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.configure_ttk()

        self.shell = tk.Frame(self.root, bg=self.bg)
        self.shell.pack(fill="both", expand=True)
        self.sidebar = tk.Frame(self.shell, bg=self.panel, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.content = tk.Frame(self.shell, bg=self.bg)
        self.content.pack(side="left", fill="both", expand=True)

        self.build_sidebar()
        self.show_page("home")
        self.root.after(100, self.poll_events)

    @staticmethod
    def mix_color(first: str, second: str, ratio: float) -> str:
        try:
            a = tuple(int(first[i:i + 2], 16) for i in (1, 3, 5))
            b = tuple(int(second[i:i + 2], 16) for i in (1, 3, 5))
            values = [round(x * (1 - ratio) + y * ratio) for x, y in zip(a, b)]
            return "#" + "".join(f"{v:02x}" for v in values)
        except (ValueError, TypeError):
            return "#1d2b42"

    def configure_ttk(self):
        self.style.configure(
            "TEntry",
            fieldbackground=self.panel,
            foreground=self.text,
            insertcolor=self.text,
            padding=8,
        )
        self.style.configure(
            "TCheckbutton",
            background=self.bg,
            foreground=self.text,
            font=("Segoe UI", max(9, round(10 * self.font_scale))),
        )
        self.style.map(
            "TCheckbutton",
            background=[("active", self.bg)],
            foreground=[("disabled", self.muted)],
        )
        self.style.configure(
            "Horizontal.TProgressbar",
            troughcolor=self.panel,
            background=self.accent,
            bordercolor=self.panel,
            lightcolor=self.accent,
            darkcolor=self.accent,
        )

    def build_sidebar(self):
        brand = tk.Frame(self.sidebar, bg=self.panel)
        brand.pack(fill="x", padx=18, pady=(26, 28))
        tk.Label(
            brand, text="IG", bg=self.accent, fg="#ffffff",
            font=("Segoe UI", 18, "bold"), width=3, height=1,
        ).pack(anchor="w")
        tk.Label(
            brand, text="INSTAGRAM\nARCHIVE", bg=self.panel, fg=self.text,
            font=("Segoe UI", 13, "bold"), justify="left",
        ).pack(anchor="w", pady=(12, 3))
        tk.Label(
            brand, text="Desktop edition", bg=self.panel, fg=self.muted,
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        self.nav_buttons = {}
        for key, label in [
            ("home", "⌂   Main menu"),
            ("download", "↓   Download account"),
            ("settings", "⚙   Settings"),
            ("info", "ⓘ   About / GitHub"),
        ]:
            button = tk.Button(
                self.sidebar,
                text=label,
                anchor="w",
                relief="flat",
                bd=0,
                padx=18,
                pady=13,
                cursor="hand2",
                font=("Segoe UI", 10, "bold"),
                command=lambda page=key: self.show_page(page),
            )
            button.pack(fill="x", padx=12, pady=3)
            self.nav_buttons[key] = button

        tk.Frame(self.sidebar, bg=self.panel).pack(fill="both", expand=True)
        tk.Label(
            self.sidebar,
            text="Made by Ramdan Olii\nGitHub: @ramdanolii14",
            bg=self.panel,
            fg=self.muted,
            justify="left",
            font=("Segoe UI", 8),
        ).pack(anchor="w", padx=18, pady=20)

    def button(self, parent, text, command, *, primary=False, width=None):
        return tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            bg=self.accent if primary else self.panel,
            fg="#ffffff" if primary else self.text,
            activebackground=self.mix_color(self.accent, "#ffffff", 0.18)
            if primary else self.card,
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=16,
            pady=10,
            cursor="hand2",
            font=("Segoe UI", max(9, round(10 * self.font_scale)), "bold"),
        )

    def label(self, parent, text, *, size=10, color=None, bold=False, **kwargs):
        return tk.Label(
            parent,
            text=text,
            bg=kwargs.pop("bg", self.bg),
            fg=color or self.text,
            font=("Segoe UI", max(8, round(size * self.font_scale)),
                  "bold" if bold else "normal"),
            **kwargs,
        )

    def card_frame(self, parent, **kwargs):
        return tk.Frame(parent, bg=self.card, padx=18, pady=16, **kwargs)

    def clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()

    def show_page(self, page: str):
        self.current_page = page
        self.clear_content()
        for key, button in self.nav_buttons.items():
            selected = key == page
            button.configure(
                bg=self.accent if selected else self.panel,
                fg="#ffffff" if selected else self.muted,
                activebackground=self.accent if selected else self.card,
            )

        title_map = {
            "home": ("Main menu", "Kelola arsip Instagram dari satu aplikasi."),
            "download": ("Download account", "Arsipkan konten akun yang kamu miliki atau berhak kamu simpan."),
            "settings": ("Settings", "Atur tampilan dan preferensi aplikasi."),
            "info": ("About & GitHub", "Informasi aplikasi dan profil pengembang."),
        }
        title, subtitle = title_map[page]
        header = tk.Frame(self.content, bg=self.bg)
        header.pack(fill="x", padx=30, pady=(26, 18))
        self.label(header, title, size=22, bold=True).pack(anchor="w")
        self.label(header, subtitle, size=10, color=self.muted).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self.content, bg=self.bg)
        body.pack(fill="both", expand=True, padx=30, pady=(0, 28))

        if page == "home":
            self.render_home(body)
        elif page == "download":
            self.render_download(body)
        elif page == "settings":
            self.render_settings(body)
        elif page == "info":
            self.render_info(body)

    def render_home(self, body):
        hero = tk.Frame(body, bg=self.card, padx=25, pady=24)
        hero.pack(fill="x", pady=(0, 18))
        self.label(hero, "Your memories, in one archive.", size=21, bold=True, bg=self.card).pack(anchor="w")
        self.label(
            hero,
            "Simpan foto, video, carousel, reels, stories aktif, dan highlights "
            "yang dapat diakses oleh akunmu.",
            size=10, color=self.muted, bg=self.card, wraplength=720, justify="left",
        ).pack(anchor="w", pady=(9, 16))
        self.button(hero, "Start archiving  →", lambda: self.show_page("download"), primary=True).pack(anchor="w")

        cards = tk.Frame(body, bg=self.bg)
        cards.pack(fill="x", pady=(0, 18))
        for title, detail, action, command in [
            ("Download account", "Pilih akun, kategori konten, cookies, dan folder tujuan.", "Open downloader →", lambda: self.show_page("download")),
            ("Personalize", "Ubah warna latar, warna aksen, dan ukuran teks.", "Open settings →", lambda: self.show_page("settings")),
            ("About this project", "Lihat informasi pengembang dan repository GitHub.", "View information →", lambda: self.show_page("info")),
        ]:
            item = self.card_frame(cards)
            item.pack(fill="x", pady=6)
            self.label(item, title, size=13, bold=True, bg=self.card).pack(anchor="w")
            self.label(item, detail, size=9, color=self.muted, bg=self.card).pack(anchor="w", pady=(5, 9))
            self.button(item, action, command).pack(anchor="w")

        notice = tk.Frame(body, bg=self.panel, padx=16, pady=13)
        notice.pack(fill="x", side="bottom")
        self.label(
            notice,
            "Privacy first: cookies disimpan di perangkatmu. Jangan unggah atau bagikan file cookies.txt.",
            size=9, color=self.yellow, bg=self.panel, wraplength=760, justify="left",
        ).pack(anchor="w")

    def render_download(self, body):
        form = tk.Frame(body, bg=self.bg)
        form.pack(fill="both", expand=True)

        account_card = self.card_frame(form)
        account_card.pack(fill="x", pady=(0, 12))
        self.label(account_card, "1. Instagram account", size=12, bold=True, bg=self.card).pack(anchor="w")
        self.label(account_card, "Username atau URL profil Instagram", size=9, color=self.muted, bg=self.card).pack(anchor="w", pady=(8, 4))
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(account_card, textvariable=self.username_var)
        username_entry.pack(fill="x", ipady=2)
        username_entry.focus_set()

        self.label(account_card, "2. Session cookies", size=12, bold=True, bg=self.card).pack(anchor="w", pady=(15, 0))
        self.label(
            account_card,
            "Pilih file cookies.txt hasil ekspor dari browser yang sudah login. "
            "Aplikasi hanya menyimpan lokasi file, bukan menyalin isi cookies.",
            size=9, color=self.muted, bg=self.card, wraplength=780, justify="left",
        ).pack(anchor="w", pady=(5, 7))
        cookie_row = tk.Frame(account_card, bg=self.card)
        cookie_row.pack(fill="x")
        self.cookies_var = tk.StringVar(value=self.settings.get("cookies_path", ""))
        ttk.Entry(cookie_row, textvariable=self.cookies_var).pack(side="left", fill="x", expand=True, ipady=2)
        self.button(cookie_row, "Browse", self.browse_cookies).pack(side="left", padx=(8, 0))

        self.label(account_card, "3. Destination folder", size=12, bold=True, bg=self.card).pack(anchor="w", pady=(15, 0))
        output_row = tk.Frame(account_card, bg=self.card)
        output_row.pack(fill="x", pady=(6, 0))
        self.output_var = tk.StringVar(value=self.settings.get("output_path", DEFAULT_SETTINGS["output_path"]))
        ttk.Entry(output_row, textvariable=self.output_var).pack(side="left", fill="x", expand=True, ipady=2)
        self.button(output_row, "Choose folder", self.browse_output).pack(side="left", padx=(8, 0))

        categories = self.card_frame(form)
        categories.pack(fill="x", pady=(0, 12))
        self.label(categories, "4. Content to archive", size=12, bold=True, bg=self.card).pack(anchor="w")
        self.all_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            categories,
            text="All available categories (recommended)",
            variable=self.all_var,
            command=self.toggle_categories,
        ).pack(anchor="w", pady=(8, 5))
        self.category_vars = {}
        self.category_checks = tk.Frame(categories, bg=self.card)
        self.category_checks.pack(fill="x", padx=(12, 0))
        for index, (title, key) in enumerate(CATEGORY_OPTIONS):
            var = tk.BooleanVar(value=True)
            self.category_vars[key] = var
            check = ttk.Checkbutton(self.category_checks, text=title, variable=var)
            check.grid(row=index // 2, column=index % 2, sticky="w", padx=(0, 28), pady=3)
        self.toggle_categories()

        progress_card = self.card_frame(form)
        progress_card.pack(fill="x", pady=(0, 10))
        progress_head = tk.Frame(progress_card, bg=self.card)
        progress_head.pack(fill="x")
        self.label(progress_head, "5. Download progress", size=11, bold=True, bg=self.card).pack(anchor="w")
        self.download_elapsed_label = self.label(
            progress_head, "Elapsed: 00:00", size=9, color=self.muted, bg=self.card
        )
        self.download_elapsed_label.pack(side="right")

        self.download_stats_label = self.label(
            progress_card, "Completed: 0   |   Skipped: 0   |   Failed: 0",
            size=9, color=self.text, bg=self.card, bold=True
        )
        self.download_stats_label.pack(anchor="w", pady=(8, 7))

        self.label(progress_card, "Current file", size=8, color=self.muted, bg=self.card).pack(anchor="w")
        self.current_file_label = self.label(
            progress_card, "Waiting to start...", size=9, color=self.text, bg=self.card,
            wraplength=760, justify="left"
        )
        self.current_file_label.pack(anchor="w", pady=(2, 3))
        self.current_file_detail = self.label(
            progress_card, "No file is being processed.", size=8, color=self.muted, bg=self.card
        )
        self.current_file_detail.pack(anchor="w", pady=(0, 7))

        self.file_progress = ttk.Progressbar(
            progress_card, mode="indeterminate", style="Horizontal.TProgressbar"
        )
        self.file_progress.pack(fill="x")
        self.file_progress_mode = None
        self.download_watch_label = self.label(
            progress_card, "Ready. Total item count will be discovered while Instagram is scanned.",
            size=8, color=self.muted, bg=self.card, wraplength=760, justify="left"
        )
        self.download_watch_label.pack(anchor="w", pady=(6, 0))

        footer = tk.Frame(form, bg=self.bg)
        footer.pack(fill="x", pady=(0, 8))
        self.status_var = tk.StringVar(value="Ready")
        self.label(footer, "Status:", size=9, color=self.muted, bg=self.bg).pack(side="left")
        self.status_label = self.label(footer, " Ready", size=9, color=self.green, bg=self.bg)
        self.status_label.pack(side="left")
        self.progress = ttk.Progressbar(footer, mode="indeterminate", length=140)
        self.progress.pack(side="right", padx=(10, 0))
        self.download_button = self.button(footer, "Start download", self.start_download, primary=True)
        self.download_button.pack(side="right")
        self.stop_button = self.button(footer, "Stop", self.stop_download)
        self.stop_button.pack(side="right", padx=(0, 8))
        self.stop_button.configure(state="disabled")

        log_card = self.card_frame(form)
        log_card.pack(fill="both", expand=True)
        log_head = tk.Frame(log_card, bg=self.card)
        log_head.pack(fill="x")
        self.label(log_head, "Activity log", size=11, bold=True, bg=self.card).pack(side="left")
        self.button(log_head, "Clear", self.clear_log).pack(side="right")
        self.log_text = tk.Text(
            log_card, height=9, wrap="word", bg="#0a1220", fg="#d9e3f5",
            insertbackground="#ffffff", relief="flat", bd=0, padx=10, pady=9,
            font=("Consolas", 9),
        )
        self.log_text.pack(fill="both", expand=True, pady=(9, 0))
        if self.download_log_history:
            self.log_text.insert("end", "".join(line + "\n" for line in self.download_log_history[-300:]))
        else:
            self.log_text.insert("end", "Ready. Pilih akun, cookies, dan folder tujuan untuk memulai.\n")
        self.log_text.configure(state="disabled")
        self.set_download_state(self.download_active)
        self.update_download_dashboard()

    def toggle_categories(self):
        state = "disabled" if self.all_var.get() else "normal"
        for widget in self.category_checks.winfo_children():
            try:
                widget.configure(state=state)
            except tk.TclError:
                pass

    def browse_cookies(self):
        path = filedialog.askopenfilename(
            title="Select Instagram cookies.txt",
            filetypes=[("Cookie files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.cookies_var.set(path)
            self.settings["cookies_path"] = path
            save_settings(self.settings)

    def browse_output(self):
        path = filedialog.askdirectory(title="Choose archive destination")
        if path:
            self.output_var.set(path)

    def append_log(self, message: str):
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {message.rstrip()}"
        self.download_log_history.append(line)
        self.download_log_history = self.download_log_history[-1000:]
        try:
            if hasattr(self, "log_text") and self.log_text.winfo_exists():
                self.log_text.configure(state="normal")
                self.log_text.insert("end", line + "\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except tk.TclError:
            pass

    def clear_log(self):
        self.download_log_history.clear()
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def set_status(self, text: str, color: str):
        try:
            if hasattr(self, "status_label") and self.status_label.winfo_exists():
                self.status_label.configure(text=text, fg=color)
        except tk.TclError:
            pass

    def set_download_state(self, running: bool):
        self.download_active = running
        try:
            if not hasattr(self, "download_button") or not self.download_button.winfo_exists():
                return
            self.download_button.configure(state="disabled" if running else "normal")
            self.stop_button.configure(state="normal" if running else "disabled")
            if running:
                self.progress.start(12)
                self.set_status(" Downloading...", self.yellow)
            else:
                self.progress.stop()
            self.update_download_dashboard()
        except tk.TclError:
            pass

    @staticmethod
    def format_bytes(value: int | float) -> str:
        number = max(0.0, float(value))
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if number < 1024 or unit == "TB":
                return f"{number:.1f} {unit}" if unit != "B" else f"{int(number)} B"
            number /= 1024
        return f"{number:.1f} TB"

    @staticmethod
    def format_elapsed(seconds: float) -> str:
        total = max(0, int(seconds))
        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def set_file_progress_mode(self, mode: str):
        try:
            if not hasattr(self, "file_progress") or not self.file_progress.winfo_exists():
                return
            if self.file_progress_mode == mode:
                return
            self.file_progress.stop()
            self.file_progress.configure(mode=mode, maximum=100)
            self.file_progress_mode = mode
            if mode == "indeterminate" and self.download_active:
                self.file_progress.start(12)
        except tk.TclError:
            pass

    def update_download_dashboard(self):
        try:
            if not hasattr(self, "download_stats_label") or not self.download_stats_label.winfo_exists():
                return
            metrics = self.download_metrics
            self.download_stats_label.configure(
                text=(
                    f"Completed: {metrics['completed']}   |   "
                    f"Skipped: {metrics['skipped']}   |   "
                    f"Failed: {metrics['failed']}"
                )
            )

            started_at = metrics.get("started_at")
            elapsed = time.monotonic() - started_at if started_at else 0
            self.download_elapsed_label.configure(text=f"Elapsed: {self.format_elapsed(elapsed)}")

            current_file = metrics.get("current_file") or ""
            if current_file:
                file_name = Path(current_file).name or current_file
                self.current_file_label.configure(text=file_name)
                detail = f"Downloaded: {self.format_bytes(metrics.get('current_bytes', 0))}"
                speed = metrics.get("current_speed", 0.0)
                if speed > 0:
                    detail += f"   |   Speed: {self.format_bytes(speed)}/s"
                transfer_detail = metrics.get("transfer_detail")
                if transfer_detail:
                    detail += f"   |   {transfer_detail.strip()}"
                percent = metrics.get("current_percent")
                if percent is not None:
                    detail += f"   |   {percent:.1f}%"
                    self.set_file_progress_mode("determinate")
                    self.file_progress.configure(value=max(0, min(100, percent)))
                else:
                    self.set_file_progress_mode("indeterminate")
                self.current_file_detail.configure(text=detail)
            else:
                self.current_file_label.configure(
                    text="Scanning account / waiting for the next file..."
                    if self.download_active else "No file is currently being processed."
                )
                self.current_file_detail.configure(text=metrics.get("phase") or "Ready")
                self.set_file_progress_mode("indeterminate" if self.download_active else "determinate")
                if not self.download_active:
                    self.file_progress.configure(value=0)

            if self.download_active:
                last_activity = metrics.get("last_activity") or time.monotonic()
                idle = int(max(0, time.monotonic() - last_activity))
                if current_file and idle >= 15:
                    state = f"No new file data for {idle}s. Waiting for network response or retry timeout."
                elif current_file:
                    state = f"Downloading file • last data update {idle}s ago"
                elif idle >= 15:
                    state = f"Waiting for Instagram response ({idle}s). Request timeout and retry limits are active."
                else:
                    state = "Scanning Instagram posts and preparing the next file..."
                self.download_watch_label.configure(text=state, fg=self.yellow if idle >= 15 else self.muted)
            else:
                self.download_watch_label.configure(
                    text=metrics.get("phase") or "Ready. Total item count is not known before scanning.",
                    fg=self.green if metrics.get("phase") == "Download completed." else self.muted,
                )
        except tk.TclError:
            pass

    def start_download(self):
        if self.download_active:
            messagebox.showinfo("Download is running", "Satu proses arsip masih berjalan.")
            return

        username = normalize_username(self.username_var.get())
        if not username:
            messagebox.showerror("Invalid account", "Masukkan username atau URL profil Instagram yang valid.")
            return

        cookie_path = Path(self.cookies_var.get().strip()).expanduser()
        if not cookie_path.is_file():
            messagebox.showerror(
                "Cookies not found",
                "Pilih file cookies.txt yang valid. Jangan mengirim file ini kepada siapa pun.",
            )
            return

        output_dir = Path(self.output_var.get().strip()).expanduser()
        if not self.output_var.get().strip():
            output_dir = Path.home() / "Documents" / "Instagram Archive"
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Cannot create folder", str(exc))
            return

        if importlib.util.find_spec("gallery_dl") is None:
            messagebox.showwarning(
                "Downloader is not installed",
                "Install dependency terlebih dahulu menggunakan tombol Install dependencies di halaman Settings.",
            )
            self.show_page("settings")
            return

        if self.all_var.get():
            include = "all"
        else:
            selected = [key for key, var in self.category_vars.items() if var.get()]
            if not selected:
                messagebox.showerror("No content selected", "Pilih minimal satu kategori konten.")
                return
            include = ",".join(selected)

        self.settings["cookies_path"] = str(cookie_path)
        self.settings["output_path"] = str(output_dir)
        save_settings(self.settings)

        profile_url = f"https://www.instagram.com/{username}/"
        target_dir = output_dir / username
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Cannot create archive folder", str(exc))
            return
        archive_file = target_dir / ".gallery-dl-archive.sqlite3"
        log_file = target_dir / "download.log"

        command = [
            sys.executable, "-m", "gallery_dl",
            "--cookies", str(cookie_path),
            "--directory", str(target_dir),
            "--download-archive", str(archive_file),
            "--sleep-request", "2",
            "--sleep-429", "60",
            "--http-timeout", "45",
            "--retries", "3",
            "--no-colors",
            "-o", f"extractor.instagram.include={include}",
            "-o", "extractor.instagram.metadata-path=_path",
            "-o", "downloader.timeout=90",
            "-o", "downloader.retries=3",
            "-o", "downloader.part=true",
            "-o", "downloader.progress=1.0",
            "-o", "output.mode=terminal",
            "--Print", "prepare-after:IGARCHIVE_PREPARE|{_path.path}",
            "--Print", "after:IGARCHIVE_DONE|{_path.path}",
            "--Print", "skip:IGARCHIVE_SKIP|{_path.path}",
            "--Print", "error:IGARCHIVE_ERROR|{_path.path}",
            profile_url,
        ]

        now = time.monotonic()
        self.download_metrics = {
            "started_at": now,
            "last_activity": now,
            "current_file": "",
            "current_bytes": 0,
            "current_speed": 0.0,
            "current_percent": None,
            "completed": 0,
            "skipped": 0,
            "failed": 0,
            "phase": "Connecting to Instagram...",
        }
        self.download_stop_event = threading.Event()
        self.set_download_state(True)
        self.append_log(f"Target: @{username}")
        self.append_log(f"Destination: {target_dir}")
        self.append_log(f"Categories: {include}")
        self.append_log("Download dimulai. Konten yang sudah ada di archive database akan dilewati.")
        self.append_log("Timeout koneksi: 45 detik; timeout download file: 90 detik; retry dibatasi 3 kali.")
        self.append_log("Progress file memakai ukuran transfer aktual; persentase muncul bila ukuran total file tersedia.")
        self.append_log("Gunakan tombol Stop untuk menghentikan proses dengan aman.")

        self.worker_thread = threading.Thread(
            target=self.run_downloader,
            args=(command, log_file, target_dir, self.download_stop_event),
            daemon=True,
        )
        self.worker_thread.start()

    def run_downloader(
        self,
        command: list[str],
        log_file: Path,
        target_dir: Path,
        stop_event: threading.Event,
    ):
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        return_code = -1
        monitor_stop = threading.Event()
        monitor_state = {"path": None}
        monitor_lock = threading.Lock()
        process = None

        def handle_segment(segment: str):
            segment = segment.strip()
            if not segment:
                return

            markers = (
                ("IGARCHIVE_PREPARE|", "file_prepare"),
                ("IGARCHIVE_DONE|", "file_done"),
                ("IGARCHIVE_SKIP|", "file_skip"),
                ("IGARCHIVE_ERROR|", "file_error"),
            )
            for marker, event_name in markers:
                if segment.startswith(marker):
                    path = segment[len(marker):].strip()
                    with monitor_lock:
                        monitor_state["path"] = path if event_name == "file_prepare" else None
                    self.events.put((event_name, path))
                    return

            # gallery-dl updates terminal download meters with carriage returns.
            if re.search(r"(?i)\bB/s\b", segment) or re.search(r"\d{1,3}%\s+[^ ]+\s+[^ ]+", segment):
                self.events.put(("file_meter", segment))
            else:
                self.events.put(("log", segment))

        try:
            with log_file.open("a", encoding="utf-8", errors="replace") as logfile:
                logfile.write(f"\n--- Session {datetime.now().isoformat(timespec='seconds')} ---\n")
                logfile.write("Target command: gallery-dl (arguments hidden)\n")
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=False,
                    bufsize=0,
                    env=env,
                    creationflags=creationflags,
                )
                self.process = process
                self.events.put(("download_process_started", None))

                monitor_thread = threading.Thread(
                    target=self.monitor_partial_file,
                    args=(monitor_state, monitor_lock, monitor_stop),
                    daemon=True,
                )
                monitor_thread.start()

                if stop_event.is_set():
                    process.terminate()

                assert process.stdout is not None
                decoder = codecs.getincrementaldecoder("utf-8")("replace")
                buffer = ""
                while True:
                    chunk = process.stdout.read(4096)
                    if not chunk:
                        break
                    buffer += decoder.decode(chunk)
                    while True:
                        positions = [pos for pos in (buffer.find("\r"), buffer.find("\n")) if pos >= 0]
                        if not positions:
                            break
                        cut = min(positions)
                        segment = buffer[:cut]
                        buffer = buffer[cut + 1:]
                        if segment.strip():
                            handle_segment(segment)
                            logfile.write(segment + "\n")
                            logfile.flush()

                buffer += decoder.decode(b"", final=True)
                if buffer.strip():
                    handle_segment(buffer)
                    logfile.write(buffer + "\n")
                    logfile.flush()
                return_code = process.wait()
        except FileNotFoundError:
            self.events.put(("log", "Python module gallery-dl tidak ditemukan. Buka Settings lalu Install dependencies."))
        except Exception as exc:
            self.events.put(("log", f"Downloader error: {exc}"))
        finally:
            monitor_stop.set()
            if process is not None:
                try:
                    if process.stdout:
                        process.stdout.close()
                except OSError:
                    pass
            self.process = None
            self.events.put(("finished", return_code))

    def monitor_partial_file(
        self,
        monitor_state: dict,
        monitor_lock: threading.Lock,
        stop_event: threading.Event,
    ):
        previous_path = None
        previous_size = 0
        previous_time = time.monotonic()
        while not stop_event.wait(0.6):
            with monitor_lock:
                current_path = monitor_state.get("path")

            if not current_path:
                previous_path = None
                previous_size = 0
                previous_time = time.monotonic()
                continue

            part_path = Path(current_path + ".part")
            try:
                size = part_path.stat().st_size
            except OSError:
                # The extractor may still be resolving a URL before creating its .part file.
                continue

            now = time.monotonic()
            if current_path != previous_path:
                previous_path = current_path
                previous_size = size
                previous_time = now
                speed = 0.0
                changed = size > 0
            else:
                elapsed = max(0.001, now - previous_time)
                changed = size > previous_size
                speed = max(0.0, (size - previous_size) / elapsed) if changed else 0.0
                previous_size = max(previous_size, size)
                previous_time = now

            self.events.put(("file_progress", (current_path, size, speed, changed)))

    def stop_download(self):
        if not self.download_active:
            return
        self.append_log("Permintaan berhenti dikirim...")
        if self.download_stop_event:
            self.download_stop_event.set()
        process = self.process
        if process and process.poll() is None:
            try:
                process.terminate()
            except OSError as exc:
                self.append_log(f"Tidak dapat menghentikan proses: {exc}")

    def render_settings(self, body):
        appearance = self.card_frame(body)
        appearance.pack(fill="x", pady=(0, 14))
        self.label(appearance, "Appearance", size=13, bold=True, bg=self.card).pack(anchor="w")
        self.label(
            appearance,
            "Sesuaikan warna latar dan aksen aplikasi. Perubahan diterapkan langsung.",
            size=9, color=self.muted, bg=self.card,
        ).pack(anchor="w", pady=(5, 14))

        row1 = tk.Frame(appearance, bg=self.card)
        row1.pack(fill="x", pady=5)
        self.label(row1, "Background color", size=10, bg=self.card).pack(side="left")
        self.button(row1, f"Choose  {self.bg}", self.choose_background).pack(side="right")
        row2 = tk.Frame(appearance, bg=self.card)
        row2.pack(fill="x", pady=5)
        self.label(row2, "Accent color", size=10, bg=self.card).pack(side="left")
        self.button(row2, f"Choose  {self.accent}", self.choose_accent).pack(side="right")
        row3 = tk.Frame(appearance, bg=self.card)
        row3.pack(fill="x", pady=5)
        self.label(row3, "Text size", size=10, bg=self.card).pack(side="left")
        self.scale_var = tk.StringVar(value=str(self.font_scale))
        scale_menu = tk.OptionMenu(row3, self.scale_var, "0.9", "1.0", "1.1", "1.2", command=self.change_font_scale)
        scale_menu.configure(bg=self.panel, fg=self.text, activebackground=self.card, activeforeground=self.text, relief="flat", bd=0)
        scale_menu["menu"].configure(bg=self.panel, fg=self.text)
        scale_menu.pack(side="right")

        dependencies = self.card_frame(body)
        dependencies.pack(fill="both", expand=True, pady=(0, 14))
        self.label(dependencies, "Downloader components", size=13, bold=True, bg=self.card).pack(anchor="w")
        self.label(
            dependencies,
            "Instalasi berjalan langsung di aplikasi. Tahap, output pip, dan status setiap paket "
            "akan muncul di bawah ini.",
            size=9, color=self.muted, bg=self.card, wraplength=780, justify="left",
        ).pack(anchor="w", pady=(6, 10))

        self.dependency_status = self.label(
            dependencies, self.dependency_summary(), size=9, color=self.green, bg=self.card
        )
        self.dependency_status.pack(anchor="w", pady=(0, 7))

        self.install_state_label = self.label(
            dependencies,
            "Installation in progress..." if self.install_running else "Ready to install",
            size=9,
            color=self.yellow if self.install_running else self.muted,
            bg=self.card,
            bold=True,
        )
        self.install_state_label.pack(anchor="w", pady=(0, 6))

        self.dependency_progress = ttk.Progressbar(
            dependencies, mode="indeterminate", length=500, style="Horizontal.TProgressbar"
        )
        self.dependency_progress.pack(fill="x", pady=(0, 9))
        if self.install_running:
            self.dependency_progress.start(12)

        actions = tk.Frame(dependencies, bg=self.card)
        actions.pack(fill="x", pady=(0, 9))
        self.install_button = self.button(
            actions, "Installing..." if self.install_running else "Install / update dependencies",
            self.install_dependencies, primary=True
        )
        self.install_button.pack(side="left")
        self.check_button = self.button(actions, "Check again", self.refresh_dependency_status)
        self.check_button.pack(side="left", padx=8)
        if self.install_running:
            self.install_button.configure(state="disabled")
            self.check_button.configure(state="disabled")

        self.label(dependencies, "Installation log", size=9, color=self.muted, bg=self.card, bold=True).pack(anchor="w", pady=(1, 5))
        self.dependency_log = tk.Text(
            dependencies,
            height=6,
            wrap="word",
            bg="#0a1220",
            fg="#d9e3f5",
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            padx=9,
            pady=7,
            font=("Consolas", 8),
        )
        self.dependency_log.pack(fill="both", expand=True)
        self.dependency_log.configure(state="disabled")
        for line in self.install_logs[-200:]:
            self.dependency_log.configure(state="normal")
            self.dependency_log.insert("end", line + "\n")
            self.dependency_log.configure(state="disabled")
        self.dependency_log.see("end")

        storage = self.card_frame(body)
        storage.pack(fill="x")
        self.label(storage, "Local app data", size=12, bold=True, bg=self.card).pack(anchor="w")
        self.label(
            storage,
            f"Settings: {settings_path()}\nCookies: path only (cookie content is not copied into app settings).",
            size=9, color=self.muted, bg=self.card, justify="left",
        ).pack(anchor="w", pady=(6, 0))

    def dependency_summary(self):
        gallery = importlib.util.find_spec("gallery_dl") is not None
        video = importlib.util.find_spec("yt_dlp") is not None
        return f"gallery-dl: {'Installed' if gallery else 'Not installed'}   |   yt-dlp: {'Installed' if video else 'Not installed'}"

    def refresh_dependency_status(self):
        if self.install_running:
            self.set_dependency_state("Installation is currently running.", self.yellow)
            return
        if hasattr(self, "dependency_status") and self.dependency_status.winfo_exists():
            self.dependency_status.configure(text=self.dependency_summary())
        self.set_dependency_state("Ready to install or update dependencies.", self.muted)

    def install_dependencies(self):
        if self.install_running:
            return

        self.install_running = True
        self.install_last_error = ""
        if hasattr(self, "install_button") and self.install_button.winfo_exists():
            self.install_button.configure(text="Installing...", state="disabled")
        if hasattr(self, "check_button") and self.check_button.winfo_exists():
            self.check_button.configure(state="disabled")
        if hasattr(self, "dependency_progress") and self.dependency_progress.winfo_exists():
            self.dependency_progress.configure(mode="indeterminate")
            self.dependency_progress.start(12)
        self.set_dependency_state("Preparing dependency installer...", self.yellow)
        self.append_dependency_log("Starting dependency installation.")
        self.append_dependency_log(f"Python: {sys.executable}")
        self.append_dependency_log("Packages: gallery-dl, yt-dlp")

        def worker():
            exit_code = 0
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["PIP_PROGRESS_BAR"] = "off"

            packages = ("gallery-dl", "yt-dlp")
            try:
                for index, package in enumerate(packages, start=1):
                    self.events.put(("install_stage", (index, len(packages), package)))
                    command = [
                        sys.executable, "-u", "-m", "pip", "install",
                        "--upgrade", "--disable-pip-version-check", "--no-input",
                        "--progress-bar", "off", package,
                    ]
                    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        bufsize=1,
                        env=env,
                        creationflags=creationflags,
                    )
                    self.install_process = process
                    if process.stdout is not None:
                        for raw_line in process.stdout:
                            line = raw_line.rstrip()
                            if line:
                                self.events.put(("install_line", line))
                    exit_code = process.wait()
                    self.install_process = None
                    if exit_code != 0:
                        self.events.put(("install_line", f"pip exited with code {exit_code} while installing {package}."))
                        break

                self.events.put(("install_finished", exit_code))
            except Exception as exc:
                self.install_process = None
                self.events.put(("install_line", f"Installer error: {exc}"))
                self.events.put(("install_finished", -1))

        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()

    def append_dependency_log(self, message: str):
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {message}"
        self.install_logs.append(line)
        self.install_logs = self.install_logs[-500:]
        try:
            if hasattr(self, "dependency_log") and self.dependency_log.winfo_exists():
                self.dependency_log.configure(state="normal")
                self.dependency_log.insert("end", line + "\n")
                self.dependency_log.see("end")
                self.dependency_log.configure(state="disabled")
        except tk.TclError:
            pass

    def set_dependency_state(self, message: str, color: str):
        try:
            if hasattr(self, "install_state_label") and self.install_state_label.winfo_exists():
                self.install_state_label.configure(text=message, fg=color)
        except tk.TclError:
            pass

    def finish_dependency_install(self, exit_code: int):
        self.install_running = False
        if hasattr(self, "dependency_progress") and self.dependency_progress.winfo_exists():
            self.dependency_progress.stop()
        if hasattr(self, "install_button") and self.install_button.winfo_exists():
            self.install_button.configure(text="Install / update dependencies", state="normal")
        if hasattr(self, "check_button") and self.check_button.winfo_exists():
            self.check_button.configure(state="normal")

        self.refresh_dependency_status()
        if exit_code == 0:
            self.set_dependency_state("Installation completed successfully.", self.green)
            self.append_dependency_log("All dependencies installed successfully.")
        else:
            self.set_dependency_state(f"Installation failed (exit code {exit_code}). See log above.", self.red)
            self.append_dependency_log("Installation failed. Review the last pip messages above.")

    def choose_background(self):
        selected = colorchooser.askcolor(color=self.bg, title="Choose background color")
        if selected and selected[1]:
            self.settings["background"] = selected[1]
            self.save_and_refresh_theme()

    def choose_accent(self):
        selected = colorchooser.askcolor(color=self.accent, title="Choose accent color")
        if selected and selected[1]:
            self.settings["accent"] = selected[1]
            self.save_and_refresh_theme()

    def change_font_scale(self, value):
        try:
            self.settings["font_scale"] = float(value)
            self.save_and_refresh_theme()
        except ValueError:
            pass

    def save_and_refresh_theme(self):
        save_settings(self.settings)
        self.bg = self.settings["background"]
        self.accent = self.settings["accent"]
        self.font_scale = float(self.settings.get("font_scale", 1.0))
        self.card = self.mix_color(self.bg, self.panel, 0.55)
        self.root.configure(bg=self.bg)
        self.shell.configure(bg=self.bg)
        self.content.configure(bg=self.bg)
        self.configure_ttk()
        self.show_page(self.current_page)

    def render_info(self, body):
        profile = self.card_frame(body)
        profile.pack(fill="x", pady=(0, 14))
        self.label(profile, "Developer", size=13, bold=True, bg=self.card).pack(anchor="w")
        self.label(profile, "Ramdan Olii", size=20, bold=True, bg=self.card).pack(anchor="w", pady=(9, 0))
        self.label(profile, "@ramdanolii14", size=10, color=self.muted, bg=self.card).pack(anchor="w")
        self.label(
            profile,
            "GitHub profile and repository are public links. Profile statistics are fetched from the GitHub API.",
            size=9, color=self.muted, bg=self.card,
        ).pack(anchor="w", pady=(9, 12))
        links = tk.Frame(profile, bg=self.card)
        links.pack(anchor="w")
        self.button(links, "GitHub profile", lambda: webbrowser.open(GITHUB_PROFILE_URL)).pack(side="left")
        self.button(links, "Project repository", lambda: webbrowser.open(GITHUB_REPO_URL)).pack(side="left", padx=8)

        project = self.card_frame(body)
        project.pack(fill="x", pady=(0, 14))
        self.label(project, "InstagramDownloader-CLI", size=13, bold=True, bg=self.card).pack(anchor="w")
        self.label(
            project,
            "A Windows-native desktop interface for the original Instagram downloader project. "
            "The legacy Bash CLI remains available for Linux users.",
            size=9, color=self.muted, bg=self.card, wraplength=780, justify="left",
        ).pack(anchor="w", pady=(6, 0))
        self.github_status = self.label(project, "Loading public GitHub information...", size=9, color=self.yellow, bg=self.card)
        self.github_status.pack(anchor="w", pady=(12, 0))
        threading.Thread(target=self.load_github_info, daemon=True).start()

        note = tk.Frame(body, bg=self.panel, padx=16, pady=13)
        note.pack(fill="x", side="bottom")
        self.label(
            note,
            "Use only for your own account or content you have permission to archive. "
            "Private content is accessible only when Instagram authorizes the signed-in session. "
            "This application does not bypass access controls.",
            size=9, color=self.yellow, bg=self.panel, wraplength=780, justify="left",
        ).pack(anchor="w")

    def load_github_info(self):
        try:
            profile = fetch_json(f"https://api.github.com/users/{GITHUB_USER}")
            repo = fetch_json(f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}")
            data = {
                "profile_name": profile.get("name") or GITHUB_USER,
                "bio": profile.get("bio") or "No public bio set.",
                "public_repos": profile.get("public_repos", "—"),
                "followers": profile.get("followers", "—"),
                "stars": repo.get("stargazers_count", "—"),
                "forks": repo.get("forks_count", "—"),
                "default_branch": repo.get("default_branch", "main"),
            }
            self.events.put(("github", data))
        except (OSError, ValueError, urllib.error.URLError) as exc:
            self.events.put(("github_error", str(exc)))

    def on_close(self):
        if self.download_active:
            close = messagebox.askyesno(
                "Download in progress",
                "Download sedang berjalan. Hentikan proses dan tutup aplikasi?",
            )
            if not close:
                return
            if self.download_stop_event:
                self.download_stop_event.set()
            if self.process and self.process.poll() is None:
                try:
                    self.process.terminate()
                except OSError:
                    pass
        save_settings(self.settings)
        self.root.destroy()

    def poll_events(self):
        try:
            while True:
                event, value = self.events.get_nowait()
                if event == "log":
                    self.download_metrics["last_activity"] = time.monotonic()
                    self.append_log(value)
                    low = value.lower()
                    if "429" in low or "rate limit" in low:
                        self.download_metrics["phase"] = "Instagram rate-limited the request; waiting before retry."
                        self.set_status(" Rate limit detected", self.yellow)
                        self.append_log("Instagram memberi respons pembatasan. Hindari percobaan berulang dalam waktu dekat.")
                    elif "timeout" in low or "timed out" in low:
                        self.download_metrics["phase"] = "Request timed out; gallery-dl will retry within its configured limit."
                        self.set_status(" Retrying after timeout...", self.yellow)
                elif event == "download_process_started":
                    self.download_metrics["phase"] = "Connected to downloader; scanning account..."
                    self.download_metrics["last_activity"] = time.monotonic()
                    self.update_download_dashboard()
                elif event == "file_prepare":
                    self.download_metrics.update({
                        "current_file": value,
                        "current_bytes": 0,
                        "current_speed": 0.0,
                        "current_percent": None,
                        "phase": "Preparing download...",
                        "last_activity": time.monotonic(),
                    })
                    self.append_log(f"Preparing: {value}")
                elif event == "file_progress":
                    path, size, speed, changed = value
                    self.download_metrics.update({
                        "current_file": path,
                        "current_bytes": size,
                        "current_speed": speed,
                        "phase": "Downloading file data..." if changed else "Waiting for file data...",
                    })
                    if changed:
                        self.download_metrics["last_activity"] = time.monotonic()
                elif event == "file_meter":
                    self.download_metrics["last_activity"] = time.monotonic()
                    self.download_metrics["phase"] = "Receiving file data..."
                    percent_match = re.search(r"(\d{1,3})%", value)
                    if percent_match:
                        self.download_metrics["current_percent"] = float(percent_match.group(1))
                    self.download_metrics["transfer_detail"] = value.strip()
                elif event == "file_done":
                    self.download_metrics["completed"] += 1
                    self.download_metrics["last_activity"] = time.monotonic()
                    self.download_metrics["current_file"] = ""
                    self.download_metrics["current_bytes"] = 0
                    self.download_metrics["current_speed"] = 0.0
                    self.download_metrics["current_percent"] = None
                    self.download_metrics["phase"] = "File completed."
                    self.append_log(f"Completed: {value}")
                elif event == "file_skip":
                    self.download_metrics["skipped"] += 1
                    self.download_metrics["last_activity"] = time.monotonic()
                    self.download_metrics["current_file"] = ""
                    self.download_metrics["phase"] = "Existing file skipped."
                    self.append_log(f"Skipped: {value}")
                elif event == "file_error":
                    self.download_metrics["failed"] += 1
                    self.download_metrics["last_activity"] = time.monotonic()
                    self.download_metrics["current_file"] = ""
                    self.download_metrics["phase"] = "A file failed; checking the next item."
                    self.append_log(f"File error: {value}")
                elif event == "finished":
                    self.download_metrics["current_file"] = ""
                    self.download_metrics["current_speed"] = 0.0
                    self.download_metrics["current_percent"] = None
                    self.download_metrics["phase"] = (
                        "Download completed." if value == 0
                        else f"Download ended with exit code {value}."
                    )
                    self.download_metrics["last_activity"] = time.monotonic()
                    self.set_download_state(False)
                    if value == 0:
                        self.set_status(" Completed", self.green)
                        self.append_log("Selesai. Periksa folder arsip untuk hasil unduhan.")
                    else:
                        self.set_status(f" Finished ({value})", self.yellow)
                        self.append_log(f"gallery-dl selesai dengan exit code {value}. Periksa log untuk detail.")
                elif event == "install_stage":
                    index, total, package = value
                    self.set_dependency_state(
                        f"Installing {package} ({index}/{total})...",
                        self.yellow,
                    )
                    self.append_dependency_log(f"Step {index}/{total}: installing {package}.")
                elif event == "install_line":
                    self.append_dependency_log(value)
                elif event == "install_finished":
                    self.finish_dependency_install(value)
                elif event == "github":
                    self.profile_info = value
                    if hasattr(self, "github_status") and self.github_status.winfo_exists():
                        summary = (
                            f"{value['profile_name']}  •  {value['bio']}\n"
                            f"Public repositories: {value['public_repos']}   |   Followers: {value['followers']}\n"
                            f"Repository stars: {value['stars']}   |   Forks: {value['forks']}   |   Branch: {value['default_branch']}"
                        )
                        self.github_status.configure(text=summary, fg=self.green)
                elif event == "github_error":
                    if hasattr(self, "github_status") and self.github_status.winfo_exists():
                        self.github_status.configure(
                            text="GitHub information could not be loaded. Open the profile or repository links above.",
                            fg=self.yellow,
                        )
        except queue.Empty:
            pass
        if self.download_active and time.monotonic() - self._last_download_ui_refresh >= 0.5:
            self._last_download_ui_refresh = time.monotonic()
            self.update_download_dashboard()
        self.root.after(100, self.poll_events)

def main():
    root = tk.Tk()
    InstagramArchiveApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
