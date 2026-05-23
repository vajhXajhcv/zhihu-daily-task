"""
基于话题生成知乎文章内容（使用 Kimi API）。

功能：
  1. 从话题池随机选择话题
  2. 使用 Kimi API 生成高质量人文艺术类文章
  3. 保存生成的内容到本地

使用：
    python scripts/content_generator.py              # 随机选题并生成
    python scripts/content_generator.py "自定义话题"  # 指定话题生成

环境变量：
    MOONSHOT_API_KEY - Moonshot AI 的 API 密钥
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 加载 .env 文件
sys.path.insert(0, str(Path(__file__).parent))
from env_loader import load_env
load_env()

try:
    import requests
except ImportError:
    print("[错误] 未安装 requests，请先运行：")
    print("    pip install -r requirements.txt")
    sys.exit(1)


# ---------- 路径常量 ----------
ROOT = Path(__file__).resolve().parent.parent
TOPIC_POOL_FILE = ROOT / "topic_pool.json"
PROMPTS_DIR = ROOT / "prompts"
OUTPUT_DIR = ROOT / "outputs"
LOG_FILE = ROOT / "logs" / "content_generator.log"

# Kimi API 配置
KIMI_API_BASE = "https://api.moonshot.cn/v1"
KIMI_MODEL = "moonshot-v1-128k"  # 支持长文本


def log(msg: str) -> None:
    """同时打印到控制台和日志文件。"""
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_prompt_template() -> str:
    """加载提示词模板。"""
    template_file = PROMPTS_DIR / "article_template.txt"

    if not template_file.exists():
        # 如果模板不存在，使用默认模板
        log("未找到提示词模板，使用默认模板")
        return """你是一位资深的人文艺术领域作者，擅长撰写深度、有见地的知乎文章。

请根据以下话题，撰写一篇高质量的知乎文章：

话题：{topic}

要求：
1. 文章长度：2000-3000字
2. 结构清晰：引言、正文（2-3个小节）、结语
3. 内容深度：有学术性但不晦涩，引用经典但不堆砌
4. 语言风格：优雅流畅，适合知乎读者
5. 观点独特：提供新颖的视角和深刻的洞察
6. 适当引用：引用经典著作、名家观点，增强说服力
7. 贴近读者：用生动的例子和比喻帮助理解

请直接输出文章内容，不要包含"标题："等前缀。"""

    with template_file.open("r", encoding="utf-8") as f:
        return f.read()


def pick_random_topic() -> dict | None:
    """从话题池随机选择一个话题（优先 topics.yaml，兼容 topic_pool.json）。"""
    config_file = ROOT / "config" / "topics.yaml"
    topics: list[dict] = []

    if config_file.exists():
        try:
            import yaml
            with config_file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            topics = data.get("topics", [])
        except Exception as e:
            log(f"[警告] 读取 topics.yaml 失败：{e}，尝试读取 topic_pool.json")

    if not topics and TOPIC_POOL_FILE.exists():
        with TOPIC_POOL_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        topics = data.get("topics", [])

    if not topics:
        log("[错误] 话题池为空，请先运行 topic_manager.py init")
        return None

    import random
    topic = random.choice(topics)
    log(f"随机选择话题：{topic['title']}")
    return topic


def generate_content(topic: str, api_key: str) -> str | None:
    """使用 Kimi API 生成文章内容。"""
    log(f"正在生成内容：{topic}")

    # 加载提示词模板
    template = load_prompt_template()
    prompt = template.format(topic=topic)

    # 调用 Kimi API
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": KIMI_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }

    try:
        response = requests.post(
            f"{KIMI_API_BASE}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        log(f"内容生成成功，长度：{len(content)} 字符")
        return content

    except requests.exceptions.RequestException as e:
        log(f"[错误] API 调用失败：{e}")
        if hasattr(e, 'response') and e.response is not None:
            log(f"响应内容：{e.response.text}")
        return None


def save_content(topic: str, content: str, category: str = "") -> Path:
    """保存生成的内容到本地。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(c for c in topic[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
    filename = f"{timestamp}_{safe_topic}.md"
    filepath = OUTPUT_DIR / filename

    # 构建完整内容
    full_content = f"""# {topic}

> 分类：{category or '未分类'}
> 生成时间：{datetime.now():%Y-%m-%d %H:%M:%S}

---

{content}
"""

    with filepath.open("w", encoding="utf-8") as f:
        f.write(full_content)

    log(f"内容已保存到：{filepath}")
    return filepath


def main() -> int:
    log("===== 内容生成开始 =====")

    # 检查 API Key
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        log("[错误] 未设置 MOONSHOT_API_KEY 环境变量")
        log("请设置环境变量：")
        log("  Windows: set MOONSHOT_API_KEY=your_api_key")
        log("  Linux/Mac: export MOONSHOT_API_KEY=your_api_key")
        return 1

    # 获取话题
    if len(sys.argv) > 1:
        # 使用命令行指定的话题
        topic_title = sys.argv[1]
        topic_data = {"title": topic_title, "category": ""}
        log(f"使用指定话题：{topic_title}")
    else:
        # 从话题池随机选择
        topic_data = pick_random_topic()
        if not topic_data:
            return 1
        topic_title = topic_data["title"]

    # 生成内容
    content = generate_content(topic_title, api_key)
    if not content:
        log("===== 内容生成失败 =====")
        return 1

    # 保存内容
    category = topic_data.get("category", "")
    filepath = save_content(topic_title, content, category)

    log("===== 内容生成完成 =====")
    log(f"文件路径：{filepath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
