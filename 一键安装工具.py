# -*- coding: utf-8 -*-
r"""
一键安装工具
============
静默安装 VC++ 运行库、Git、TortoiseGit、灵基,安装完成后自动克隆代码仓库
(不在本工具中收集 Git 账号密码: 克隆需要认证时由 Git 弹出登录窗口,
由使用者自行输入,本工具全程不接触、不记录账号密码)。

本版本行为:
  * 不在任何磁盘位置记录日志文件(运行过程仅在界面内实时显示);
  * 四个安装包均在可见的 PowerShell 窗口中以命令行方式安装,
    安装失败时窗口停留显示返回码,便于现场排查;
  * 拉取代码: 在可见的 Windows PowerShell 窗口中调用本工具安装的
    git.exe 执行单条命令
    git clone <仓库地址> <目标目录>(如 C:\kingdee\kingdeecode\cmssc)。

安装目录规则(用户选择一个"安装根目录",所有软件与代码安装到其子目录中):
  Git         -> <安装根目录>\git          (Inno Setup,/DIR= 指定)
  TortoiseGit -> <安装根目录>\TortoiseGit   (msiexec INSTALLDIR 指定)
  灵基        -> <安装根目录>\lingdee       (NSIS,/D= 指定,不支持带空格路径)
  VC++ 运行库 -> 系统默认位置(微软限制,不支持自定义安装目录)
  代码仓库    -> <安装根目录>\kingdeecode

安装顺序:
  1. VC_redist.x64.exe          (Visual C++ 运行库)
  2. Git-2.54.0-64-bit.exe      (Git, Inno Setup 格式)
  3. TortoiseGit-2.18.0.1-64bit.msi (TortoiseGit, 依赖 Git)
  4. LingeeSetup_ia32_*.exe     (灵基, NSIS 格式)

容错: 单个软件安装失败不影响后续软件继续安装,也不影响拉取代码
      (仅当 Git 未安装成功时跳过拉取代码)。

拉取代码前先执行 git --version 检测 Git 版本号(预检): 检测通过后在
界面日志区与提示框中显示版本号,再开始克隆; 检测失败视为 Git 不可用,
跳过拉取代码(与 Git 未安装成功时的处理一致)。

每个仓库克隆失败后自动重试两次(RETRY_TIMES = 2): 非最后一次尝试失败
时窗口短暂显示返回码后自动关闭、无需人工按键,工具自动清理上次克隆的
残留目录并重新打开一个新的命令行窗口继续执行; 重试成功在结果中标注
"成功(重试)"; 最后一次尝试仍失败才记为失败(此时窗口停留显示返回码,
便于现场排查)。

拉取代码: 在可见的 Windows PowerShell 窗口中调用本工具安装的
      git.exe(如安装根目录为 c:\kingdee 时用 C:\kingdee\git\bin\git.exe)
      执行与手动敲入完全相同的命令:
      git clone <仓库地址> <目标目录>
      目标目录为 Windows 路径,如安装根目录为 c:\kingdee 时:
      git clone https://.../cmssc.git C:\kingdee\kingdeecode\cmssc
      (kingdeecode 为代码总目录,cmbas、cmssc 各自独立子目录);
      只使用本工具安装目录下的 Git,不依赖系统 PATH 中的 git;
      仓库地址必须用 https: 服务器会把 http 301 重定向到 https,而认证
      信息无法跟随重定向传递,http 地址会导致自动认证失败、弹出登录窗口;
      账号密码不由本工具收集: 克隆需要认证时由 Git 弹出登录窗口,由使用者
      自行输入(Git 自带的凭据管理器会记住已输入的凭据,同一台机器上后续
      克隆通常无需重复输入);本工具不接触、不记录任何账号密码。

打包方式(见 打包exe.bat,四个安装包会被打进 exe):
  pyinstaller --onefile --noconsole --uac-admin --name "一键安装工具" ...
生成的 exe 在 dist/ 目录下,单个文件即可分发。
"""

