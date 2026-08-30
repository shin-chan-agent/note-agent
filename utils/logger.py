from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


# ========================================
# ログ保存先
# ========================================

LOG_DIR = Path("logs")

TOKYO_TZ = ZoneInfo("Asia/Tokyo")


def _write_log(level: str, message: str):
    """
    ログをGitHub Actionsのコンソールと
    ログファイルの両方へ出力する。
    """

    now = datetime.now(
        TOKYO_TZ
    )

    timestamp = now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    log_message = (
        f"[{timestamp}] "
        f"[{level}] "
        f"{message}"
    )

    # ====================================
    # GitHub Actionsへ出力
    # ====================================

    print(log_message)

    # ====================================
    # ログディレクトリ作成
    # ====================================

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ====================================
    # 日付ごとのログファイル
    # ====================================

    log_file = LOG_DIR / (
        now.strftime("%Y-%m-%d") + ".log"
    )

    # ====================================
    # ログ保存
    # ====================================

    with open(
        log_file,
        "a",
        encoding="utf-8",
    ) as f:

        f.write(
            log_message + "\n"
        )


def log_info(message: str):
    _write_log(
        "INFO",
        message,
    )


def log_warning(message: str):
    _write_log(
        "WARNING",
        message,
    )


def log_error(message: str):
    _write_log(
        "ERROR",
        message,
    )