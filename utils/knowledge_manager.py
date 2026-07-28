import json
import os

KNOWLEDGE_FILE = "ai_knowledge.json"


def load_knowledge():
    """
    AI知識DBを読み込む。
    """

    if not os.path.exists(KNOWLEDGE_FILE):
        return {
            "services": {}
        }

    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_knowledge(data):
    """
    AI知識DBを保存する。
    """

    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4,
        )


def get_service(service_name):
    """
    指定サービスの情報を取得する。
    """

    data = load_knowledge()

    return data["services"].get(service_name)


def update_service(service_name, service_data):
    """
    指定サービスの情報を更新する。
    """

    data = load_knowledge()

    data["services"][service_name] = service_data

    save_knowledge(data)


def get_all_services():
    """
    全サービス情報を取得する。
    """

    data = load_knowledge()

    return data["services"]