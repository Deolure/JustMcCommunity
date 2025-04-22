

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
from dotenv import load_dotenv
from keep_alive import keep_alive
keep_alive()
load_dotenv()

token = os.getenv("TOKEN")
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
        return match.group(1)  # Возвращаем найденное значение
    else:
        item = extract_id_from_encoded_data(minecraft_str)
        if item:
            return item.replace("ID: ","")
        else:
            return "minecraft:grass_block"

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
    text = text.split('\\n')[0]

    return text.strip(), f"#{first_color}" if first_color else "#ffffff"


def colourr(hex_color):
    return int(hex_color.lstrip('#'), 16)

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@client.event
async def on_ready():
    await client.tree.sync()

@client.tree.command(name="world",description="Получает информацию о мире по айди мира")
@app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
@app_commands.user_install()
async def hello(interaction: discord.Interaction, id: str):
    response = requests.get(f"http://api.creative.justmc.io/public/creative/worlds/get/{id}")
    if response.status_code == 200:
        data = response.json()

        owner_data = data["owner"]
        owner_name = owner_data["name"]

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
        defaultName, color = strip_minecraft_colors(displayName)

        itemData = get_item_id(data["displayItem"])
        itemData = itemData.replace("minecraft:","")

        embed = discord.Embed(title=f"{defaultName}", description=f"Владелец мира: {owner_name}", color=colourr(f"{color}"))
        embed.add_field(name="Дата создания", value=f"🕦 {createdTime}", inline=True)
        embed.add_field(name="Размер", value=f"🗺️ {size * 32}x{size * 32}", inline=True)
        embed.add_field(name="Голосов", value=f"⭐ {votes}",inline=True)

        embed.add_field(name="",value="",inline=False)

        embed.add_field(name="Доступность", value=f"🚪 {locked}", inline=True)
        embed.add_field(name="Опубликован", value=f"📢 {published}", inline=True)
        embed.add_field(name="Рекомендован", value=f"⭐ {recommended}", inline=True)

        embed.add_field(name="", value="", inline=False)

        embed.add_field(name="Белый список", value=f"📄 {whitelist_text}",inline=True)
        embed.add_field(name="Разработчики", value=f"👨‍💻 {developers_text}", inline=True)
        embed.add_field(name="Строители", value=f"⚒️ {builders_text}", inline=True)

        embed.add_field(name="", value="", inline=False)

        embed.add_field(name="Чёрный список", value=f"🚫 {blacklist_text}")

        embed.set_thumbnail(url=f"https://mc.nerothe.com/img/1.21.4/minecraft_{itemData}.png")

        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("**Мира не существует!**")

@client.tree.command(name="about",description="Показывает информацию о боте")
@app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
@app_commands.user_install()
async def about(interaction: discord.Interaction):
    await interaction.response.send_message("Бот взаимодействует с **API** JustMc, благодаря чему ты можешь получать данные о мирах.\n\nЕсли вы нашли баг то сообщите создателю бота:\n- DS **dominosmersi**\n- TG **@DominosMersi**")


client.run(token)
