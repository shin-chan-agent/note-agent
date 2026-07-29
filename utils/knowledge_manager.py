from pathlib import Path
import json

from config import AI_SERVICES


KNOWLEDGE_FILE = Path(__file__).parent / "ai_knowledge.json"


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


def get_service(service_id):
    """
    指定サービスの情報を取得する。
    """

    data = load_knowledge()

    return data["services"].get(service_id)


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
        data["services"][service_id] = new_data
        save_knowledge(data)
        return data["services"][service_id]

    current = data["services"][service_id]

    for key, value in new_data.items():

        if isinstance(value, dict):
            if key not in current:
                current[key] = value
            else:
                current[key].update(value)

        else:
            current[key] = value

    save_knowledge(data)

    return current