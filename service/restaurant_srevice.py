import logging

from telebot import types

from entities.Restaurant import Restaurant
from shared.shared_resource import shared_resource

logging.basicConfig(
    format="[%(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

restaurant_db = shared_resource.get_restaurant_db()
bot = shared_resource.get_bot()


def process_create_restaurant(message, message_id):
    new_restaurant = {'user_id': message.chat.id}
    return process_restaurant_name_step(message, new_restaurant, message_id)


def process_restaurant_name_step(message, restaurant, message_id):
    logger.info(f"=Inserting restaurant name: {message.text} #{message.chat.id}/{message.from_user.username!r}")
    restaurant['name'] = message.text
    msg = bot.edit_message_text('Please provide some description for your restaurant.', chat_id=message.chat.id, message_id=message_id)
    bot.delete_message(chat_id=message.chat.id, message_id=message.id)
    bot.register_next_step_handler(msg, process_restaurant_description_step, restaurant, message_id)


def process_restaurant_description_step(message, restaurant, message_id):
    logger.info(f"=Inserting restaurant description: {message.text} #{message.chat.id}/{message.from_user.username!r}")
    restaurant['description'] = message.text
    msg = bot.edit_message_text('What is the category of your restaurant.', chat_id=message.chat.id,
                                message_id=message_id)
    bot.delete_message(chat_id=message.chat.id, message_id=message.id)
    bot.register_next_step_handler(msg, process_restaurant_category_step, restaurant, message_id)


def process_restaurant_category_step(message, restaurant, message_id):
    logger.info(f"=Inserting restaurant category: {message.text} #{message.chat.id}/{message.from_user.username!r}")
    restaurant['category'] = message.text
    res = restaurant_db.add(Restaurant.from_dict(restaurant))
    logger.info(f"=Done inserting restaurant {restaurant['name']} #{message.chat.id}/{message.from_user.username!r}")
    msg = bot.edit_message_text(f'Creating {res["name"]} done 😁', chat_id=message.chat.id,
                                message_id=message_id)
    bot.delete_message(chat_id=message.chat.id, message_id=message.id)


def edit_restaurant(message):
    keyboard = types.InlineKeyboardMarkup()
    edit_restaurant_name = types.InlineKeyboardButton(
        text="Edit restaurant name",
        callback_data="edit_restaurant_name"
    )
    edit_restaurant_des = types.InlineKeyboardButton(
        text="Edit restaurant description",
        callback_data="edit_restaurant_des"
    )
    edit_restaurant_category = types.InlineKeyboardButton(
        text="Edit restaurant category",
        callback_data="edit_restaurant_category"
    )
    add_dish_button = types.InlineKeyboardButton(
        text="Add new dish",
        callback_data="add_dish_to_restaurant"
    )
    edit_dish_button = types.InlineKeyboardButton(
        text="Edit a dish",
        callback_data="edit_dish_in_restaurant"
    )
    keyboard.add(edit_restaurant_name)
    keyboard.add(edit_restaurant_des)
    keyboard.add(edit_restaurant_category)
    keyboard.add(add_dish_button)
    keyboard.add(edit_dish_button)

    bot.send_message(message.chat.id, "Options:", reply_markup=keyboard)


def handle_add_dish(message):
    msg = bot.reply_to(message, 'Please provide a name for the dish.')
    bot.register_next_step_handler(msg, process_dish_name_step)


def process_dish_name_step(message):
    logger.info(f"=Inserting dish name: {message.text} #{message.chat.id}/{message.from_user.username!r}")
    dish = {'name': message.text}
    msg = bot.send_message(message.chat.id, 'Please provide a description for the dish.')
    bot.register_next_step_handler(msg, process_dish_description_step, dish)


def process_dish_description_step(message, dish):
    logger.info(f"=Inserting dish description: {message.text} #{message.chat.id}/{message.from_user.username!r}")
    dish['description'] = message.text
    msg = bot.send_message(message.chat.id, 'What is the price of the dish?')
    bot.register_next_step_handler(msg, process_dish_price_step, dish)


def process_dish_price_step(message, dish):
    try:
        price = float(message.text)
        dish['price'] = price
    except ValueError:
        bot.reply_to(message, 'Invalid price format. Please enter a numerical value.')
        return process_dish_price_step(message, dish)

    chat_id = message.chat.id

    res = restaurant_db.add_dish(chat_id, dish)
    logger.info(f"=Done inserting dish {dish['name']} #{message.chat.id}/{message.from_user.username!r}")
    bot.send_message(chat_id, f'Adding dish {res["name"]} done :)')


def handle_edit_dish(message):
    return None


def process_edit_restaurant(message, filed):
    new_value = message.text
    chat_id = message.chat.id
    result = restaurant_db.update_restaurant(chat_id, {filed: new_value})
    if result:
        bot.send_message(chat_id, "Done editing restaurant")


def handle_edit_restaurant_name(message):
    msg = bot.send_message(message.chat.id, "Please enter the new name for the restaurant.")
    bot.register_next_step_handler(msg, process_edit_restaurant, 'name')


def handle_edit_restaurant_des(message):
    msg = bot.send_message(message.chat.id, "Please enter the new description for the restaurant.")
    bot.register_next_step_handler(msg, process_edit_restaurant, 'description')


def handle_edit_restaurant_category(message):
    msg = bot.send_message(message.chat.id, "Please enter the new category for the restaurant.")
    bot.register_next_step_handler(msg, process_edit_restaurant, 'category')


def remove_restaurant(message):
    confirm_markup = types.InlineKeyboardMarkup(row_width=2)
    confirm_button = types.InlineKeyboardButton("Yes, delete", callback_data="confirm_delete_restaurant")
    cancel_button = types.InlineKeyboardButton("No, cancel", callback_data="cancel_delete_restaurant")
    confirm_markup.add(confirm_button, cancel_button)

    bot.send_message(message.chat.id, "Are you sure you want to delete your restaurant? This action cannot be undone.",
                     reply_markup=confirm_markup)


def handle_confirm_delete_restaurant(message):
    user_id = message.chat.id
    try:
        result = restaurant_db.remove_restaurant(user_id)
        if result:
            bot.send_message(message.chat.id, "Your restaurant has been successfully deleted.")
            logger.info(f"Deleted restaurant for user_id {user_id}")
        else:
            bot.send_message(message.chat.id, "Failed to delete the restaurant. It may not exist.")
            logger.warning(f"Failed to delete restaurant for user_id {user_id}")
    except Exception as e:
        bot.send_message(message.chat.id, "An error occurred while deleting the restaurant.")
        logger.error(f"Error deleting restaurant for user_id {user_id}: {str(e)}")