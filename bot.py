import telebot
from PIL import Image, ImageOps
import io
from telebot import types
import random

TOKEN = '<token goes here>'
bot = telebot.TeleBot(TOKEN)

user_states = {}  # тут будем хранить информацию о действиях пользователя

# набор символов из которых составляем изображение
ASCII_CHARS = '@%#*+=-:. '

# Список шуток
JOKES = [
    "У мухи, прилипшей к луковице, закончились слёзы!",
    "Алкоголик Николай упал в море, но его спасли круги под глазами.",
    "У нас может быть только 2 реальных прогноза погоды: грязь подсохла и грязь подмёрзла. Остальное просто: грязь!",
    "Сигареты Петр I - Проруби окно в легких!",
    "Почему в Африке так много болезней? Потому что таблетки нужно запивать водой.",
    "У вас болит спина? Ломает кости? Крутит суставы? Идите работать в прогноз погоды!",
    "Парень, который в школе читал только краткие пересказы произведений, вырос, состарился и умер."
]

# Список комплиментов
COMPLIMENTS = [
    "Ты выглядишь потрясающе сегодня!",
    "Ты просто совершенство.",
    "У меня начинает быстрее биться сердце, когда я вижу тебя",
    "Мне нравится твой стиль.",
    "У тебя самый лучший смех.",
    "Ты талантлив!",
    "Ты самый  умный"
]

def resize_image(image, new_width=100):
    width, height = image.size
    ratio = height / width
    new_height = int(new_width * ratio)
    return image.resize((new_width, new_height))


def grayify(image):
    return image.convert("L")


def image_to_ascii(image_stream, new_width=40):
    # Переводим в оттенки серого
    image = Image.open(image_stream).convert('L')

    # меняем размер сохраняя отношение сторон
    width, height = image.size
    aspect_ratio = height / float(width)
    new_height = int(
        aspect_ratio * new_width * 0.55)  # 0,55 так как буквы выше чем шире
    img_resized = image.resize((new_width, new_height))

    img_str = pixels_to_ascii(img_resized)
    img_width = img_resized.width

    max_characters = 4000 - (new_width + 1)
    max_rows = max_characters // (new_width + 1)

    ascii_art = ""
    for i in range(0, min(max_rows * img_width, len(img_str)), img_width):
        ascii_art += img_str[i:i + img_width] + "\n"

    return ascii_art


def pixels_to_ascii(image):
    pixels = image.getdata()
    characters = ""
    for pixel in pixels:
        characters += ASCII_CHARS[pixel * len(ASCII_CHARS) // 256]
    return characters


# Огрубляем изображение
def pixelate_image(image, pixel_size):
    image = image.resize(
        (image.size[0] // pixel_size, image.size[1] // pixel_size),
        Image.NEAREST
    )
    image = image.resize(
        (image.size[0] * pixel_size, image.size[1] * pixel_size),
        Image.NEAREST
    )
    return image


# Меняет цвета изображения на противоположные, тем самым создавая "негатив" изображения.
def invert_colors(image):
    return ImageOps.invert(image)


# Создает отраженную копию изображения по горизонтали.
def mirror_image(image):
   return ImageOps.mirror(image)


# Изображение преобразуется так, чтобы его цвета отображались в виде тепловой карты, от синего (холодные области) до красного (теплые области)
def convert_to_heatmap(image):
    return ImageOps.colorize(image.convert('L'), black='blue', white='red', mid='#984f4f', midpoint=127)


# Изменяет размер изображения, сохраняя пропорции, чтобы его максимальное измерение не превышало заданного максимума (например, 512 пикселей)
def resize_for_sticker(image, max_size=512):
    width, height = image.size
    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        image = image.resize((new_width, new_height))
    return image


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Send me an image, and I'll provide options for you!")

# Отправляет случайную шутку пользователю.
@bot.message_handler(commands=['random_joke'])
def send_random_joke(message):
    joke = random.choice(JOKES)
    bot.reply_to(message, joke)


# Отправляет случайный комплимент
@bot.message_handler(commands=['RandomCompliment'])
def send_random_compliment(message):
    random_compliment = random.choice(COMPLIMENTS)
    bot.send_message(message.chat.id, random_compliment)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "I got your photo! Please choose what you'd like to do with it.",
                 reply_markup=get_options_keyboard())
    user_states[message.chat.id] = {'photo': message.photo[-1].file_id}


def get_options_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    pixelate_btn = types.InlineKeyboardButton("Pixelate", callback_data="pixelate")
    ascii_btn = types.InlineKeyboardButton("ASCII Art", callback_data="ascii")
    keyboard.add(pixelate_btn, ascii_btn)
    return keyboard


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "pixelate":
        bot.answer_callback_query(call.id, "Pixelating your image...")
        pixelate_and_send(call.message)
    elif call.data == "ascii":
        bot.answer_callback_query(call.id, "Converting your image to ASCII art...")
        ascii_and_send(call.message)


def pixelate_and_send(message):
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    pixelated = pixelate_image(image, 20)

    output_stream = io.BytesIO()
    pixelated.save(output_stream, format="JPEG")
    output_stream.seek(0)
    bot.send_photo(message.chat.id, output_stream)


def handle_message(message):
    global ASCII_CHARS
    ASCII_CHARS = list(set(message.text))

def ascii_and_send(message):
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    ascii_art = image_to_ascii(image_stream)
    bot.send_message(message.chat.id, f"```\n{ascii_art}\n```", parse_mode="MarkdownV2")



bot.polling(none_stop=True)
