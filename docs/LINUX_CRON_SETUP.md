# Linux/Mac Cron 配置指南

## 快速开始

### 1. 修改脚本路径
编辑 `run_scheduler.sh`，修改以下变量：

```bash
PYTHON_PATH="/usr/bin/python3"  # Python 路径
PROJECT_DIR="/path/to/zhihu-daily-task"  # 项目路径
```

### 2. 添加执行权限
```bash
chmod +x run_scheduler.sh
```

### 3. 测试脚本
```bash
./run_scheduler.sh
```

检查 `logs/task_scheduler.log` 确认运行正常。

---

## 配置 Cron 定时任务

### 编辑 crontab
```bash
crontab -e
```

### 添加定时任务
```bash
# 知乎自动发布 - 每天 08:00、12:30、20:00
0 8 * * * /path/to/zhihu-daily-task/run_scheduler.sh
30 12 * * * /path/to/zhihu-daily-task/run_scheduler.sh
0 20 * * * /path/to/zhihu-daily-task/run_scheduler.sh
```

**注意**：将 `/path/to/zhihu-daily-task` 替换为实际路径。

### Cron 时间格式说明
```
* * * * * 命令
│ │ │ │ │
│ │ │ │ └─ 星期几 (0-7, 0和7都表示周日)
│ │ │ └─── 月份 (1-12)
│ │ └───── 日期 (1-31)
│ └─────── 小时 (0-23)
└───────── 分钟 (0-59)
```

### 常用示例
```bash
# 每天早上 8 点
0 8 * * * /path/to/script.sh

# 每天中午 12:30
30 12 * * * /path/to/script.sh

# 每周一到周五早上 9 点
0 9 * * 1-5 /path/to/script.sh

# 每 2 小时执行一次
0 */2 * * * /path/to/script.sh

# 每天晚上 8 点到 11 点，每小时执行一次
0 20-23 * * * /path/to/script.sh
```

---

## 管理 Cron 任务

### 查看当前任务
```bash
crontab -l
```

### 删除所有任务
```bash
crontab -r
```

### 编辑任务
```bash
crontab -e
```

### 查看 Cron 日志
```bash
# Ubuntu/Debian
grep CRON /var/log/syslog

# CentOS/RHEL
grep CRON /var/log/cron

# macOS
log show --predicate 'process == "cron"' --last 1h
```

---

## 使用 systemd timer（推荐，适用于现代 Linux）

### 1. 创建服务文件
创建 `/etc/systemd/system/zhihu-publisher.service`：

```ini
[Unit]
Description=Zhihu Auto Publisher
After=network.target

[Service]
Type=oneshot
User=your_username
WorkingDirectory=/path/to/zhihu-daily-task
Environment="MOONSHOT_API_KEY=your_api_key"
ExecStart=/usr/bin/python3 /path/to/zhihu-daily-task/scheduler.py --now --headless
StandardOutput=append:/path/to/zhihu-daily-task/logs/systemd.log
StandardError=append:/path/to/zhihu-daily-task/logs/systemd.log

[Install]
WantedBy=multi-user.target
```

### 2. 创建定时器文件
创建 `/etc/systemd/system/zhihu-publisher.timer`：

```ini
[Unit]
Description=Zhihu Auto Publisher Timer
Requires=zhihu-publisher.service

[Timer]
# 每天 08:00
OnCalendar=*-*-* 08:00:00
# 每天 12:30
OnCalendar=*-*-* 12:30:00
# 每天 20:00
OnCalendar=*-*-* 20:00:00

Persistent=true

[Install]
WantedBy=timers.target
```

### 3. 启用并启动定时器
```bash
sudo systemctl daemon-reload
sudo systemctl enable zhihu-publisher.timer
sudo systemctl start zhihu-publisher.timer
```

### 4. 管理定时器
```bash
# 查看状态
sudo systemctl status zhihu-publisher.timer

# 查看下次运行时间
sudo systemctl list-timers zhihu-publisher.timer

# 手动触发一次
sudo systemctl start zhihu-publisher.service

# 查看日志
sudo journalctl -u zhihu-publisher.service -f

# 停止定时器
sudo systemctl stop zhihu-publisher.timer

# 禁用定时器
sudo systemctl disable zhihu-publisher.timer
```

---

## 注意事项

### 1. 环境变量
Cron 运行时的环境变量与交互式 shell 不同，需要在脚本中显式设置：

```bash
# 在 run_scheduler.sh 中添加
export PATH=/usr/local/bin:/usr/bin:/bin
export MOONSHOT_API_KEY="your_api_key"
```

或者在 crontab 顶部设置：
```bash
PATH=/usr/local/bin:/usr/bin:/bin
MOONSHOT_API_KEY=your_api_key

0 8 * * * /path/to/run_scheduler.sh
```

### 2. 日志重定向
如果需要将输出保存到文件：
```bash
0 8 * * * /path/to/run_scheduler.sh >> /path/to/cron.log 2>&1
```

### 3. 邮件通知
Cron 默认会将输出发送到用户邮箱，如果不需要：
```bash
0 8 * * * /path/to/run_scheduler.sh > /dev/null 2>&1
```

### 4. 时区问题
确保系统时区正确：
```bash
# 查看时区
timedatectl

# 设置时区（例如上海）
sudo timedatectl set-timezone Asia/Shanghai
```

---

## 故障排查

### Cron 任务没有运行
1. 检查 cron 服务是否运行：
   ```bash
   sudo systemctl status cron  # Ubuntu/Debian
   sudo systemctl status crond  # CentOS/RHEL
   ```

2. 检查脚本权限：
   ```bash
   ls -l run_scheduler.sh
   # 应该有执行权限 (-rwxr-xr-x)
   ```

3. 检查脚本路径是否正确（使用绝对路径）

4. 查看系统日志：
   ```bash
   grep CRON /var/log/syslog | tail -20
   ```

### 任务运行但失败
1. 手动运行脚本测试：
   ```bash
   ./run_scheduler.sh
   ```

2. 检查日志文件：
   ```bash
   tail -f logs/task_scheduler.log
   ```

3. 检查 Python 环境：
   ```bash
   which python3
   python3 --version
   ```

4. 检查环境变量是否正确加载

---

## macOS 特殊说明

macOS 从 Catalina 开始推荐使用 `launchd` 代替 cron。

### 创建 launchd plist 文件
创建 `~/Library/LaunchAgents/com.zhihu.publisher.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.zhihu.publisher</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/run_scheduler.sh</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Hour</key>
            <integer>8</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <dict>
            <key>Hour</key>
            <integer>12</integer>
            <key>Minute</key>
            <integer>30</integer>
        </dict>
        <dict>
            <key>Hour</key>
            <integer>20</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
    </array>
    
    <key>StandardOutPath</key>
    <string>/path/to/zhihu-daily-task/logs/launchd.log</string>
    
    <key>StandardErrorPath</key>
    <string>/path/to/zhihu-daily-task/logs/launchd_error.log</string>
</dict>
</plist>
```

### 加载和管理
```bash
# 加载
launchctl load ~/Library/LaunchAgents/com.zhihu.publisher.plist

# 卸载
launchctl unload ~/Library/LaunchAgents/com.zhihu.publisher.plist

# 查看状态
launchctl list | grep zhihu

# 手动运行
launchctl start com.zhihu.publisher
```
