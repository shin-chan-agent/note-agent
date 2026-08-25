from utils.logger import log_info

from google.genai import types

from config import AI_SERVICES

from utils.gemini_client import call_gemini

from utils.json_parser import parse_json

from utils.knowledge_manager import (
    merge_service,
    needs_update,
)


def create_prompt(service):
    """
    最新情報取得用プロンプトを作成する。
    """

    official_domains = "\n".join(
        f"- {domain}"
        for domain in service["official_domains"]
    )

    return f"""
あなたはAIサービスの公式情報を整理する専門家です。

Google Searchを利用し、
「{service["name"]}」の最新情報を取得してください。

【情報取得ルール】

以下の公式ドメインを最優先してください。

{official_domains}

これらのドメインに情報が存在しない場合のみ、
信頼できる第三者サイトを利用してください。

【重要】

・公式サイトを最優先してください。
・公式ドキュメントを優先してください。
・推測は禁止です。
・情報が存在しない項目は、
　　"null" または "[]"
　を設定してください。

【取得対象】

・利用可能なモデル
　　→ すべて列挙してください。
　　　 無料・有料を問いません。
　　　 API専用モデルも含めてください。
・料金プラン
・API料金
・機能
　　→ 主要機能を漏れ無く列挙してください。
・制限事項
・注意事項

【情報の条件】

・現在提供中の情報を取得してください。
・公開予定・提供予定・開発予定の情報は含めないでください。
・非推奨だが利用可能なものは "deprecated" を設定してください。
・提供終了・新規利用不可のものは "discontinued" を設定してください。
・現在利用可能なものは "available" を設定してください。

【statusルール】

各項目には必ず "status" を含めてください。
使用できる値は次の3つのみです。

　・available
　　　現在利用可能
　・deprecated
　　　非推奨だが利用可能
　・discontinued
　　　提供終了・新規利用不可

statusが判断できない場合は推測せず、availableを使用してください。

【出力】

・JSONのみ返してください。
・Markdown禁止
・コードブロック禁止
・説明禁止
・コメント禁止

以下のJSON構造を厳密に守ってください。

{{
  "name": "",
  "status": "",
  "last_verified": "",
  "updated_at": "",
  "sources": [
    {{
      "name": "",
      "url": "",
      "verified_at": ""
    }}
  ],
  "models": [
    {{
      "id": "",
      "name": "",
      "aliases": [],
      "status": "",
      "effective_date": "",
      "last_updated": "",
      "description": "",
      "modalities": [],
      "api_available": true
    }}
  ],
  "plans": [
    {{
      "id": "",
      "name": "",
      "aliases": [],
      "status": "",
      "effective_date": "",
      "last_updated": "",
      "billing": "",
      "description": "",
      "pricing": [
        {{
          "name": "",
          "unit": "",
          "price": "",
          "currency": ""
        }}
      ]
    }}
  ],
  "features": [
    {{
      "id": "",
      "name": "",
      "aliases": [],
      "status": "",
      "effective_date": "",
      "last_updated": "",
      "description": "",
      "category": ""
    }}
  ],
  "limitations": [
    {{
      "id": "",
      "name": "",
      "status": "",
      "last_updated": "",
      "description": "",
      "category": ""
    }}
  ],
  "notes": [
    {{
      "id": "",
      "title": "",
      "category": "",
      "status": "",
      "description": "",
      "last_updated": ""
    }}
  ]
}}
"""


def fetch_service_info(client, service_id):
    """
    1サービス分の最新情報を取得する。
    """

    service = AI_SERVICES[service_id]

    prompt = create_prompt(service)

    response = call_gemini(
        client,
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(
                    google_search=types.GoogleSearch()
                )
            ]
        ),
    )

    if not response.text:
        raise Exception(
            f"Gemini response is empty: {service_id}"
        )

    if response.text is None:
        print(f"[ERROR] Gemini response is empty: {service_id}")
        return None

    with open(
        "gemini_response.txt",
        "w",
        encoding="utf-8"
    ) as f:
        f.write(response.text)

    try:
        service_data = parse_json(response.text)

    except Exception as e:
        log_error(f"JSON解析失敗: {service_id}")
        log_error(str(e))
        return None


    # ==========================
    # AI知識DBデータ軽量化
    # ==========================

    # ① sourcesを最大5件
    if "sources" in service_data:
        service_data["sources"] = service_data["sources"][:5]


    # ② descriptionを200文字まで
    for section in [
        "models",
        "features",
        "limitations",
        "notes",
    ]:
        for item in service_data.get(section, []):
            if "description" in item:
                item["description"] = item["description"][:200]


    # ③ aliasesを最大3件
    for section in [
        "models",
        "plans",
        "features",
    ]:
        for item in service_data.get(section, []):
            if "aliases" in item:
                item["aliases"] = item["aliases"][:3]


    log_info(f"取得サービス: {service_id}")

    return service_data


def fetch_latest_info(client, services):
    """
    指定したサービスの最新情報を取得し、
    AI知識DBへ反映する。
    """

    for service_id in services:

        if not needs_update(service_id):
            log_info(f"{service_id} は更新不要のためスキップ")
            continue

        log_info(f"{service_id} の最新情報を取得します")

        service_data = fetch_service_info(
            client,
            service_id,
        )

        if service_data is None:
            mark_update_failed(service_id)
            continue

        service_data["update_failed"] = False

        merge_service(
            service_id,
           service_data,
        )