import os
import random
import string
from telethon import events, Button
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from datetime import datetime, timedelta
import logging
import sqlite3


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


db_file = "media_storage.db"
if not os.path.exists(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token TEXT UNIQUE,
                    file_id INTEGER,
                    chat_id INTEGER,
                    file_size TEXT,
                    upload_time TEXT,
                    expiry_time TEXT,
                    user_id INTEGER,
                    description TEXT)""")

    conn.commit()
    conn.close()




def save_file_data(token, file_id, chat_id, file_size, expiry_time, user_id, description):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    upload_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO files (token, file_id, chat_id, file_size, upload_time, expiry_time, user_id, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (token, file_id, chat_id, file_size, upload_time, expiry_time, user_id, description))
    conn.commit()
    conn.close()


def fetch_file_data(token):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE token = ?", (token,))
    result = cursor.fetchone()
    conn.close()
    return result

def fetch_user_files(user_id):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE user_id = ?", (user_id,))
    result = cursor.fetchall()
    conn.close()
    return result


def delete_file(token):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM files WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def delete_expired_tokens():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM files WHERE expiry_time < ?", (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),))
    conn.commit()
    conn.close()

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

# Token expiration time (24 hours from the creation time) , Customisable
def get_token_expiry(hours=24):
    return (datetime.utcnow() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")

# Bot settings
bot_username = 'DataPocket_bot'  # Replace with your Bot Username
storage_channel_id = -1002324683289  # Replace with your private group's ID ()


@client.on(events.NewMessage(pattern='/upload'))
async def start_upload(event):
    user_id = event.sender_id
    await event.reply(
        "Send me a photo, document, or video, and I will provide you with a link to download it.\n\n"
        "You can also add a description for your file.\n"
        "Supported formats: Photos, Documents, and Videos.",
        buttons=[Button.inline("Cancel", b"cancel_upload")]
    )
    global allow_upload
    allow_upload[user_id] = True


@client.on(events.CallbackQuery(pattern=b'cancel_upload'))
async def cancel_upload(event):
    user_id = event.sender_id
    allow_upload[user_id] = False
    await event.edit("Upload canceled.")


allow_upload = {}

@client.on(events.NewMessage)
async def upload_file(event):
    user_id = event.sender_id
    if user_id not in allow_upload or not allow_upload[user_id]:
        return

    if event.media:
        msg = event.message
        token = generate_token()

        try:

            description = "No description"
            if isinstance(msg.media, MessageMediaPhoto):
                file_size = "Unknown size"
                uploaded_message = await client.send_message(storage_channel_id, file=msg.media)
            elif isinstance(msg.media, MessageMediaDocument):
                file_size = msg.media.size if hasattr(msg.media, 'size') else "Unknown size"
                uploaded_message = await client.send_message(storage_channel_id, file=msg.media)
            else:

                await event.reply("Unsupported media type. Please upload photos, documents, or videos.")
                return

            if msg.raw_text:
                description = msg.raw_text


            expiry_time = get_token_expiry()
            save_file_data(token, uploaded_message.id, uploaded_message.chat_id, file_size, expiry_time, user_id, description)


            download_link = f"https://t.me/{bot_username}?start={token}"
            await event.reply(
                f"File uploaded successfully!\n\n"
                f"Download Link: [Click Here]({download_link})\n"
                f"This link will expire in 24 hours.\n"
                f"Description: {description}"
            )

            logger.info(f"File uploaded. Token generated: {token}")
            allow_upload[user_id] = False

        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            await event.reply("An error occurred while uploading the file. Please try again.")





@client.on(events.NewMessage)
async def handle_start_link(event):
    if event.text.startswith(f'/start '):
        token = event.text.split(' ')[1]
        file_info = fetch_file_data(token)

        if file_info:
            file_id, chat_id, file_size, upload_time, expiry_time, user_id, description = file_info[2:]


            if datetime.utcnow() > datetime.strptime(expiry_time, "%Y-%m-%d %H:%M:%S"):
                await event.reply("The download link has expired. Please upload the file again to get a new link.")
                return

            try:

                message = await client.get_messages(chat_id, ids=file_id)
                await client.send_file(event.sender_id, file=message.media, caption=f"Here's your file:\n\n{description}")

                logger.info(f"File sent to user {event.sender_id} using token: {token}")

            except Exception as e:
                logger.error(f"Error downloading file: {str(e)}")
                await event.reply("An error occurred while fetching the file. Please try again.")
        else:
            await event.reply("Invalid or expired token. Please try again.")


@client.on(events.NewMessage(pattern='/myfiles'))
async def list_user_files(event):
    user_id = event.sender_id
    files = fetch_user_files(user_id)
    if not files:
        await event.reply("You haven't uploaded any files yet.")
        return

    message = "Here are your uploaded files:\n\n"
    for file in files[:10]:  # Show only the latest 10 files
        token, upload_time, expiry_time, description = file[1], file[4], file[5], file[7]
        message += f"[File Link](https://t.me/{bot_username}?start={token})\n"
        message += f"Uploaded: {upload_time}\n"
        message += f"Expires: {expiry_time}\n"
        message += f"Description: {description}\n\n"

    await event.reply(message, link_preview=False)

import json


with open('config.json', 'r') as f:
    config = json.load(f)
OWNER_ID = config['owner_id']

@client.on(events.NewMessage(pattern=r'/delete (.+)'))
async def delete_user_file(event):
    full_link = event.pattern_match.group(1)
    token = full_link.split('=')[-1]  # Extract the token from the link
    file_info = fetch_file_data(token)

    if not file_info:
        await event.reply("Invalid token or the file does not exist.")
        return


    if event.sender_id != OWNER_ID and file_info[6] != event.sender_id:
        await event.reply("You don't have permission to delete this file.")
        return

    delete_file(token)
    await event.reply("File deleted successfully.")



@client.on(events.NewMessage(pattern='/cleanup'))
async def cleanup_command(event):
    delete_expired_tokens()
    await event.reply("Expired tokens have been cleaned up from the database.")

@client.on(events.NewMessage(pattern=r'/uploaddb (\d+)'))
async def upload_to_user_database(event):
    if event.sender_id != OWNER_ID:
        await event.reply("You don't have permission to upload to databases.")
        return

    user_id = int(event.pattern_match.group(1))
    if event.media:
        msg = event.message
        token = generate_token()

        try:

            description = "No description"
            if isinstance(msg.media, MessageMediaPhoto):
                file_size = "Unknown size"
                uploaded_message = await client.send_message(storage_channel_id, file=msg.media)
            elif isinstance(msg.media, MessageMediaDocument):
                file_size = msg.media.size if hasattr(msg.media, 'size') else "Unknown size"
                uploaded_message = await client.send_message(storage_channel_id, file=msg.media)
            else:

                await event.reply("Unsupported media type. Please upload photos, documents, or videos.")
                return

            if msg.raw_text:
                description = msg.raw_text


            expiry_time = get_token_expiry()
            save_file_data(token, uploaded_message.id, uploaded_message.chat_id, file_size, expiry_time, user_id, description)


            download_link = f"https://t.me/{bot_username}?start={token}"
            await event.reply(
                f"File uploaded successfully to user {user_id}'s database!\n\n"
                f"Download Link: [Click Here]({download_link})\n"
                f"This link will expire in 24 hours.\n"
                f"Description: {description}"
            )

            logger.info(f"File uploaded to user {user_id}'s database. Token generated: {token}")

        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            await event.reply("An error occurred while uploading the file. Please try again.")


@client.on(events.NewMessage(pattern=r'/deletedb (\d+)'))
async def delete_user_database(event):
    if event.sender_id != OWNER_ID:
        await event.reply("You don't have permission to delete databases.")
        return

    user_id = int(event.pattern_match.group(1))
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM files WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    await event.reply(f"All files for user {user_id} have been deleted.")






@client.on(events.NewMessage(pattern=r"^/help$"))
async def help_command(event):
    help_text = (
        "**Help Menu** \n\n"
        "Here are the commands you can use:\n\n"
        "/start - Start the bot and get a welcome message.\n"
        "/upload - Upload a photo, document, or video and get a download link.\n"
        "/myfiles - List all files you have uploaded.\n"
        "/delete <token> - Delete a file using its token.\n"
        "/cleanup - Clean up expired tokens from the database.\n"
        "/help - Show this help menu.\n\n"
        "Feel free to reach out if you have any questions or need assistance!"
    )
    await event.reply(help_text)
