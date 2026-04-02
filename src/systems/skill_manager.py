class Skill:
    def __init__(self, name):
        self.name = name
        self.level = 1
        self.xp = 0

    def xp_threshold(self):
        return self.level * 50

    def gain_xp(self, amount):
        self.xp += amount
        leveled_up = False
        while self.xp >= self.xp_threshold():
            self.xp -= self.xp_threshold()
            self.level += 1
            leveled_up = True
        return leveled_up


class SkillManager:
    def __init__(self):
        self.woodcutting = Skill("Woodcutting")
        self.mining      = Skill("Mining")
        self.farming     = Skill("Farming")
        self.melee       = Skill("Melee")
        self.crafting    = Skill("Crafting")
        self._skills = {
            "woodcutting": self.woodcutting,
            "mining":      self.mining,
            "farming":     self.farming,
            "melee":       self.melee,
            "crafting":    self.crafting,
        }

    def gain_xp(self, skill_name, amount):
        skill = self._skills.get(skill_name)
        if skill:
            return skill.gain_xp(amount)
        return False

    def to_dict(self):
        return {n: {"level": s.level, "xp": s.xp} for n, s in self._skills.items()}

    @classmethod
    def from_dict(cls, data):
        sm = cls()
        for name, d in data.items():
            if name in sm._skills:
                sm._skills[name].level = d.get("level", 1)
                sm._skills[name].xp    = d.get("xp", 0)
        return sm

    def all_skills(self):
        return list(self._skills.values())
