import json
import os

class DialogueManager:
    def __init__(self):
        self.dialogue_db = {}
        self.load_dialogue()

    def load_dialogue(self):
        path = os.path.join("data", "dialogue.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                self.dialogue_db = json.load(f)

    def get_node(self, node_id):
        return self.dialogue_db.get(node_id)
