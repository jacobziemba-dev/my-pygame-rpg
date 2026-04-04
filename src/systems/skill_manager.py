# Skill IDs and display metadata (issue #19 taxonomy).
# Order: combat, gathering, artisan, support — used for UI and save stability.
SKILL_SPECS = [
    # Combat
    ("attack", "Attack", "combat"),
    ("strength", "Strength", "combat"),
    ("defense", "Defense", "combat"),
    ("ranged", "Ranged", "combat"),
    ("magic", "Magic", "combat"),
    ("prayer", "Prayer", "combat"),
    ("constitution", "Constitution", "combat"),
    ("summoning", "Summoning", "combat"),
    ("necromancy", "Necromancy", "combat"),
    # Gathering
    ("mining", "Mining", "gathering"),
    ("woodcutting", "Woodcutting", "gathering"),
    ("fishing", "Fishing", "gathering"),
    ("farming", "Farming", "gathering"),
    ("hunter", "Hunter", "gathering"),
    ("divination", "Divination", "gathering"),
    ("archaeology", "Archaeology", "gathering"),
    # Artisan
    ("smithing", "Smithing", "artisan"),
    ("crafting", "Crafting", "artisan"),
    ("fletching", "Fletching", "artisan"),
    ("cooking", "Cooking", "artisan"),
    ("herblore", "Herblore", "artisan"),
    ("runecrafting", "Runecrafting", "artisan"),
    ("construction", "Construction", "artisan"),
    ("invention", "Invention", "artisan"),
    ("firemaking", "Firemaking", "artisan"),
    # Support
    ("agility", "Agility", "support"),
    ("thieving", "Thieving", "support"),
    ("slayer", "Slayer", "support"),
    ("dungeoneering", "Dungeoneering", "support"),
]

CATEGORY_LABELS = {
    "combat": "Combat",
    "gathering": "Gathering",
    "artisan": "Artisan",
    "support": "Support",
}


class Skill:
    def __init__(self, skill_id, display_name, category):
        self.id = skill_id
        self.name = display_name
        self.category = category
        self.level = 1
        self.xp = 0

    def xp_threshold(self):
        return self.level * self.level * 30

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
        self._skills = {}
        for sid, display, cat in SKILL_SPECS:
            s = Skill(sid, display, cat)
            self._skills[sid] = s
            setattr(self, sid, s)

    def gain_xp(self, skill_name, amount):
        skill = self._skills.get(skill_name)
        if skill:
            return skill.gain_xp(amount)
        return False

    def to_dict(self):
        return {n: {"level": s.level, "xp": s.xp} for n, s in self._skills.items()}

    @staticmethod
    def _migrate_legacy_keys(data):
        """Melee → strength; foraging → hunter. Documented for save compatibility."""
        raw = dict(data) if data else {}
        m = raw.pop("melee", None)
        if m is not None and "strength" not in raw:
            raw["strength"] = m
        f = raw.pop("foraging", None)
        if f is not None and "hunter" not in raw:
            raw["hunter"] = f
        return raw

    @classmethod
    def from_dict(cls, data):
        sm = cls()
        raw = cls._migrate_legacy_keys(data)
        for name, d in raw.items():
            if name in sm._skills:
                sm._skills[name].level = d.get("level", 1)
                sm._skills[name].xp = d.get("xp", 0)
        return sm

    def all_skills(self):
        """Flat list in SKILL_SPECS order (for iteration / simple lists)."""
        return [self._skills[sid] for sid, _, _ in SKILL_SPECS]

    def skills_by_category(self):
        """Ordered list of (category_key, category_label, [Skill, ...])."""
        buckets = {"combat": [], "gathering": [], "artisan": [], "support": []}
        for sid, _, _ in SKILL_SPECS:
            s = self._skills[sid]
            buckets[s.category].append(s)
        out = []
        for key in ("combat", "gathering", "artisan", "support"):
            out.append((key, CATEGORY_LABELS[key], buckets[key]))
        return out
