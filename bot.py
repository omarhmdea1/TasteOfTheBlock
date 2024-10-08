import logging

import telebot
from telebot import types

from shared.shared_resource import shared_resource
from service import restaurant_srevice, load_demo_restaurants
from db_cart import CartsDB
from utilities.picture import send_pic

logging.basicConfig(
    format="[%(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

restaurant_db = shared_resource.get_restaurant_db()
cart_db = CartsDB()
bot = shared_resource.get_bot()

bot.set_my_commands([
    telebot.types.BotCommand("/create_restaurant", "Create a new restaurant"),
    telebot.types.BotCommand("/edit_restaurant", "Edit your restaurant"),
    telebot.types.BotCommand("/remove_restaurant", "Remove restaurant"),
    telebot.types.BotCommand("/show_restaurants", "List all restaurants"),
    telebot.types.BotCommand("/load_demo", "Load demo restaurants data"),
    telebot.types.BotCommand("/my_cart", "Show my cart")
])


@bot.message_handler(commands=['start'])
def start(message):
    start_message = """
Welcome to Taste of The Block, here you can add your restaurant or buy something delicious ;)
These commands will help you:

/create_restaurant - Create a new restaurant
/edit_restaurant - Edit your restaurant
/remove_restaurant - Remove restaurant
/show_restaurants - List all restaurants
/load_demo - Load demo restaurants data
/my_cart - Show my cart
    """
    bot.send_message(message.chat.id, start_message)


@bot.message_handler(commands=['load_demo'])
def load_demo(message):
    load_demo_restaurants.load_demo()
    bot.send_message(message.chat.id, "Demo data loaded successfully.")


@bot.message_handler(commands=['show_restaurants'])
# TODO: What if there is no restaurants ?
def show_restaurants(message):
    restaurants = list(restaurant_db.find_all())
    if not restaurants:
        bot.send_message(message.chat.id, "No restaurants available at the moment.")
        return

    for restaurant in restaurants:
        restaurant_info = f"Restaurant name: {restaurant['name']}\n\n" \
                          f"{restaurant['description']}\n\n" \
                          f"Category: {restaurant['category']}"

        keyboard = types.InlineKeyboardMarkup()
        menu_button = types.InlineKeyboardButton(
            text="Menu",
            callback_data=f"menu_{restaurant['user_id']}"
        )
        keyboard.add(menu_button)
        bot.send_message(message.chat.id, restaurant_info, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def show_menu(call):
    user_id = int(call.data.split("_")[1])
    restaurant = restaurant_db.restaurants.find_one({'user_id': user_id})
    if not restaurant:
        bot.send_message(call.message.chat.id, "Restaurant not found.")
        return

    restaurant_info = f"Restaurant name: {restaurant['name']}\n\n" \
                      f"{restaurant['description']}\n\n" \
                      f"Category: {restaurant['category']}"
    bot.send_message(call.message.chat.id, restaurant_info)

    if 'menu' in restaurant and restaurant['menu']:
        dishes_msg = "\nThese are the dishes we offer:\n"
        bot.send_message(call.message.chat.id, dishes_msg)

        for dish in restaurant['menu']:
            keyboard = types.InlineKeyboardMarkup()
            if 'photo' in dish:
                send_pic(call.message, dish['photo'])
            dish_info = f"Dish name: {dish['name']}\n\n" \
                        f"{dish['description']}\n\n" \
                        f"Price: {dish['price']}"
            menu_button = types.InlineKeyboardButton(
                text="ADD TO CART",
                callback_data=f"add_to_cart_{user_id}_{dish['name']}"
            )
            keyboard.row(menu_button)
            bot.send_message(call.message.chat.id, dish_info, reply_markup=keyboard)
            bot.send_message(call.message.chat.id, "Thank you for visiting our restaurant, hope to see soon 🤩")

    else:
        bot.send_message(call.message.chat.id, "No dishes available for this restaurant.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("add_to_cart_"))
def add_to_cart(call):
    data = call.data.split("_")

    try:
        restaurant_id = int(data[3])
    except (ValueError, IndexError):
        bot.send_message(call.message.chat.id, "Invalid restaurant ID.")
        return

    dish_name = "_".join(data[4:])
    dish = None

    restaurant = restaurant_db.restaurants.find_one({'user_id': restaurant_id})
    if restaurant and 'menu' in restaurant:
        dish = next((item for item in restaurant['menu'] if item['name'] == dish_name), None)

    if dish:
        user_cart = cart_db.carts.find_one({'user_id': call.from_user.id})
        if user_cart:
            cart = user_cart['cart']
            restaurant_key = str(restaurant_id)  # Convert restaurant_id to string
            if restaurant_key not in cart:
                cart[restaurant_key] = {}
            if dish_name in cart[restaurant_key]:
                cart[restaurant_key][dish_name]['quantity'] += 1
            else:
                cart[restaurant_key][dish_name] = {'dish': dish, 'quantity': 1}
            cart_db.carts.update_one({'user_id': call.from_user.id}, {"$set": {'cart': cart}})
        else:
            cart = {str(restaurant_id): {dish_name: {'dish': dish, 'quantity': 1}}}
            cart_db.carts.insert_one({'user_id': call.from_user.id, 'cart': cart})

        bot.send_message(call.message.chat.id, f"Added {dish['name']} to your cart.")
    else:
        bot.send_message(call.message.chat.id, "Dish not found or unavailable.")


@bot.message_handler(commands=['my_cart'])
def show_cart(message):
    user_cart = cart_db.carts.find_one({'user_id': message.from_user.id})
    if not user_cart:
        bot.send_message(message.chat.id, "No cart available. Please add items to the cart and try again.")
        return

    cart = user_cart.get('cart', {})
    total_quantity = 0
    total_sum = 0

    for restaurant_id, dishes in cart.items():
        for dish_name, item in dishes.items():
            dish = item['dish']
            quantity = item['quantity']
            total_price = quantity * dish['price']
            total_quantity += quantity
            total_sum += total_price
            cart_info = f"Dish name: {dish['name']}\n" \
                        f"Dish Price: {dish['price']}\n" \
                        f"Quantity: {quantity}\n" \
                        f"Total price: {total_price}"

            keyboard = types.InlineKeyboardMarkup()
            add_button = types.InlineKeyboardButton(text="+",
                                                    callback_data=f"add_dish_to_cart|{restaurant_id}|{dish_name}")
            remove_button = types.InlineKeyboardButton(text="-",
                                                       callback_data=f"remove_dish_from_cart|{restaurant_id}|{dish_name}")
            delete_button = types.InlineKeyboardButton(text="Delete",
                                                       callback_data=f"delete_dish_from_cart|{restaurant_id}|{dish_name}")
            keyboard.add(add_button, remove_button, delete_button)

            bot.send_message(message.chat.id, cart_info, reply_markup=keyboard)

    summary_message = f"The cart contains {total_quantity} items with a total price of {total_sum}."
    bot.send_message(message.chat.id, summary_message)


@bot.callback_query_handler(
    func=lambda call: call.data.startswith(("add_dish_to_cart|", "remove_dish_from_cart|", "delete_dish_from_cart|"))
)
def edit_cart(call):
    action, restaurant_id, dish_name = call.data.split("|", 2)
    user_id = call.from_user.id
    restaurant_id = int(restaurant_id)

    user_cart = cart_db.carts.find_one({'user_id': user_id})
    if not user_cart:
        bot.send_message(call.message.chat.id, "Cart not found.")
        return

    cart = user_cart.get('cart', {})
    restaurant_key = str(restaurant_id)
    if restaurant_key not in cart or dish_name not in cart[restaurant_key]:
        bot.send_message(call.message.chat.id, "Dish not found in cart.")
        return

    if action == "add_dish_to_cart":
        cart[restaurant_key][dish_name]['quantity'] += 1
    elif action == "remove_dish_from_cart":
        if cart[restaurant_key][dish_name]['quantity'] > 1:
            cart[restaurant_key][dish_name]['quantity'] -= 1
        else:
            del cart[restaurant_key][dish_name]
            if not cart[restaurant_key]:
                del cart[restaurant_key]
    elif action == "delete_dish_from_cart":
        del cart[restaurant_key][dish_name]
        if not cart[restaurant_key]:
            del cart[restaurant_key]

    cart_db.carts.update_one({'user_id': user_id}, {"$set": {'cart': cart}})
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    show_cart_with_user_id(call.message.chat.id)


def show_cart_with_user_id(user_id):
    user_cart = cart_db.carts.find_one({'user_id': user_id})
    if not user_cart:
        bot.send_message(user_id, "No cart available. Please add items to the cart and try again.")
        return

    cart = user_cart.get('cart', {})
    total_quantity = 0
    total_sum = 0

    for restaurant_id, dishes in cart.items():
        for dish_name, item in dishes.items():
            if 'dish' not in item:
                continue
            dish = item['dish']
            quantity = item['quantity']
            total_price = quantity * dish['price']
            total_quantity += quantity
            total_sum += total_price
            cart_info = f"Dish name: {dish['name']}\n" \
                        f"Dish Price: {dish['price']}\n" \
                        f"Quantity: {quantity}\n" \
                        f"Total price: {total_price}"

            keyboard = types.InlineKeyboardMarkup()
            add_button = types.InlineKeyboardButton(text="+",
                                                    callback_data=f"add_dish_to_cart|{restaurant_id}|{dish_name}")
            remove_button = types.InlineKeyboardButton(text="-",
                                                       callback_data=f"remove_dish_from_cart|{restaurant_id}|{dish_name}")
            delete_button = types.InlineKeyboardButton(text="Delete",
                                                       callback_data=f"delete_dish_from_cart|{restaurant_id}|{dish_name}")
            keyboard.add(add_button, remove_button, delete_button)

            bot.send_message(user_id, cart_info, reply_markup=keyboard)

    summary_message = f"The cart contains {total_quantity} items with a total price of {total_sum}."
    bot.send_message(user_id, summary_message)


@bot.message_handler(commands=['create_restaurant'])
def create_restaurant(message):
    logger.info(f"= Creating restaurant: #{message.chat.id}/{message.from_user.username!r}")
    msg = bot.send_message(message.chat.id, "Please choose a name for your restaurant.")
    print(msg)
    bot.register_next_step_handler(msg, restaurant_srevice.process_create_restaurant, msg.message_id)


@bot.message_handler(commands=['edit_restaurant'])
def edit_restaurant(message):
    logger.info(f"= Editing restaurant: #{message.chat.id}/{message.from_user.username!r}")
    restaurant_srevice.edit_restaurant(message)


@bot.message_handler(commands=['remove_restaurant'])
def remove_restaurant(message):
    logger.info(f"= Editing restaurant: #{message.chat.id}/{message.from_user.username!r}")
    restaurant_srevice.remove_restaurant(message)


# @bot.callback_query_handler(func=lambda call: True)
# def handle_delete_confirmation(call):
#     if call.data == "confirm_delete_restaurant":
#         restaurant_srevice.handle_confirm_delete_restaurant(call.message)
#     elif call.data == "cancel_delete_restaurant":
#         bot.send_message(call.message.chat.id, "Restaurant deletion canceled.")
#         logger.info(f"User {call.message.chat.id} canceled restaurant deletion.")


@bot.callback_query_handler(func=lambda call: True)
def handle_option(call):
    print(edit_restaurant)
    if call.data == "edit_restaurant_name":
        restaurant_srevice.handle_edit_restaurant_name(message=call.message)
    elif call.data == "edit_restaurant_des":
        restaurant_srevice.handle_edit_restaurant_des(message=call.message)
    elif call.data == "edit_restaurant_category":
        restaurant_srevice.handle_edit_restaurant_category(message=call.message)
    elif call.data == "add_dish_to_restaurant":
        restaurant_srevice.handle_add_dish(call.message)
    elif call.data == "edit_dish_in_restaurant":
        restaurant_srevice.handle_edit_dish(call.message)
    if call.data == "confirm_delete_restaurant":
        restaurant_srevice.handle_confirm_delete_restaurant(call.message)
    elif call.data == "cancel_delete_restaurant":
        bot.send_message(call.message.chat.id, "Restaurant deletion canceled.")
        logger.info(f"User {call.message.chat.id} canceled restaurant deletion.")


logger.info("* Start polling...")
bot.infinity_polling()
logger.info("* Bye!")
