@echo off
REM 知乎自动发布 - Windows 计划任务启动脚本
REM
REM 使用方法：
REM   1. 修改下面的路径为你的实际路径
REM   2. 在 Windows 计划任务中配置定时运行此脚本
REM   3. 建议配置三个任务，分别在 08:00、12:30、20:00 运行

REM ========== 配置区域 ==========
REM Python 解释器路径（如果 python 在 PATH 中可以直接用 python）
SET PYTHON_PATH=python

REM 项目根目录
SET PROJECT_DIR=E:\zhihu-daily-task

REM 日志文件
SET LOG_DIR=%PROJECT_DIR%\logs
SET TASK_LOG=%LOG_DIR%\task_scheduler.log
REM ==============================

REM 创建日志目录
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM 记录启动时间
echo ========================================== >> "%TASK_LOG%"
echo [%date% %time%] 计划任务启动 >> "%TASK_LOG%"
echo ========================================== >> "%TASK_LOG%"

REM 切换到项目目录
cd /d "%PROJECT_DIR%"

REM 运行调度器
"%PYTHON_PATH%" scheduler.py --now --headless >> "%TASK_LOG%" 2>&1

REM 记录结束时间
echo [%date% %time%] 计划任务结束 >> "%TASK_LOG%"
echo. >> "%TASK_LOG%"

exit /b 0
