# 知乎每日任务自动化

人文艺术垂直领域的知乎内容自动化工具，支持自动生成内容并发布到知乎。

## ✨ 核心功能

- 🤖 **智能内容生成**：使用 Moonshot AI 生成高质量人文艺术类文章
- 📝 **多种发布类型**：支持回答问题、发想法、写文章
- ⏰ **定时自动发布**：配置时段自动运行，无需人工干预
- 🛡️ **风控检测**：自动识别验证码和异常，触发后暂停 24 小时
- 🎭 **真人模拟**：随机延迟、滚动页面，模拟真实用户行为
- 📊 **发布历史**：记录所有发布记录和统计数据

## 目录结构

```
zhihu-daily-task/
├── config/                      # 配置文件
│   └── topics.yaml              # 话题池和发布配置
├── data/                        # 数据文件
│   └── published_history.json   # 发布历史记录
├── docs/                        # 文档
│   ├── WINDOWS_TASK_SETUP.md    # Windows 计划任务配置
│   └── LINUX_CRON_SETUP.md      # Linux/Mac Cron 配置
├── prompts/                     # 提示词模板
│   └── article_template.txt
├── scripts/                     # 自动化脚本
│   ├── check_login.py           # 登录检查
│   ├── topic_manager.py         # 选题管理
│   ├── content_generator.py     # 内容生成
│   ├── publisher.py             # 知乎发布器
│   └── env_loader.py            # 环境变量加载
├── cookies/                     # 登录态（已加入 .gitignore）
├── logs/                        # 运行日志（已加入 .gitignore）
├── outputs/                     # 生成的文章（已加入 .gitignore）
├── scheduler.py                 # 自动发布调度器
├── run_scheduler.bat            # Windows 启动脚本
├── run_scheduler.sh             # Linux/Mac 启动脚本
├── topic_pool.json              # 旧版选题池（兼容）
├── requirements.txt
├── .env.example                 # 环境变量示例
└── setup_env.py                 # 一键装依赖
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的 API Key：

```bash
cp .env.example .env
# 编辑 .env 文件，填入 MOONSHOT_API_KEY
```

或者直接设置环境变量：

```bash
# Windows
set MOONSHOT_API_KEY=your_api_key_here

# Linux/Mac
export MOONSHOT_API_KEY=your_api_key_here
```

### 3. 登录知乎

首次运行会弹出浏览器扫码：

```bash
python scripts/check_login.py
```

登录成功后 cookie 会保存到 `cookies/zhihu.json`，下次运行自动复用。

### 4. 初始化话题池

预置了 20 个人文艺术类话题：

```bash
python scripts/topic_manager.py init
```

### 5. 生成内容

随机选择话题并生成文章：

```bash
python scripts/topic_manager.py pick    # 查看随机选中的话题
python scripts/content_generator.py     # 生成文章
```

或指定话题生成：

```bash
python scripts/content_generator.py "如何理解王国维《人间词话》中的'境界'说？"
```

生成的文章保存在 `outputs/` 目录。

---

## 🚀 自动发布功能

### 立即发布测试

```bash
# 生成内容并立即发布（有头模式，可以看到浏览器操作）
python scheduler.py --now

# 无头模式发布（后台运行）
python scheduler.py --now --headless
```

### 查看发布状态

```bash
# 查看发布历史
python scheduler.py --history

# 查看统计信息
python scheduler.py --stats
```

### 配置定时任务

#### Windows 系统

1. 修改 `run_scheduler.bat` 中的路径
2. 按照 [Windows 计划任务配置指南](docs/WINDOWS_TASK_SETUP.md) 设置定时任务
3. 推荐时段：08:00、12:30、20:00

快速配置（管理员 PowerShell）：

```powershell
# 早上 8:00
schtasks /create /tn "知乎自动发布-早上" /tr "E:\zhihu-daily-task\run_scheduler.bat" /sc daily /st 08:00 /f

# 中午 12:30
schtasks /create /tn "知乎自动发布-中午" /tr "E:\zhihu-daily-task\run_scheduler.bat" /sc daily /st 12:30 /f

# 晚上 20:00
schtasks /create /tn "知乎自动发布-晚上" /tr "E:\zhihu-daily-task\run_scheduler.bat" /sc daily /st 20:00 /f
```

#### Linux/Mac 系统

1. 修改 `run_scheduler.sh` 中的路径
2. 添加执行权限：`chmod +x run_scheduler.sh`
3. 按照 [Linux Cron 配置指南](docs/LINUX_CRON_SETUP.md) 设置 cron 任务

快速配置：

```bash
crontab -e

# 添加以下行
0 8 * * * /path/to/zhihu-daily-task/run_scheduler.sh
30 12 * * * /path/to/zhihu-daily-task/run_scheduler.sh
0 20 * * * /path/to/zhihu-daily-task/run_scheduler.sh
```

### 发布配置

编辑 `config/topics.yaml` 自定义：

- **话题池**：添加/修改话题，设置发布类型（answer/idea/article）
- **发布时段**：修改 `schedule` 部分
- **延迟设置**：调整 `random_delay_min/max`（模拟真人）
- **风控设置**：配置暂停时长、每日最大发布数

### 风控保护

系统会自动检测：
- ✅ 验证码（网易易盾、极验等）
- ✅ 风控提示（操作频繁、账号异常等）
- ✅ 触发后自动暂停 24 小时
- ✅ 暂停期过后自动恢复

---

## 选题管理

话题池侧重人文艺术垂直领域，不追逐时效性热点。

```bash
# 查看所有话题
python scripts/topic_manager.py list

