# 知乎自动发布系统 - 部署检查清单

## ✅ 安装和配置检查

### 1. 环境准备
- [ ] Python 3.8+ 已安装
- [ ] pip 可用
- [ ] 网络连接正常

### 2. 依赖安装
```bash
pip install -r requirements.txt
python -m playwright install chromium
```
- [ ] playwright 已安装
- [ ] requests 已安装
- [ ] pyyaml 已安装
- [ ] chromium 浏览器已安装

### 3. 环境变量配置
```bash
cp .env.example .env
# 编辑 .env 文件
```
- [ ] `.env` 文件已创建
- [ ] `MOONSHOT_API_KEY` 已填写
- [ ] API Key 有效（可以调用）

### 4. 知乎登录
```bash
python scripts/check_login.py
```
- [ ] 成功扫码登录
- [ ] `cookies/zhihu.json` 已生成
- [ ] 登录态有效

### 5. 配置文件
- [ ] `config/topics.yaml` 存在
- [ ] 话题池已配置（至少 5 个话题）
- [ ] 发布时段已设置
- [ ] 发布策略已配置

---

## 🧪 功能测试检查

### 1. 系统测试
```bash
python test_publisher.py
```
- [ ] 浏览器启动成功
- [ ] 登录状态正常
- [ ] 无风控异常
- [ ] 搜索功能可用

### 2. 内容生成测试
```bash
python scripts/content_generator.py
```
- [ ] API 调用成功
- [ ] 内容生成正常
- [ ] 文件保存成功
- [ ] 日志记录正常

### 3. 调度器测试
```bash
python scheduler.py --stats
python scheduler.py --history
```
- [ ] 统计信息显示正常
- [ ] 历史记录功能正常
- [ ] 无编码错误

### 4. 手动发布测试（可选）
```bash
python scheduler.py --now
```
- [ ] 话题选择成功
- [ ] 内容生成成功
- [ ] 发布流程正常
- [ ] 历史记录已更新

---

## ⏰ 定时任务配置检查

### Windows 系统

#### 方法一：PowerShell 命令
```powershell
schtasks /create /tn "知乎自动发布-早上" /tr "E:\zhihu-daily-task\run_scheduler.bat" /sc daily /st 08:00 /f
```
- [ ] 任务创建成功
- [ ] 路径正确
- [ ] 时间设置正确

#### 方法二：图形界面
- [ ] 打开任务计划程序
- [ ] 创建基本任务
- [ ] 设置触发器
- [ ] 设置操作
- [ ] 测试运行

#### 验证
```powershell
schtasks /query /tn "知乎自动发布*"
schtasks /run /tn "知乎自动发布-早上"
```
- [ ] 任务列表显示正常
- [ ] 手动运行成功
- [ ] 日志文件生成

### Linux/Mac 系统

#### 配置 Cron
```bash
chmod +x run_scheduler.sh
crontab -e
# 添加：0 8 * * * /path/to/run_scheduler.sh
```
- [ ] 脚本有执行权限
- [ ] Cron 任务已添加
- [ ] 路径正确

#### 验证
```bash
crontab -l
./run_scheduler.sh  # 手动测试
```
- [ ] Cron 列表显示正常
- [ ] 手动运行成功
- [ ] 日志文件生成

---

## 📊 监控和维护检查

### 1. 日志文件
- [ ] `logs/scheduler.log` 正常写入
- [ ] `logs/publisher.log` 正常写入
- [ ] `logs/task_scheduler.log` 正常写入
- [ ] 日志内容可读（无乱码）

### 2. 数据文件
- [ ] `data/published_history.json` 格式正确
- [ ] 发布记录完整
- [ ] 统计数据准确

### 3. 定期检查项
- [ ] 每周查看日志
- [ ] 每周查看统计：`python scheduler.py --stats`
- [ ] 每月更新话题池
- [ ] 每月检查登录态

---

## 🛡️ 安全检查

### 1. 敏感信息保护
- [ ] `.env` 文件已加入 `.gitignore`
- [ ] `cookies/` 目录已加入 `.gitignore`
- [ ] API Key 未泄露
- [ ] Cookie 文件权限正确

