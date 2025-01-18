import json
import os


def readConfig(name: str = "config.json"):
    with open(name, "r", encoding="utf-8") as f:
        return json.load(f)
