import json
import os

RECIPES_FILE = os.path.join("data", "recipes.json")


class RecipeManager:
    def __init__(self, path=RECIPES_FILE):
        self._recipes = []
        self._load(path)

    def _load(self, path):
        with open(path, "r") as f:
            data = json.load(f)
        self._recipes = data["recipes"]

    def get_all(self):
        return list(self._recipes)

    def get_handcrafted(self):
        """Returns recipes that require no station."""
        return [r for r in self._recipes if not r.get("station")]

    def get_for_station(self, station_type):
        """Returns recipes that require the given station type."""
        return [r for r in self._recipes if r.get("station") == station_type]

    def get_by_name(self, name):
        """Returns the recipe dict for the given name, or None."""
        return next((r for r in self._recipes if r["name"] == name), None)
