import discord
import re
import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()
Discord_Token= os.getenv('Discord_Token')

#Setup Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gspread_client = gspread.authorize(creds)
sheet = gspread_client.open("Copy of List Harga Item GEP").sheet1

#Setup Discord
intents = discord.Intents.default()
intents.message_content = True
client_discord = discord.Client(intents=intents)

#Regex untuk mengangkap string
spot_pattern = re.compile(r"spot[:\-]?\s*(.+)", re.IGNORECASE)
price_pattern = re.compile(r"(?:change\s+price|price)(?:\s+to)?\s*[:\-]?\s*(.+)", re.IGNORECASE)

@client_discord.event
async def on_ready():
    print(f'Bot {client_discord.user} telah aktif!')
    
@client_discord.event
async def on_message(message):
    if client_discord.user.mentioned_in(message) and not message.author.bot:
        content = message.content

        # Ambil semua pasangan item dan harga dari pesan
        spot_matches = spot_pattern.findall(content)
        price_matches = price_pattern.findall(content)

        if not spot_matches or not price_matches or len(spot_matches) != len(price_matches):
            await message.channel.send("❌ Format tidak sesuai atau jumlah Spot dan Price tidak seimbang.")
            return

        # Ambil semua item dari Google Sheets
        item_list = sheet.col_values(1)
        item_lower_list = [i.lower().strip() for i in item_list]

        response_messages = []

        for item_raw, harga_raw in zip(spot_matches, price_matches):
            item_input = item_raw.strip().lower()
            harga = harga_raw.strip()

            try:
                index = item_lower_list.index(item_input) + 1
                sheet.update_cell(index, 2, harga)
                response_messages.append(f"✅ Harga untuk **{item_list[index - 1]}** diubah menjadi **{harga}**.")
            except ValueError:
                response_messages.append(f"⚠️ Item **{item_raw.strip()}** tidak ditemukan di Google Sheets.")

        # Kirim semua respon dalam satu balasan
        await message.channel.send("\n".join(response_messages))


client_discord.run(Discord_Token)