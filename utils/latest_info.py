from google.genai import types

from config import AI_SERVICES

from utils.gemini_client import call_gemini

from utils.json_parser import parse_json

from utils.knowledge_manager import merge_service


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

・現在提供中の情報のみ取得してください。
・公開予定・提供予定・開発予定の情報は含めないでください。
・提供終了したものは
　　"status" を
　　"deprecated" または "discontinued"
　としてください。

【出力】

・JSONのみ返してください。
・Markdown禁止
・コードブロック禁止
・説明禁止
・コメント禁止

以下のJSON構造を厳密に守ってください。

{{
  "name": "",
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

    return parse_json(response.text)


def fetch_latest_info(client, services):
    """
    指定したサービスの最新情報を取得し、
    AI知識DBへ反映する。
    """

    for service_id in services:

        service_data = fetch_service_info(
            client,
            service_id,
        )

        merge_service(
            service_id,
            service_data,
        )