import ctypes
import os
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ---------------------------------------------------------------------------
# 安装任务定义。
# kind: vc=Burn 引导程序(仅支持系统默认目录)  inno=Inno Setup(/DIR=)
#       msi=Windows Installer(INSTALLDIR)     nsis=NSIS(/D=)
# subdir: 安装到 <安装根目录>\subdir (vc 为 None,装到系统默认位置)
# ---------------------------------------------------------------------------
TASKS = [
    {
        "name": "Visual C++ 运行库",
        "file": "VC_redist.x64.exe",
        "kind": "vc",
        "subdir": None,
        "ok_codes": {0, 1638, 3010},   # 1638=已有更新版本  3010=成功但需重启
        "reboot_code": 3010,
    },
    {
        "name": "Git",
        "file": "Git-2.54.0-64-bit.exe",
        "kind": "inno",
        "subdir": "git",
        "ok_codes": {0},
        "reboot_code": None,
    },
    {
        "name": "TortoiseGit",
        "file": "TortoiseGit-2.18.0.1-64bit.msi",
        "kind": "msi",
        "subdir": "TortoiseGit",
        "ok_codes": {0, 1638, 3010},
        "reboot_code": 3010,
    },
    {
        "name": "灵基",
        "file": "LingeeSetup_ia32_1.0.0_2608241831.exe",
        "kind": "nsis",
        "subdir": "lingdee",
        # NSIS 安装包:/S 静默,/allusers 为所有用户安装,/D= 指定安装目录
        "ok_codes": {0, 1223},   # 1223=用户取消了向导,不算错误(可稍后自行安装)
        "reboot_code": None,
    },
]

# ---------------------------------------------------------------------------
# 需要克隆的代码仓库(统一克隆到 <安装根目录>/kingdeecode/ 下)
# 注意: 仓库地址使用 https —— 服务器会把 http 301 重定向到 https,而账号
# 密码等认证信息无法跟随重定向传递,用 http 地址会导致自动认证失败
# (cmbas 与 cmssc 均需登录才能拉取)。
# ---------------------------------------------------------------------------
REPOS = [
    "https://code.kingdee.com/gitlab/collaborative_dev_platform/cosmic/p20240425-000008/cmbas.git",
    "https://code.kingdee.com/gitlab/collaborative_dev_platform/cosmic/p20240320-000002/cmssc.git",
]

CODE_FOLDER = "kingdeecode"

# 每个仓库克隆失败后自动重试次数: 每次重试清理残留目录并重新打开
# 新的命令行窗口继续执行,总尝试次数 = RETRY_TIMES + 1
RETRY_TIMES = 2

# ---------------------------------------------------------------------------
# Git 账号密码: 本工具不收集、不内置、不记录任何账号密码。
# 克隆需要认证时由 Git 自行弹出登录窗口、由使用者输入,
# 因此这里不需要任何凭据相关的常量与辅助函数。
# ---------------------------------------------------------------------------

def ps_quote(text):
    """把文本包装成安全的 PowerShell 单引号字符串字面量。"""
    return "'" + str(text).replace("'", "''") + "'"


# ---------------------------------------------------------------------------
# 管理员权限处理
# ---------------------------------------------------------------------------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def elevate_and_restart():
    """以管理员权限重新启动本程序(弹出 UAC 提示),然后退出当前进程。"""
    if getattr(sys, "frozen", False):
        # 打包后的 exe,直接重新运行自己
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, "", None, 1)
    else:
        # 直接运行 .py 源码时,用 python 重新运行脚本
        params = '"{}"'.format(os.path.abspath(sys.argv[0]))
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1)
    sys.exit(0)


# ---------------------------------------------------------------------------
# 查找安装包位置
#   优先:打包时嵌入的资源目录 -> exe/脚本所在目录 -> 其下的 installers 子目录
# ---------------------------------------------------------------------------
def search_dirs():
    dirs = []
    if getattr(sys, "frozen", False):
        dirs.append(getattr(sys, "_MEIPASS", None))     # pyinstaller --onefile 嵌入
        dirs.append(os.path.dirname(sys.executable))    # exe 旁边
    else:
        dirs.append(os.path.dirname(os.path.abspath(__file__)))
    result = []
    for d in dirs:
        if d:
            result.append(d)
            result.append(os.path.join(d, "installers"))
    return result


def find_installer(filename):
    for d in search_dirs():
        path = os.path.join(d, filename)
        if os.path.exists(path):
            return path
    return None


def get_short_path(path):
    """返回 8.3 短路径形式(NSIS /D= 不支持带空格的路径,用短路径规避);
    卷禁用了 8.3 短名或调用失败时返回空字符串。"""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(path, buf, 1024):
            return buf.value
    except Exception:
        pass
    return ""


