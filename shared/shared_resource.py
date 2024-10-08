import telebot

import bot_secrets
from db import RestaurantDB


class SharedResource:
    def __init__(self):
        self.restaurant_db = RestaurantDB()
        self.bot = telebot.TeleBot(bot_secrets.BOT_TOKEN)

    def get_restaurant_db(self):
        return self.restaurant_db

    def get_bot(self):
        return self.bot


shared_resource = SharedResource()
