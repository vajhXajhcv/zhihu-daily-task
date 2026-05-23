"""
知乎选题管理脚本（人文艺术垂直领域）。

功能：
  1. 手动添加自定义话题
  2. 从话题池随机选择话题
  3. 查看和管理话题池
  4. 初始化预置人文艺术话题

使用：
    python scripts/topic_manager.py init       # 初始化预置人文艺术话题
    python scripts/topic_manager.py add "话题标题" ["分类"] ["描述"]  # 手动添加话题
    python scripts/topic_manager.py pick       # 随机选择一个话题
    python scripts/topic_manager.py list       # 列出所有话题
    python scripts/topic_manager.py clear      # 清空话题池
    python scripts/topic_manager.py invited    # 从知乎同步邀请回答的问题
"""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[错误] 未安装 pyyaml，请运行：pip install pyyaml")
    sys.exit(1)


# ---------- 路径常量 ----------
ROOT = Path(__file__).resolve().parent.parent
TOPIC_POOL_FILE = ROOT / "topic_pool.json"      # 旧版兼容
CONFIG_FILE = ROOT / "config" / "topics.yaml"   # 新版统一配置
LOG_FILE = ROOT / "logs" / "topic_manager.log"

# 预置人文艺术话题
PRESET_TOPICS = [
    {"title": "如何理解王国维《人间词话》中的'境界'说？", "category": "文学理论"},
    {"title": "中国古典园林的审美特征是什么？", "category": "建筑美学"},
    {"title": "印象派绘画对现代艺术的影响", "category": "艺术史"},
    {"title": "《红楼梦》中的诗词与人物性格的关系", "category": "古典文学"},
    {"title": "如何欣赏巴洛克音乐？", "category": "音乐鉴赏"},
    {"title": "宋代文人画的精神内核", "category": "中国画"},
    {"title": "存在主义哲学对文学创作的影响", "category": "哲学与文学"},
    {"title": "敦煌壁画的艺术价值与保护", "category": "文化遗产"},
    {"title": "如何理解中国传统戏曲的'虚拟性'？", "category": "戏剧理论"},
    {"title": "西方古典雕塑的人体美学", "category": "雕塑艺术"},
    {"title": "唐诗宋词中的自然意象", "category": "古典诗词"},
    {"title": "文艺复兴时期的人文主义思想", "category": "思想史"},
    {"title": "中国书法的线条美学", "category": "书法艺术"},
    {"title": "如何理解电影的蒙太奇语言？", "category": "电影理论"},
    {"title": "日本物哀美学的文化根源", "category": "比较美学"},
    {"title": "《诗经》中的民俗与礼制", "category": "古代文化"},
    {"title": "现代主义文学的叙事革新", "category": "现代文学"},
    {"title": "中国古代建筑的木构体系", "category": "建筑技术"},
    {"title": "如何欣赏抽象表现主义绘画？", "category": "现代艺术"},
    {"title": "《庄子》的寓言艺术", "category": "先秦哲学"}
]