def default_install_base():
    """默认安装根目录: 优先选已存在的非系统盘,否则退回 C 盘。"""
    for drive in ("D:\\", "E:\\", "F:\\"):
        if os.path.isdir(drive):
            return drive
    return "C:\\"


# ---------------------------------------------------------------------------
# 图形界面
# ---------------------------------------------------------------------------
class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.need_reboot = False
        self.install_base = None   # 用户选择的安装根目录
        self.git_exe = None
        self.git_version = None    # 拉取代码前检测到的 Git 版本号
        root.title("一键安装工具 (Git + TortoiseGit + VC++ 运行库 + 灵基)")
        root.geometry("640x640")
        root.resizable(False, False)

        ttk.Label(root, text="请选择安装根目录(软件与代码将安装到其子目录中):",
                  font=("Microsoft YaHei UI", 11)).pack(pady=(15, 5))

        # 安装根目录选择行(安装开始后锁定)
        dir_frame = ttk.Frame(root)
        dir_frame.pack(fill="x", padx=30, pady=(0, 5))
        ttk.Label(dir_frame, text="安装根目录:").pack(side="left")
        self.dir_var = tk.StringVar(value=default_install_base())
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.browse_btn = ttk.Button(dir_frame, text="浏览...",
                                     command=self.browse_dir)
        self.browse_btn.pack(side="left")

        ttk.Label(
            root, wraplength=560, foreground="gray",
            text="软件将安装到子目录: git、TortoiseGit、lingdee"
                 "(VC++ 运行库为系统默认位置);\n"
                 "代码将克隆到子目录: kingdeecode;\n"
                 "拉取代码需要认证时,由 Git 弹出登录窗口自行输入账号密码;\n"
                 "单个软件失败不影响后续安装与拉取代码。"
        ).pack(pady=(0, 2))

        # 安装任务列表(带复选框)
        self.task_checks = {}
        self.task_check_widgets = {}
        self.status_vars = {}
        task_frame = ttk.Frame(root)
        task_frame.pack(fill="x", padx=30, pady=5)
        for task in TASKS:
            row = ttk.Frame(task_frame)
            row.pack(fill="x", pady=3)
            chk_var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(row, text=task["name"],
                                 variable=chk_var, width=28)
            cb.pack(side="left")
            var = tk.StringVar(value="等待安装")
            lbl = ttk.Label(row, textvariable=var, foreground="gray")
            lbl.pack(side="left")
            self.task_checks[task["file"]] = chk_var
            self.task_check_widgets[task["file"]] = cb
            self.status_vars[task["file"]] = (var, lbl)

        # 分隔线
        ttk.Separator(root, orient="horizontal").pack(
            fill="x", padx=30, pady=8)

        # 代码仓库列表(带复选框)
        ttk.Label(root, text="代码仓库(勾选后将自动克隆):",
                  font=("Microsoft YaHei UI", 10)).pack(pady=(0, 3))
        self.repo_checks = {}
        self.repo_check_widgets = {}
        self.repo_status_vars = {}
        repo_frame = ttk.Frame(root)
        repo_frame.pack(fill="x", padx=30, pady=5)
        for url in REPOS:
            row = ttk.Frame(repo_frame)
            row.pack(fill="x", pady=3)
            name = repo_name(url)
            chk_var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(row, text=name,
                                 variable=chk_var, width=28)
            cb.pack(side="left")
            var = tk.StringVar(value="等待克隆")
            lbl = ttk.Label(row, textvariable=var, foreground="gray")
            lbl.pack(side="left")
            self.repo_checks[url] = chk_var
            self.repo_check_widgets[url] = cb
            self.repo_status_vars[name] = (var, lbl)

        self.progress = ttk.Progressbar(root, length=560, maximum=len(TASKS))
        self.progress.pack(pady=8)

        # 日志区
        self.log_text = tk.Text(root, height=8, width=80,
                                state="disabled", font=("Consolas", 9))
        self.log_text.pack(padx=15, pady=(0, 8))

        self.btn = ttk.Button(root, text="开始安装", command=self.start)
        self.btn.pack(pady=(0, 15))

    def browse_dir(self):
        chosen = filedialog.askdirectory(
            title="请选择安装根目录",
            initialdir=self.dir_var.get() or os.path.expanduser("~"))
        if chosen:
            self.dir_var.set(chosen)

    def log(self, msg):
        # 只在界面日志区显示,不再写入任何日志文件
        def _append():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        self.root.after(0, _append)

    def set_status(self, filename, text, color):
        def _set():
            var, lbl = self.status_vars[filename]
            var.set(text)
            lbl.configure(foreground=color)
        self.root.after(0, _set)

    def set_repo_status(self, name, text, color):
        """设置仓库的状态显示文本和颜色。"""
        def _set():
            var, lbl = self.repo_status_vars[name]
            var.set(text)
            lbl.configure(foreground=color)
        self.root.after(0, _set)

    def _set_checks_state(self, state):
        """启用或禁用所有复选框(安装期间禁用,防止中途修改选择)。"""
        for w in self.task_check_widgets.values():
            w.configure(state=state)
        for w in self.repo_check_widgets.values():
            w.configure(state=state)

    def start(self):
        base = self.dir_var.get().strip()
        if not base:
            messagebox.showwarning("提示", "请先选择安装根目录。")
            return
        base = os.path.abspath(base)
        if not os.path.isdir(base):
            messagebox.showwarning(
                "提示", "安装目录 %s 不存在,请选择一个已存在的磁盘目录。" % base)
            return

        self.install_base = base
        # 检查是否有勾选任何项目
        has_task = any(v.get() for v in self.task_checks.values())
        has_repo = any(v.get() for v in self.repo_checks.values())
        if not has_task and not has_repo:
            messagebox.showwarning("提示", "请至少勾选一个软件或代码仓库。")
            return
        self.log("安装根目录: " + base)
        self.log("Git -> %s" % os.path.join(base, "git"))
        self.log("TortoiseGit -> %s" % os.path.join(base, "TortoiseGit"))
        self.log("灵基 -> %s" % os.path.join(base, "lingdee"))
        self.log("VC++ 运行库 -> 系统默认位置(微软限制,不支持自定义目录)")
        self.log("代码仓库 -> " + os.path.join(base, CODE_FOLDER))
        # 提前创建软件子目录(NSIS 短路径转换要求目录已存在)
        for sub in ("git", "TortoiseGit", "lingdee"):
            try:
                os.makedirs(os.path.join(base, sub), exist_ok=True)
            except Exception as e:
                self.log("创建子目录 %s 失败: %s" % (sub, e))
        # 锁定路径选择、按钮和复选框,防止中途修改
        self.dir_entry.configure(state="disabled")
        self.browse_btn.configure(state="disabled")
        self.btn.configure(state="disabled", text="安装中...")
        self._set_checks_state("disabled")
        threading.Thread(target=self.run_all, daemon=True).start()

    def run_task(self, task):
        path = find_installer(task["file"])
        if not path:
            raise FileNotFoundError("找不到安装包: " + task["file"])
        script = self.build_install_script(task, path)
        try:
            # 在可见的 PowerShell 窗口中执行安装命令(与拉取代码风格一致),
            # 失败时窗口停留显示返回码,便于现场排查。
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile",
                 "-ExecutionPolicy", "Bypass", "-Command", script])
            self.log("返回码: %d" % proc.returncode)
            return proc.returncode
        except Exception as e:
            self.log("启动 PowerShell 失败: %s" % e)
            return -1

    def build_install_script(self, task, path):
        """生成单个安装包的 PowerShell 命令行安装脚本(在可见窗口中运行)。"""
        kind = task["kind"]
        name = task["name"]

        if kind == "vc":
            # VC++ 运行库仅支持系统默认目录(微软限制),不指定自定义路径
            body = (
                "Write-Host 'VC++ 运行库不支持自定义安装目录,"
                "将安装到系统默认位置。' -ForegroundColor Yellow; "
                "& {exe} /install /quiet /norestart"
            ).format(exe=ps_quote(path))
        elif kind == "inno":
            inst_dir = os.path.join(self.install_base, task["subdir"])
            body = (
                "& {exe} /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- {dir}"
            ).format(exe=ps_quote(path), dir=ps_quote("/DIR=" + inst_dir))
        elif kind == "msi":
            # MSI 直接从 PyInstaller 的 _MEI 临时目录运行会返回 1603,
            # 先复制到普通临时目录再执行 msiexec(此前已验证可行)。
            inst_dir = os.path.join(self.install_base, task["subdir"])
            body = (
                "$stage = New-Item -ItemType Directory -Path (Join-Path "
                "$env:TEMP ('一键安装临时_' + "
                "[guid]::NewGuid().ToString('N'))) -Force; "
                "Copy-Item -LiteralPath {src} -Destination (Join-Path "
                "$stage '{file}') -Force; "
                "$p = Start-Process msiexec.exe -Wait -PassThru -ArgumentList "
                "'/i', (Join-Path $stage '{file}'), '/qn', '/norestart', "
                "('INSTALLDIR=' + [char]34 + '{dir}' + [char]34); "
                "Remove-Item -LiteralPath $stage.FullName -Recurse -Force; "
                "$LASTEXITCODE = $p.ExitCode"
            ).format(src=ps_quote(path), file=task["file"], dir=inst_dir)
        else:   # nsis
            inst_dir = os.path.join(self.install_base, task["subdir"])
            # NSIS /D= 不支持带空格的路径,用 8.3 短路径规避;
            # /D= 必须是最后一个参数
            if " " in inst_dir:
                short = get_short_path(inst_dir)
                if short:
                    self.log("路径含空格,使用短路径: " + short)
                    inst_dir = short
                else:
                    self.log("警告: 路径含空格且无法获取短路径,"
                             "灵基将安装到其默认目录。")
                    inst_dir = None
            dirarg = " " + ps_quote("/D=" + inst_dir) if inst_dir else ""
            body = ("& {exe} /S /allusers{dirarg}"
                    .format(exe=ps_quote(path), dirarg=dirarg))

        return (
            "try {{ $host.UI.RawUI.WindowTitle = {title} }} catch {{ }}; "
            "Set-Location -LiteralPath {cwd}; "
            "Write-Host '===== 开始安装 {name} =====' -ForegroundColor Cyan; "
            "{body}; "
            "$ec = if ($null -ne $LASTEXITCODE) {{ $LASTEXITCODE }} else {{ 0 }}; "
            "if ($ec -eq 0) {{ "
            "Write-Host '{name} 安装完成' -ForegroundColor Green }} "
            "else {{ "
            "Write-Host ('{name} 安装失败, 返回码: ' + $ec) "
            "-ForegroundColor Red; "
            "Read-Host '按回车键关闭此窗口' }}; "
            "exit $ec"
        ).format(title=ps_quote("一键安装工具 - " + task["file"]),
                 cwd=ps_quote(os.path.dirname(path)),
                 name=name, body=body)

    def run_all(self):
        results = []   # (软件名, 结果文本)
        try:
            # 仅处理勾选的安装任务
            selected_tasks = [t for t in TASKS
                              if self.task_checks[t["file"]].get()]
            checked_repo_urls = [url for url in REPOS
                                 if self.repo_checks[url].get()]

            # 重新设定进度条最大值(勾选的任务数 + 勾选的仓库数)
            progress_max = len(selected_tasks) + len(checked_repo_urls)
            self.root.after(0, lambda: self.progress.configure(
                maximum=max(progress_max, 1)))

            # ---- 逐个安装: 单个失败不中断,继续安装后面的软件 ----
            for i, task in enumerate(selected_tasks):
                self.set_status(task["file"], "正在安装...", "blue")
                self.log("===== 开始安装 %s =====" % task["name"])
                try:
                    code = self.run_task(task)
                except Exception as e:
                    self.log("%s 安装出错: %s" % (task["name"], e))
                    self.set_status(task["file"], "安装失败(%s)" % e, "red")
                    results.append((task["name"], "失败(%s)" % e))
                    self.progress["value"] = i + 1
                    continue
                if code in task["ok_codes"]:
                    self.set_status(task["file"], "安装成功", "green")
                    results.append((task["name"], "成功(返回码 %d)" % code))
                    if task["reboot_code"] and code == task["reboot_code"]:
                        self.need_reboot = True
                else:
                    self.set_status(task["file"],
                                    "安装失败(返回码 %d)" % code, "red")
                    results.append((task["name"], "失败(返回码 %d)" % code))
                self.progress["value"] = i + 1

            self.log("===== 安装结果汇总 =====")
            for name, text in results:
                self.log("%s: %s" % (name, text))
            failed = [t for t in results if t[1].startswith("失败")]
            if failed:
                lines = ["%s  ——  %s" % (n, s) for n, s in results]
                msg = ("部分软件安装失败:\n\n" + "\n".join(lines) +
                       "\n\n失败的软件可重新运行本工具单独重装。")
            else:
                msg = "全部软件安装完成!"
                if self.need_reboot:
                    msg += "\n\n建议重启电脑以使所有组件生效。"

            # 没有勾选仓库,直接结束
            if not checked_repo_urls:
                self.root.after(0, lambda: messagebox.showinfo(
                    "安装结束", msg))
                self.root.after(0, self.unlock_ui)
                return

            # ---- 验证 Git ----
            self.log("验证 Git 安装...")
            git_exe = find_git_exe(self.install_base)
            git_ok = bool(git_exe)
            self.log("验证结果: " + (
                "Git 已就绪 (" + git_exe + ")" if git_ok else
                "未检测到本工具安装的 git,跳过拉取代码(可重装 Git 后重试)"))
            self.git_exe = git_exe

            code_dir = os.path.join(self.install_base, CODE_FOLDER)
            os.makedirs(code_dir, exist_ok=True)
            self.log("代码存放目录: " + code_dir)

            if not git_ok:
                self.root.after(0, lambda: messagebox.showwarning(
                    "安装结束",
                    msg + "\n\nGit 未安装成功,本次跳过拉取代码。\n"
                           "可重新运行本工具重试。\n\n代码将拉取到:\n"
                    + code_dir))
                self.root.after(0, self.unlock_ui)
                return

            # 拉取代码前先检测 Git 版本号
            self.log("检测 Git 版本...")
            git_ver = self.check_git_version(git_exe)
            self.git_version = git_ver
            if not git_ver:
                self.root.after(0, lambda: messagebox.showwarning(
                    "安装结束",
                    msg + "\n\nGit 版本检测失败,本次跳过拉取代码。\n"
                           "请确认 Git 安装完整后重试。\n\n代码将拉取到:\n"
                    + code_dir))
                self.root.after(0, self.unlock_ui)
                return
            self.log("Git 版本: " + git_ver)

            clone_tail = ("\n\nGit 版本: " + git_ver +
                          "\n\n克隆需要认证时,会由 Git 弹出登录窗口,"
                          "请在窗口中输入您的 Git 账号密码。")
            self.root.after(0, lambda: messagebox.showinfo(
                "安装结束",
                msg + "\n\n即将开始拉取代码到:\n" + code_dir + clone_tail))
            # 当前已在后台线程中,直接继续克隆仓库
            self.clone_all(code_dir, checked_repo_urls)
        except Exception as e:
            self.log("出错: %s" % e)
            err = str(e)
            self.root.after(0, lambda: messagebox.showerror("安装失败", err))
            # 失败后解锁路径选择,允许用户重试或改选其他路径
            self.root.after(0, self.unlock_ui)

    def unlock_ui(self):
        """恢复路径选择和按钮为可操作状态(安装失败时调用)。"""
        self.dir_entry.configure(state="normal")
        self.browse_btn.configure(state="normal")
        self.btn.configure(state="normal", text="重试安装")
        self._set_checks_state("normal")

    def check_git_version(self, git_exe):
        """拉取代码前的预检: 执行 git --version 检测版本号并返回版本字符串;
        检测失败返回 None(视为 Git 不可用,跳过拉取代码)。"""
        try:
            proc = subprocess.run(
                [git_exe, "--version"], capture_output=True, text=True,
                timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            self.log("执行 git --version 失败: %s" % e)
            return None
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        if proc.returncode == 0 and out:
            return out
        self.log("git --version 返回码: %d" % proc.returncode)
        if out:
            self.log("git --version 输出: " + out)
        if err:
            self.log("git --version 错误: " + err)
        return None

    # -----------------------------------------------------------------------
    # 代码仓库拉取流程(安装完成后自动执行;
    # 需要认证时由 Git 弹出登录窗口,由使用者自行输入账号密码)
    # -----------------------------------------------------------------------
    def clone_all(self, code_dir, checked_repo_urls):
        """逐个克隆勾选的仓库:在可见的 Windows PowerShell 窗口中调用本工具安装的
        git.exe(如 C:/kingdee/git/bin/git.exe)执行与手动敲入一致的命令:
            git clone <仓库地址> <目标目录>
        目标目录为 Windows 绝对路径(如 C:/kingdee/kingdeecode/cmssc),
        cmbas、cmssc 各自克隆到 kingdeecode 下自己的子目录;
        只使用本工具安装目录下的 Git,不依赖系统 PATH 中的 git;
        账号密码不由本工具收集: 克隆需要认证时由 Git 弹出登录窗口,
        由使用者自行输入。
        每个仓库克隆失败后自动重试两次: 每次重试清理残留目录后重新打开
        新的命令行窗口继续执行。"""
        git_exe = (getattr(self, "git_exe", None)
                   or find_git_exe(self.install_base))
        if not git_exe:
            self.log("未找到本工具安装的 git.exe,跳过拉取代码。")
            tip = ("未找到 Git 安装目录下的 git.exe,本次跳过拉取代码。\n"
                   "请确认 Git 已安装到: " + os.path.join(self.install_base,
                                                          "git"))
            self.root.after(0, lambda: messagebox.showwarning(
                "跳过拉取代码", tip))
            self.root.after(0, self.unlock_ui)
            return
        self.log("使用 Git: " + git_exe)
        # 账号密码不由本工具收集: 需要认证时由 Git 弹出登录窗口
        self.log("克隆需要认证时,请在弹出的 Git 登录窗口中输入账号密码。")
        results = []
        for url in checked_repo_urls:
            name = repo_name(url)
            target = os.path.join(code_dir, name)
            self.set_repo_status(name, "检查中...", "blue")
            if os.path.isdir(os.path.join(target, ".git")):
                self.log("%s 已存在,跳过克隆。" % name)
                self.set_repo_status(name, "已存在,跳过", "gray")
                results.append((name, "已存在,跳过"))
                self.progress["value"] = self.progress["value"] + 1
                continue
            if os.path.exists(target):
                self.log("目录 %s 已存在但不是 Git 仓库,跳过。" % target)
                self.set_repo_status(name, "目录存在,跳过", "gray")
                results.append((name, "目录已存在,跳过"))
                self.progress["value"] = self.progress["value"] + 1
                continue

            self.log("===== 开始克隆 %s =====" % name)
            self.set_repo_status(name, "克隆中...", "blue")
            ok = False
            for attempt in range(RETRY_TIMES + 1):
                if attempt > 0:
                    self.log("%s 第 %d 次尝试失败,"
                             "正在重新打开命令行重试..." % (name, attempt))
                    self.cleanup_clone_dir(target)
                ok = self.clone_repo(
                    git_exe, url, target, name,
                    final_attempt=(attempt == RETRY_TIMES))
                if ok:
                    break

            if ok:
                if attempt > 0:
                    self.log("%s 重试后克隆成功。" % name)
                    self.set_repo_status(name, "成功(重试)", "green")
                    results.append((name, "成功(重试)"))
                else:
                    self.log("%s 克隆成功。" % name)
                    self.set_repo_status(name, "克隆成功", "green")
                    results.append((name, "成功"))
                self.progress["value"] = self.progress["value"] + 1
                continue

            self.log("%s 重试 %d 次后仍克隆失败,"
                     "请查看 PowerShell 窗口中的报错。" % (name, RETRY_TIMES))
            self.log("若为认证失败,请在 Git 登录窗口中确认账号密码是否正确、"
                     "是否有该仓库的访问权限,再重新运行本工具重试。")
            self.set_repo_status(name, "克隆失败", "red")
            results.append((name, "失败"))
            self.progress["value"] = self.progress["value"] + 1

        def _report():
            lines = ["%s  ——  %s" % (n, s) for n, s in results]
            failed = [n for n, s in results if s == "失败"]
            msg = ("代码拉取完成:\n\n" + "\n".join(lines) +
                   "\n\n存放位置: " + code_dir)
            if failed:
                msg += "\n\n失败的仓库可重新运行本工具重试。"
                messagebox.showwarning("部分失败", msg)
            else:
                messagebox.showinfo("拉取完成", msg)
            self.unlock_ui()
            self.btn.configure(text="重新执行")
        self.root.after(0, _report)

    def clone_repo(self, git_exe, url, target, name, final_attempt=False):
        """在可见的 PowerShell 窗口中执行克隆,
        以 .git 目录是否生成作为克隆成功的判据(比窗口退出码更可靠),
        成功返回 True,失败返回 False; final_attempt=True 表示最后一次
        尝试,失败时窗口停留等待按键便于现场排查。
        克隆成功后添加 git safe.directory 配置,
        避免管理员权限导致 TortoiseGit 报 'not owned by current user'。"""
        self.log("git clone %s %s" % (url, target))
        script = self.build_clone_script(
            git_exe, url, target, name, final_attempt)
        try:
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile",
                 "-ExecutionPolicy", "Bypass", "-Command", script])
            self.log("返回码: %d" % proc.returncode)
        except Exception as e:
            self.log("启动 PowerShell 失败: %s" % e)
        success = os.path.isdir(os.path.join(target, ".git"))
        if success:
            self._add_safe_directory(target)
        return success

    def _add_safe_directory(self, repo_path):
        """克隆后将仓库路径添加到 git safe.directory 配置,
        避免管理员权限克隆导致 TortoiseGit 报
        'repository path is not owned by current user'。"""
        safe_path = repo_path.replace("\\", "/")
        try:
            subprocess.run(
                [self.git_exe, "config", "--global", "--add",
                 "safe.directory", safe_path],
                capture_output=True, timeout=10)
            self.log("已添加 safe.directory: " + safe_path)
        except Exception as e:
            self.log("添加 safe.directory 失败: %s" % e)

    def cleanup_clone_dir(self, target):
        """重试前清理上一次克隆失败的残留目录: git clone 失败时通常
        会自行移除目标目录,个别残留(空目录或半成品)需在此删除,
        否则重试时 git 会报目标目录已存在。"""
        if (os.path.exists(target)
                and not os.path.isdir(os.path.join(target, ".git"))):
            try:
                shutil.rmtree(target)
                self.log("已清理克隆残留目录: " + target)
            except Exception as e:
                self.log("清理克隆残留目录失败(将直接重试): %s" % e)

    def build_clone_script(self, git_exe, url, target, name,
                           final_attempt=False):
        """生成单个仓库的 PowerShell 克隆脚本(在可见窗口中运行):
        & '<本工具安装的 git.exe>' clone <仓库地址> <目标目录>;
        失败时: 非最后一次尝试(final_attempt=False)窗口短暂显示
        返回码后自动关闭,无需人工按键,由工具自动清理残留并重新打开
        命令行窗口重试; 最后一次尝试失败则窗口停留等待按键,便于现场
        排查最终失败原因。"""
        # 未收集账号密码,克隆需要认证时由 Git 自行弹出登录窗口
        cred_echo = (
            "Write-Host '如需认证,请在弹出的 Git 登录窗口中输入账号密码' "
            "-ForegroundColor Yellow; ")
        # 非最后一次尝试: 自动关闭窗口继续重试; 最后一次: 停留等待按键
        pause = (
            "Read-Host '按回车键关闭此窗口'"
            if final_attempt else
            "Write-Host '窗口 3 秒后自动关闭,本工具将自动重试' "
            "-ForegroundColor Yellow; "
            "Start-Sleep -Seconds 3")
        return (
            "try {{ $host.UI.RawUI.WindowTitle = {title} }} catch {{ }}; "
            "Write-Host '===== 开始克隆 {name} =====' -ForegroundColor Cyan; "
            "{cred_echo}"
            "& {git} clone {url} {target}; "
            "$ec = if ($null -ne $LASTEXITCODE) {{ $LASTEXITCODE }} else {{ -1 }}; "
            "if ($ec -eq 0) {{ "
            "Write-Host '{name} 克隆成功' -ForegroundColor Green }} "
            "else {{ "
            "Write-Host ('{name} 克隆失败, 返回码: ' + $ec) "
            "-ForegroundColor Red; "
            "{pause} }}; "
            "exit $ec"
        ).format(title=ps_quote("一键安装工具 - 克隆 " + name),
                 name=name, cred_echo=cred_echo, pause=pause,
                 git=ps_quote(git_exe),
                 url=ps_quote(url),
                 target=ps_quote(target))


def repo_name(url):
    """从仓库 URL 中提取仓库名,如 cmssc.git -> cmssc。"""
    name = url.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name


def find_git_exe(install_base=None):
    r"""返回本工具安装的 git.exe 完整路径: 优先 <安装根目录>\git\bin\git.exe
    (与 Git Bash 共用),其次 <安装根目录>\git\cmd\git.exe;
    只认本工具安装目录下的 Git,找不到返回空字符串(不回退系统 PATH)。"""
    if install_base:
        for rel in (os.path.join("bin", "git.exe"),
                    os.path.join("cmd", "git.exe")):
            p = os.path.join(install_base, "git", rel)
            if os.path.exists(p):
                return p
    return ""


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def main():
    if not is_admin():
        elevate_and_restart()
        return

    root = tk.Tk()
    InstallerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
