"""
知乎自动发布调度器。

功能：
  1. 按配置的时段自动选题并发布
  2. 支持回答、想法、文章三种类型
  3. 智能风控检测，遇到验证码自动暂停24小时
  4. 记录发布历史，避免重复发布
  5. 随机延迟模拟真人操作
  6. 内置守护进程模式，无需系统定时任务

使用：
    # 立即执行一次发布任务
    python scheduler.py --now

    # 守护进程模式（后台自动按配置时间发布）
    python scheduler.py --daemon

    # 查看发布历史
    python scheduler.py --history

    # 查看今日统计
    python scheduler.py --stats

    # 单次检查（配合 Windows 计划任务或 Linux cron）
    python scheduler.py
"""

from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

# 添加脚本目录到路径
SCRIPT_DIR = Path(__file__).parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

try:
    import yaml
except ImportError:
    print("[错误] 未安装 pyyaml，请运行：pip install pyyaml")
    sys.exit(1)

from env_loader import load_env
from content_generator import generate_content, save_content
from publisher import ZhihuPublisher, log
from reviewer import ContentReviewer

# 加载环境变量
load_env()

# ---------- 路径常量 ----------
ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / "config" / "topics.yaml"
HISTORY_FILE = ROOT / "data" / "published_history.json"
LOG_FILE = ROOT / "logs" / "scheduler.log"


