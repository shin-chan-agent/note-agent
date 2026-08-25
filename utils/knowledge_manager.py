from pathlib import Path
import json

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from config import (
    AI_SERVICES,
    KNOWLEDGE_UPDATE_INTERVAL_DAYS,
    MISSING_LIMIT,
)


KNOWLEDGE_FILE = Path(__file__).parent / "ai_knowledge.json"

LIST_FIELDS = [
    "models",
    "plans",
    "features",
    "limitations",
    "notes",
]

TOKYO_TZ = ZoneInfo("Asia/Tokyo")


def parse_datetime(date_text):
    """
    DBの日付文字列をdatetimeへ変換する。

    タイムゾーンなしの場合は東京時間として扱う。
    不正な日付の場合はNoneを返す。
    """

    if not date_text:
        return None

    try:
        dt = datetime.fromisoformat(
            str(date_text)
        )

    except (TypeError, ValueError):
        return None

    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=TOKYO_TZ
        )

    return dt


def create_default_knowledge():
    """
    初期状態のAI知識DBを作成する。
    """

    return {
        "version": 1,
        "services": {
            service_id: {
                "name": service["name"],
                "last_verified": None,
                "updated_at": None,
                "update_failed": False,
                "sources": [],
                "models": [],
                "plans": [],
                "features": [],
                "limitations": [],
                "notes": [],
            }
            for service_id, service in AI_SERVICES.items()
        }
    }


def load_knowledge():
    """
    AI知識DBを読み込む。

    存在しない場合は初期DBを作成する。
    """

    if not KNOWLEDGE_FILE.exists():

        data = create_default_knowledge()

        save_knowledge(data)

        return data

    with open(
        KNOWLEDGE_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        data = json.load(f)

    # servicesが存在しない場合の安全対策
    if "services" not in data:
        data["services"] = {}

    return data


def get_article_knowledge(service_ids):
    """
    記事生成用に必要な情報だけを返す。

    deprecated / discontinued の情報は記事生成用DBから除外する。
    """

    data = load_knowledge()

    result = {}

    for service_id in service_ids:

        service = data["services"].get(
            service_id
        )

        if not service:
            continue

        result[service_id] = {
            "name": service.get("name"),
            "updated_at": service.get("updated_at"),

            "models": [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "status": item.get("status"),
                    "description": item.get(
                        "description",
                        "",
                    )[:80],
                }
                for item in filter_active_items(
                    service.get("models", [])
                )
            ],

            "plans": [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "status": item.get("status"),
                    "description": item.get(
                        "description",
                        "",
                    )[:80],
                    "pricing": item.get(
                        "pricing",
                        [],
                    ),
                }
                for item in filter_active_items(
                    service.get("plans", [])
                )
            ],

            "features": [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "status": item.get("status"),
                    "description": item.get(
                        "description",
                        "",
                    )[:80],
                }
                for item in filter_active_items(
                    service.get("features", [])
                )
            ],

            "limitations": [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "status": item.get("status"),
                    "description": item.get(
                        "description",
                        "",
                    )[:80],
                }
                for item in filter_active_items(
                    service.get("limitations", [])
                )
            ],

            "notes": [
                {
                    "title": item.get("title"),
                    "status": item.get("status"),
                    "description": item.get(
                        "description",
                        "",
                    )[:80],
                }
                for item in filter_active_items(
                    service.get("notes", [])
                )
            ],
        }

    return result


def save_knowledge(data):
    """
    AI知識DBを保存する。
    """

    with open(
        KNOWLEDGE_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4,
        )

    print("[INFO] AI知識DB保存")
    print(
        f"[DEBUG] 保存パス: {KNOWLEDGE_FILE}"
    )
    print(
        f"[DEBUG] 更新日時: "
        f"{KNOWLEDGE_FILE.stat().st_mtime}"
    )


def needs_update(service_id):
    """
    指定サービスのAI知識DB更新が必要か判定する。

    True:
        更新必要

    False:
        更新不要
    """

    data = load_knowledge()

    service = data["services"].get(
        service_id
    )

    if not service:
        return True

    # 前回取得失敗の場合は再取得
    if service.get("update_failed", False):
        return True

    updated_at = service.get(
        "updated_at"
    )

    if not updated_at:
        return True

    updated_time = parse_datetime(
        updated_at
    )

    # 不正な日付の場合は安全のため更新
    if updated_time is None:
        return True

    now = datetime.now(
        timezone.utc
    )

    elapsed_seconds = (
        now - updated_time
    ).total_seconds()

    elapsed_days = (
        elapsed_seconds / 86400
    )

    return (
        elapsed_days
        >= KNOWLEDGE_UPDATE_INTERVAL_DAYS
    )


def needs_retry(service_id):
    """
    前回の更新が失敗したサービスは
    再取得対象とする。
    """

    data = load_knowledge()

    service = data["services"].get(
        service_id
    )

    if not service:
        return True

    return service.get(
        "update_failed",
        False,
    )


def get_background_update_service(
    exclude_services
):
    """
    テーマ更新対象を除き、
    最も長期間更新されていないサービスを
    1件返す。

    一度も取得していないサービスを最優先する。
    """

    data = load_knowledge()

    candidates = []

    for service_id, service in data[
        "services"
    ].items():

        if service_id in exclude_services:
            continue

        if not needs_update(service_id):
            continue

        updated_at = service.get(
            "updated_at"
        )

        if not updated_at:

            return service_id

        updated_time = parse_datetime(
            updated_at
        )

        if updated_time is None:

            return service_id

        candidates.append(
            (
                updated_time,
                service_id,
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0]
    )

    return candidates[0][1]


