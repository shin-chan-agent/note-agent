from pathlib import Path
import json

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from config import AI_SERVICES, KNOWLEDGE_UPDATE_INTERVAL_DAYS

from config import MISSING_LIMIT


KNOWLEDGE_FILE = Path(__file__).parent / "ai_knowledge.json"

LIST_FIELDS = [
    "models",
    "plans",
    "features",
    "limitations",
    "notes",
]


def parse_datetime(date_text):
    """
    DBの日付文字列を東京時間のdatetimeへ変換する。
    """

    dt = datetime.fromisoformat(date_text)

    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=ZoneInfo("Asia/Tokyo")
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
                "sources": [],
                "models": [],
                "plans": [],
                "features": [],
                "limitations": [],
                "notes": []
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
        encoding="utf-8"
    ) as f:
        return json.load(f)


def get_article_knowledge(service_ids):
    """
    記事生成用に必要な情報だけを返す。
    """

    data = load_knowledge()

    result = {}

    for service_id in service_ids:

        service = data["services"].get(service_id)

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
                    "description": item.get("description", "")[:80],
                }
                for item in service.get("models", [])
            ],

            "plans": [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "status": item.get("status"),
                    "description": item.get("description", "")[:80],
                    "pricing": item.get("pricing", []),
                }
                for item in service.get("plans", [])
            ],

            "features": [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "status": item.get("status"),
                    "description": item.get("description", "")[:80],
                }
                for item in service.get("features", [])
            ],

            "limitations": [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "status": item.get("status"),
                    "description": item.get("description", "")[:80],
                }
                for item in service.get("limitations", [])
            ],

            "notes": [
                {
                    "title": item.get("title"),
                    "status": item.get("status"),
                    "description": item.get("description", "")[:80],
                }
                for item in service.get("notes", [])
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
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4,
        )

    print("[INFO] AI知識DB保存")
    print(f"[DEBUG] 保存パス: {KNOWLEDGE_FILE}")
    print(f"[DEBUG] 更新日時: {KNOWLEDGE_FILE.stat().st_mtime}")


def needs_update(service_id):
    """
    指定サービスのAI知識DB更新が必要か判定する。

    True:
        更新必要

    False:
        更新不要
    """

    data = load_knowledge()

    service = data["services"].get(service_id)

    if not service:
        return True

    updated_at = service.get("updated_at")

    if not updated_at:
        return True

    updated_time = parse_datetime(
        updated_at
    )

    if updated_time is None:
        return True

    now = datetime.now(timezone.utc)

    elapsed_days = (
        now - updated_time
    ).days

    if elapsed_days >= KNOWLEDGE_UPDATE_INTERVAL_DAYS:
        return True

    return False


def needs_retry(service_id):
    """
    前回の更新が失敗したサービスは再取得する。
    """

    data = load_knowledge()

    service = data["services"].get(service_id)

    if not service:
        return True

    return service.get("update_failed", False)


def get_background_update_service(exclude_services):
    """
    テーマ更新対象を除き、
    最も長期間更新されていないサービスを1件返す。
    """

    data = load_knowledge()

    candidates = []

    for service_id, service in data["services"].items():

        if service_id in exclude_services:
            continue

        if not needs_update(service_id):
            continue

        updated_at = service.get("updated_at")

        if not updated_at:
            # 一度も取得していないサービスを最優先
            return service_id

        updated_time = parse_datetime(updated_at)

        if updated_time is None:
            continue

        candidates.append(
            (
                updated_time,
                service_id,
            )
        )

    if not candidates:
        return None

    # 更新日時が最も古いサービスを返す
    candidates.sort(key=lambda x: x[0])

    return candidates[0][1]


def mark_update_failed(service_id):
    """
    最新情報取得失敗を記録する。
    """

    data = load_knowledge()

    service = data["services"].get(service_id)

    if service is None:
        return

    service["update_failed"] = True

    save_knowledge(data)


def get_service(service_id):
    """
    指定サービスの情報を取得する。
    """

    data = load_knowledge()

    return data["services"].get(service_id)


def get_services(service_ids):
    """
    指定したサービス情報を取得する。
    """

    data = load_knowledge()

    services = {
        service_id: data["services"][service_id]
        for service_id in service_ids
        if service_id in data["services"]
    }

    for service in services.values():

        for field in LIST_FIELDS:

            if field in service:
                service[field] = filter_active_items(
                    service[field]
                )

    return services


def filter_active_items(items):
    """
    利用可能な情報だけ抽出する。

    deprecated:
    非推奨のため除外

    discontinued:
    提供終了のため除外
    """

    return [
        item
        for item in items
        if item.get("status", "available")
        not in [
            "deprecated",
            "discontinued",
        ]
    ]


def update_service(service_id, service_data):
    """
    指定サービスの情報を更新する。
    """

    data = load_knowledge()

    data["services"][service_id] = service_data

    save_knowledge(data)


def merge_service(service_id, new_data):
    """
    指定サービスの情報を差分更新する。

    新しい情報:
    - 新規項目 → 追加
    - 既存項目 → 更新
    - 存在しない項目 → 維持
    """

    data = load_knowledge()

    if service_id not in data["services"]:

        for section in [
            "models",
            "plans",
            "features",
            "limitations",
            "notes",
        ]:
            for item in new_data.get(section, []):
                item.setdefault("missing_count", 0)

        data["services"][service_id] = new_data
        save_knowledge(data)
        print("[INFO] 新規サービス保存")
        return data["services"][service_id]

    current = data["services"][service_id]

    for key, value in new_data.items():

        if key in LIST_FIELDS:
            current[key] = merge_list_items(
                current.get(key, []),
                value,
            )

        elif isinstance(value, dict):

            if key not in current:
                current[key] = value

            else:
                current[key].update(value)

        else:
            current[key] = value

    for section in [
        "models",
        "plans",
        "features",
        "limitations",
        "notes",
    ]:
        mark_missing_items(
            current.get(section, []),
            new_data.get(section, []),
        )

    save_knowledge(data)

    return current


def mark_missing_items(old_items, new_items):
    """
    取得できなかった項目を管理する。
    """

    new_map = {
        item["id"]: item
        for item in new_items
        if "id" in item
    }

    for old_item in old_items:

        item_id = old_item.get("id")

        if not item_id:
            continue

        if item_id in new_map:

            # 再取得できたので復活
            old_item["missing_count"] = 0

            if "status" in new_map[item_id]:
                old_item["status"] = new_map[item_id]["status"]

        else:

            old_item["missing_count"] = (
                old_item.get("missing_count", 0) + 1
            )

            if old_item["missing_count"] >= MISSING_LIMIT:
                old_item["status"] = "discontinued"


def merge_list_items(current_list, new_list):
    """
    リスト型データを差分更新する。

    ルール:
    - 同じidがある場合 → 更新
    - 新しいidの場合 → 追加
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

        item_id = new_item.get("id")

        if not item_id:
            continue

        if item_id in current_map:
            current_map[item_id].update(new_item)

        else:
            new_item.setdefault("missing_count", 0)
            current_list.append(new_item)

    return current_list


def merge_list_by_id(old_list, new_list):
    """
    IDをキーにリストをマージする。

    ・新しいIDは追加
    ・同じIDは上書き
    ・古いデータは削除しない
    """

    merged = {
        item["id"]: item
        for item in old_list
    }

    for item in new_list:
        merged[item["id"]] = item

    return list(merged.values())