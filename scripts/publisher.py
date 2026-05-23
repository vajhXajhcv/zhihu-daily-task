"""
知乎自动发布模块。

功能：
  1. 支持三种发布类型：回答问题、发想法、写文章
  2. 自动检测验证码和风控
  3. 模拟真人操作（随机延迟、滚动等）
  4. 记录发布历史

使用：
    from publisher import ZhihuPublisher

    publisher = ZhihuPublisher()
    publisher.publish_answer(question_title, content)
    publisher.publish_idea(content)
    publisher.publish_article(title, content)
"""

from __future__ import annotations

import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Literal

try:
    from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout
except ImportError:
    print("[错误] 未安装 playwright，请先运行：")
    print("    pip install -r requirements.txt")
    print("    python -m playwright install chromium")
    raise


# ---------- 路径常量 ----------
ROOT = Path(__file__).resolve().parent.parent
COOKIE_FILE = ROOT / "cookies" / "zhihu.json"
LOG_FILE = ROOT / "logs" / "publisher.log"

# 知乎 URL
ZHIHU_HOME = "https://www.zhihu.com/"
ZHIHU_WRITE = "https://www.zhihu.com/creator"
ZHIHU_SEARCH = "https://www.zhihu.com/search"


def log(msg: str) -> None:
    """记录日志。"""
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


