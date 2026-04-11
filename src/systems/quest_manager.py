import json
import os

class QuestManager:
    def __init__(self):
        self.quests_db = {}
        self.player_quests = {}  # id: "unstarted", "active", "completed"
        self.quest_points = 0
        self.load_quests()

    def load_quests(self):
        path = os.path.join("data", "quests.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                self.quests_db = json.load(f)
        
        for qid in self.quests_db:
            self.player_quests[qid] = "unstarted"
            
    def get_status(self, quest_id):
        return self.player_quests.get(quest_id, "unstarted")

    def start_quest(self, quest_id):
        if self.get_status(quest_id) == "unstarted":
            self.player_quests[quest_id] = "active"
            return True
        return False

    def complete_quest(self, quest_id):
        if self.get_status(quest_id) == "active":
            self.player_quests[quest_id] = "completed"
            qp = self.quests_db.get(quest_id, {}).get("points", 1)
            self.quest_points += qp
            return True
        return False
