#!/bin/bash
# 知乎自动发布系统 - 快速开始脚本

echo "=========================================="
echo "知乎自动发布系统 - 快速开始"
echo "=========================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3，请先安装 Python"
    exit 1
fi

echo "✅ Python 版本："
python3 --version
echo ""

# 检查依赖
echo "📦 检查依赖..."
if ! python3 -c "import playwright" 2>/dev/null; then
    echo "⚠️ 未安装 playwright，正在安装..."
    pip install -r requirements.txt
    python3 -m playwright install chromium
fi

if ! python3 -c "import yaml" 2>/dev/null; then
    echo "⚠️ 未安装 pyyaml，正在安装..."
    pip install pyyaml
fi

echo "✅ 依赖检查完成"
echo ""

# 检查环境变量
if [ ! -f ".env" ]; then
    echo "⚠️ 未找到 .env 文件"
    echo "请复制 .env.example 为 .env 并填入 API Key："
    echo "  cp .env.example .env"
    echo "  vim .env"
    exit 1
fi

echo "✅ 环境变量配置存在"
echo ""

# 检查登录态
echo "🔐 检查知乎登录状态..."
if [ ! -f "cookies/zhihu.json" ]; then
    echo "⚠️ 未找到登录 Cookie，请先登录："
    echo "  python scripts/check_login.py"
    exit 1
fi

echo "✅ 登录状态正常"
echo ""

# 运行测试
echo "🧪 运行系统测试..."
python3 test_publisher.py

echo ""
echo "=========================================="
echo "✅ 快速开始完成！"
echo "=========================================="
echo ""
echo "📝 下一步："
echo "  1. 查看统计：python scheduler.py --stats"
echo "  2. 手动发布：python scheduler.py --now"
echo "  3. 配置定时任务：参考 docs/LINUX_CRON_SETUP.md"
echo ""
