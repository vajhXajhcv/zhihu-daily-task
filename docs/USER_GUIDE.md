# 知乎自动发布系统使用指南

## 🎯 快速开始

### 1. 测试系统状态

```bash
# 测试登录态和页面元素（Dry-Run，不实际发布）
python test_publisher.py
```

### 2. 查看当前状态

```bash
# 查看发布统计
python scheduler.py --stats

# 查看发布历史
python scheduler.py --history
```

### 3. 手动发布一次（测试）

```bash
# 有头模式（可以看到浏览器操作过程）
python scheduler.py --now

# 无头模式（后台运行）
python scheduler.py --now --headless
```

---

## 📋 系统功能说明

### 自动化流程

1. **选题** - 从 `config/topics.yaml` 随机选择未发布的话题
2. **生成** - 调用 Moonshot API 生成高质量内容
3. **延迟** - 随机延迟 30-300 秒，模拟真人
4. **发布** - 使用 Playwright 自动发布到知乎
5. **记录** - 保存发布历史到 `data/published_history.json`

### 发布类型

- **answer** - 回答问题（自动搜索问题或使用指定 URL）
- **idea** - 发想法（类似朋友圈，内容会自动截取前 500 字）
- **article** - 写文章（完整文章发布）

### 风控保护

系统会自动检测：
- ✅ 验证码（网易易盾、极验等）
- ✅ 风控提示（操作频繁、账号异常等）
- ✅ 触发后自动暂停 24 小时
- ✅ 暂停期过后自动恢复

---

## ⚙️ 配置说明

### 话题池配置 (`config/topics.yaml`)

```yaml
topics:
  - title: "如何理解王国维《人间词话》中的'境界'说？"
    category: "文学理论"
    type: "answer"           # 发布类型：answer/idea/article
    question_id: ""          # 可选，指定问题 URL

  - title: "印象派绘画对现代艺术的影响"
    category: "艺术史"
    type: "article"

# 发布时段配置
schedule:
  - time: "08:00"
    enabled: true
  - time: "12:30"
    enabled: true
  - time: "20:00"
    enabled: true

# 发布设置
settings:
  random_delay_min: 30      # 最小延迟（秒）
  random_delay_max: 300     # 最大延迟（秒）
  pause_on_captcha: true    # 遇到验证码时暂停
  pause_duration: 86400     # 暂停时长（秒，24小时）
  max_daily_posts: 3        # 每日最大发布数
```

### 提示词模板 (`prompts/article_template.txt`)

自定义文章生成的提示词，使用 `{topic}` 作为话题占位符。

---

## 🤖 定时任务配置

### Windows 系统

**方法一：命令行快速配置**

以管理员身份运行 PowerShell：

```powershell
# 早上 8:00
schtasks /create /tn "知乎自动发布-早上" /tr "E:\zhihu-daily-task\run_scheduler.bat" /sc daily /st 08:00 /f

# 中午 12:30
schtasks /create /tn "知乎自动发布-中午" /tr "E:\zhihu-daily-task\run_scheduler.bat" /sc daily /st 12:30 /f

# 晚上 20:00
schtasks /create /tn "知乎自动发布-晚上" /tr "E:\zhihu-daily-task\run_scheduler.bat" /sc daily /st 20:00 /f
```

**方法二：图形界面**

详见 [Windows 计划任务配置指南](WINDOWS_TASK_SETUP.md)

### Linux/Mac 系统

**配置 Cron**

```bash
# 编辑 crontab
crontab -e

# 添加定时任务
0 8 * * * /path/to/zhihu-daily-task/run_scheduler.sh
30 12 * * * /path/to/zhihu-daily-task/run_scheduler.sh
0 20 * * * /path/to/zhihu-daily-task/run_scheduler.sh
```

详见 [Linux Cron 配置指南](LINUX_CRON_SETUP.md)

---

## 📊 监控和管理

### 查看日志

