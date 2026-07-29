from utils.knowledge_manager import (
    load_knowledge,
    merge_service,
)


service_id = "gemini"


test_data = {
    "name": "Gemini",
    "updated_at": "2026-07-29",
    "models": [
        {
            "id": "gemini-2-5-flash",
            "name": "Gemini 2.5 Flash",
            "status": "deprecated",
        },
        {
            "id": "gemini-3-flash",
            "name": "Gemini 3 Flash",
            "status": "available",
        }
    ],
    "plans": [
        {
            "id": "gemini-pro",
            "name": "Gemini Pro",
            "billing": "monthly",
            "price": {
                "amount": 2900,
                "currency": "JPY"
            }
        }
    ]
}


result = merge_service(
    service_id,
    test_data,
)


print(result)