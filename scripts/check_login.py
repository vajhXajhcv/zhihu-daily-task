"""
检查知乎登录状态。

逻辑：
  1. 若 cookies/zhihu.json 已存在，则用它启动浏览器并验证是否仍然有效；
     - 有效：刷新一次最新 cookie 并退出。
     - 失效：删除旧 cookie 并走扫码流程。
  2. 若不存在或已失效，则启动有头浏览器，引导用户扫码登录；
     检测到登录成功后把 storage_state 保存到 cookies/zhihu.json。

使用：
    python scripts/check_login.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Playwright 在没装的情况下给出友好提示，而不是抛出难懂的 ImportError
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("[错误] 未安装 playwright，请先运行：")
    print("    pip install -r requirements.txt")
    print("    python -m playwright install chromium")
    sys.exit(1)


# ---------- 路径常量 ----------
ROOT = Path(__file__).resolve().parent.parent          # 项目根目录
COOKIE_FILE = ROOT / "cookies" / "zhihu.json"          # storage_state 存放位置
LOG_FILE = ROOT / "logs" / "check_login.log"           # 本脚本日志

ZHIHU_HOME = "https://www.zhihu.com/"
ZHIHU_SIGNIN = "https://www.zhihu.com/signin"

# 登录成功的判定：页面 cookie 中存在 z_c0（知乎登录态 token）
LOGIN_COOKIE_NAME = "z_c0"
# 扫码等待上限（秒），超时则放弃
SCAN_TIMEOUT = 180


def log(msg: str) -> None:
    """同时打印到控制台和日志文件，带时间戳。"""
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def has_login_cookie(state: dict) -> bool:
    """判断 storage_state 字典里是否带有知乎登录 cookie。"""
    for c in state.get("cookies", []):
        if c.get("name") == LOGIN_COOKIE_NAME and c.get("value"):
            return True
    return False


def verify_existing_cookie() -> bool:
    """用已保存的 cookie 打开知乎，看是否仍是登录态。"""
    if not COOKIE_FILE.exists():
        return False

    log("检测到已存在的 cookie，正在验证有效性…")
    with sync_playwright() as p:
        # headless 验证即可，不打扰用户
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(COOKIE_FILE))
        page = context.new_page()
        try:
            page.goto(ZHIHU_HOME, wait_until="domcontentloaded", timeout=30_000)
        except PWTimeout:
            log("访问知乎首页超时，按未登录处理。")
            browser.close()
            return False

        # 取当前 context 的 cookie 列表来判断
        cookies = context.cookies()
        is_logged_in = any(
            c.get("name") == LOGIN_COOKIE_NAME and c.get("value") for c in cookies
        )

        if is_logged_in:
            # 顺手刷新一次最新 storage_state（cookie 可能滚动更新）
            context.storage_state(path=str(COOKIE_FILE))
            log("Cookie 仍然有效，已刷新保存。")
        else:
            log("Cookie 已失效。")

        browser.close()
        return is_logged_in


def login_by_qrcode() -> bool:
    """打开有头浏览器，引导用户扫码登录，登录成功后保存 storage_state。"""
    log("启动浏览器，请使用知乎 App 扫码登录…")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(ZHIHU_SIGNIN, wait_until="domcontentloaded")

        deadline = time.time() + SCAN_TIMEOUT
        success = False
        while time.time() < deadline:
            cookies = context.cookies()
            if any(
                c.get("name") == LOGIN_COOKIE_NAME and c.get("value") for c in cookies
            ):
                success = True
                break
            time.sleep(2)

        if success:
            COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=str(COOKIE_FILE))
            log(f"登录成功，cookie 已保存到 {COOKIE_FILE}")
        else:
            log(f"在 {SCAN_TIMEOUT} 秒内未检测到登录，已放弃。")

        browser.close()
        return success


def main() -> int:
    log("===== 知乎登录状态检查开始 =====")

    if verify_existing_cookie():
        log("===== 已登录，无需重新扫码 =====")
        return 0

    # 走到这里说明没 cookie 或 cookie 失效
    if COOKIE_FILE.exists():
        try:
            COOKIE_FILE.unlink()
            log("已删除失效的旧 cookie。")
        except OSError as e:
            log(f"删除旧 cookie 失败：{e}")

    if login_by_qrcode():
        log("===== 扫码登录完成 =====")
        return 0

    log("===== 登录失败，请稍后重试 =====")
    return 1


if __name__ == "__main__":
    sys.exit(main())
