
import logging
import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1

API_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

DATA_FILE = "songs.json"
ADMIN_ID = 1918624551

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("👋 Welcome to Squonk Radio V0.5.0!
Use /setup to link your group.")

@dp.message_handler(commands=['setup'])
async def cmd_setup(message: types.Message):
    if message.chat.type != "private":
        return await message.reply("❗ Use /setup in a private chat.")
    if message.from_user.id != ADMIN_ID:
        return await message.reply("❌ Only the bot admin can use /setup at this time.")
    await message.reply("📨 Send me `GroupID: <your_group_id>` to register a group.")

@dp.message_handler(commands=['playlist'])
async def cmd_playlist(message: types.Message):
    data = load_data()
    group_id = str(message.chat.id)
    songs = data.get(group_id, [])
    if not songs:
        return await message.reply("❌ No songs found for this group.")
    text = "🎵 Playlist:
" + "
".join(f"- {s['title']} by {s['artist']}" for s in songs)
    await message.reply(text)

@dp.message_handler(content_types=types.ContentType.AUDIO)
async def handle_audio(message: types.Message):
    data = load_data()
    if message.audio:
        audio = message.audio
        file_name = audio.file_name or "Unknown.mp3"
        group_id = str(message.caption or message.chat.id)
        if not group_id.startswith("GroupID:"):
            return await message.reply("❗ Please first send `GroupID: <your_group_id>`.")
        group_id = group_id.split(":")[1].strip()
        file_info = await bot.get_file(audio.file_id)
        file_path = file_info.file_path
        file = await bot.download_file(file_path)
        with open(file_name, "wb") as f:
            f.write(file.read())
        audiofile = MP3(file_name, ID3=ID3)
        title = audiofile.tags.get("TIT2", TIT2(encoding=3, text="Unknown")).text[0]
        artist = audiofile.tags.get("TPE1", TPE1(encoding=3, text="Unknown")).text[0]
        os.remove(file_name)
        if group_id not in data:
            data[group_id] = []
        data[group_id].append({"title": title, "artist": artist})
        save_data(data)
        await message.reply(f"✅ Saved `{title}` by `{artist}` for group {group_id}")

def main():
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    main()
