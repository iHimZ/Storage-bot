import sys
import asyncio
import time
from telethon import events
from telethon.tl.types import User  # Import User class to check sender type

# Ensure UTF-8 encoding for console output
sys.stdout.reconfigure(encoding='utf-8')

# Log storage
log_data = []
LOG_CHANNEL = config.get("log_channel")  # Set this in config.json

if not LOG_CHANNEL:
    raise ValueError("Please set 'log_channel' in config.json.")

# Ensure log channel is an integer
try:
    LOG_CHANNEL = int(LOG_CHANNEL)  # Convert from string to integer if needed
except ValueError:
    raise ValueError("Invalid log_channel ID! Make sure it's a valid integer.")

OWNER_ID = config.get("owner_id")  # Get OWNER_ID from config.json

if not OWNER_ID:
    raise ValueError("Please set 'OWNER_ID' in config.json.")

# Function to log events
def log_event(user, user_id, command, event_type="command"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    if event_type == "error":
        log_entry = f"**DEBUG:** {command}\n"  # Error Logs
    elif user_id == OWNER_ID:
        log_entry = f"**OWNER:** {user} {command}"  # Owner Commands
    else:
        log_entry = f"{user} ({user_id}) used command `{command}\n`"  # Normal User Commands

    log_data.append(log_entry)
    try:
        with open("logs.txt", "a", encoding="utf-8", errors="ignore") as log_file:
            log_file.write(log_entry + "\n")
    except UnicodeEncodeError as e:
        print(f" Error writing to log file: {e}")

# Log user commands
@client.on(events.NewMessage())
async def log_commands(event):
    if event.text.startswith("/"):  # Only log commands
        sender = await event.get_sender()
        if isinstance(sender, User):  # Check if the sender is a user
            user_name = sender.first_name or "Unknown"
            user_id = sender.id
            command = event.text
            log_event(user_name, user_id, command)
        else:
            # Handle the case when the sender is a channel or group
            log_event("Unknown", event.sender_id, event.text)

# Log errors/debug messages
@client.on(events.NewMessage(pattern=r"/debug"))
async def debug_command(event):
    if event.sender_id == OWNER_ID:
        log_event("DEBUG", "SYSTEM", "Bot debug command executed", event_type="error")
        await event.reply("Debug mode activated!")

# Periodically send logs in conversation format
async def send_logs():
    global log_data
    while True:
        await asyncio.sleep(30)  # Send logs every 30 seconds
        if log_data:
            log_text = "\n".join(log_data)
            try:
                if isinstance(LOG_CHANNEL, int):  # Check if the channel ID is an integer
                    await client.send_message(LOG_CHANNEL, f" **Last 30 Seconds Logs:**\n\n{log_text}")
                else:
                    print(f"Error: LOG_CHANNEL is not a valid integer.")
                log_data.clear()  # Clear logs after sending
            except Exception as e:
                print(f" Error sending logs: {e}")

# Ensure logging task starts after bot connects
async def start_logger():
    await asyncio.sleep(5)  # Delay startup to avoid DB conflicts
    client.loop.create_task(send_logs())  # Start logging task

client.loop.create_task(start_logger())  # Start logging task
