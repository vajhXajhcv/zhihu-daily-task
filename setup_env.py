"""
一键安装项目依赖。

做两件事：
  1. pip install -r requirements.txt
  2. python -m playwright install chromium

直接运行：
    python setup_env.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQ_FILE = ROOT / "requirements.txt"


def run(cmd: list[str]) -> int:
    """打印并执行命令，返回退出码。"""
    print(f"\n>>> {' '.join(cmd)}")
    return subprocess.call(cmd)


def main() -> int:
    if not REQ_FILE.exists():
        print(f"[错误] 找不到 {REQ_FILE}")
        return 1

    # 1) 安装 Python 依赖
    code = run([sys.executable, "-m", "pip", "install", "-r", str(REQ_FILE)])
    if code != 0:
        print("[错误] pip 依赖安装失败。")
        return code

    # 2) 安装 Playwright 浏览器二进制（只装 chromium，体积最小）
    code = run([sys.executable, "-m", "playwright", "install", "chromium"])
    if code != 0:
        print("[错误] Playwright 浏览器安装失败。")
        return code

    print("\n[完成] 依赖安装完毕，可以运行 python scripts/check_login.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