def mark_update_failed(service_id):
    """
    最新情報取得失敗を記録する。
    """

    data = load_knowledge()

    service = data["services"].get(
        service_id
    )

    if service is None:
        return

    service["update_failed"] = True

    save_knowledge(data)


def get_service(service_id):
    """
    指定サービスの情報を取得する。
    """

    data = load_knowledge()

    return data["services"].get(
        service_id
    )


def get_services(service_ids):
    """
    指定したサービス情報を取得する。

    deprecated / discontinued の項目は除外する。
    """

    data = load_knowledge()

    services = {
        service_id: data["services"][
            service_id
        ]
        for service_id in service_ids
        if service_id in data["services"]
    }

    for service in services.values():

        for field in LIST_FIELDS:

            if field in service:

                service[field] = (
                    filter_active_items(
                        service[field]
                    )
                )

    return services


def filter_active_items(items):
    """
    現在利用可能な情報だけ抽出する。

    deprecated:
        非推奨のため除外

    discontinued:
        提供終了のため除外
    """

    return [
        item
        for item in items
        if item.get(
            "status",
            "available",
        )
        not in [
            "deprecated",
            "discontinued",
        ]
    ]


def update_service(
    service_id,
    service_data,
):
    """
    指定サービスの情報を完全更新する。
    """

    data = load_knowledge()

    data["services"][
        service_id
    ] = service_data

    save_knowledge(data)


def merge_service(
    service_id,
    service_data,
):
    """
    指定サービスの情報を差分更新する。

    新しい情報:
    - 新規項目 → 追加
    - 既存項目 → 更新
    - 存在しない項目 → 維持
    """

    data = load_knowledge()

    # ========================================
    # 新規サービス
    # ========================================

    if service_id not in data["services"]:

        service_data.setdefault(
            "update_failed",
            False,
        )

        for section in LIST_FIELDS:

            for item in service_data.get(
                section,
                [],
            ):

                item.setdefault(
                    "missing_count",
                    0,
                )

        data["services"][
            service_id
        ] = service_data

        save_knowledge(data)

        print(
            "[INFO] 新規サービス保存"
        )

        return data["services"][
            service_id
        ]

    # ========================================
    # 既存サービス
    # ========================================

    current = data["services"][
        service_id
    ]

    for key, value in service_data.items():

        if key in LIST_FIELDS:

            current[key] = merge_list_items(
                current.get(key, []),
                value,
            )

        elif isinstance(
            value,
            dict,
        ):

            if key not in current:
                current[key] = value

            else:
                current[key].update(value)

        else:

            current[key] = value

    # ========================================
    # 今回取得できなかった項目を確認
    # ========================================

    for section in LIST_FIELDS:

        mark_missing_items(
            current.get(
                section,
                [],
            ),
            service_data.get(
                section,
                [],
            ),
        )

    # ========================================
    # 更新成功
    # ========================================

    current["update_failed"] = False

    save_knowledge(data)

    return current


def mark_missing_items(
    old_items,
    new_items,
):
    """
    今回取得できなかった項目を管理する。

    1回取得できない:
        missing_count +1

    MISSING_LIMIT回連続で取得できない:
        discontinued

    再び取得できた:
        missing_count = 0
        statusを新しい情報に更新
    """

    new_map = {
        item["id"]: item
        for item in new_items
        if "id" in item
    }

    for old_item in old_items:

        item_id = old_item.get(
            "id"
        )

        if not item_id:
            continue

        # ====================================
        # 今回も取得できた
        # ====================================

        if item_id in new_map:

            old_item["missing_count"] = 0

            new_item = new_map[
                item_id
            ]

            if "status" in new_item:

                old_item["status"] = (
                    new_item["status"]
                )

        # ====================================
        # 今回取得できなかった
        # ====================================

        else:

            old_item[
                "missing_count"
            ] = (
                old_item.get(
                    "missing_count",
                    0,
                ) + 1
            )

            if (
                old_item[
                    "missing_count"
                ]
                >= MISSING_LIMIT
            ):

                old_item[
                    "status"
                ] = "discontinued"


def merge_list_items(
    current_list,
    new_list,
):
    """
    リスト型データを差分更新する。

    ルール:
    - 同じID → 新しい情報で更新
    - 新しいID → 追加
    - 新しい情報に存在しない項目 → 維持
    """

    if not new_list:
        return current_list

    current_map = {
        item["id"]: item
        for item in current_list
        if "id" in item
    }

    for new_item in new_list:

        item_id = new_item.get(
            "id"
        )

        if not item_id:
            continue

        # ====================================
        # 既存項目
        # ====================================

        if item_id in current_map:

            current_map[
                item_id
            ].update(new_item)

            # 再取得できたので復活
            current_map[
                item_id
            ]["missing_count"] = 0

        # ====================================
        # 新規項目
        # ====================================

        else:

            new_item.setdefault(
                "missing_count",
                0,
            )

            current_list.append(
                new_item
            )

    return current_list


def merge_list_by_id(
    old_list,
    new_list,
):
    """
    IDをキーにリストをマージする。

    ・新しいIDは追加
    ・同じIDは上書き
    ・古いデータは削除しない
    """

    merged = {
        item["id"]: item
        for item in old_list
        if "id" in item
    }

    for item in new_list:

        if "id" not in item:
            continue

        merged[
            item["id"]
        ] = item

    return list(
        merged.values()
    )