### 2. 风控设置
- [ ] `pause_on_captcha` 已启用
- [ ] `pause_duration` 设置合理（建议 24 小时）
- [ ] `max_daily_posts` 设置合理（建议 2-3 次）
- [ ] 随机延迟设置合理（30-300 秒）

### 3. 发布频率
- [ ] 每天不超过 3 次
- [ ] 间隔至少 4 小时
- [ ] 避免深夜发布（23:00-06:00）

---

## 🔧 故障排查检查

### 1. 常见问题自查

**问题：任务没有运行**
- [ ] 计划任务已启用
- [ ] 电脑已开机
- [ ] 查看 `logs/task_scheduler.log`
- [ ] 手动运行测试

**问题：发布失败**
- [ ] 登录态有效：`python scripts/check_login.py`
- [ ] API Key 正确
- [ ] 查看 `logs/publisher.log`
- [ ] 运行 `python test_publisher.py`

**问题：触发风控**
- [ ] 查看暂停状态：`python scheduler.py --stats`
- [ ] 等待暂停期结束
- [ ] 调整发布频率
- [ ] 增加随机延迟

**问题：页面元素找不到**
- [ ] 运行 `python test_publisher.py`
- [ ] 检查知乎页面是否变化
- [ ] 更新 `scripts/publisher.py` 选择器
- [ ] 查看项目更新

### 2. 日志检查
```bash
# 查看最近的错误
tail -50 logs/scheduler.log | grep -i error
tail -50 logs/publisher.log | grep -i error

# 查看最近的发布记录
tail -20 logs/scheduler.log
```
- [ ] 无严重错误
- [ ] 发布成功率 > 80%
- [ ] 无频繁风控

---

## 📝 文档检查

### 1. 必读文档
- [ ] README.md - 项目概述
- [ ] docs/USER_GUIDE.md - 使用指南
- [ ] docs/WINDOWS_TASK_SETUP.md - Windows 配置
- [ ] docs/LINUX_CRON_SETUP.md - Linux 配置
- [ ] CHANGELOG.md - 更新日志
- [ ] PROJECT_SUMMARY.md - 项目总结

### 2. 快速参考
```bash
# 测试系统
python test_publisher.py

# 查看统计
python scheduler.py --stats

# 查看历史
python scheduler.py --history

# 手动发布
python scheduler.py --now

# 刷新登录
python scripts/check_login.py
```

---

## ✅ 最终检查清单

### 部署前
- [ ] 所有依赖已安装
- [ ] 环境变量已配置
- [ ] 知乎已登录
- [ ] 配置文件已设置
- [ ] 系统测试通过

### 部署后
- [ ] 定时任务已配置
- [ ] 手动运行测试成功
- [ ] 日志文件正常
- [ ] 监控机制就绪

### 运行中
- [ ] 定期查看日志
- [ ] 关注发布成功率
- [ ] 及时处理风控
- [ ] 定期更新话题

---

## 🎯 成功标准

### 短期（1 周内）
- [ ] 至少成功发布 5 篇内容
- [ ] 发布成功率 > 80%
- [ ] 无严重错误
- [ ] 未触发风控

### 中期（1 个月内）
- [ ] 累计发布 30+ 篇内容
- [ ] 发布成功率 > 90%
- [ ] 定时任务稳定运行
- [ ] 风控触发 < 2 次

### 长期（3 个月内）
- [ ] 累计发布 100+ 篇内容
- [ ] 发布成功率 > 95%
- [ ] 系统稳定运行
- [ ] 内容质量良好

---

## 📞 获取帮助

### 问题排查顺序
1. 查看日志文件
2. 运行测试脚本
3. 查看文档
4. 搜索常见问题
5. 提交 Issue

### 有用的命令
```bash
# 完整测试流程
python test_publisher.py
python scheduler.py --stats
python scheduler.py --now
python scheduler.py --history

# 维护命令
python scripts/check_login.py
python scripts/topic_manager.py list
tail -f logs/scheduler.log
```

---

**检查完成日期：** ___________

**检查人员：** ___________

**备注：** ___________