def log(msg: str) -> None:
    """同时打印到控制台和日志文件。"""
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_config() -> dict:
    """加载 YAML 配置文件。"""
    if not CONFIG_FILE.exists():
        return {"topics": [], "schedule": [], "settings": {}}
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_config(config: dict) -> None:
    """保存 YAML 配置文件。"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    log(f"配置已保存，共 {len(config.get('topics', []))} 个话题。")


def load_topics() -> list[dict]:
    """加载话题池（优先 topics.yaml，兼容 topic_pool.json）。"""
    if CONFIG_FILE.exists():
        return load_config().get("topics", [])
    # 兼容旧版 json
    if not TOPIC_POOL_FILE.exists():
        return []
    with TOPIC_POOL_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("topics", [])


def save_topics(topics: list[dict]) -> None:
    """保存话题池到 topics.yaml。"""
    config = load_config()
    config["topics"] = topics
    save_config(config)


def init_preset_topics() -> None:
    """初始化预置的人文艺术话题。"""
    topics = load_topics()

    # 检查是否已有话题
    if topics:
        log(f"话题池已有 {len(topics)} 个话题，是否要追加预置话题？(y/n)")
        response = input().strip().lower()
        if response != 'y':
            log("已取消初始化")
            return

    # 添加预置话题
    existing_titles = {t["title"] for t in topics}
    new_count = 0

    for preset in PRESET_TOPICS:
        if preset["title"] not in existing_titles:
            topics.append({
                "title": preset["title"],
                "category": preset["category"],
                "type": "article",
                "source": "preset",
                "added_at": datetime.now().isoformat()
            })
            new_count += 1

    save_topics(topics)
    log(f"已添加 {new_count} 个预置话题")


def add_topic(title: str, category: str = "", description: str = "") -> None:
    """手动添加话题到话题池。"""
    topics = load_topics()

    # 检查是否已存在
    if any(t["title"] == title for t in topics):
        log(f"话题已存在：{title}")
        return

    topic_data = {
        "title": title,
        "type": "article",
        "source": "manual",
        "added_at": datetime.now().isoformat()
    }
    if category:
        topic_data["category"] = category
    if description:
        topic_data["description"] = description

    topics.append(topic_data)
    save_topics(topics)
    log(f"已添加话题：{title}")


def pick_topic() -> dict | None:
    """从话题池随机选择一个话题。"""
    topics = load_topics()

    if not topics:
        log("话题池为空，请先添加话题")
        return None

    topic = random.choice(topics)
    log(f"随机选择话题：{topic['title']}")
    return topic


def list_topics() -> None:
    """列出所有话题。"""
    topics = load_topics()

    if not topics:
        log("话题池为空")
        return

    log(f"话题池共有 {len(topics)} 个话题：")
    for i, topic in enumerate(topics, 1):
        category = topic.get("category", "未分类")
        source = topic.get("source", "unknown")
        topic_type = topic.get("type", "article")
        print(f"{i}. [{category}] {topic['title']} (类型: {topic_type}, 来源: {source})")
        if topic.get("description"):
            print(f"   描述：{topic['description'][:50]}...")


def clear_topics() -> None:
    """清空话题池。"""
    save_topics([])
    log("话题池已清空")


def sync_invited_questions(questions: list[dict]) -> int:
    """将邀请回答的问题同步到话题池。"""
    topics = load_topics()
    existing_urls = {t.get("question_url", "") for t in topics}
    added = 0

    for q in questions:
        url = q.get("url", "")
        if url and url not in existing_urls:
            topics.append({
                "title": q["title"],
                "type": "answer",
                "category": "邀请回答",
                "question_url": url,
                "source": "invited",
                "added_at": datetime.now().isoformat()
            })
            added += 1

    save_topics(topics)
    log(f"已同步 {added} 个邀请问题到话题池")
    return added


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    command = sys.argv[1].lower()

    if command == "init":
        init_preset_topics()
        return 0

    elif command == "add":
        if len(sys.argv) < 3:
            log("[错误] 请提供话题标题")
            return 1
        title = sys.argv[2]
        category = sys.argv[3] if len(sys.argv) > 3 else ""
        description = sys.argv[4] if len(sys.argv) > 4 else ""
        add_topic(title, category, description)
        return 0

    elif command == "pick":
        topic = pick_topic()
        if topic:
            print(json.dumps(topic, ensure_ascii=False, indent=2))
        return 0 if topic else 1

    elif command == "list":
        list_topics()
        return 0

    elif command == "clear":
        clear_topics()
        return 0

    elif command == "invited":
        log("从知乎获取邀请回答的问题...")
        try:
            from publisher import ZhihuPublisher
            with ZhihuPublisher(headless=False) as publisher:
                questions = publisher.fetch_invited_questions()
                if questions:
                    print(f"\n找到 {len(questions)} 个邀请问题：\n")
                    for i, q in enumerate(questions, 1):
                        print(f"{i}. {q['title']}")
                        print(f"   {q['url']}\n")
                    sync_invited_questions(questions)
                else:
                    log("未找到邀请回答的问题")
            return 0
        except Exception as e:
            log(f"获取邀请问题失败：{e}")
            return 1

    else:
        log(f"[错误] 未知命令：{command}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