# 随机选择话题
python scripts/topic_manager.py pick

# 手动添加话题
python scripts/topic_manager.py add "话题标题" "分类" "描述"

# 清空话题池
python scripts/topic_manager.py clear
```

## 自定义提示词

编辑 `prompts/article_template.txt` 来自定义文章生成的提示词模板。

## 备注

- 话题池初始包含 20 个人文艺术类话题
- 生成的文章以 Markdown 格式保存在 `outputs/` 目录
- 日志统一写到 `logs/` 下
- 发布历史记录在 `data/published_history.json`

---

## 📚 文档

- [用户使用指南](docs/USER_GUIDE.md) - 完整的使用说明和最佳实践
- [Windows 计划任务配置](docs/WINDOWS_TASK_SETUP.md) - Windows 定时任务详细配置
- [Linux Cron 配置](docs/LINUX_CRON_SETUP.md) - Linux/Mac 定时任务详细配置

---

## 🔄 工作流程

```
1. 定时触发（或手动运行）
   ↓
2. 检查暂停状态（风控保护）
   ↓
3. 检查今日发布数量
   ↓
4. 从话题池随机选择未发布话题
   ↓
5. 调用 Moonshot API 生成内容
   ↓
6. 随机延迟 30-300 秒（模拟真人）
   ↓
7. 使用 Playwright 自动发布
   ↓
8. 检测验证码/风控（触发则暂停 24 小时）
   ↓
9. 记录发布历史和统计数据
```

---

## 🛡️ 安全特性

- ✅ **智能风控检测** - 自动识别验证码和异常提示
- ✅ **自动暂停机制** - 触发风控后暂停 24 小时
- ✅ **真人行为模拟** - 随机延迟、滚动页面、模拟打字
- ✅ **发布频率限制** - 每日最大发布数可配置
- ✅ **去重机制** - 避免重复发布相同话题
- ✅ **日志记录** - 完整的操作日志便于排查问题

---

## 🎯 使用场景

- 📝 **内容创作者** - 自动化日常内容发布，节省时间
- 🎓 **知识分享** - 定期分享人文艺术领域知识
- 📊 **账号运营** - 保持账号活跃度，提升影响力
- 🤖 **自动化实践** - 学习 Web 自动化和 AI 内容生成

---

## ⚠️ 注意事项

1. **合规使用** - 仅用于个人学习和合法内容发布
2. **内容质量** - 确保生成的内容符合知乎社区规范
3. **频率控制** - 避免过度频繁发布，建议每天 2-3 次
4. **账号安全** - 定期检查登录态，不要在多设备同时登录
5. **风控应对** - 遇到风控及时暂停，不要强行继续
6. **电脑开机** - 计划任务需要电脑开机才能运行

---

## 🔧 高级配置

### 自定义提示词

编辑 `prompts/article_template.txt` 自定义文章生成风格：

```
你是一位资深的人文艺术领域作者...

话题：{topic}

要求：
1. 文章长度：2000-3000字
2. 结构清晰：引言、正文、结语
...
```

### 调整发布策略

编辑 `config/topics.yaml`：

```yaml
settings:
  random_delay_min: 30      # 最小延迟（秒）
  random_delay_max: 300     # 最大延迟（秒）
  pause_duration: 86400     # 风控暂停时长（秒）
  max_daily_posts: 3        # 每日最大发布数
```

### 添加新话题

```bash
# 方法一：编辑 config/topics.yaml
vim config/topics.yaml

# 方法二：使用命令行（旧版兼容）
python scripts/topic_manager.py add "话题标题" "分类" "描述"
```

---

## 📊 监控和统计

```bash
# 查看发布统计
python scheduler.py --stats

# 输出示例：
# 📊 发布统计：
#   总发布数：15
#   成功：14
#   失败：1
#   触发风控次数：0
#   今日已发布：2

# 查看发布历史
python scheduler.py --history

# 输出示例：
# 📜 最近 10 条发布记录：
# 时间                  话题                            类型        状态
# 2026-05-23 08:05:32  如何理解王国维《人间词话》...    answer     ✅ 成功
# 2026-05-23 12:35:18  印象派绘画对现代艺术的影响      article    ✅ 成功
```

---

## 🐛 故障排查

### 常见问题

**Q: 任务没有运行？**
- 检查计划任务是否启用
- 确认电脑已开机
- 查看 `logs/task_scheduler.log`

**Q: 发布失败？**
- 运行 `python test_publisher.py` 测试系统状态
- 检查登录态：`python scripts/check_login.py`
- 查看 `logs/publisher.log` 和 `logs/scheduler.log`

**Q: 触发风控？**
- 系统会自动暂停 24 小时
- 查看状态：`python scheduler.py --stats`
- 暂停期过后自动恢复

**Q: 页面元素找不到？**
- 知乎页面结构可能变化
- 运行 `python test_publisher.py` 查看具体错误
- 修改 `scripts/publisher.py` 中的选择器

详见 [用户使用指南](docs/USER_GUIDE.md)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [Moonshot AI](https://www.moonshot.cn/) - 提供高质量的内容生成 API
- [Playwright](https://playwright.dev/) - 强大的浏览器自动化工具
- 知乎 - 优质的知识分享平台
