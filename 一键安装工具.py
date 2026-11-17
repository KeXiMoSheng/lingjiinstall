# -*- coding: utf-8 -*-
r"""
一键安装工具
============
静默安装 VC++ 运行库、Git、TortoiseGit、灵基,安装完成后自动克隆代码仓库
(代码仓库需要认证才能拉取: 账号密码已内置在工具中,克隆时直接拼进
 git clone 的 https 地址里自动完成认证,使用者无需手动输入)。

本版本行为:
  * 不在任何磁盘位置记录日志文件(运行过程仅在界面内实时显示);
  * 四个安装包均在可见的 PowerShell 窗口中以命令行方式安装,
    安装失败时窗口停留显示返回码,便于现场排查;
  * 拉取代码: 在可见的 Windows PowerShell 窗口中调用本工具安装的
    git.exe 执行单条命令
    git clone <仓库地址> <目标目录>(如 C:\kingdee\kingdeecode\cmssc);
  * 拉完代码后自动更新代码: 把 cmssc、cmbas 强制同步到远程写死分支
    patch_8.0(SYNC_BRANCH),与远程完全一致;
  * 界面上有"同步最新代码"按钮,可随时单独把 cmssc、cmbas 再次同步到
    远程 patch_8.0 分支(只更新代码,不安装软件);
  * 记住用户选择的安装根目录: 保存在 %APPDATA%\一键安装工具\config.json,
    下次打开程序自动恢复(配置里的目录已不存在时退回默认目录);
  * 代码仓库列表中,每个仓库下方会显示"分支: xxx"与"最近同步: 时间":
    分支在拉取完代码、同步完成后都会读取并刷新(启动时也会在后台读一次
    真实分支,用户在 TortoiseGit 中切换过分支也能正确显示);
    最近同步时间在每次同步成功后刷新,并和分支一起写入 config.json,
    因此关闭/重启本程序后仍然显示上次的结果;
  * 同时记住最近一次安装/同步成功的安装根目录(last_success_base):
    若用户误改了安装路径,点"同步最新代码"时找不到安装目录 / 代码目录,
    弹出的提示窗口中会显示上次成功的位置,路径可选中复制,也可一键复制
    或填回输入框;
  * 界面与日志里的所有路径统一用 Windows 的右斜杠(反斜杠)显示,
    手动输入的正斜杠在离开输入框时自动换成反斜杠。

同步最新代码(强制与远程一致):
      依次在仓库目录执行(在可见的 PowerShell 窗口中):
      git fetch --prune origin '+refs/heads/patch_8.0:refs/remotes/origin/patch_8.0'
      git checkout -f -B patch_8.0 origin/patch_8.0
      git branch --set-upstream-to=origin/patch_8.0 patch_8.0
      git reset --hard origin/patch_8.0
      git clean -fd
      即: 本地未提交的改动、多余文件一律丢弃,强制与远程 patch_8.0 一致
      (被 .gitignore 忽略的文件保留); 执行后用 git 校验 HEAD 与
      origin/patch_8.0 的提交号相同,相同才算同步成功。

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
      执行:
      git -c credential.helper= clone -- <带账号密码的仓库地址> <目标目录>
      目标目录为 Windows 路径,如安装根目录为 c:\kingdee 时:
      git clone https://.../cmssc.git C:\kingdee\kingdeecode\cmssc
      (kingdeecode 为代码总目录,cmbas、cmssc 各自独立子目录);
      只使用本工具安装目录下的 Git,不依赖系统 PATH 中的 git;
      仓库地址必须用 https: 服务器会把 http 301 重定向到 https,而认证
      信息无法跟随重定向传递,http 地址会导致自动认证失败;
      账号密码已内置在工具中(GIT_USERNAME / GIT_PASSWORD),克隆时
      按 https://账号:密码@主机/路径 的格式拼进地址,自动完成认证,
      使用者无需手动输入;密码中的特殊字符(@ ! # 等)会做 URL 百分号编码;
      界面日志与提示只显示账号、不显示密码(用 mask_url 遮蔽);
      -c credential.helper= 加 GIT_TERMINAL_PROMPT=0: 万一账号密码失效,
      Git 直接报错退出,不会弹出凭据登录窗口把流程卡住;
      密码会随远程地址保存在各仓库的 .git/config 中,因此后续用
      TortoiseGit 拉取/更新也不需要再输入密码(如不需要保留,可在仓库中执行
      git remote set-url origin <不带账号的地址> 清除)。

打包方式(见 打包exe.bat,四个安装包会被打进 exe):
  pyinstaller --onefile --noconsole --uac-admin --name "一键安装工具" ...
生成的 exe 在 dist/ 目录下,单个文件即可分发。
"""

import ctypes
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from urllib.parse import quote

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
        "file": "LingeeSetup_ia32_1.10.2_2611121930.exe",
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

# ---------------------------------------------------------------------------
# 同步最新代码(写死分支): 拉完代码后、以及点"同步最新代码"按钮时,
# 强制让本地仓库与远程该分支保持一致
#   git fetch -> git checkout -f -B patch_8.0 origin/patch_8.0
#   -> git reset --hard origin/patch_8.0 -> git clean -fd
# 本地改动会被丢弃,与远程完全一致(被 .gitignore 忽略的文件保留)。
# ---------------------------------------------------------------------------
SYNC_BRANCH = "patch_8.0"

# 参与强制同步的仓库(按 REPOS 中的仓库名匹配): cmssc 与 cmbas
SYNC_REPOS = ["cmssc", "cmbas"]

# 每个仓库克隆失败后自动重试次数: 每次重试清理残留目录并重新打开
# 新的命令行窗口继续执行,总尝试次数 = RETRY_TIMES + 1
RETRY_TIMES = 2

