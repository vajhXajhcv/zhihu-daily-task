# 更新日志

## [1.0.0] - 2026-05-23

### 新增功能

#### 核心功能
- ✅ 自动内容生成（基于 Moonshot AI）
- ✅ 三种发布类型支持（回答问题、发想法、写文章）
- ✅ 智能话题池管理
- ✅ 自动发布调度器

#### 安全特性
- ✅ 智能风控检测（验证码、异常提示）
- ✅ 自动暂停机制（触发风控后暂停 24 小时）
- ✅ 真人行为模拟（随机延迟、滚动、模拟打字）
- ✅ 发布频率限制（每日最大发布数可配置）
- ✅ 去重机制（避免重复发布）

#### 定时任务
- ✅ Windows 计划任务支持
- ✅ Linux/Mac Cron 支持
- ✅ 多时段配置（早中晚）

#### 监控和管理
- ✅ 发布历史记录
- ✅ 统计数据展示
- ✅ 完整的日志系统
- ✅ Dry-run 测试模式

#### 文档
- ✅ 用户使用指南
- ✅ Windows 计划任务配置指南
- ✅ Linux Cron 配置指南
- ✅ 完整的 README

### 技术栈

- Python 3.8+
- Playwright - 浏览器自动化
- Moonshot AI - 内容生成
- PyYAML - 配置管理

### 文件结构

```
zhihu-daily-task/
├── config/                      # 配置文件
│   └── topics.yaml
├── data/                        # 数据文件
│   └── published_history.json
├── docs/                        # 文档
│   ├── USER_GUIDE.md
│   ├── WINDOWS_TASK_SETUP.md
│   └── LINUX_CRON_SETUP.md
├── scripts/                     # 核心脚本
│   ├── check_login.py
│   ├── topic_manager.py
│   ├── content_generator.py
│   ├── publisher.py
│   └── env_loader.py
├── scheduler.py                 # 调度器
├── test_publisher.py            # 测试脚本
├── run_scheduler.bat            # Windows 启动脚本
└── run_scheduler.sh             # Linux/Mac 启动脚本
```

### 已知问题

- 知乎页面结构可能变化，需要定期更新选择器
- Windows 控制台编码问题已修复

### 下一步计划

- [ ] 支持更多发布平台（微信公众号、小红书等）
- [ ] 增加内容审核功能
- [ ] 支持图片自动配图
- [ ] 增加数据分析和报表
- [ ] Web 管理界面
