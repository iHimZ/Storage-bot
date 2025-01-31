import json
import os
from telethon import TelegramClient, events
import asyncio


with open("config.json", "r") as config_file:
    config = json.load(config_file)


BOT_TOKEN = config.get("bot_token")
OWNER_ID = config.get("owner_id")


if not OWNER_ID or not BOT_TOKEN:
    raise ValueError("Please set 'owner_id' and 'bot_token' in config.json.")


client = TelegramClient('bot', config["api_id"], config["api_hash"]).start(bot_token=BOT_TOKEN)


PLUGINS_DIR = "plugins"

if not os.path.exists(PLUGINS_DIR):
    os.makedirs(PLUGINS_DIR)
    print(f"Error creating plugins directory")


# Load plugins dynamically
def load_plugins():
    for file in os.listdir(PLUGINS_DIR):
        if file.endswith(".py"):
            try:
                plugin_name = file[:-3]
                exec(open(os.path.join(PLUGINS_DIR, file)).read(), globals())
                print(f"Loaded plugin: {plugin_name}")
            except Exception as e:
                print(f"Error loading plugin {file}: {e}")




@client.on(events.NewMessage(pattern=r"^/start$"))
async def start(event):
    if event.sender_id == OWNER_ID:
        await event.reply("Bot is running and ready!")
    else:
        await event.reply("Hello! I am your Storage bot.\nHit /help to get started.")



@client.on(events.NewMessage(pattern=r"/reload"))
async def reload(event):
    if event.sender_id == OWNER_ID:
        load_plugins()
        await event.reply("Plugins reloaded successfully!")
    else:
        await event.reply("You don't have permission to do this.")


@client.on(events.NewMessage(pattern='/ping'))
async def ping(event):
    await event.reply('Pong!')


@client.on(events.NewMessage(pattern='/fine'))
async def fine(event):
    await event.reply('**Perfectly fine!**')



@client.on(events.NewMessage(pattern=r'/id'))
async def get_id(event):
    reply = await event.get_reply_message()

    if reply:

        user_id = reply.sender_id
        await event.reply(
            f"**Replied User ID:** `{user_id}`\n"
        )
    else:

        chat_id = event.chat_id
        await event.reply(
            f"**Chat ID:** `{chat_id}`\n"
        )


if __name__ == "__main__":
    print("Starting bot...")
    load_plugins()
    client.run_until_disconnected()
