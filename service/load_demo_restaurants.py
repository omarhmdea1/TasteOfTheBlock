from shared.shared_resource import shared_resource
from utilities.generate import generate_from_json

restaurant_db = shared_resource.get_restaurant_db()


def load_demo():
    taste_of_the_block = generate_from_json("restaurants.json")
    for res in taste_of_the_block.restaurants:
        restaurant_db.add(res)