class PublishScheduler:
    """发布调度器。"""

    def __init__(self):
        self.config = self.load_config()
        self.history = self.load_history()

    def load_config(self) -> dict:
        """加载配置文件。"""
        if not CONFIG_FILE.exists():
            raise FileNotFoundError(f"配置文件不存在：{CONFIG_FILE}")

        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_history(self) -> dict:
        """加载发布历史。"""
        if not HISTORY_FILE.exists():
            return {
                "history": [],
                "last_pause": None,
                "pause_until": None,
                "stats": {
                    "total_published": 0,
                    "success_count": 0,
                    "failed_count": 0,
                    "captcha_count": 0,
                }
            }

        with HISTORY_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save_history(self) -> None:
        """保存发布历史。"""
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with HISTORY_FILE.open("w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def is_paused(self) -> bool:
        """检查是否处于暂停状态。"""
        pause_until = self.history.get("pause_until")
        if not pause_until:
            return False

        pause_time = datetime.fromisoformat(pause_until)
        if datetime.now() < pause_time:
            remaining = (pause_time - datetime.now()).total_seconds() / 3600
            log(f"⏸️ 当前处于暂停状态，还需等待 {remaining:.1f} 小时")
            return True

        # 暂停期已过，清除暂停状态
        self.history["pause_until"] = None
        self.save_history()
        log("✅ 暂停期已结束，恢复正常")
        return False

    def pause_for_risk(self, hours: int = 24) -> None:
        """因风控暂停指定小时数。"""
        pause_until = datetime.now() + timedelta(hours=hours)
        self.history["last_pause"] = datetime.now().isoformat()
        self.history["pause_until"] = pause_until.isoformat()
        self.history["stats"]["captcha_count"] += 1
        self.save_history()
        log(f"⚠️ 检测到风控，暂停 {hours} 小时至 {pause_until:%Y-%m-%d %H:%M:%S}")

    def get_today_published_count(self) -> int:
        """获取今日已成功发布数量。"""
        today = datetime.now().date()
        count = 0
        for record in self.history["history"]:
            if not record.get("success", False):
                continue
            pub_time = datetime.fromisoformat(record["published_at"])
            if pub_time.date() == today:
                count += 1
        return count

    def is_topic_published(self, topic_title: str) -> bool:
        """检查话题是否已发布过。"""
        for record in self.history["history"]:
            if record["topic"] == topic_title:
                return True
        return False

    def pick_topic(self) -> dict | None:
        """从配置中随机选择一个未发布的话题。优先选邀请/推荐/人气问题。"""
        topics = self.config.get("topics", [])
        if not topics:
            log("配置中没有话题")
            return None

        # 过滤未发布的话题
        unpublished = [t for t in topics if not self.is_topic_published(t["title"])]

        if not unpublished:
            log("所有话题都已发布过")
            return None

        # 优先级：invited > recommended > trending > 普通话题
        priority_sources = ["invited", "recommended", "trending"]
        for source in priority_sources:
            candidates = [t for t in unpublished if t.get("source") == source]
            if candidates:
                topic = random.choice(candidates)
                log(f"优先选择【{source}】话题：{topic['title']} ({topic['category']})")
                return topic

        # 没有高优先级话题，从普通话题中随机选择
        topic = random.choice(unpublished)
        log(f"选择话题：{topic['title']} ({topic['category']})")
        return topic

    def generate_and_publish(
        self,
        topic: dict,
        api_key: str,
        headless: bool = False
    ) -> tuple[bool, Path | None]:
        """生成内容并发布。返回 (是否成功, 文件路径)。"""
        topic_title = topic["title"]
        topic_type = topic.get("type", "answer")
        category = topic.get("category", "")

        # 随机延迟
        settings = self.config.get("settings", {})
        delay_min = settings.get("random_delay_min", 30)
        delay_max = settings.get("random_delay_max", 300)
        delay = random.randint(delay_min, delay_max)
        log(f"⏱️ 随机延迟 {delay} 秒，模拟真人操作...")
        time.sleep(delay)

        # 生成内容
        log(f"📝 正在生成内容：{topic_title}")
        content = generate_content(topic_title, api_key)
        if not content:
            log("内容生成失败")
            return False, None

        # 保存到本地
        filepath = save_content(topic_title, content, category)
        log(f"💾 内容已保存：{filepath}")

        # 内容质量审查（底线保障）
        log("🔍 正在进行内容质量审查...")
        reviewer = ContentReviewer()
        review_result = reviewer.review(content, topic=topic_title)

        if not review_result["passed"]:
            log("❌ 内容审查未通过，禁止发布")
            log(review_result["report"].replace("\n", "\n  "))
            # 仍然保存内容到本地以便排查，但返回失败
            return False, filepath

        log(f"✅ 内容审查通过（得分：{review_result['total_score']:.1f}）")

        # 发布到知乎
        log(f"🚀 开始发布到知乎（类型：{topic_type}）")

        try:
            with ZhihuPublisher(headless=headless) as publisher:
                success = False
                risk_triggered = False

                if topic_type == "answer":
                    question_url = topic.get("question_url") or topic.get("question_id")
                    success = publisher.publish_answer(topic_title, content, question_url)

                elif topic_type == "idea":
                    # 想法需要精简内容
                    idea_content = content[:500] + "..." if len(content) > 500 else content
                    success = publisher.publish_idea(idea_content)

                elif topic_type == "article":
                    success = publisher.publish_article(topic_title, content)

                else:
                    log(f"未知的发布类型：{topic_type}")
                    return False, filepath

                # 若发布失败，再检查是否是风控导致的
                if not success:
                    try:
                        risk_triggered = publisher.check_captcha() or publisher.check_risk_control()
                    except Exception:
                        pass

                if risk_triggered:
                    pause_duration = settings.get("pause_duration", 86400) // 3600
                    self.pause_for_risk(hours=pause_duration)
                    return False, filepath

                return success, filepath

        except Exception as e:
            log(f"发布过程出错：{e}")
            return False, filepath

    def record_publish(self, topic: dict, success: bool, filepath: Path) -> None:
        """记录发布结果。"""
        record = {
            "topic": topic["title"],
            "category": topic.get("category", ""),
            "type": topic.get("type", "answer"),
            "published_at": datetime.now().isoformat(),
            "success": success,
            "filepath": str(filepath),
        }

        self.history["history"].append(record)
        self.history["stats"]["total_published"] += 1

        if success:
            self.history["stats"]["success_count"] += 1
        else:
            self.history["stats"]["failed_count"] += 1

        self.save_history()
        log(f"📊 发布记录已保存（成功：{success}）")

    def run_once(self, headless: bool = False) -> bool:
        """执行一次发布任务。"""
        log("=" * 60)
        log("🤖 知乎自动发布任务开始")
        log("=" * 60)

        # 检查是否暂停
        if self.is_paused():
            return False

        # 检查今日发布数量
        settings = self.config.get("settings", {})
        max_daily = settings.get("max_daily_posts", 3)
        today_count = self.get_today_published_count()

        if today_count >= max_daily:
            log(f"⚠️ 今日已发布 {today_count} 篇，达到上限 {max_daily}")
            return False

        # 检查 API Key
        import os
        api_key = os.getenv("MOONSHOT_API_KEY")
        if not api_key:
            log("❌ 未设置 MOONSHOT_API_KEY 环境变量")
            return False

        # 选择话题
        topic = self.pick_topic()
        if not topic:
            return False

        # 生成并发布
        success, filepath = self.generate_and_publish(topic, api_key, headless)

        # 记录结果
        if filepath is None:
            filepath = ROOT / "outputs" / f"{datetime.now():%Y%m%d_%H%M%S}_{topic['title'][:20]}.md"
        self.record_publish(topic, success, filepath)

        if success:
            log("=" * 60)
            log("✅ 发布任务完成")
            log("=" * 60)
        else:
            log("=" * 60)
            log("❌ 发布任务失败")
            log("=" * 60)

        return success

    def show_history(self, limit: int = 10) -> None:
        """显示发布历史。"""
        history = self.history["history"]
        if not history:
            print("暂无发布记录")
            return

        print(f"\n📜 最近 {min(limit, len(history))} 条发布记录：\n")
        print(f"{'时间':<20} {'话题':<30} {'类型':<10} {'状态':<10}")
        print("-" * 80)

        for record in reversed(history[-limit:]):
            pub_time = datetime.fromisoformat(record["published_at"])
            topic = record["topic"][:28] + "..." if len(record["topic"]) > 28 else record["topic"]
            pub_type = record.get("type", "answer")
            status = "✅ 成功" if record["success"] else "❌ 失败"

            print(f"{pub_time:%Y-%m-%d %H:%M:%S}  {topic:<30} {pub_type:<10} {status}")

    def show_stats(self) -> None:
        """显示统计信息。"""
        stats = self.history["stats"]
        today_count = self.get_today_published_count()

        print("\n📊 发布统计：\n")
        print(f"  总发布数：{stats['total_published']}")
        print(f"  成功：{stats['success_count']}")
        print(f"  失败：{stats['failed_count']}")
        print(f"  触发风控次数：{stats['captcha_count']}")
        print(f"  今日已发布：{today_count}")

        if self.history.get("pause_until"):
            pause_time = datetime.fromisoformat(self.history["pause_until"])
            if datetime.now() < pause_time:
                remaining = (pause_time - datetime.now()).total_seconds() / 3600
                print(f"\n  ⚠️ 当前暂停中，剩余 {remaining:.1f} 小时")

    def run_daemon(self, headless: bool = False) -> None:
        """
        守护进程模式：后台循环运行，按配置时间点自动发布。
        每 6 小时自动同步一次知乎消息中心的邀请/推荐/人气问题。

        逻辑：
          - 每分钟检查一次当前时间
          - 匹配 schedule 中的时间点且今天未执行过，则触发发布
          - 每 6 小时自动拉取消息中心新问题
          - 新的一天自动清空执行记录
          - Ctrl+C 优雅退出
        """
        log("=" * 60)
        log("🔁 守护进程启动")
        log("按 Ctrl+C 停止")
        log("=" * 60)

        executed_today: set[str] = set()
        last_date = datetime.now().date()
        last_sync_time = 0.0  # 上次同步时间戳
        sync_interval = 6 * 3600  # 每 6 小时同步一次

        while True:
            try:
                now = datetime.now()
                current_date = now.date()
                current_time = f"{now.hour:02d}:{now.minute:02d}"
                current_timestamp = now.timestamp()

                # 新的一天，清空执行记录
                if current_date != last_date:
                    executed_today.clear()
                    last_date = current_date
                    log("🌅 新的一天，已清空执行记录")

                # 每 6 小时自动同步邀请问题
                if current_timestamp - last_sync_time >= sync_interval:
                    log("🔄 开始自动同步知乎消息中心问题...")
                    try:
                        from publisher import ZhihuPublisher
                        from topic_manager import sync_invited_questions
                        with ZhihuPublisher(headless=headless) as publisher:
                            result = publisher.fetch_invited_questions()
                            counts = sync_invited_questions(result)
                            total = sum(counts.values())
                            if total > 0:
                                log(f"✅ 自动同步完成：邀请 {counts['invited']} / 推荐 {counts['recommended']} / 人气 {counts['trending']}")
                    except Exception as e:
                        log(f"⚠️ 自动同步失败：{e}")
                    last_sync_time = current_timestamp

                # 检查是否在发布时段内
                schedule = self.config.get("schedule", [])
                for slot in schedule:
                    if not slot.get("enabled", True):
                        continue
                    slot_time = slot["time"]
                    if slot_time == current_time and slot_time not in executed_today:
                        log(f"⏰ 到达发布时间点：{slot_time}")
                        self.run_once(headless=headless)
                        executed_today.add(slot_time)
                        break

                # 睡眠到下一分钟（对齐到整分钟）
                next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
                sleep_seconds = (next_minute - datetime.now()).total_seconds()
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)

            except KeyboardInterrupt:
                log("=" * 60)
                log("🛑 收到停止信号，守护进程退出")
                log("=" * 60)
                break
            except Exception as e:
                log(f"❌ 守护进程异常：{e}")
                time.sleep(60)


