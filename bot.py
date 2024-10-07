import os, logging, asyncio, time
from telethon import Button
from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError

logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - [%(levelname)s] - %(message)s'
)
LOGGER = logging.getLogger(__name__)

# Environment variables
api_id = int(os.environ.get(26730559))
api_hash = os.environ.get("54e0fd326f54b4ea91fdcbdf98e3cf4e")
bot_token = os.environ.get("1671481145:AAEqfQr54lHeH6w1MeGbFe2ygWT-Bz6KLPY")
owner_id = int(os.environ.get("1472568994"))  # Tambahkan OWNER_ID sebagai environment variable

client = TelegramClient('client', api_id, api_hash).start(bot_token=bot_token)

# Variables for managing tagall and allowed users/groups
allowed_users = {}  # Dictionary untuk user yang diizinkan tagall (user_id: last_tagall_time)
free_users = []  # List untuk user yang bebas tagall lebih dari 1x
allowed_groups = []  # List grup yang diizinkan menggunakan tagall
open_groups = {}  # Dictionary untuk status open/close tagall di grup (chat_id: True/False)
TAGALL_COOLDOWN = 86400  # Cooldown 24 jam (1 hari) dalam detik
spam_chats = []

# Fungsi untuk cek apakah user adalah owner
def is_owner(user_id):
    return user_id == owner_id

# Command /start
@client.on(events.NewMessage(pattern="^/start$"))
async def start(event):
    await event.reply(
        "__**I'm MentionAll Bot**, I will help you to mention all members in your group and channel 👻\nClick **/help** for more information__",
        link_preview=False,
        buttons=(
            [
                Button.url('📣 Channel', 'https://t.me/The_SHIKARI_Network'),
                Button.url('📦 Source', 'https://github.com/ShikariBaaZ/MentionAll_Bot')
            ]
        )
    )

# Command /help
@client.on(events.NewMessage(pattern="^/help$"))
async def help(event):
    helptext = "**Help Menu of MentionAll_Bot**\n\nCommand: /mentionall\n__Use this command with text to mention others.__\n\nFollow [@The_Shikarii](https://github.com/ShikariBaaZ)"
    await event.reply(helptext, link_preview=False)

# Command /mentionall
@client.on(events.NewMessage(pattern="^/mentionall ?(.*)"))
async def mentionall(event):
    chat_id = event.chat_id
    sender_id = event.sender_id
    current_time = time.time()

    # Cek apakah grup diizinkan untuk menggunakan tagall
    if chat_id not in allowed_groups:
        return await event.respond("__This group is not allowed to use the tagall feature.__")
    
    # Cek apakah tagall diizinkan di grup ini
    if chat_id not in open_groups or not open_groups[chat_id]:
        return await event.respond("__Tagall is currently closed for this group.__")
    
    # Cek apakah user diizinkan menggunakan tagall
    if sender_id not in allowed_users and sender_id not in free_users:
        return await event.respond("__You are not allowed to perform tagall.__")

    # Cek cooldown 24 jam untuk pengguna biasa
    if sender_id not in free_users and current_time - allowed_users[sender_id] < TAGALL_COOLDOWN:
        return await event.respond("__You can only perform tagall once every 24 hours.__")

    # Cek apakah user adalah admin
    is_admin = False
    try:
        partici_ = await client(GetParticipantRequest(chat_id, sender_id))
    except UserNotParticipantError:
        is_admin = False
    else:
        if isinstance(partici_.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)):
            is_admin = True
    if not is_admin:
        return await event.respond("__Only admins can mention all members!__")
    
    # Mulai tagall
    spam_chats.append(chat_id)
    usrnum = 0
    usrtxt = ''
    async for usr in client.iter_participants(chat_id):
        if chat_id not in spam_chats:
            break
        usrnum += 1
        usrtxt += f"[{usr.first_name}](tg://user?id={usr.id}) "
        if usrnum == 5:
            await client.send_message(chat_id, f"{usrtxt}\n\n{event.pattern_match.group(1)}")
            await asyncio.sleep(2)
            usrnum = 0
            usrtxt = ''

    try:
        spam_chats.remove(chat_id)
    except:
        pass

    # Update last usage time untuk non-free users
    if sender_id not in free_users:
        allowed_users[sender_id] = current_time

