

import discord
from discord.ext import commands
from discord import app_commands
import requests

import json
import html
import re
import zlib
import base64
import os
import gzip
from typing import Optional
import io
from io import BytesIO
import nbtlib
from typing import Dict, Any
from gzip import GzipFile
from base64 import b64decode
from dotenv import load_dotenv
from keep_alive import keep_alive
keep_alive()
load_dotenv()

token = os.getenv("TOKEN")

parameters = {
    "Уникальный айди": "uniqueId",
    "Порядковый айди": "numberId",
    "Владелец": "owner",
    "Отображаемое имя": "displayName",
    "Размер": "size",
    "Голосов": "votes",
    "Тип генератора": "generatorName",
    "Спавн": "spawnPosition",
    "Строители": "builders",
    "Разработчики": "developers",
    "Игроки с полётом": "flyers",
    "Белый список": "whitelist",
    "Чёрный список": "blacklist",
    "Доступность": "locked",
    "Время": "time",
    "allowBuild": "allowBuild",
    "allowFlight": "allowFlight",
    "allowPhysics": "allowPhysics",
    "Дата создания": "createdTime",
    "Опубликованность": "published",
    "Рекомендованность": "recommended",
    "Отображаемый предмет": "displayItem",
    "Ресурспак": "resourcepacks",
    "Категории": "categories"
}

gen_type = {
    "flat": "🌄 Плоский",
    "void": "🕳️ Пустой",
    "coding": "💻 Кодинг",
    "debug": "🔧 Откладка",
    "sponge": "🧽 Губка Менгера"
}

categories = {
    "arcade": "Аркада",
    "versus": "Противостояния",
    "combat": "Сражение",
    "parkour": "Паркур",
    "adventure": "Приключение",
    "roleplay": "Ролевая",
    "strategy": "Стратегия",
    "puzzle": "Головоломки",
    "resources": "Ресурсы",
    "elimination": "Устранение",
    "creation": "Творчество",
    "miscellaneous": "Другое"
}


def decode_base64_to_json(base64_str: str) -> dict:
    """
    Декодирует Base64-строку и преобразует её в JSON-объект (dict).
    """
    decoded_bytes = base64.b64decode(base64_str)
    decoded_str = decoded_bytes.decode("utf-8")
    return json.loads(decoded_str)

def get_skin_value_nbt(snbt_str: str) -> str:
    """
    Извлекает значение Value текстуры скина из SNBT-строки с помощью nbtlib.
    Пример входной строки: '{Count:1b,id:"minecraft:player_head",tag:{SkullOwner:{...}}}'
    """
    # Парсим строку в NBT-объект
    nbt = nbtlib.parse_nbt(snbt_str)

    # Переход по вложенным ключам к Value
    value = nbt["tag"]["SkullOwner"]["Properties"]["textures"][0]["Value"]

    return value



def extract_id_from_encoded_data(encoded_data):
    try:
        # Декодируем строку из base64
        decoded_data = base64.b64decode(encoded_data)

        # Распаковываем данные (gzip)
        decompressed_data = zlib.decompress(decoded_data, zlib.MAX_WBITS | 16)

        # Преобразуем байты в строку
        text = decompressed_data.decode('utf-8', errors='ignore')

        # Ищем значение id
        match = re.search(r'minecraft:[a-z0-9_]+', text)
        if match:
            return match.group(0)
        else:
            return "minecraft:grass_block"  # Значение по умолчанию
    except Exception as e:
        print(f"Ошибка при декодировании: {e}")
        return "minecraft:grass_block"
def get_item_id(minecraft_str):
    # Находим значение после id:
    match = re.search(r'id:"([^"]+)"', minecraft_str)
    if match:
        if "player_head" in match.group(1):
            value = get_skin_value_nbt(minecraft_str)
            base64 = decode_base64_to_json(value)
            skin_hash = str(base64['textures']['SKIN']['url']).split('/')[-1]
            return f"https://mc-heads.net/head/{skin_hash}"
        else:
            print(1)
            return match.group(1)  # Возвращаем найденное значение
    else:
        item = extract_id_from_encoded_data(minecraft_str)
        if "player_head" not in item:
            if item:
                return item.replace("ID: ","")
            else:
                return "minecraft:grass_block"
        else:
            with GzipFile(fileobj=BytesIO(b64decode(minecraft_str.encode()))) as f:
                root = nbtlib.File.from_fileobj(f)  # сразу корень
                value = (
                    root.get("components", {})
                    .get("minecraft:profile", {})
                    .get("properties", [{}])[0]
                    .get("value")
                )

            if not value:
                return "minecraft:player_head"

            base64 = decode_base64_to_json(value)
            skin_hash = str(base64['textures']['SKIN']['url']).split('/')[-1]

            return f"https://mc-heads.net/head/{skin_hash}"


