# Windows 计划任务配置指南

## 方法一：使用图形界面

### 1. 打开任务计划程序
- 按 `Win + R`，输入 `taskschd.msc`，回车

### 2. 创建基本任务
1. 点击右侧"创建基本任务"
2. 名称：`知乎自动发布-早上`
3. 描述：`每天早上8点自动发布知乎内容`

### 3. 触发器设置
1. 选择"每天"
2. 开始时间：`08:00:00`
3. 每隔：`1` 天

### 4. 操作设置
1. 选择"启动程序"
2. 程序或脚本：`E:\zhihu-daily-task\run_scheduler.bat`
3. 起始于：`E:\zhihu-daily-task`

### 5. 高级设置
- ✅ 勾选"如果过了计划开始时间，立即启动任务"
- ✅ 勾选"如果任务失败，按以下方式重新启动"，间隔 `10 分钟`，尝试 `3` 次

### 6. 重复以上步骤创建其他时段任务
- `知乎自动发布-中午`：12:30
- `知乎自动发布-晚上`：20:00

---

## 方法二：使用命令行（推荐）

以管理员身份运行 PowerShell，执行以下命令：

```powershell
# 早上 8:00
schtasks /create /tn "知乎自动发布-早上" /tr "E:\zhihu-daily-task\run_scheduler.bat" /sc daily /st 08:00 /f

# 中午 12:30
schtasks /create /tn "知乎自动发布-中午" /tr "E:\zhihu-daily-task\run_scheduler.bat" /sc daily /st 12:30 /f

# 晚上 20:00
schtasks /create /tn "知乎自动发布-晚上" /tr "E:\zhihu-daily-task\run_scheduler.bat" /sc daily /st 20:00 /f
```

---

## 查看和管理任务

### 查看任务列表
```powershell
schtasks /query /tn "知乎自动发布*"
```

### 手动运行任务（测试）
```powershell
schtasks /run /tn "知乎自动发布-早上"
```

### 删除任务
```powershell
schtasks /delete /tn "知乎自动发布-早上" /f
```

### 禁用/启用任务
```powershell
# 禁用
schtasks /change /tn "知乎自动发布-早上" /disable

# 启用
schtasks /change /tn "知乎自动发布-早上" /enable
```

---

## 注意事项

1. **确保路径正确**：修改 `run_scheduler.bat` 中的路径为你的实际路径

2. **测试脚本**：先手动运行 `run_scheduler.bat`，确保没有错误

3. **检查日志**：任务运行后查看 `logs/task_scheduler.log` 确认执行情况

4. **权限问题**：如果遇到权限问题，在任务属性中勾选"使用最高权限运行"

5. **电脑需要开机**：计划任务只在电脑开机时运行，如果关机会错过

6. **避免冲突**：不要在同一时间配置多个任务

---

## 故障排查

### 任务没有运行
1. 检查任务是否启用：`schtasks /query /tn "知乎自动发布-早上"`
2. 查看任务历史记录：任务计划程序 → 选中任务 → 历史记录
3. 检查日志文件：`logs/task_scheduler.log`

### 任务运行但失败
1. 手动运行 `run_scheduler.bat`，查看错误信息
2. 检查 Python 环境是否正确
3. 检查 `.env` 文件中的 API Key 是否有效
4. 检查知乎登录状态：`python scripts/check_login.py`

### 触发风控
- 系统会自动暂停 24 小时
- 查看状态：`python scheduler.py --stats`
- 暂停期过后会自动恢复