# ---------------------------------------------------------------------------
# Git 账号密码(内置): 克隆代码仓库时需要认证,这里直接把账号密码拼进
# git clone 的 https 地址,使用者无需手动输入。
# 注意: 修改账号密码只需改这两行;密码中的特殊字符会做 URL 百分号编码,
# 不需要在这里手工转义。
# ---------------------------------------------------------------------------
GIT_USERNAME = "jiang_wusz@kingdee.com"
GIT_PASSWORD = "123qwe123!@#"


def build_auth_url(url, username=GIT_USERNAME, password=GIT_PASSWORD):
    """把内置账号密码拼进 https 仓库地址,供 git clone 自动认证。

    形如: https://jiang_wusz%40kingdee.com:123qwe123%21%40%23@host/x.git
    账号/密码中的 @ ! # 等字符按 URL 规范做百分号编码,避免被当成
    地址分隔符;非 http(s) 地址原样返回。
    """
    if not url.lower().startswith(("http://", "https://")):
        return url
    scheme, _, rest = url.partition("://")
    user = quote(str(username), safe="")
    pwd = quote(str(password), safe="")
    return "%s://%s:%s@%s" % (scheme, user, pwd, rest)


def mask_url(url):
    """显示用的地址脱敏: 只保留账号,密码替换成 ****,
    保证界面日志和 PowerShell 窗口里都不出现明文密码。"""
    scheme, sep, rest = url.partition("://")
    if not sep:
        return url
    authority, slash, tail = rest.partition("/")
    if "@" not in authority:
        return url
    userinfo, _, host = authority.rpartition("@")
    user = userinfo.split(":", 1)[0]
    return "%s://%s:****@%s%s%s" % (scheme, user, host, slash, tail)


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


def win_path(path):
    """把路径统一成 Windows 风格(与资源管理器显示一致,全部用反斜杠)。

    * 正斜杠 "/" 一律换成反斜杠 "\\"(文件选择框返回的目录常是 C:/kingdee
      这种形式,直接显示会与 Windows 习惯不一致);
    * 去掉多余的分隔符、结尾多余的反斜杠(盘符根目录如 C:\\ 保留);
    * 去掉用户粘贴时可能带上的成对双引号。
    只做显示与保存用的规范化,不改变路径指向;空值返回空字符串。
    """
    text = str(path or "").strip().strip('"').strip()
    if not text:
        return ""
    text = text.replace("/", "\\")
    try:
        text = os.path.normpath(text)
    except Exception:
        return text
    if len(text) == 2 and text[1] == ":":
        # 只写了盘符(如 D:)时补上根目录分隔符,与资源管理器的 D:\ 一致
        text += "\\"
    return text


def default_install_base():
    """默认安装根目录: 优先选已存在的非系统盘,否则退回 C 盘。"""
    for drive in ("D:\\", "E:\\", "F:\\"):
        if os.path.isdir(drive):
            return drive
    return "C:\\"


# ---------------------------------------------------------------------------
# 用户配置(记住上次选择的安装根目录,下次启动自动恢复)
#   文件位置: 优先 %APPDATA%\一键安装工具\config.json,
#   取不到 APPDATA 时退回 exe/脚本所在目录;
#   读写失败一律静默忽略,不影响安装主流程。
# ---------------------------------------------------------------------------
CONFIG_FILE_NAME = "config.json"
CONFIG_APP_DIR = "一键安装工具"
# 配置项: install_base=当前选择的安装根目录;
#        last_success_base / last_success_time=最近一次安装或同步成功的
#        安装根目录及其时间(用户误改了安装路径、点"同步最新代码"时,
#        用它把上次成功的位置显示出来,可直接复制粘贴回去);
#        repo_info=各仓库的显示信息 {"仓库名": {"branch": 分支, "sync_time": 时间}},
#        供重启程序后仍显示每个仓库的当前分支与最近一次同步时间
CONFIG_KEY_BASE = "install_base"
CONFIG_KEY_LAST_BASE = "last_success_base"
CONFIG_KEY_LAST_TIME = "last_success_time"
CONFIG_KEY_REPO_INFO = "repo_info"


def config_path():
    base = os.environ.get("APPDATA") or ""
    if base:
        return os.path.join(base, CONFIG_APP_DIR, CONFIG_FILE_NAME)
    return os.path.join(search_dirs()[0] or os.getcwd(), CONFIG_FILE_NAME)


