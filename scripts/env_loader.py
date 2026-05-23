"""
加载 .env 文件中的环境变量的辅助函数。
"""

from pathlib import Path


def load_env(env_file: Path = None) -> None:
    """
    从 .env 文件加载环境变量到 os.environ。

    Args:
        env_file: .env 文件路径，默认为项目根目录的 .env
    """
    import os

    if env_file is None:
        # 默认使用项目根目录的 .env
        root = Path(__file__).resolve().parent.parent
        env_file = root / ".env"

    if not env_file.exists():
        return

    with env_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue

            # 解析 KEY=VALUE
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # 移除引号
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                os.environ[key] = value
