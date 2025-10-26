import os
import re
os.system("pip install -r requirement.txt")
import discord
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()
Discord_Token= os.getenv('Discord_Token')

#Setup Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gspread_client = gspread.authorize(creds)
sheet = gspread_client.open("Spot Mass GEP").sheet1

#Setup Discord
intents = discord.Intents.default()
intents.message_content = True
client_discord = discord.Client(intents=intents)

#Regex untuk mengangkap string
spot_pattern = re.compile(r"spot[:\-]?\s*(.+)", re.IGNORECASE)
price_pattern = re.compile(r"(?:change\s+price|price)(?:\s+to)?\s*[:\-]?\s*(.+)", re.IGNORECASE)

ALLOWED_GUILDS = [
"1273930569335705600"
"1376936819958087800"
]  

@client_discord.event
async def on_guild_join(guild):
    if str(guild.id) not in ALLOWED_GUILDS:
        print(f"❌ Unauthorized guild joined: {guild.name} ({guild.id}), leaving...")
        await guild.leave()
    else:
        print(f"✅ Joined authorized guild: {guild.name} ({guild.id})")

@client_discord.event
async def on_ready():
    print(f'{client_discord.user} telah aktif!')
    
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

        # Ambil semua data dari Google Sheets
        all_data = sheet.get_all_values()
        headers = all_data[0]
        rows = all_data[1:]
        
        #Mencari indeks kolom "Nama Item"
        try:
            idx_nama_item = headers.index("Nama Item")
            idx_harga = headers.index("Harga")
        except ValueError:
            await message.channel.send("❌ Kolom 'Nama Item' atau 'Harga' tidak ditemukan di Google Sheets.")
            return

        response_messages = []

        for item_raw, harga_raw in zip(spot_matches, price_matches):
            item_input = item_raw.strip().lower()
            harga = harga_raw.strip()

            found = False
            for i, row  in enumerate(rows):
                item_name = row[idx_nama_item].strip().lower()
                if item_input == item_name:
                    sheet.update_cell(i + 2, idx_harga + 1, harga)
                    response_messages.append(f"✅ Harga untuk **{row[idx_nama_item]}** diubah menjadi **{harga}**.")
                    found = True
                    break
                
            if not found:
                response_messages.append(f"⚠️ Item **{item_raw.strip()}** tidak ditemukan di Google Sheets.")

        # Kirim semua respon dalam satu balasan
        await message.channel.send("\n".join(response_messages))


client_discord.run(Discord_Token)