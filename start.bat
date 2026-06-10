@echo off
echo 启动 PhotoLib...
echo.

:: 启动后端
start "PhotoLib Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

:: 等待后端就绪
timeout /t 3 /nobreak > nul

:: 启动前端开发服务器
start "PhotoLib Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo 后端: http://localhost:8000
echo 前端: http://localhost:3000
echo.
echo 浏览器打开 http://localhost:3000 即可使用
pause
