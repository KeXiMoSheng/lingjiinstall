@echo off
chcp 65001 >nul
echo ========================================
echo  打包一键安装工具(需要已安装 Python)
echo ========================================

REM 1. 安装 PyInstaller
python -m pip install pyinstaller
if errorlevel 1 goto :fail

REM 清理旧的打包产物,避免旧 spec/缓存残留导致安装包未嵌入
del /q 一键安装工具.spec 2>nul
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

REM 2. 打包:把四个安装包嵌入到一个 exe 中,带管理员权限清单,无控制台窗口
python -m PyInstaller --onefile --noconsole --uac-admin --noconfirm --name 一键安装工具 ^
    --add-data "Git-2.54.0-64-bit.exe;." ^
    --add-data "TortoiseGit-2.18.0.1-64bit.msi;." ^
    --add-data "VC_redist.x64.exe;." ^
    --add-data "LingeeSetup_ia32_1.0.0_2608241831.exe;." ^
    一键安装工具.py
if errorlevel 1 goto :fail

echo.
echo ========================================
echo  打包成功! 生成的文件位于:
echo    dist\一键安装工具.exe
echo  把这一个 exe 发给用户,双击即可安装。
echo ========================================
pause
exit /b 0

:fail
echo.
echo 打包失败,请检查上方错误信息。
pause
exit /b 1
