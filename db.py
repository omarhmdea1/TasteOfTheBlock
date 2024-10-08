from pymongo import MongoClient

from entities.Restaurant import Restaurant


class RestaurantDB:
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.get_database("taste_of_the_block_bot")
        self.restaurants = self.db.get_collection("restaurants")

    def add(self, restaurant: Restaurant):
        self.restaurants.insert_one(restaurant.to_dict())
        return self.restaurants.find_one({'user_id': restaurant.user_id})

    def find_all(self):
        return self.restaurants.find()

    def add_dish(self, user_id, dish: dict):
        new_dish = {
            'name': dish.get("name"),
            'description': dish.get("description"),
            'price': dish.get("price")
        }
        restaurant = self.restaurants.find_one({'user_id': user_id})

        if restaurant:
            restaurant['menu'].append(new_dish)

            result = self.restaurants.update_one(
                {'user_id': user_id},
                {'$set': {'menu': restaurant['menu']}}
            )

            if result.modified_count > 0:
                return new_dish
            else:
                raise Exception("Failed to update restaurant with new dish.")
        else:
            raise ValueError("Restaurant not found for the given user_id.")

    def update_restaurant(self, user_id, updates: dict):
        result = self.restaurants.update_one(
            {'user_id': user_id},
            {'$set': updates}
        )
        return result.modified_count > 0

    def remove_restaurant(self, user_id):
        result = self.restaurants.delete_one({'user_id': user_id})
        return result.deleted_count > 0

