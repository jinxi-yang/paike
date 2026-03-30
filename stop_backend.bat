@echo off
echo 正在查找并终止占用 5000 端口的进程（通常是未关闭的 Flask 后端）...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do (
    echo 发现进程 PID: %%a
    taskkill /F /PID %%a 2>nul
)
echo 清理完毕！所有占用 5000 端口的后台应用都已被关闭。
pause
