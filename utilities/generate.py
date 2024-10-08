import json

from entities.TasteOfTheBlock import TasteOfTheBlock


def generate_from_json(file):
    with open(file) as f:
        return TasteOfTheBlock(**json.load(f))