def strip_minecraft_colors(text):
    first_color = None

    # Ищем первый цвет: HTML-стиль или Minecraft-style (&a, §c и т.д.)
    color_match = re.search(r'&?#([0-9a-fA-F]{6})|[§&]([0-9a-fA-F])', text, flags=re.IGNORECASE)
    if color_match:
        if color_match.group(1):  # HTML-цвет, например #ff00ff
            first_color = color_match.group(1).lower()
        elif color_match.group(2):  # Minecraft код, например §a
            mc_colors = {
                '0': '000000', '1': '0000aa', '2': '00aa00', '3': '00aaaa',
                '4': 'aa0000', '5': 'aa00aa', '6': 'ffaa00', '7': 'aaaaaa',
                '8': '555555', '9': '5555ff', 'a': '55ff55', 'b': '55ffff',
                'c': 'ff5555', 'd': 'ff55ff', 'e': 'ffff55', 'f': 'ffffff'
            }
            first_color = mc_colors[color_match.group(2).lower()]

    # Удаляем все цветовые и форматирующие коды
    text = re.sub(r'&?#(?:[0-9a-fA-F]{6})', '', text)
    text = re.sub(r'§[0-9a-fklmnor]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'&[0-9a-fklmnor]', '', text, flags=re.IGNORECASE)

    # Декодируем HTML-сущности
    text = html.unescape(text)

    # Обработка строки типа '\\n'
    parts = text.split('\\n', 1)
    title = parts[0].strip()
    description = parts[1].strip() if len(parts) > 1 else None
    if description is None:
        description = ""
        
    description = description.replace("\\n","\n")

    return title, description, f"#{first_color}" if first_color else "#ffffff"


def colourr(hex_color):
    return int(hex_color.lstrip('#'), 16)

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@client.event
async def on_ready():
    await client.tree.sync()
    print(f'Бот {client.user} готов!')

@client.tree.command(name="world",description="Получает информацию о мире по айди мира")
@app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
@app_commands.choices(
    parameter=[
        app_commands.Choice(name="Уникальный айди", value="uniqueId"),
        app_commands.Choice(name="Порядковый айди", value="numberId"),
        app_commands.Choice(name="Владелец", value="owner"),
        app_commands.Choice(name="Отображаемое имя", value="displayName"),
        app_commands.Choice(name="Размер", value="size"),
        app_commands.Choice(name="Голосов", value="votes"),
        app_commands.Choice(name="Тип генератора", value="generatorName"),
        app_commands.Choice(name="Спавн", value="spawnPosition"),
        app_commands.Choice(name="Строители", value="builders"),
        app_commands.Choice(name="Разработчики", value="developers"),
        app_commands.Choice(name="Игроки с полётом", value="flyers"),
        app_commands.Choice(name="Белый список", value="whitelist"),
        app_commands.Choice(name="Чёрный список", value="blacklist"),
        app_commands.Choice(name="Доступность", value="locked"),
        app_commands.Choice(name="Время", value="time"),
        app_commands.Choice(name="allowBuild", value="allowBuild"),
        app_commands.Choice(name="allowFlight", value="allowFlight"),
        app_commands.Choice(name="allowPhysics", value="allowPhysics"),
        app_commands.Choice(name="Дата создания", value="createdTime"),
        app_commands.Choice(name="Опубликованность", value="published"),
        app_commands.Choice(name="Рекомендованность", value="recommended"),
        app_commands.Choice(name="Отображаемый предмет", value="displayItem"),
        app_commands.Choice(name="Ресурспак", value="resourcepacks"),
        app_commands.Choice(name="Категории", value="categories")
    ]
)
@app_commands.user_install()
async def world(interaction: discord.Interaction, id: str, parameter: Optional[str] = None):
    response = requests.get(f"http://api.creative.justmc.io/public/creative/worlds/get/{id}")
    if response.status_code == 200:
        data = response.json()
        if parameter:
            if parameter in data:
                await interaction.response.send_message(f"**{next((k for k, v in parameters.items() if v == parameter), None)}:**\n\n``{data[parameter]}``", ephemeral=True)


        if parameter is None:


            owner_data = data["owner"]
            owner_name = owner_data["name"]

            genType = data["generatorName"]

            if genType not in gen_type:
                genName = "❓ Неизвестен"
            else:
                genName = gen_type[genType]

            categories_list = data["categories"]
            categoriess = ', '.join([
                translated_category.capitalize() if i == 0 else translated_category.lower()
                for i, category in enumerate(categories_list)
                for translated_category in [categories.get(category, category)]
            ])

            size = data["size"]
            votes = data["votes"]

            builders_list = data["builders"]
            builders_text = ""
            for player in builders_list:
                player = player["name"]
                builders_text = builders_text + f"{player}, "
            builders_text = builders_text[:-2] + ""
            if len(builders_list)<1:
                builders_text = "Нет"

            developers_list = data["developers"]
            developers_text = ""
            for player in developers_list:
                player = player["name"]
                developers_text = developers_text + f"{player}, "
            developers_text = developers_text[:-2] + ""
            if len(developers_list)<1:
                developers_text = "Нет"

            flyers_list = data["flyers"]
            flyers_text = ""
            for player in flyers_list:
                player = player["name"]
                flyers_text = flyers_text + f"{player}, "
            flyers_text = flyers_text[:-2] + ""
            if len(flyers_list)<1:
                flyers_text = "Нет"

            whitelist_data = data["whitelist"]
            whitelist_text = ""
            for player in whitelist_data:
                player = player["name"]
                whitelist_text = whitelist_text + f"{player}, "
            whitelist_text = whitelist_text[:-2] + ""
            if len(whitelist_data)<1:
                whitelist_text = "Нет"

            blacklist_data = data["blacklist"]
            blacklist_text = ""
            for player in blacklist_data:
                player = player["name"]
                blacklist_text = blacklist_text + f"{player}, "
            blacklist_text = blacklist_text[:-2] + ""
            if len(blacklist_data)<1:
                blacklist_text = "Нет"

            createdTime = data["createdTime"]
            createdTime = createdTime.split("T")[0:]
            createdTime = createdTime[0]
            createdTime = createdTime.split("-")[0:]

            locked = data["locked"]
            if locked == True:
                locked = "Закрыт"
            else:
                locked = "Открыт"

            year = createdTime[0]
            month = createdTime[1]
            day = createdTime[2]

            createdTime = f"{day}/{month}/{year}"

            published = data["published"]
            if published == True:
                published = "Да"
            else:
                published = "Нет"

            recommended = data["recommended"]
            if recommended == True:
                recommended = "Да"
            else:
                recommended = "Нет"

            displayName = data["displayName"]
            defaultName, description, color = strip_minecraft_colors(displayName)

            item_raw = data["displayItem"]

            if item_raw != None:
                itemData = get_item_id(data["displayItem"])
                if "https://mc-heads.net/head/" not in itemData:
                    itemData = itemData.replace("minecraft:", "")
                    url_item = f"https://mc.nerothe.com/img/1.21.4/minecraft_{itemData}.png"
                else:
                    url_item = itemData
            else:
                itemData = "grass_block"

            embed = discord.Embed(title=f"{defaultName}", description=description, color=colourr(f"{color}"))
            embed.add_field(name="Создатель", value=f"👤 {owner_name}")
            embed.add_field(name="Айди", value=f"🆔 {id}")
            embed.add_field(name="Дата создания", value=f"🕦 {createdTime}", inline=True)

            embed.add_field(name="",value="",inline=False)

            embed.add_field(name="Доступность", value=f"🚪 {locked}", inline=True)
            embed.add_field(name="Опубликован", value=f"📢 {published}", inline=True)
            embed.add_field(name="Рекомендован", value=f"🌟 {recommended}", inline=True)

            embed.add_field(name="", value="", inline=False)

            embed.add_field(name="Размер", value=f"🗺️ {size * 32}x{size * 32}", inline=True)
            embed.add_field(name="Голосов", value=f"⭐ {votes}", inline=True)
            embed.add_field(name="Тип генератора", value=genName)


            embed.add_field(name="", value="", inline=False)

            embed.add_field(name="Категории", value=f"🗂️ {categoriess}")
            embed.add_field(name="Белый список", value=f"📄 {whitelist_text}",inline=True)
            embed.add_field(name="Разработчики", value=f"👨‍💻 {developers_text}", inline=True)

            embed.add_field(name="", value="", inline=False)

            embed.add_field(name="Строители", value=f"⚒️ {builders_text}", inline=True)
            embed.add_field(name="Чёрный список", value=f"🚫 {blacklist_text}")

            embed.set_thumbnail(url=url_item)

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("**Мира не существует!**")

@client.tree.command(name="about",description="Показывает информацию о боте")
@app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
@app_commands.user_install()
async def about(interaction: discord.Interaction):
    await interaction.response.send_message("Бот взаимодействует с **API** JustMc, благодаря чему ты можешь получать данные о мирах.\n\nЕсли вы нашли баг то сообщите создателю бота:\n- DS **dominosmersi**\n- TG **@DominosMersi**")


client.run(token)