class ZhihuPublisher:
    """知乎发布器。"""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.page: Page | None = None
        self.context = None
        self.browser = None
        self.playwright = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def start(self) -> None:
        """启动浏览器。"""
        if not COOKIE_FILE.exists():
            raise FileNotFoundError(
                f"Cookie 文件不存在：{COOKIE_FILE}\n"
                "请先运行 python scripts/check_login.py 登录知乎"
            )

        log("启动浏览器...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=["--no-proxy-server"]
        )
        self.context = self.browser.new_context(storage_state=str(COOKIE_FILE))
        self.page = self.context.new_page()
        log("浏览器启动成功")

    def close(self) -> None:
        """关闭浏览器。"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        log("浏览器已关闭")

    def random_delay(self, min_sec: int = 2, max_sec: int = 5) -> None:
        """随机延迟，模拟真人。"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def _clean_markdown(self, text: str) -> str:
        """清理 Markdown 标记，适配知乎富文本编辑器。"""
        import re
        # 去掉标题符号
        cleaned = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # 去掉加粗 **text** -> text
        cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)
        # 去掉斜体 *text* -> text
        cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)
        # 去掉代码块标记
        cleaned = re.sub(r'`{3}.*?\n', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'`(.+?)`', r'\1', cleaned)
        return cleaned

    def human_type(self, selector: str, text: str) -> None:
        """模拟人类打字速度。"""
        element = self.page.wait_for_selector(selector, timeout=10000)
        element.click()
        self.random_delay(0.5, 1)

        # 分段输入，模拟真人
        for char in text:
            element.type(char, delay=random.randint(50, 150))
            if random.random() < 0.1:  # 10% 概率暂停
                time.sleep(random.uniform(0.2, 0.5))

    def scroll_slowly(self) -> None:
        """缓慢滚动页面。"""
        self.page.evaluate("""
            window.scrollBy({
                top: Math.random() * 300 + 200,
                behavior: 'smooth'
            });
        """)
        self.random_delay(1, 2)

    def _wait_and_click(self, selectors: list[str], timeout: int = 10000, post_delay: tuple = (2, 3)) -> bool:
        """等待并点击第一个可用的元素（visible + enabled）。"""
        deadline = time.time() + (timeout / 1000)
        for selector in selectors:
            try:
                locator = self.page.locator(selector).first
                # 1. 等待可见
                locator.wait_for(state="visible", timeout=timeout)
                # 2. 轮询等待 enabled（避开 disabled/loading 状态）
                while time.time() < deadline:
                    try:
                        if locator.is_enabled() and not locator.is_disabled():
                            break
                    except Exception:
                        pass
                    time.sleep(0.3)
                # 3. 点击
                locator.click(timeout=max(1000, int((deadline - time.time()) * 1000)))
                if post_delay:
                    self.random_delay(*post_delay)
                return True
            except Exception:
                continue
        return False

    def _handle_publish_confirm(self) -> bool:
        """处理可能出现的二次确认弹窗。"""
        confirm_selectors = [
            'button:has-text("确定发布")',
            'button:has-text("确认")',
            'button:has-text("确定")',
            '.ModalButton--primary',
            '[data-testid="publish-confirm"]',
        ]
        for selector in confirm_selectors:
            try:
                self.page.click(selector, timeout=5000)
                self.random_delay(2, 3)
                return True
            except Exception:
                pass
        return False

    def _close_popups(self) -> bool:
        """检测并关闭页面上的弹窗、活动广告、遮罩层。"""
        close_selectors = [
            'button[aria-label="关闭"]',
            '.Modal-close',
            '.Modal-closeButton',
            '[data-testid="modal-close"]',
            '.ZhiHuAppBanner-close',
            '.AdBanner-close',
            'button:has-text("不再提示")',
            'button:has-text("我知道了")',
            'button:has-text("跳过")',
            'button:has-text("关闭")',
        ]
        closed_any = False
        for selector in close_selectors:
            try:
                for loc in self.page.locator(selector).all():
                    if loc.is_visible():
                        loc.click(timeout=3000)
                        self.random_delay(0.5, 1)
                        closed_any = True
            except Exception:
                pass
        if closed_any:
            log("已关闭页面弹窗/广告")
        return closed_any

    def _select_column(self) -> bool:
        """
        处理文章发布时的专栏选择。
        知乎写文章点击发布后，可能会弹出面板要求选择专栏（或个人主页）。
        如果不选，发布按钮可能 disabled 或点了没反应，导致只进草稿箱。
        """
        column_indicators = [
            'text=请选择专栏',
            'text=未选择专栏',
            '.PublishPanel-columnSelect',
            '[data-testid="column-select"]',
            '.ColumnSelect',
        ]
        has_column = False
        for indicator in column_indicators:
            try:
                if self.page.locator(indicator).count() > 0:
                    has_column = True
                    break
            except Exception:
                pass

        if not has_column:
            return True

        log("📂 检测到专栏选择，尝试自动选择...")

        # 优先选"个人主页"
        personal_options = [
            'text=个人主页',
            'text=不选专栏',
            'label:has-text("个人主页")',
            '[data-testid="personal-home"]',
        ]
        for option in personal_options:
            try:
                self.page.click(option, timeout=3000)
                log("已选择：个人主页")
                self.random_delay(1, 2)
                return True
            except Exception:
                pass

        #  fallback：选第一个可用选项
        try:
            first = self.page.locator('.ColumnSelect-item, [data-testid="column-option"], .ColumnOption').first
            if first.is_visible():
                first.click(timeout=3000)
                log("已选择第一个可用专栏")
                self.random_delay(1, 2)
                return True
        except Exception:
            pass

        log("⚠️ 未能自动选择专栏，发布可能失败")
        return False

    def _verify_published(self, original_url: str | None = None) -> bool:
        """验证发布是否成功（URL 变化或出现成功提示）。"""
        try:
            current_url = self.page.url
            # 如果 URL 变了（跳转到文章页、回答页等），大概率成功
            if original_url and current_url != original_url and "/draft" not in current_url:
                return True
            # 检查成功提示
            success_indicators = [
                "text=发布成功",
                "text=已发布",
                ".Notification-success",
            ]
            for indicator in success_indicators:
                try:
                    if self.page.locator(indicator).count() > 0:
                        return True
                except Exception:
                    pass
            # 检查是否仍在编辑器页面（如果仍在，可能没发布成功）
            if "/write" in current_url or "/draft" in current_url:
                return False
            return True
        except Exception:
            return False

    def check_captcha(self) -> bool:
        """检测是否出现验证码。"""
        captcha_selectors = [
            ".yidun",  # 网易易盾
            ".geetest",  # 极验
            "iframe[src*='captcha']",
            "text=请完成安全验证",
            "text=验证码",
        ]

        for selector in captcha_selectors:
            try:
                if self.page.locator(selector).count() > 0:
                    log("⚠️ 检测到验证码")
                    return True
            except Exception:
                pass
        return False

    def check_risk_control(self) -> bool:
        """检测风控提示。"""
        risk_keywords = [
            "操作频繁",
            "账号异常",
            "暂时无法",
            "稍后再试",
            "系统检测",
        ]

        page_text = self.page.content()
        for keyword in risk_keywords:
            if keyword in page_text:
                log(f"⚠️ 检测到风控提示：{keyword}")
                return True
        return False

    def search_question(self, question_title: str) -> str | None:
        """搜索问题并返回第一个匹配的问题 URL。"""
        log(f"搜索问题：{question_title}")

        try:
            self.page.goto(ZHIHU_SEARCH, wait_until="domcontentloaded")
            self.random_delay(2, 3)

            # 输入搜索关键词
            search_input = 'input[placeholder*="搜索"]'
            self.page.wait_for_selector(search_input, timeout=10000)
            self.page.fill(search_input, question_title)
            self.random_delay(1, 2)
            self.page.keyboard.press("Enter")

            # 等待搜索结果
            self.page.wait_for_load_state("networkidle", timeout=15000)
            self.random_delay(2, 3)

            # 查找问题链接
            question_links = self.page.locator('a[href*="/question/"]').all()
            if question_links:
                href = question_links[0].get_attribute("href")
                if href:
                    full_url = f"https://www.zhihu.com{href}" if href.startswith("/") else href
                    log(f"找到问题：{full_url}")
                    return full_url

            log("未找到匹配的问题")
            return None

        except Exception as e:
            log(f"搜索问题失败：{e}")
            return None

    def publish_answer(
        self,
        question_title: str,
        content: str,
        question_url: str | None = None
    ) -> bool:
        """发布回答。"""
        log(f"准备发布回答：{question_title}")

        try:
            # 如果没有提供问题 URL，先搜索
            if not question_url:
                question_url = self.search_question(question_title)
                if not question_url:
                    log("无法找到问题，发布失败")
                    return False

            # 打开问题页面
            self.page.goto(question_url, wait_until="domcontentloaded")
            self.random_delay(3, 5)

            # 检查风控
            if self.check_captcha() or self.check_risk_control():
                return False

            # 点击"写回答"按钮
            write_button_selectors = [
                'button:has-text("写回答")',
                'a:has-text("写回答")',
                '.QuestionAnswers-writeAnswer',
            ]

            clicked = False
            for selector in write_button_selectors:
                try:
                    self.page.click(selector, timeout=5000)
                    clicked = True
                    break
                except Exception:
                    continue

            if not clicked:
                log("未找到'写回答'按钮")
                return False

            self.random_delay(2, 3)
            self._close_popups()

            # 等待编辑器加载
            editor_selector = '.ProseMirror, .RichText-editor, [contenteditable="true"]'
            self.page.wait_for_selector(editor_selector, timeout=15000)
            self.random_delay(1, 2)

            # 输入内容（清理 Markdown 标记）
            log("正在输入回答内容...")
            self.page.fill(editor_selector, self._clean_markdown(content))
            self.random_delay(2, 4)

            # 滚动查看内容
            self.scroll_slowly()
            self._close_popups()

            # 点击发布按钮（等待可用后点击）
            publish_selectors = [
                'button:has-text("发布回答")',
                'button:has-text("发布")',
                'button.AnswerForm-submit',
                '[data-testid="publish-button"]',
                '.PublishButton',
            ]

            original_url = self.page.url
            if self._wait_and_click(publish_selectors, timeout=10000, post_delay=(2, 3)):
                self._handle_publish_confirm()
                if self._verify_published(original_url=original_url):
                    log("✅ 回答发布成功")
                    self.random_delay(3, 5)
                    return True
                else:
                    log("⚠️ 点击发布按钮后未检测到成功状态，可能进了草稿箱")
                    return False

            log("未找到可用的发布按钮")
            return False

        except Exception as e:
            log(f"发布回答失败：{e}")
            return False

    def publish_idea(self, content: str) -> bool:
        """发布想法（类似朋友圈）。"""
        log("准备发布想法...")

        try:
            self.page.goto(ZHIHU_HOME, wait_until="domcontentloaded")
            self.random_delay(3, 5)

            # 检查风控
            if self.check_captcha() or self.check_risk_control():
                return False

            # 点击"写想法"
            idea_button_selectors = [
                'button:has-text("写想法")',
                'a:has-text("写想法")',
                '.PushContent-button',
            ]

            clicked = False
            for selector in idea_button_selectors:
                try:
                    self.page.click(selector, timeout=5000)
                    clicked = True
                    break
                except Exception:
                    continue

            if not clicked:
                log("未找到'写想法'按钮")
                return False

            self.random_delay(2, 3)
            self._close_popups()

            # 输入内容（清理 Markdown 标记）
            editor_selector = 'textarea, [contenteditable="true"]'
            self.page.wait_for_selector(editor_selector, timeout=10000)
            self.page.fill(editor_selector, self._clean_markdown(content))
            self.random_delay(2, 4)
            self._close_popups()

            # 发布（等待可用后点击）
            publish_selectors = [
                'button:has-text("发布")',
                '.PushContent-submit',
                '[data-testid="publish-button"]',
                'button[type="submit"]',
            ]

            original_url = self.page.url
            if self._wait_and_click(publish_selectors, timeout=10000, post_delay=(2, 3)):
                self._handle_publish_confirm()
                if self._verify_published(original_url=original_url):
                    log("✅ 想法发布成功")
                    self.random_delay(3, 5)
                    return True
                else:
                    log("⚠️ 点击发布按钮后未检测到成功状态，可能进了草稿箱")
                    return False

            log("未找到可用的发布按钮")
            return False

        except Exception as e:
            log(f"发布想法失败：{e}")
            return False

    def publish_article(self, title: str, content: str) -> bool:
        """发布文章。"""
        log(f"准备发布文章：{title}")

        try:
            self.page.goto(ZHIHU_WRITE, wait_until="domcontentloaded")
            self.random_delay(3, 5)

            # 检查风控
            if self.check_captcha() or self.check_risk_control():
                return False

            # 点击"写文章"
            article_button_selectors = [
                'button:has-text("写文章")',
                'a:has-text("写文章")',
                'a[href*="/write"]',
            ]

            clicked = False
            for selector in article_button_selectors:
                try:
                    self.page.click(selector, timeout=5000)
                    clicked = True
                    break
                except Exception:
                    continue

            if not clicked:
                log("未找到'写文章'按钮，尝试直接访问编辑器")
                self.page.goto("https://zhuanlan.zhihu.com/write", wait_until="domcontentloaded")

            self.random_delay(3, 5)
            self._close_popups()

            # 输入标题
            title_selector = 'input[placeholder*="标题"], .WriteIndex-titleInput'
            self.page.wait_for_selector(title_selector, timeout=15000)
            self.page.fill(title_selector, title)
            self.random_delay(1, 2)

            # 输入内容（清理 Markdown 标记）
            content_selector = '.ProseMirror, [contenteditable="true"]'
            self.page.fill(content_selector, self._clean_markdown(content))
            self.random_delay(3, 5)

            # 滚动查看
            self.scroll_slowly()
            self._close_popups()

            # 发布文章（等待可用后点击 + 专栏选择 + 二次确认 + 成功验证）
            publish_selectors = [
                'button:has-text("发布文章")',
                'button:has-text("发布")',
                '.PublishPanel-stepTwoButton',
                '[data-testid="publish-button"]',
                '.PublishButton',
                'button[type="submit"]',
            ]

            original_url = self.page.url
            if self._wait_and_click(publish_selectors, timeout=15000, post_delay=(2, 3)):
                # 点击发布后，可能出现专栏选择面板
                self._select_column()
                self._handle_publish_confirm()
                if self._verify_published(original_url=original_url):
                    log("✅ 文章发布成功")
                    self.random_delay(3, 5)
                    return True
                else:
                    log("⚠️ 点击发布按钮后未检测到成功状态，可能进了草稿箱")
                    return False

            log("未找到可用的发布按钮")
            return False

        except Exception as e:
            log(f"发布文章失败：{e}")
            return False


def test_publisher():
    """测试发布器。"""
    with ZhihuPublisher(headless=False) as publisher:
        # 测试发布想法
        test_content = "这是一条测试想法，用于验证自动发布功能。\n\n" + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success = publisher.publish_idea(test_content)
        print(f"发布结果：{'成功' if success else '失败'}")


if __name__ == "__main__":
    test_publisher()