def load_config():
    """读取配置文件,返回 dict; 文件不存在或解析失败返回空 dict。"""
    try:
        with open(config_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_config(data):
    """把配置写入文件(整体覆盖),失败返回 False。"""
    path = config_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


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
        self.config = load_config()   # 上次保存的配置(记住安装根目录)
        root.title("一键安装工具 (Git + TortoiseGit + VC++ 运行库 + 灵基)")
        root.geometry("640x760")
        root.resizable(False, False)

        ttk.Label(root, text="请选择安装根目录(软件与代码将安装到其子目录中):",
                  font=("Microsoft YaHei UI", 11)).pack(pady=(15, 5))

        # 安装根目录选择行(安装开始后锁定)
        dir_frame = ttk.Frame(root)
        dir_frame.pack(fill="x", padx=30, pady=(0, 5))
        ttk.Label(dir_frame, text="安装根目录:").pack(side="left")
        self.dir_var = tk.StringVar(value=self.initial_install_base())
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=8)
        # 手动输入完离开输入框时,把正斜杠统一成 Windows 的反斜杠
        self.dir_entry.bind("<FocusOut>", self._on_dir_focus_out)
        self.browse_btn = ttk.Button(dir_frame, text="浏览...",
                                     command=self.browse_dir)
        self.browse_btn.pack(side="left")
        # 用户手动改了目录也立即记住,不必等点开始安装
        self.dir_var.trace_add("write", self._on_dir_changed)

        ttk.Label(
            root, wraplength=560, foreground="gray",
            text="软件将安装到子目录: git、TortoiseGit、lingdee"
                 "(VC++ 运行库为系统默认位置);\n"
                 "代码将克隆到子目录: kingdeecode;\n"
                 "代码仓库的账号密码已内置,拉取时自动认证,无需手动输入;\n"
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
        ttk.Label(root, text="代码仓库(勾选后将自动克隆,并强制同步到远程 %s 分支):"
                  % SYNC_BRANCH,
                  font=("Microsoft YaHei UI", 10)).pack(pady=(0, 3))
        self.repo_checks = {}
        self.repo_check_widgets = {}
        self.repo_status_vars = {}
        self.repo_branch_vars = {}     # 仓库名 -> 当前分支显示
        self.repo_time_vars = {}       # 仓库名 -> 最近同步时间显示
        repo_frame = ttk.Frame(root)
        repo_frame.pack(fill="x", padx=30, pady=5)
        for url in REPOS:
            name = repo_name(url)
            row = ttk.Frame(repo_frame)
            row.pack(fill="x", pady=(3, 0))
            chk_var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(row, text=name,
                                 variable=chk_var, width=28)
            cb.pack(side="left")
            var = tk.StringVar(value="等待克隆")
            lbl = ttk.Label(row, textvariable=var, foreground="gray")
            lbl.pack(side="left")
            # 第二行: 当前分支 + 最近一次同步时间(重启后从配置恢复)
            info_row = ttk.Frame(repo_frame)
            info_row.pack(fill="x", pady=(0, 3))
            branch_var = tk.StringVar(value="")
            time_var = tk.StringVar(value="")
            ttk.Label(info_row, textvariable=branch_var, foreground="gray",
                      font=("Microsoft YaHei UI", 9)).pack(
                side="left", padx=(28, 12))
            ttk.Label(info_row, textvariable=time_var, foreground="gray",
                      font=("Microsoft YaHei UI", 9)).pack(side="left")
            self.repo_checks[url] = chk_var
            self.repo_check_widgets[url] = cb
            self.repo_status_vars[name] = (var, lbl)
            self.repo_branch_vars[name] = branch_var
            self.repo_time_vars[name] = time_var
            self._show_repo_info(name)

        self.progress = ttk.Progressbar(root, length=560, maximum=len(TASKS))
        self.progress.pack(pady=8)

        # 日志区
        self.log_text = tk.Text(root, height=8, width=80,
                                state="disabled", font=("Consolas", 9))
        self.log_text.pack(padx=15, pady=(0, 8))

        # 底部按钮: 开始安装 + 同步最新代码(只更新代码,不安装软件)
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=(0, 15))
        self.btn = ttk.Button(btn_frame, text="开始安装", command=self.start)
        self.btn.pack(side="left", padx=6)
        self.sync_btn = ttk.Button(btn_frame, text="同步最新代码",
                                   command=self.sync_clicked)
        self.sync_btn.pack(side="left", padx=6)

        # 启动时先按配置显示各仓库的分支与最近同步时间(重启后仍可见),
        # 再在后台用 git 读一次真实分支(不阻塞界面)
        self.refresh_branches_on_startup()

    def initial_install_base(self):
        """启动时恢复上次选择的目录: 配置中的目录仍存在就用它,否则用默认目录。
        取出来的路径统一按 Windows 的右斜杠形式显示。"""
        saved = win_path(self.config.get(CONFIG_KEY_BASE) or "")
        if saved and os.path.isdir(saved):
            return saved
        return default_install_base()

    def last_success_base(self):
        """最近一次安装/同步成功的安装根目录(没记录过返回空字符串)。"""
        return win_path(self.config.get(CONFIG_KEY_LAST_BASE) or "")

    def current_base(self):
        """读取输入框里的安装根目录并规范化(绝对路径 + Windows 右斜杠);
        为空返回空字符串。"""
        text = win_path(self.dir_var.get())
        if not text:
            return ""
        return win_path(os.path.abspath(text))

    def mark_success(self, base=None):
        """记录最近一次安装/同步成功的安装根目录及时间,供误改路径时提示。"""
        base = win_path(base or self.install_base or self.current_base())
        if not base:
            return
        base = win_path(os.path.abspath(base))
        self.config[CONFIG_KEY_LAST_BASE] = base
        self.config[CONFIG_KEY_LAST_TIME] = time.strftime("%Y-%m-%d %H:%M:%S")
        save_config(self.config)

    def _on_dir_changed(self, *_args):
        """目录内容变化时记住选择(只记非空值,避免清空输入框时把配置冲掉;
        写进配置的统一是 Windows 右斜杠形式,不动输入框里的原文以免递归)。"""
        text = win_path(self.dir_var.get())
        if not text:
            return
        if self.config.get(CONFIG_KEY_BASE) == text:
            return
        self.config[CONFIG_KEY_BASE] = text
        save_config(self.config)

    def _on_dir_focus_out(self, _event=None):
        """手动输入完离开输入框时,把路径统一成 Windows 的右斜杠形式,
        并顺手去掉可能粘贴进来的成对双引号 / 结尾多余反斜杠。
        (赋值会触发 dir_var 的 trace,顺带把新值记进配置)"""
        text = self.dir_var.get()
        fixed = win_path(text)
        if fixed and fixed != text:
            self.dir_var.set(fixed)

    def browse_dir(self):
        chosen = filedialog.askdirectory(
            title="请选择安装根目录",
            initialdir=self.dir_var.get() or os.path.expanduser("~"))
        if chosen:
            # 文件选择框返回的是 C:/xxx 这种正斜杠形式,统一成 Windows 的显示方式
            self.dir_var.set(win_path(chosen))

    def show_missing_dir_tip(self, title, message, base=None):
        """未找到安装目录 / 代码目录时的提示窗口:
        把最近一次安装或同步成功的安装根目录显示出来,路径可选中复制,
        也可一键复制或直接填回"安装根目录"输入框,避免用户记不清上次装哪;
        下方按仓库分别列出各自的当前分支与最近一次同步时间
        (没有成功记录时同样会显示这部分信息)。"""
        last = self.last_success_base()
        exists = bool(last) and os.path.isdir(last)
        same_as_current = bool(base) and bool(last) and win_path(base) == last

        top = tk.Toplevel(self.root)
        top.title(title)
        top.resizable(False, False)
        top.transient(self.root)
        body = ttk.Frame(top, padding=15)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text=message, wraplength=470, justify="left").pack(
            anchor="w")
        path_entry = None
        if last:
            ttk.Label(body, text="最近一次安装/同步成功的安装根目录:",
                      foreground="#0a7a3d",
                      font=("Microsoft YaHei UI", 10, "bold")).pack(
                anchor="w", pady=(12, 3))
            path_entry = ttk.Entry(body, width=64, font=("Consolas", 10))
            path_entry.insert(0, last)
            path_entry.configure(state="readonly")   # 可选中 / Ctrl+C,但不可误改
            path_entry.pack(fill="x")
            path_entry.focus_set()
            path_entry.selection_range(0, "end")
            if not exists:
                ttk.Label(body,
                          text="(该目录当前已不存在,可能是磁盘被移除或目录被删)",
                          foreground="gray").pack(anchor="w", pady=(2, 0))
            elif same_as_current:
                ttk.Label(body, text="(这就是输入框里的路径,说明该目录下确实没有"
                                     "安装文件,请确认是否装到了别的目录)",
                          foreground="gray", wraplength=470,
                          justify="left").pack(anchor="w", pady=(2, 0))

        # 各仓库分别记录的当前分支与最近一次同步时间
        # (与主界面一致,重启后仍可查)
        ttk.Label(body, text="各仓库最近一次同步(按仓库分别记录):",
                  foreground="#0a7a3d",
                  font=("Microsoft YaHei UI", 10, "bold")).pack(
            anchor="w", pady=(12, 3))
        info_box = ttk.Frame(body)
        info_box.pack(fill="x")
        self.repo_sync_rows(info_box)

        def copy_path():
            self.root.clipboard_clear()
            self.root.clipboard_append(last)
            copy_btn.configure(text="已复制")
            top.after(1500, lambda: copy_btn.configure(text="复制路径"))

        def fill_path():
            # 赋值会触发 dir_var 的 trace,自动同步到配置
            self.dir_var.set(last)
            top.destroy()

        btns = ttk.Frame(body)
        btns.pack(fill="x", pady=(12, 0))
        if last:
            copy_btn = ttk.Button(btns, text="复制路径", command=copy_path)
            copy_btn.pack(side="left")
            if exists:
                ttk.Button(btns, text="填回安装目录", command=fill_path).pack(
                    side="left", padx=8)
        ttk.Button(btns, text="关闭", command=top.destroy).pack(side="right")
        top.bind("<Escape>", lambda _e: top.destroy())

        top.update_idletasks()
        x = self.root.winfo_rootx() + (
            self.root.winfo_width() - top.winfo_width()) // 2
        y = self.root.winfo_rooty() + 120
        top.geometry("+%d+%d" % (max(x, 0), max(y, 0)))
        top.grab_set()

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

    # -----------------------------------------------------------------------
    # 仓库的分支 / 最近同步时间显示(重启后从配置文件恢复)
    # -----------------------------------------------------------------------
    def repo_info(self):
        """读取配置里各仓库的显示信息 dict,结构异常时返回空 dict。"""
        info = self.config.get(CONFIG_KEY_REPO_INFO)
        return info if isinstance(info, dict) else {}

    def save_repo_info(self, name, branch=None, sync_time=None):
        """把某个仓库的分支 / 最近同步时间写进配置(重启后仍能显示)。"""
        info = self.repo_info()
        item = info.get(name)
        if not isinstance(item, dict):
            item = {}
        if branch is not None:
            item["branch"] = branch
        if sync_time is not None:
            item["sync_time"] = sync_time
        info[name] = item
        self.config[CONFIG_KEY_REPO_INFO] = info
        save_config(self.config)

    def _show_repo_info(self, name):
        """按配置里的信息刷新某个仓库的分支 / 最近同步时间文字。"""
        item = self.repo_info().get(name)
        item = item if isinstance(item, dict) else {}
        branch = str(item.get("branch") or "").strip()
        sync_time = str(item.get("sync_time") or "").strip()
        self.set_repo_branch(name, branch)
        self.set_repo_time(name, sync_time)

    def set_repo_branch(self, name, text):
        """设置仓库的当前分支显示(空值显示为"分支: 未知")。"""
        var = self.repo_branch_vars.get(name)
        if var is not None:
            self.root.after(0, lambda: var.set("分支: " + (text or "未知")))

    def set_repo_time(self, name, text):
        """设置仓库的最近一次同步时间显示。"""
        var = self.repo_time_vars.get(name)
        if var is not None:
            self.root.after(
                0, lambda: var.set("最近同步: " + (text or "未同步")))

    def current_repo_branch(self, git_exe, target):
        """读取仓库当前分支名(如 patch_8.0); 读取失败返回空字符串。"""
        return self.git_output(
            git_exe, target, ["rev-parse", "--abbrev-ref", "HEAD"])

    def refresh_repo_branch(self, git_exe, target, name):
        """把仓库当前的本地分支刷新到界面,并记进配置(重启后仍显示)。"""
        branch = self.current_repo_branch(git_exe, target)
        if branch and branch != "HEAD":
            self.set_repo_branch(name, branch)
            self.save_repo_info(name, branch=branch)
            return branch
        return ""

    def record_synced(self, name, branch=None):
        """同步成功后记录时间: 界面显示"最近同步: 时间",并写进配置文件,
        重启程序后仍然显示。"""
        when = time.strftime("%Y-%m-%d %H:%M:%S")
        self.set_repo_time(name, when)
        self.save_repo_info(name, branch=branch, sync_time=when)
        return when

    def refresh_branches_on_startup(self):
        """启动时在后台读一次各仓库的真实分支(用户可能在 TortoiseGit 里
        切换过分支),读到的分支更新到界面并记进配置;
        只更新分支,不改动"最近同步"时间的显示。"""
        base = win_path(self.config.get(CONFIG_KEY_BASE) or "")
        if not base or not os.path.isdir(base):
            return
        git_exe = find_git_exe(base)
        if not git_exe:
            return
        code_dir = win_path(os.path.join(base, CODE_FOLDER))

        def _worker():
            for url in REPOS:
                name = repo_name(url)
                target = win_path(os.path.join(code_dir, name))
                if os.path.isdir(os.path.join(target, ".git")):
                    self.refresh_repo_branch(git_exe, target, name)

        threading.Thread(target=_worker, daemon=True).start()

    def _set_checks_state(self, state):
        """启用或禁用所有复选框(安装期间禁用,防止中途修改选择)。"""
        for w in self.task_check_widgets.values():
            w.configure(state=state)
        for w in self.repo_check_widgets.values():
            w.configure(state=state)

    def start(self):
        base = self.current_base()
        if not base:
            messagebox.showwarning("提示", "请先选择安装根目录。")
            return
        if not os.path.isdir(base):
            self.show_missing_dir_tip(
                "安装目录不存在",
                "安装目录 %s 不存在,请选择一个已存在的磁盘目录。\n\n"
                "如果只是记不清上次装在哪,可直接使用下面记录的路径。" % base,
                base)
            return

        self.install_base = base
        # 记住用户选择的目录,下次打开程序自动恢复
        if self.config.get(CONFIG_KEY_BASE) != base:
            self.config[CONFIG_KEY_BASE] = base
            save_config(self.config)
        # 检查是否有勾选任何项目
        has_task = any(v.get() for v in self.task_checks.values())
        has_repo = any(v.get() for v in self.repo_checks.values())
        if not has_task and not has_repo:
            messagebox.showwarning("提示", "请至少勾选一个软件或代码仓库。")
            return
        self.log("安装根目录: " + base)
        self.log("Git -> %s" % win_path(os.path.join(base, "git")))
        self.log("TortoiseGit -> %s"
                 % win_path(os.path.join(base, "TortoiseGit")))
        self.log("灵基 -> %s" % win_path(os.path.join(base, "lingdee")))
        self.log("VC++ 运行库 -> 系统默认位置(微软限制,不支持自定义目录)")
        self.log("代码仓库 -> " + win_path(os.path.join(base, CODE_FOLDER)))
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
        self.sync_btn.configure(state="disabled")
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
            installed_ok = 0
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
                    installed_ok += 1
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

            # 有软件安装成功就记住这个安装根目录(供下次误改路径时提示)
            if installed_ok:
                self.mark_success(self.install_base)

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

            code_dir = win_path(os.path.join(self.install_base, CODE_FOLDER))
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
                          "\n\n拉取代码使用工具内置账号 "
                          + GIT_USERNAME + " 自动认证,无需手动输入。")
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
        self.sync_btn.configure(state="normal")
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
    # 账号密码内置,克隆时直接拼进地址自动认证,使用者无需手动输入)
    # -----------------------------------------------------------------------
    def clone_all(self, code_dir, checked_repo_urls):
        """逐个克隆勾选的仓库:在可见的 Windows PowerShell 窗口中调用本工具安装的
        git.exe(如 C:/kingdee/git/bin/git.exe)执行:
            git clone https://账号:密码@主机/路径.git <目标目录>
        账号密码取内置常量 GIT_USERNAME / GIT_PASSWORD,自动完成认证;
        目标目录为 Windows 绝对路径(如 C:/kingdee/kingdeecode/cmssc),
        cmbas、cmssc 各自克隆到 kingdeecode 下自己的子目录;
        只使用本工具安装目录下的 Git,不依赖系统 PATH 中的 git;
        每个仓库克隆失败后自动重试两次: 每次重试清理残留目录后重新打开
        新的命令行窗口继续执行。"""
        git_exe = (getattr(self, "git_exe", None)
                   or find_git_exe(self.install_base))
        if not git_exe:
            self.log("未找到本工具安装的 git.exe,跳过拉取代码。")
            tip = ("未找到 Git 安装目录下的 git.exe,本次跳过拉取代码。\n"
                   "请确认 Git 已安装到: "
                   + win_path(os.path.join(self.install_base, "git")))
            self.root.after(0, lambda: messagebox.showwarning(
                "跳过拉取代码", tip))
            self.root.after(0, self.unlock_ui)
            return
        self.log("使用 Git: " + git_exe)
        # 账号密码内置: 克隆时直接拼进地址自动认证
        self.log("使用内置账号自动认证: " + GIT_USERNAME)
        results = []
        cloned_any = False
        for url in checked_repo_urls:
            name = repo_name(url)
            target = win_path(os.path.join(code_dir, name))
            self.set_repo_status(name, "检查中...", "blue")
            if os.path.isdir(os.path.join(target, ".git")):
                self.log("%s 已存在,跳过克隆。" % name)
                self.set_repo_status(name, "已存在,跳过", "gray")
                results.append((name, "已存在,跳过"))
                # 已有仓库同样把当前分支刷新到界面上
                self.refresh_repo_branch(git_exe, target, name)
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
                cloned_any = True
                if attempt > 0:
                    self.log("%s 重试后克隆成功。" % name)
                    self.set_repo_status(name, "成功(重试)", "green")
                    results.append((name, "成功(重试)"))
                else:
                    self.log("%s 克隆成功。" % name)
                    self.set_repo_status(name, "克隆成功", "green")
                    results.append((name, "成功"))
                self.progress["value"] = self.progress["value"] + 1

                # 拉完代码之后立刻更新代码: 强制与远程写死分支保持一致
                if name in SYNC_REPOS:
                    self.set_repo_status(name, "同步 %s 中..." % SYNC_BRANCH,
                                         "blue")
                    self.log("继续把 %s 同步到远程 %s 分支..." % (
                        name, SYNC_BRANCH))
                    if self.sync_repo(git_exe, target, name):
                        self.set_repo_status(name, "已同步 " + SYNC_BRANCH,
                                             "green")
                        results.append((name, "已同步 " + SYNC_BRANCH))
                    else:
                        self.log("%s 同步 %s 失败,请查看 PowerShell "
                                 "窗口中的报错。" % (name, SYNC_BRANCH))
                        self.set_repo_status(name, "同步失败", "red")
                        results.append((name, "同步失败"))
                else:
                    # 同步对象之外的仓库只显示其当前分支
                    self.refresh_repo_branch(git_exe, target, name)
                continue

            self.log("%s 重试 %d 次后仍克隆失败,"
                     "请查看 PowerShell 窗口中的报错。" % (name, RETRY_TIMES))
            self.log("若为认证失败,请确认内置账号 %s 的密码是否正确、"
                     "是否有该仓库的访问权限,再重新运行本工具重试。"
                     % GIT_USERNAME)
            self.set_repo_status(name, "克隆失败", "red")
            results.append((name, "失败"))
            self.progress["value"] = self.progress["value"] + 1

        def _report():
            lines = ["%s  ——  %s" % (n, s) for n, s in results]
            failed = [n for n, s in results if s in ("失败", "同步失败")]
            msg = ("代码拉取完成:\n\n" + "\n".join(lines) +
                   "\n\n存放位置: " + win_path(code_dir) +
                   "\n\n" + self.repo_info_text())
            if failed:
                msg += "\n\n失败的仓库可重新运行本工具重试。"
                messagebox.showwarning("部分失败", msg)
            else:
                messagebox.showinfo("拉取完成", msg)
            self.unlock_ui()
            self.btn.configure(text="重新执行")
        # 代码成功拉到本地,记住这个安装根目录(供下次误改路径时提示)
        if cloned_any:
            self.mark_success(self.install_base)
        self.root.after(0, _report)

    def clone_repo(self, git_exe, url, target, name, final_attempt=False):
        """在可见的 PowerShell 窗口中执行克隆(地址已拼入内置账号密码),
        以 .git 目录是否生成作为克隆成功的判据(比窗口退出码更可靠),
        成功返回 True,失败返回 False; final_attempt=True 表示最后一次
        尝试,失败时窗口停留等待按键便于现场排查。
        克隆成功后添加 git safe.directory 配置,
        避免管理员权限导致 TortoiseGit 报 'not owned by current user'。"""
        auth_url = build_auth_url(url)
        # 日志中只显示脱敏地址,不出现明文密码
        self.log("git clone %s %s" % (mask_url(auth_url), target))
        script = self.build_clone_script(
            git_exe, auth_url, target, name, final_attempt)
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
        git_exe = getattr(self, "git_exe", None)
        if not git_exe:
            return
        safe_path = repo_path.replace("\\", "/")
        try:
            proc = subprocess.run(
                [git_exe, "config", "--global", "--get-all", "safe.directory"],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW)
            if safe_path in (proc.stdout or "").splitlines():
                return   # 已存在,不重复追加,避免 config 里堆一堆重复项
            subprocess.run(
                [git_exe, "config", "--global", "--add",
                 "safe.directory", safe_path],
                capture_output=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW)
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
        & '<本工具安装的 git.exe>' -c credential.helper= clone -- <带账号密码的地址> <目标目录>;
        * 地址里已带内置账号密码,认证自动完成,不需要人工输入;
        * -c credential.helper= 与 GIT_TERMINAL_PROMPT=0 让认证失败时直接
          报错退出,不会弹出凭据输入窗口把流程卡住;
        失败时: 非最后一次尝试(final_attempt=False)窗口短暂显示
        返回码后自动关闭,无需人工按键,由工具自动清理残留并重新打开
        命令行窗口重试; 最后一次尝试失败则窗口停留等待按键,便于现场
        排查最终失败原因。"""
        # 账号密码已拼进地址,窗口里只提示使用内置账号(不显示明文密码)
        cred_echo = "Write-Host {msg} -ForegroundColor Yellow; ".format(
            msg=ps_quote("使用内置账号 %s 自动认证,无需手动输入" % GIT_USERNAME))
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
            "$env:GIT_TERMINAL_PROMPT = '0'; "
            "{cred_echo}"
            "& {git} -c credential.helper= clone -- {url} {target}; "
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

    # -----------------------------------------------------------------------
    # 同步最新代码(强制与远程写死分支 patch_8.0 保持一致)
    #   拉完代码后自动执行一次,也可点界面上的"同步最新代码"按钮单独执行;
    #   同步对象为 cmssc 与 cmbas(SYNC_REPOS)。
    # -----------------------------------------------------------------------
    def sync_clicked(self):
        """按钮入口: 只更新代码,不安装软件。
        若安装目录或代码目录找不到(用户误改了安装路径),提示最近一次
        安装/同步成功的安装位置,可用它把路径改回去。"""
        base = self.current_base()
        if not base:
            messagebox.showwarning("提示", "请先选择安装根目录。")
            return
        if not os.path.isdir(base):
            self.show_missing_dir_tip(
                "安装目录不存在",
                "安装目录 %s 不存在,请选择一个已存在的磁盘目录。\n\n"
                "如果只是记不清上次装在哪,可直接使用下面记录的路径。" % base,
                base)
            return
        self.install_base = base
        if self.config.get(CONFIG_KEY_BASE) != base:
            self.config[CONFIG_KEY_BASE] = base
            save_config(self.config)
        code_dir = win_path(os.path.join(base, CODE_FOLDER))
        if not os.path.isdir(code_dir):
            self.show_missing_dir_tip(
                "未找到代码目录",
                "未找到代码目录 %s。\n\n请先执行一次安装并把代码拉取下来,"
                "再使用本按钮同步;\n若只是把安装路径改错了,可改用下面"
                "记录的路径。" % code_dir, base)
            return
        git_exe = getattr(self, "git_exe", None) or find_git_exe(base)
        if not git_exe:
            self.show_missing_dir_tip(
                "未找到 Git",
                "未找到本工具安装的 git.exe,请确认 Git 已安装到:\n"
                + win_path(os.path.join(base, "git")) + "\n\n"
                "若只是把安装路径改错了,可改用下面记录的路径。", base)
            return
        self.git_exe = git_exe
        self._btn_text_before_sync = self.btn.cget("text")
        self.log("===== 开始同步最新代码(%s 分支) =====" % SYNC_BRANCH)
        self.log("安装根目录: " + base)
        self.log("使用 Git: " + git_exe)
        # 同步期间锁定目录与按钮,避免中途改路径
        self.dir_entry.configure(state="disabled")
        self.browse_btn.configure(state="disabled")
        self.btn.configure(state="disabled")
        self.sync_btn.configure(state="disabled", text="同步中...")
        self._set_checks_state("disabled")
        threading.Thread(target=self.sync_all,
                         args=(code_dir, list(SYNC_REPOS)),
                         daemon=True).start()

    def sync_all(self, code_dir, names):
        """逐个把仓库强制同步到远程 SYNC_BRANCH 分支。"""
        git_exe = getattr(self, "git_exe", None) or find_git_exe(
            self.install_base)
        if not git_exe:
            self.root.after(0, lambda: messagebox.showwarning(
                "跳过同步", "未找到本工具安装的 git.exe,本次跳过同步。"))
            self.root.after(0, self._reset_sync_buttons)
            return
        results = []
        synced_any = False
        try:
            self.root.after(0, lambda: self.progress.configure(
                maximum=max(len(names), 1)))
            self.root.after(0, lambda: self.progress.configure(value=0))
            for i, name in enumerate(names):
                target = win_path(os.path.join(code_dir, name))
                self.set_repo_status(name, "检查中...", "blue")
                if not os.path.isdir(os.path.join(target, ".git")):
                    self.log("%s 尚未拉取(%s 不存在 .git),跳过同步。"
                             % (name, target))
                    self.set_repo_status(name, "未拉取,跳过", "gray")
                    results.append((name, "未拉取,跳过"))
                    self.root.after(0, lambda v=i + 1: self.progress.configure(
                        value=v))
                    continue
                self.set_repo_status(name, "同步中...", "blue")
                ok = self.sync_repo(git_exe, target, name)
                if ok:
                    synced_any = True
                    self.set_repo_status(name, "已同步 " + SYNC_BRANCH, "green")
                    results.append((name, "已同步 " + SYNC_BRANCH))
                else:
                    self.log("%s 同步失败,请查看 PowerShell 窗口中的报错。"
                             % name)
                    self.set_repo_status(name, "同步失败", "red")
                    results.append((name, "同步失败"))
                self.root.after(0, lambda v=i + 1: self.progress.configure(
                    value=v))
        except Exception as e:
            self.log("同步出错: %s" % e)
            self.root.after(0, lambda: messagebox.showerror("同步失败", str(e)))
        finally:
            # 至少有一个仓库同步成功才记录位置(供误改路径时提示)
            if synced_any:
                self.mark_success(self.install_base)
            self.root.after(0, lambda: self._report_sync(results, code_dir))

    def _report_sync(self, results, code_dir):
        lines = ["%s  ——  %s" % (n, s) for n, s in results]
        failed = [n for n, s in results if s == "同步失败"]
        code_dir = win_path(code_dir)
        msg = ("同步最新代码完成(分支 %s):\n\n" % SYNC_BRANCH
               + "\n".join(lines) + "\n\n代码位置: " + code_dir
               + "\n\n" + self.repo_info_text())
        if failed:
            msg += "\n\n同步失败的仓库可稍后点击\"同步最新代码\"按钮重试。"
            messagebox.showwarning("部分失败", msg)
        else:
            messagebox.showinfo("同步完成", msg)
        self._reset_sync_buttons()

    def repo_info_text(self):
        """把每个仓库的当前分支与最近同步时间拼成多行文字(供提示框显示)。"""
        lines = []
        for url in REPOS:
            name = repo_name(url)
            item = self.repo_info().get(name)
            item = item if isinstance(item, dict) else {}
            branch = str(item.get("branch") or "").strip() or "未知"
            sync_time = str(item.get("sync_time") or "").strip() or "未同步"
            lines.append("%s    分支: %s    最近同步: %s"
                         % (name, branch, sync_time))
        return "\n".join(lines)

    def repo_sync_rows(self, parent):
        """在提示窗口中按仓库逐行列出"分支 / 最近一次同步时间"
        (用于找不到代码目录等场景: 各仓库的同步时间分别展示,便于判断
        哪个仓库需要重新拉取或同步)。"""
        saved = win_path(self.config.get(CONFIG_KEY_BASE) or "")
        for url in REPOS:
            name = repo_name(url)
            item = self.repo_info().get(name)
            item = item if isinstance(item, dict) else {}
            branch = str(item.get("branch") or "").strip() or "未知"
            sync_time = str(item.get("sync_time") or "").strip() or "未同步"
            row = ttk.Frame(parent)
            row.pack(fill="x", pady=1)
            ttk.Label(row, text=name, width=8,
                      font=("Microsoft YaHei UI", 10, "bold")).pack(side="left")
            ttk.Label(row, text="分支: %s" % branch, width=18,
                      font=("Consolas", 10)).pack(side="left")
            ttk.Label(row, text="最近同步: %s" % sync_time,
                      font=("Consolas", 10)).pack(side="left")
            if saved:
                repo_dir = win_path(os.path.join(saved, CODE_FOLDER, name))
                if not os.path.isdir(os.path.join(repo_dir, ".git")):
                    ttk.Label(row, text="(本地无该仓库)", foreground="gray",
                              font=("Microsoft YaHei UI", 9)).pack(
                        side="left", padx=(6, 0))

    def _reset_sync_buttons(self):
        """同步结束后恢复按钮可用状态; "开始安装"按钮保持点击前的文字。"""
        self.unlock_ui()
        self.btn.configure(
            text=getattr(self, "_btn_text_before_sync", "开始安装"))
        self.sync_btn.configure(text="同步最新代码")

    def sync_repo(self, git_exe, target, name):
        """在可见的 PowerShell 窗口中把仓库强制同步到远程 SYNC_BRANCH:
        fetch -> checkout -f -B -> reset --hard -> clean -fd,
        同步完成后用 git 校验 HEAD 与 origin/SYNC_BRANCH 一致,一致返回 True;
        同步后刷新界面上的当前分支,并把"最近同步时间"写进配置(重启后仍显示)。"""
        git_exe = git_exe or self.git_exe
        self.git_exe = git_exe
        self.log("同步 %s -> 远程 %s 分支(本地改动会被丢弃)"
                 % (name, SYNC_BRANCH))
        self._add_safe_directory(target)
        script = self.build_sync_script(git_exe, target, name)
        try:
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile",
                 "-ExecutionPolicy", "Bypass", "-Command", script])
            self.log("返回码: %d" % proc.returncode)
            ok = self.verify_synced(git_exe, target, name)
        except Exception as e:
            self.log("启动 PowerShell 失败: %s" % e)
            ok = False
        # 无论成功失败都把当前分支同步到界面(失败时可能已切到别的分支)
        branch = self.refresh_repo_branch(git_exe, target, name)
        if ok:
            when = self.record_synced(name, branch or SYNC_BRANCH)
            self.log("%s 同步完成,已记录同步时间: %s" % (name, when))
        return ok

    def git_output(self, git_exe, target, args, timeout=60):
        """在指定仓库目录执行 git 命令并返回 stdout(失败返回空字符串)。"""
        cmd = [git_exe, "-c", "safe.directory=*", "-C", target] + list(args)
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            self.log("执行 git %s 失败: %s" % (" ".join(args), e))
            return ""
        if proc.returncode != 0:
            err = (proc.stderr or "").strip()
            if err:
                self.log("git %s 错误: %s" % (" ".join(args), err))
            return ""
        return (proc.stdout or "").strip()

    def verify_synced(self, git_exe, target, name):
        """校验仓库当前分支为 SYNC_BRANCH 且 HEAD 与 origin/SYNC_BRANCH 相同。"""
        branch = self.git_output(git_exe, target,
                                 ["rev-parse", "--abbrev-ref", "HEAD"])
        head = self.git_output(git_exe, target, ["rev-parse", "HEAD"])
        remote = self.git_output(git_exe, target,
                                 ["rev-parse", "origin/" + SYNC_BRANCH])
        if branch == SYNC_BRANCH and head and head == remote:
            self.log("%s 已与远程 %s 一致,当前提交: %s"
                     % (name, SYNC_BRANCH, head[:8]))
            return True
        self.log("%s 校验未通过(当前分支: %s, 本地: %s, 远程: %s)"
                 % (name, branch or "未知", (head or "未知")[:8],
                    (remote or "未知")[:8]))
        return False

    def build_sync_script(self, git_exe, target, name):
        """生成单个仓库的 PowerShell 同步脚本(在可见窗口中运行):
             git fetch --prune origin '+refs/heads/patch_8.0:refs/remotes/origin/patch_8.0'
             git checkout -f -B patch_8.0 origin/patch_8.0
             git branch --set-upstream-to=origin/patch_8.0 patch_8.0
             git reset --hard origin/patch_8.0
             git clean -fd
        * 仓库地址已带内置账号密码(克隆时写入 .git/config),fetch 自动认证;
        * -c credential.helper= 与 GIT_TERMINAL_PROMPT=0 让认证失败时直接
          报错退出,不弹凭据输入窗口;
        * 强制与远程一致: 本地未提交的改动/多余文件会被丢弃
          (被 .gitignore 忽略的文件保留)。"""
        return (
            "try {{ $host.UI.RawUI.WindowTitle = {title} }} catch {{ }}; "
            "Set-Location -LiteralPath {target}; "
            "Write-Host '===== 同步 {name} 到远程 {branch} 分支 =====' "
            "-ForegroundColor Cyan; "
            "Write-Host '本地未提交的改动将会被丢弃,强制与远程保持一致' "
            "-ForegroundColor Yellow; "
            "$env:GIT_TERMINAL_PROMPT = '0'; "
            "& {git} -c credential.helper= fetch --prune origin "
            "'+refs/heads/{branch}:refs/remotes/origin/{branch}'; "
            "$ec = if ($null -ne $LASTEXITCODE) {{ $LASTEXITCODE }} else {{ -1 }}; "
            "if ($ec -eq 0) {{ "
            "& {git} checkout -f -B {branch} origin/{branch}; "
            "$ec = if ($null -ne $LASTEXITCODE) {{ $LASTEXITCODE }} else {{ -1 }} }}; "
            "if ($ec -eq 0) {{ "
            "& {git} branch --set-upstream-to=origin/{branch} {branch} "
            "2>$null | Out-Null }}; "
            "if ($ec -eq 0) {{ "
            "& {git} reset --hard origin/{branch}; "
            "$ec = if ($null -ne $LASTEXITCODE) {{ $LASTEXITCODE }} else {{ -1 }} }}; "
            "if ($ec -eq 0) {{ "
            "& {git} clean -fd; "
            "$ec = if ($null -ne $LASTEXITCODE) {{ $LASTEXITCODE }} else {{ -1 }} }}; "
            "& {git} --no-pager log -1 --oneline; "
            "if ($ec -eq 0) {{ "
            "Write-Host '{name} 已同步到远程 {branch} 分支' -ForegroundColor Green }} "
            "else {{ "
            "Write-Host ('{name} 同步失败, 返回码: ' + $ec) "
            "-ForegroundColor Red; "
            "Read-Host '按回车键关闭此窗口' }}; "
            "exit $ec"
        ).format(title=ps_quote("一键安装工具 - 同步 " + name),
                 name=name, branch=SYNC_BRANCH,
                 git=ps_quote(git_exe), target=ps_quote(target))


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
