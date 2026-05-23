"""
知乎发布器测试脚本 - Dry Run 模式

功能：
  1. 验证登录态是否有效
  2. 检查页面元素是否正常
  3. 不实际发布内容

使用：
    python test_publisher.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from publisher import ZhihuPublisher, log, COOKIE_FILE


def test_login_status():
    """测试登录状态。"""
    import sys
    import io

    # 修复 Windows 控制台编码问题
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    print("\n" + "=" * 60)
    print("🔍 知乎发布器 Dry-Run 测试")
    print("=" * 60)

    # 检查 Cookie 文件
    if not COOKIE_FILE.exists():
        print(f"\n❌ Cookie 文件不存在：{COOKIE_FILE}")
        print("请先运行：python scripts/check_login.py")
        return False

    print(f"\n✅ Cookie 文件存在：{COOKIE_FILE}")

    try:
        with ZhihuPublisher(headless=False) as publisher:
            print("\n✅ 浏览器启动成功")

            # 访问知乎首页
            print("\n📍 正在访问知乎首页...")
            publisher.page.goto("https://www.zhihu.com/", wait_until="domcontentloaded")
            publisher.random_delay(2, 3)

            # 检查登录状态
            print("\n🔐 检查登录状态...")

            # 检查是否有登录用户信息
            login_indicators = [
                '.AppHeader-profile',  # 用户头像
                'button[aria-label*="用户"]',
                'a[href*="/people/"]',
                '.Avatar',
            ]

            logged_in = False
            for selector in login_indicators:
                try:
                    if publisher.page.locator(selector).count() > 0:
                        logged_in = True
                        print(f"  ✅ 找到登录标识：{selector}")
                        break
                except Exception:
                    pass

            if not logged_in:
                print("  ❌ 未检测到登录状态")
                return False

            print("\n✅ 登录状态正常")

            # 检查风控
            print("\n🛡️ 检查风控状态...")
            if publisher.check_captcha():
                print("  ⚠️ 检测到验证码")
                return False

            if publisher.check_risk_control():
                print("  ⚠️ 检测到风控提示")
                return False

            print("  ✅ 无风控异常")

            # 检查"写想法"按钮
            print("\n📝 检查发布功能...")

            idea_button_selectors = [
                'button:has-text("写想法")',
                'a:has-text("写想法")',
                '.PushContent-button',
            ]

            found_idea_button = False
            for selector in idea_button_selectors:
                try:
                    count = publisher.page.locator(selector).count()
                    if count > 0:
                        found_idea_button = True
                        print(f"  ✅ 找到'写想法'按钮：{selector}")
                        break
                except Exception:
                    pass

            if not found_idea_button:
                print("  ⚠️ 未找到'写想法'按钮（可能页面结构变化）")

            # 检查"写文章"入口
            print("\n📄 检查文章发布入口...")
            publisher.page.goto("https://www.zhihu.com/creator", wait_until="domcontentloaded")
            publisher.random_delay(2, 3)

            article_indicators = [
                'button:has-text("写文章")',
                'a:has-text("写文章")',
                'a[href*="/write"]',
            ]

            found_article = False
            for selector in article_indicators:
                try:
                    if publisher.page.locator(selector).count() > 0:
                        found_article = True
                        print(f"  ✅ 找到'写文章'入口：{selector}")
                        break
                except Exception:
                    pass

            if not found_article:
                print("  ⚠️ 未找到'写文章'入口")

            # 测试搜索功能
            print("\n🔍 测试问题搜索功能...")
            test_question = "如何理解王国维《人间词话》中的'境界'说？"
            question_url = publisher.search_question(test_question)

            if question_url:
                print(f"  ✅ 搜索成功：{question_url}")
            else:
                print(f"  ⚠️ 未找到匹配问题（这是正常的，可能该问题不存在）")

            print("\n" + "=" * 60)
            print("✅ Dry-Run 测试完成")
            print("=" * 60)
            print("\n📊 测试结果总结：")
            print(f"  - 登录状态：{'✅ 正常' if logged_in else '❌ 异常'}")
            print(f"  - 风控检测：✅ 通过")
            print(f"  - 想法功能：{'✅ 可用' if found_idea_button else '⚠️ 需确认'}")
            print(f"  - 文章功能：{'✅ 可用' if found_article else '⚠️ 需确认'}")
            print(f"  - 搜索功能：{'✅ 可用' if question_url else '⚠️ 需确认'}")

            print("\n💡 提示：")
            print("  - 如果所有功能都正常，可以使用 'python scheduler.py --now' 进行实际发布")
            print("  - 建议首次发布使用非 headless 模式，观察浏览器操作过程")
            print("  - 发布后检查 logs/publisher.log 和 logs/scheduler.log 日志")

            return True

    except Exception as e:
        print(f"\n❌ 测试过程出错：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数。"""
    success = test_login_status()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
