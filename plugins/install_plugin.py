import os
from telethon import events

PLUGINS_DIR = "plugins"

# Ensure plugins directory exists
if not os.path.exists(PLUGINS_DIR):
    os.makedirs(PLUGINS_DIR)

# Handle the /install command to upload a plugin
@client.on(events.NewMessage(pattern=r'/install'))
async def install_plugin(event):
    # Check if the sender is the owner
    if event.sender_id != OWNER_ID:
        await event.reply("You are not authorized to use this command.")
        return


    if event.is_reply:

        reply_msg = await event.get_reply_message()


        if reply_msg and reply_msg.file and reply_msg.file.name.endswith('.py'):
            file_name = reply_msg.file.name
            file_path = os.path.join(PLUGINS_DIR, file_name)


            await reply_msg.download_media(file_path)


            load_plugins()

            await event.reply(f"Plugin '{file_name}' installed successfully!")
        else:
            await event.reply("Please reply to a valid Python plugin file (.py).")
    else:
        await event.reply("Reply to a message containing a plugin file to install it.")


@client.on(events.NewMessage(pattern=r'\.uninstall (.+)'))
async def uninstall_plugin(event):
    # Check if the sender is the owner
    if event.sender_id != OWNER_ID:
        await event.reply("You are not authorized to use this command.")
        return


    plugin_name = event.pattern_match.group(1).strip()


    plugin_path = os.path.join(PLUGINS_DIR, plugin_name)

    if os.path.exists(plugin_path) and plugin_name.endswith('.py'):
        os.remove(plugin_path)
        await event.reply(f"Plugin '{plugin_name}' has been uninstalled successfully!")
    else:
        await event.reply(f"Plugin '{plugin_name}' not found.")