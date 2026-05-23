#!/bin/bash
# 知乎自动发布 - Linux/Mac 定时任务脚本
#
# 使用方法：
#   1. 修改下面的路径为你的实际路径
#   2. 添加到 crontab：
#      crontab -e
#      # 每天 08:00、12:30、20:00 运行
#      0 8 * * * /path/to/run_scheduler.sh
#      30 12 * * * /path/to/run_scheduler.sh
#      0 20 * * * /path/to/run_scheduler.sh

# ========== 配置区域 ==========
# Python 解释器路径
PYTHON_PATH="/usr/bin/python3"

# 项目根目录
PROJECT_DIR="/path/to/zhihu-daily-task"

# 日志文件
LOG_DIR="$PROJECT_DIR/logs"
TASK_LOG="$LOG_DIR/task_scheduler.log"
# ==============================

# 创建日志目录
mkdir -p "$LOG_DIR"

# 记录启动时间
echo "==========================================" >> "$TASK_LOG"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 计划任务启动" >> "$TASK_LOG"
echo "==========================================" >> "$TASK_LOG"

# 切换到项目目录
cd "$PROJECT_DIR" || exit 1

# 加载环境变量（如果使用 .env 文件）
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 运行调度器
"$PYTHON_PATH" scheduler.py --now --headless >> "$TASK_LOG" 2>&1

# 记录结束时间
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 计划任务结束" >> "$TASK_LOG"
echo "" >> "$TASK_LOG"

exit 0