```bash
# 调度器日志
tail -f logs/scheduler.log

# 发布器日志
tail -f logs/publisher.log

# 计划任务日志
tail -f logs/task_scheduler.log
```

### 管理命令

```bash
# 查看统计信息
python scheduler.py --stats

# 查看发布历史（最近 10 条）
python scheduler.py --history

# 手动触发一次发布
python scheduler.py --now

# 测试系统状态（不实际发布）
python test_publisher.py
```

### Windows 计划任务管理

```powershell
# 查看任务
schtasks /query /tn "知乎自动发布*"

# 手动运行
schtasks /run /tn "知乎自动发布-早上"

# 禁用任务
schtasks /change /tn "知乎自动发布-早上" /disable

# 启用任务
schtasks /change /tn "知乎自动发布-早上" /enable

# 删除任务
schtasks /delete /tn "知乎自动发布-早上" /f
```

---

## 🔧 故障排查

### 问题：任务没有运行

**检查项：**
1. 计划任务是否启用
2. 电脑是否开机（计划任务需要电脑开机）
3. 查看 `logs/task_scheduler.log` 确认是否执行
4. 手动运行 `run_scheduler.bat` 测试

### 问题：发布失败

**检查项：**
1. 登录态是否有效：`python scripts/check_login.py`
2. API Key 是否正确：检查 `.env` 文件
3. 查看 `logs/publisher.log` 和 `logs/scheduler.log`
4. 运行 `python test_publisher.py` 测试系统状态

### 问题：触发风控

**处理方式：**
- 系统会自动暂停 24 小时
- 查看状态：`python scheduler.py --stats`
- 暂停期过后会自动恢复
- 如需调整暂停时长，修改 `config/topics.yaml` 中的 `pause_duration`

### 问题：页面元素找不到

**原因：** 知乎页面结构可能变化

**解决方式：**
1. 运行 `python test_publisher.py` 查看具体错误
2. 修改 `scripts/publisher.py` 中的选择器
3. 提交 Issue 或 PR 更新选择器

---

## 📈 最佳实践

### 1. 发布频率

- **推荐**：每天 2-3 次，间隔 4-6 小时
- **避免**：短时间内频繁发布（容易触发风控）
- **建议时段**：早上 8-9 点、中午 12-13 点、晚上 20-21 点

### 2. 内容质量

- 使用高质量的提示词模板
- 定期更新话题池，保持内容新鲜
- 避免重复发布相同话题

### 3. 账号安全

- 定期检查登录态：`python scripts/check_login.py`
- 不要在多个设备同时登录
- 遇到风控及时暂停，不要强行继续

### 4. 监控维护

- 定期查看日志文件
- 关注发布成功率：`python scheduler.py --stats`
- 及时更新话题池和提示词

---

## 🆘 获取帮助

### 日志位置

- `logs/scheduler.log` - 调度器日志
- `logs/publisher.log` - 发布器日志
- `logs/task_scheduler.log` - 计划任务日志
- `logs/content_generator.log` - 内容生成日志

### 常用命令

```bash
# 完整测试流程
python test_publisher.py              # 1. 测试系统状态
python scheduler.py --stats           # 2. 查看统计
python scheduler.py --now             # 3. 手动发布一次
python scheduler.py --history         # 4. 查看发布历史

# 维护命令
python scripts/check_login.py         # 刷新登录态
python scripts/topic_manager.py list  # 查看话题池
```

### 技术支持

- 查看项目 README.md
- 查看详细配置文档（docs/ 目录）
- 提交 Issue 报告问题

---

## 📝 更新日志

### v1.0.0 (2026-05-23)

- ✅ 实现自动内容生成
- ✅ 支持三种发布类型（回答/想法/文章）
- ✅ 智能风控检测和自动暂停
- ✅ 真人模拟（随机延迟、滚动等）
- ✅ 发布历史记录和统计
- ✅ 定时任务支持（Windows/Linux/Mac）
- ✅ Dry-run 测试模式