# Command /addgroup - Tambahkan grup ke allowed_groups (Owner only)
@client.on(events.NewMessage(pattern="^/addgroup$"))
async def add_group(event):
    if not is_owner(event.sender_id):
        return await event.reply("__Only the bot owner can execute this command.__")
    
    chat_id = event.chat_id
    if chat_id not in allowed_groups:
        allowed_groups.append(chat_id)
        await event.reply(f"Group {chat_id} has been added to the allowed groups.")
    else:
        await event.reply(f"Group {chat_id} is already in the allowed list.")

# Command /removegroup - Hapus grup dari allowed_groups (Owner only)
@client.on(events.NewMessage(pattern="^/removegroup$"))
async def remove_group(event):
    if not is_owner(event.sender_id):
        return await event.reply("__Only the bot owner can execute this command.__")
    
    chat_id = event.chat_id
    if chat_id in allowed_groups:
        allowed_groups.remove(chat_id)
        await event.reply(f"Group {chat_id} has been removed from the allowed groups.")
    else:
        await event.reply(f"Group {chat_id} is not in the allowed list.")

# Command /adduser - Tambah user yang diizinkan tagall (Owner only)
@client.on(events.NewMessage(pattern="^/adduser ?(.*)"))
async def add_user(event):
    if not is_owner(event.sender_id):
        return await event.reply("__Only the bot owner can execute this command.__")
    
    user_id = int(event.pattern_match.group(1))
    allowed_users[user_id] = 0  # User diizinkan tagall pertama kali
    await event.reply(f"User {user_id} has been added to the allowed users.")

# Command /removeuser - Hapus user dari allowed_users (Owner only)
@client.on(events.NewMessage(pattern="^/removeuser ?(.*)"))
async def remove_user(event):
    if not is_owner(event.sender_id):
        return await event.reply("__Only the bot owner can execute this command.__")
    
    user_id = int(event.pattern_match.group(1))
    if user_id in allowed_users:
        del allowed_users[user_id]
        await event.reply(f"User {user_id} has been removed from the allowed users.")
    else:
        await event.reply(f"User {user_id} is not in the allowed users list.")

# Command /free - Tambah user ke free_users (Owner only)
@client.on(events.NewMessage(pattern="^/free ?(.*)"))
async def free_user(event):
    if not is_owner(event.sender_id):
        return await event.reply("__Only the bot owner can execute this command.__")
    
    user_id = int(event.pattern_match.group(1))
    if user_id not in free_users:
        free_users.append(user_id)
        await event.reply(f"User {user_id} has been added to the free users list.")
    else:
        await event.reply(f"User {user_id} is already a free user.")

# Command /open - Buka izin tagall di grup (Owner only)
@client.on(events.NewMessage(pattern="^/open$"))
async def open_tagall(event):
    if not is_owner(event.sender_id):
        return await event.reply("__Only the bot owner can execute this command.__")
    
    chat_id = event.chat_id
    open_groups[chat_id] = True
    await event.reply("__Tagall has been opened for this group.__")

# Command /close - Tutup izin tagall di grup (Owner only)
@client.on(events.NewMessage(pattern="^/close$"))
async def close_tagall(event):
    if not is_owner(event.sender_id):
        return await event.reply("__Only the bot owner can execute this command.__")
    
    chat_id = event.chat_id
    open_groups[chat_id] = False
    await event.reply("__Tagall has been closed for this group.__")

# Command /cancel - Hentikan tagall
@client.on(events.NewMessage(pattern="^/cancel$"))
async def cancel_spam(event):
    if event.chat_id not in spam_chats:
        return await event.respond('__There is no process ongoing...__')
    else:
        try:
            spam_chats.remove(event.chat_id)
        except:
            pass
        return await event.respond('__Stopped.__')

print(">> BOT STARTED <<")
client.run_until_disconnected()
        
