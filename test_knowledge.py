from utils.knowledge_manager import load_knowledge

knowledge = load_knowledge()

print(knowledge)

import os

print(os.path.exists("utils/ai_knowledge.json"))