def main():
    """主函数。"""
    import argparse
    import sys
    import io

    # 修复 Windows 控制台编码问题
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(description="知乎自动发布调度器")
    parser.add_argument("--now", action="store_true", help="立即执行一次发布")
    parser.add_argument("--daemon", action="store_true", help="守护进程模式（后台按配置时间自动发布）")
    parser.add_argument("--history", action="store_true", help="查看发布历史")
    parser.add_argument("--stats", action="store_true", help="查看统计信息")
    parser.add_argument("--headless", action="store_true", help="无头模式运行")
    args = parser.parse_args()

    scheduler = PublishScheduler()

    if args.history:
        scheduler.show_history()
        return 0

    if args.stats:
        scheduler.show_stats()
        return 0

    if args.now:
        success = scheduler.run_once(headless=args.headless)
        return 0 if success else 1

    if args.daemon:
        scheduler.run_daemon(headless=args.headless)
        return 0

    # 默认：检查是否到了发布时间（单次运行，配合外部定时任务）
    now = datetime.now()
    current_time = f"{now.hour:02d}:{now.minute:02d}"

    schedule = scheduler.config.get("schedule", [])
    should_run = False

    for slot in schedule:
        if slot.get("enabled", True) and slot["time"] == current_time:
            should_run = True
            break

    if should_run:
        scheduler.run_once(headless=args.headless)
    else:
        log(f"当前时间 {current_time} 不在发布时段内")

    return 0


if __name__ == "__main__":
    sys.exit(main())
