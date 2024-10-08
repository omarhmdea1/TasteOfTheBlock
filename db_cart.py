from pymongo import MongoClient


class CartsDB:
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.get_database("taste_of_the_block_bot")
        self.carts = self.db.get_collection("carts")

    def add_to_cart(self, user_id: int, dish: dict):
        user_cart = self.carts.find_one({'user_id': user_id})
        dish_name = dish['name']

        if user_cart:
            cart = user_cart['cart']
            if dish_name in cart:
                cart[dish_name]['quantity'] += 1
            else:
                cart[dish_name] = {'dish': dish, 'quantity': 1}
            self.carts.update_one({'user_id': user_id}, {"$set": {'cart': cart}})
        else:
            cart = {dish_name: {'dish': dish, 'quantity': 1}}
            self.carts.insert_one({'user_id': user_id, 'cart': cart})

    def get_cart(self, user_id: int):
        return self.carts.find_one({'user_id': user_id})
