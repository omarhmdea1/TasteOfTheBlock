from PIL import Image
from io import BytesIO

from shared.shared_resource import shared_resource

bot = shared_resource.get_bot()


def send_pic(message, photo_path):
    chat_id = message.chat.id
    im = Image.open(photo_path)
    im2 = im.resize((200, 200))
    im2 = im2.rotate(90)
    bio = BytesIO()
    bio.name = 'image.jpeg'
    im2.save(bio, 'JPEG')
    bio.seek(0)
    bot.send_photo(chat_id, photo=bio)
