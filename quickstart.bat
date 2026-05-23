@echo off
REM 知乎自动发布系统 - 快速开始脚本

echo ==========================================
echo 知乎自动发布系统 - 快速开始
echo ==========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

echo ✅ Python 版本：
python --version
echo.

REM 检查依赖
echo 📦 检查依赖...
python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 未安装 playwright，正在安装...
    pip install -r requirements.txt
    python -m playwright install chromium
)

python -c "import yaml" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 未安装 pyyaml，正在安装...
    pip install pyyaml
)

echo ✅ 依赖检查完成
echo.

REM 检查环境变量
if not exist ".env" (
    echo ⚠️ 未找到 .env 文件
    echo 请复制 .env.example 为 .env 并填入 API Key：
    echo   copy .env.example .env
    echo   notepad .env
    pause
    exit /b 1
)

echo ✅ 环境变量配置存在
echo.

REM 检查登录态
echo 🔐 检查知乎登录状态...
if not exist "cookies\zhihu.json" (
    echo ⚠️ 未找到登录 Cookie，请先登录：
    echo   python scripts\check_login.py
    pause
    exit /b 1
)

echo ✅ 登录状态正常
echo.

REM 运行测试
echo 🧪 运行系统测试...
python test_publisher.py

echo.
echo ==========================================
echo ✅ 快速开始完成！
echo ==========================================
echo.
echo 📝 下一步：
echo   1. 查看统计：python scheduler.py --stats
echo   2. 手动发布：python scheduler.py --now
echo   3. 配置定时任务：参考 docs\WINDOWS_TASK_SETUP.md
echo.
pause
