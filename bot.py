# -*- coding: utf-8 -*-
"""
==============================================================================
🚀 TELEGRAM BOT PRO V90000 ULTIMATE ENTERPRISE MAX EDITION
📝 ប្រភេទ: លក់ម៉ូត / Keys / Files អូតូម៉ាតិច (មានប្រព័ន្ធ Multi-Bot ខ្នាតធំ)
⚙️ FRAMEWORK: pyTelegramBotAPI (Telebot) - STRICTLY REALLY KEYBOARD 100%
🗄 DATABASE: SQLite3 (Advanced Thread-Safe Connection Pooling)
==============================================================================
"""

import telebot
from telebot import types
import sqlite3
import random
import threading
import time
import json
import logging
import sys
import os
import traceback

# ==============================================================================
# ⚙️ [១] ការកំណត់ទូទៅ (SYSTEM CONFIGURATION)
# ==============================================================================
# 🔐 Token និង Admin ID អានពី Environment Variables (កុំដាក់ត្រង់ៗក្នុងកូដពេល Deploy)
MAIN_BOT_TOKEN = os.environ.get("MAIN_BOT_TOKEN", "8990052750:AAEFFKfM8Q-_MG-YQMlAtCFsWd0aFlyMjZU")
SUPER_ADMIN_ID = int(os.environ.get("SUPER_ADMIN_ID", "7708363434"))  # ID ម្ចាស់មេធំ @Babysupport1
VERSION = "PRO V90000 ULTIMATE"

# 📁 Persistent Disk (សម្រាប់ Render — ការពារទិន្នន័យបាត់ពេល Redeploy)
# ដាក់ Environment Variable ឈ្មោះ DATA_DIR ជា /var/data ក្នុង Render Dashboard
# បើគ្មាន Disk ភ្ជាប់ទេ វានឹងប្រើ Folder បច្ចុប្បន្នជំនួស
DATA_DIR = os.environ.get("DATA_DIR", ".")
os.makedirs(DATA_DIR, exist_ok=True)

# រៀបចំ Logging កម្រិតខ្ពស់ដើម្បីតាមដានរាល់ដំណើរការ និងការពារការគាំង
logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - [%(threadName)s] - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PRO_V90000")

# បញ្ជីផ្ទុក Bot ដែលកំពុងដំណើរការ (ការពារការ Run ជាន់គ្នា)
active_bots = {}

# ==============================================================================
# 🗄 [២] ប្រព័ន្ធទិន្នន័យការពារការគាំង (ENTERPRISE DATABASE ENGINE)
# ==============================================================================
DB_FILE = os.path.join(DATA_DIR, 'shop_v90000_enterprise_db.sqlite')
db_lock = threading.RLock()

class DatabaseEngine:
    """ ប្រព័ន្ធគ្រប់គ្រងទិន្នន័យ (Database) ធានាសុវត្ថិភាព មិនមាន Error គាំង (Database Locked) """
    
    @staticmethod
    def execute_query(query, args=(), fetchone=False, fetchall=False, commit=False):
        with db_lock:
            conn = None
            try:
                conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=120.0)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, args)
                
                result = None
                if fetchone:
                    row = cursor.fetchone()
                    result = dict(row) if row else None
                elif fetchall:
                    rows = cursor.fetchall()
                    result = [dict(row) for row in rows]
                    
                if commit:
                    conn.commit()
                return result
            except Exception as e:
                logger.error(f"🔴 DATABASE ERROR: {e} | QUERY: {query} | ARGS: {args}")
                logger.error(traceback.format_exc())
                return None
            finally:
                if conn:
                    conn.close()

    @staticmethod
    def initialize_system_tables():
        logger.info("🔄 កំពុងបង្កើតរចនាសម្ព័ន្ធ Database សម្រាប់ប្រព័ន្ធខ្នាតយក្ស...")
        tables = [
            "CREATE TABLE IF NOT EXISTS users (id INTEGER, bot_token TEXT, role TEXT, PRIMARY KEY(id, bot_token))",
            "CREATE TABLE IF NOT EXISTS admin_codes (code TEXT PRIMARY KEY, bot_token TEXT)",
            "CREATE TABLE IF NOT EXISTS child_bots (token TEXT PRIMARY KEY, username TEXT)",
            "CREATE TABLE IF NOT EXISTS settings (key TEXT, bot_token TEXT, value TEXT, PRIMARY KEY(key, bot_token))",
            "CREATE TABLE IF NOT EXISTS buttons (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_token TEXT, name TEXT, parent_id INTEGER, text_msg TEXT, order_idx INTEGER DEFAULT 0)",
            "CREATE TABLE IF NOT EXISTS packages (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_token TEXT, button_id INTEGER, name TEXT, duration TEXT, price REAL, order_idx INTEGER DEFAULT 0)",
            "CREATE TABLE IF NOT EXISTS stocks (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_token TEXT, package_id INTEGER, content TEXT)",
            "CREATE TABLE IF NOT EXISTS transactions (id TEXT PRIMARY KEY, bot_token TEXT, user_id INTEGER, package_id INTEGER, price REAL, method TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
            "CREATE TABLE IF NOT EXISTS sessions (user_id INTEGER, bot_token TEXT, state TEXT, data TEXT, PRIMARY KEY(user_id, bot_token))"
        ]
        
        for sql in tables:
            DatabaseEngine.execute_query(sql, commit=True)
            
        # ធានាថាមេធំត្រូវបានបញ្ចូលទៅក្នុង Database នៃ Main Bot
        DatabaseEngine.execute_query(
            "INSERT OR IGNORE INTO users (id, bot_token, role) VALUES (?, ?, ?)", 
            (SUPER_ADMIN_ID, MAIN_BOT_TOKEN, 'super_admin'), commit=True
        )
        logger.info("✅ ប្រព័ន្ធ Database រៀបចំរួចរាល់ ១០០%!")

DatabaseEngine.initialize_system_tables()

# ==============================================================================
# 🧠 [៣] ប្រព័ន្ធគ្រប់គ្រងសកម្មភាពអ្នកប្រើប្រាស់ (ADVANCED SESSION MEMORY)
# ==============================================================================
class SessionMemory:
    """ ទន្ទេញចាំរាល់ជំហានរបស់អ្នកប្រើ ការពារបញ្ហា 'ប៊ូតុងមិនត្រឹមត្រូវ' ទាំងស្រុង """
    
    @staticmethod
    def get_state(user_id, bot_token):
        res = DatabaseEngine.execute_query("SELECT state, data FROM sessions WHERE user_id=? AND bot_token=?", (user_id, bot_token), fetchone=True)
        if res:
            try:
                return {'state': res['state'], 'data': json.loads(res['data']) if res['data'] else {}}
            except Exception:
                return {'state': 'home', 'data': {}}
        return {'state': 'home', 'data': {}}

    @staticmethod
    def set_state(user_id, bot_token, state='home', data=None):
        if data is None: data = {}
        DatabaseEngine.execute_query(
            "REPLACE INTO sessions (user_id, bot_token, state, data) VALUES (?, ?, ?, ?)", 
            (user_id, bot_token, state, json.dumps(data)), commit=True
        )

    @staticmethod
    def clear_state(user_id, bot_token):
        SessionMemory.set_state(user_id, bot_token, 'home', {})

# ==============================================================================
# 🔐 [៤] ប្រព័ន្ធគ្រប់គ្រងសិទ្ធិ (ROLE-BASED ACCESS CONTROL)
# ==============================================================================
class SecurityManager:
    @staticmethod
    def get_user_role(user_id, bot_token):
        res = DatabaseEngine.execute_query("SELECT role FROM users WHERE id=? AND bot_token=?", (user_id, bot_token), fetchone=True)
        return res['role'] if res else 'user'

    @staticmethod
    def is_super_admin(user_id, bot_token):
        return SecurityManager.get_user_role(user_id, bot_token) == 'super_admin'

    @staticmethod
    def is_admin(user_id, bot_token):
        role = SecurityManager.get_user_role(user_id, bot_token)
        return role in ['admin', 'super_admin']

# ==============================================================================
# 🎛 [៥] រោងចក្រផលិតប៊ូតុង (REPLY KEYBOARD BUILDER 100%)
# ==============================================================================
def styled_btn(text, style=None):
    """
    បង្កើត KeyboardButton ដែលមានពណ៌ (style) ដោយសុវត្ថិភាព
    style ជម្រើស: 'primary' (ខៀវ), 'success' (បៃតង), 'danger' (ក្រហម)
    ត្រូវការ Telegram App កំណែថ្មី (Bot API 9.4+, ថ្ងៃទី 9 កុម្ភៈ 2026) ទើបបង្ហាញពណ៌
    ចំណាំសំខាន់: pyTelegramBotAPI មួយចំនួន (ជាពិសេសកំណែចាស់) ព្រំដែន to_dict()/to_dic()
    របស់វា មិនទាន់ដាក់ field 'style' ចូល JSON ដែលផ្ញើទៅ Telegram ទេ សូម្បី constructor
    នឹងទទួល argument style ដោយគ្មាន Error ក៏ដោយ (field គ្រាន់តែត្រូវបានចោល ស្ងាត់ៗ)។
    ដូច្នេះ ខាងក្រោមនេះបាន monkey-patch serializer ដោយផ្ទាល់ ដើម្បីធានាថា style
    ត្រូវបញ្ចូនទៅ Telegram ជានិច្ច មិនថា library version ណា។ (មើល _patch_keyboard_button_style())
    """
    btn = types.KeyboardButton(text)
    if style:
        btn.style = style
    return btn


def _patch_keyboard_button_style():
    """
    Monkey-patch telebot.types.KeyboardButton ដើម្បីបង្ខំបញ្ចូល field 'style'
    ទៅក្នុង JSON dict ដែលបានផ្ញើទៅ Telegram Bot API សូម្បី library កំណែដែលកំពុងដំណើរការ
    មិនទាន់គាំទ្រ Bot API 9.4 (Colored Buttons) ជាផ្លូវការក៏ដោយ។
    """
    method_name = None
    if hasattr(types.KeyboardButton, 'to_dict'):
        method_name = 'to_dict'
    elif hasattr(types.KeyboardButton, 'to_dic'):
        method_name = 'to_dic'

    if not method_name:
        logger.warning("⚠️ រកមិនឃើញ to_dict()/to_dic() លើ telebot.types.KeyboardButton — សូមពិនិត្យ library version")
        return

    original_method = getattr(types.KeyboardButton, method_name)

    def patched_method(self):
        result = original_method(self)
        style = getattr(self, 'style', None)
        if style and isinstance(result, dict):
            result['style'] = style
        return result

    setattr(types.KeyboardButton, method_name, patched_method)
    logger.info(f"🟢 Patched telebot.types.KeyboardButton.{method_name}() ដើម្បីគាំទ្រ style (Bot API 9.4+)")


_patch_keyboard_button_style()


class KeyboardBuilder:
    """ ប្រព័ន្ធនេះធានាថា គ្មាន INLINE KEYBOARD ត្រូវបានប្រើប្រាស់ដាច់ខាត """
    
    @staticmethod
    def user_home():
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        kb.add(styled_btn("🛒 Buy", "success"))
        return kb

    @staticmethod
    def cancel_only():
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        kb.add(styled_btn("❌ បោះបង់ (Cancel)", "danger"))
        return kb
        
    @staticmethod
    def back_only():
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        kb.add(styled_btn("➡️Back", "primary"))
        return kb

    @staticmethod
    def cancel_payment():
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        kb.add(styled_btn("បោះបង់", "danger"))
        return kb

    @staticmethod
    def admin_dashboard(role):
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        # ម៉ឺនុយអេតមីនធម្មតា (ខៀវ=កែ/បង្កើត, ក្រហម=លុប)
        kb.add(styled_btn("✏️អេត Button", "primary"), styled_btn("🗑លុប Button", "danger"))
        kb.add(styled_btn("📝ដាក់អក្សរ", "primary"), styled_btn("🗑លុបអក្សរ", "danger"))
        kb.add(styled_btn("រៀបចំបូតុង", "primary"), styled_btn("✏️អេតកព្ចាប់ Button", "primary"))
        kb.add(styled_btn("🗑លុប កព្ចាប់", "danger"), styled_btn("📦អេតស្តុកកព្ចាប់", "primary"))
        kb.add(styled_btn("🗑លុប ស្តុក", "danger"), styled_btn("💬ធ្ញើសារ", "primary"))
        kb.add(styled_btn("🖼ដាក់QRcode", "primary"), styled_btn("🗑លុប QRcode", "danger"))
        kb.add(styled_btn("✏️ដាក់ABA", "primary"), styled_btn("🗑លុបABA", "danger"))
        kb.add(styled_btn("🖼Wellcome Photo", "primary"), styled_btn("🗑លុប Welcome Photo", "danger"))
        kb.add(styled_btn("✏️អេតលីង/វីដេអូ", "primary"), styled_btn("🗑លុបលីង/វីដេអូ", "danger"))
        
        # ម៉ឺនុយមេធំ (Super Admin តែប៉ុណ្ណោះទើបឃើញ)
        if role == 'super_admin':
            kb.add(styled_btn("🤖Abb Bot", "primary"), styled_btn("🔐បង្កើតកូតអេតមីន", "primary"))
            kb.add(styled_btn("📊មើលចំនួនBot", "primary"), styled_btn("🗑លុប Bot", "danger"))
            
        kb.add(styled_btn("➡️Back", "primary"))
        return kb

    @staticmethod
    def store_navigation(bot_token, parent_id=None):
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        
        # ទាញយក Folder កូន
        if parent_id is None:
            query = "SELECT name FROM buttons WHERE parent_id IS NULL AND bot_token=? ORDER BY order_idx ASC"
            btns = DatabaseEngine.execute_query(query, (bot_token,), fetchall=True)
        else:
            query = "SELECT name FROM buttons WHERE parent_id=? AND bot_token=? ORDER BY order_idx ASC"
            btns = DatabaseEngine.execute_query(query, (parent_id, bot_token), fetchall=True)
            
        items = [b['name'] for b in btns] if btns else []
        
        # ទាញយក កញ្ចប់ទំនិញ
        if parent_id is not None:
            pkg_query = "SELECT name, price FROM packages WHERE button_id=? AND bot_token=? ORDER BY order_idx ASC"
            pkgs = DatabaseEngine.execute_query(pkg_query, (parent_id, bot_token), fetchall=True)
            if pkgs:
                for p in pkgs:
                    items.append(f"📦 {p['name']} | 💰 ${p['price']}")

        # ពណ៌៖ កញ្ចប់ទំនិញ (📦) = បៃតង (សម្រាប់ទិញ) / Folder ធម្មតា = ខៀវ (សម្រាប់រុករក)
        buttons = [styled_btn(name, "success" if name.startswith("📦") else "primary") for name in items]

        # រៀបប៊ូតុងជា ២ ជួរឲ្យស្អាត
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                kb.add(buttons[i], buttons[i+1])
            else:
                kb.add(buttons[i])
                
        kb.add(styled_btn("➡️Back", "primary"))
        return kb

    @staticmethod
    def list_dynamic_options(items, include_cancel=True):
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [styled_btn(item, "primary") for item in items]
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                kb.add(buttons[i], buttons[i+1])
            else:
                kb.add(buttons[i])
        if include_cancel:
            kb.add(styled_btn("❌ បោះបង់ (Cancel)", "danger"))
        return kb

    @staticmethod
    def payment_methods_menu():
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        kb.add(styled_btn("🏦 ABA MOBILE", "primary"), styled_btn("🧡QR Code", "primary"))
        kb.add(styled_btn("បោះបង់", "danger"))
        return kb

    @staticmethod
    def rearrange_keypad():
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        kb.add(styled_btn("⬅️ឆ្វេង", "primary"), styled_btn("⬆️លើ", "primary"), styled_btn("⬇️ក្រោម", "primary"), styled_btn("➡️ស្ដាំ", "primary"))
        kb.add(styled_btn("✅ រក្សាទុក", "success"), styled_btn("❌ បោះបង់ (Cancel)", "danger"))
        return kb

    @staticmethod
    def approval_keypad(trx_id):
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        kb.add(styled_btn(f"✅ យល់ព្រម TRX-{trx_id}", "success"), styled_btn(f"❌ បដិសេធ TRX-{trx_id}", "danger"))
        return kb

# ==============================================================================
# 🧩 [៦] រោងចក្រចងក្រងមុខងារ (CORE HANDLERS ROUTER)
# ==============================================================================
def create_bot_handlers(bot, bot_token, is_main=False):
    """ អនុគមន៍នេះមានតួនាទីដំឡើងរាល់មុខងារទាំងអស់ទៅកាន់ Bot នីមួយៗ """

    # --------------------------------------------------------------------------
    # 📌 មុខងារបោះបង់ និងថយក្រោយ (UNIVERSAL NAVIGATION)
    # --------------------------------------------------------------------------
    @bot.message_handler(func=lambda msg: msg.text in ["❌ បោះបង់ (Cancel)", "➡️Back", "បោះបង់"])
    def core_navigation_handler(message):
        uid = message.chat.id
        txt = message.text
        sess = SessionMemory.get_state(uid, bot_token)
        state = sess['state']
        data = sess['data']
        role = SecurityManager.get_user_role(uid, bot_token)

        # ពេលចុចបោះបង់នៅកន្លែងទូទាត់ប្រាក់ (Payment)
        if txt == "បោះបង់" and state in ['choose_payment', 'waiting_slip']:
            SessionMemory.clear_state(uid, bot_token)
            # លោតអក្សរនេះតាមការស្នើសុំ
            bot.send_message(uid, "Payment canceled. Tap 🛒 Buy to start again.", reply_markup=KeyboardBuilder.user_home())
            # បើសិនគាត់ជាអេតមីន ឲ្យផ្ទាំងអេតមីនទៅគាត់វិញ
            if role in ['admin', 'super_admin']:
                bot.send_message(uid, "🔧 ត្រលប់ទៅផ្ទាំងគ្រប់គ្រង៖", reply_markup=KeyboardBuilder.admin_dashboard(role))
            return

        if txt == "❌ បោះបង់ (Cancel)":
            SessionMemory.clear_state(uid, bot_token)
            if role in ['admin', 'super_admin']:
                bot.send_message(uid, "✅ បានបោះបង់សកម្មភាព!", reply_markup=KeyboardBuilder.admin_dashboard(role))
            else:
                bot.send_message(uid, "🏠 ទំព័រដើម", reply_markup=KeyboardBuilder.user_home())
            return

        if txt == "➡️Back":
            if state == 'navigating':
                path = data.get('path', [])
                if len(path) > 0:
                    path.pop()  # ដកទីតាំងចុងក្រោយចេញ (ថយ ១ ជំហាន)
                    parent_id = path[-1] if len(path) > 0 else None
                    SessionMemory.set_state(uid, bot_token, 'navigating', {'path': path})
                    bot.send_message(uid, "🔙 ត្រលប់ក្រោយ...", reply_markup=KeyboardBuilder.store_navigation(bot_token, parent_id))
                else:
                    SessionMemory.clear_state(uid, bot_token)
                    if role in ['admin', 'super_admin']:
                        bot.send_message(uid, "🔧 ត្រលប់ទៅផ្ទាំងគ្រប់គ្រង៖", reply_markup=KeyboardBuilder.admin_dashboard(role))
                    else:
                        bot.send_message(uid, "🏠 ទំព័រដើម", reply_markup=KeyboardBuilder.user_home())
            else:
                SessionMemory.clear_state(uid, bot_token)
                if role in ['admin', 'super_admin']:
                    bot.send_message(uid, "🔙 ត្រលប់ក្រោយ", reply_markup=KeyboardBuilder.admin_dashboard(role))
                else:
                    bot.send_message(uid, "🔙 ត្រលប់ក្រោយ", reply_markup=KeyboardBuilder.user_home())

    # --------------------------------------------------------------------------
    # 📌 មុខងារចាប់ផ្តើម និងចូលគណនី (START & ADMIN LOGIN)
    # --------------------------------------------------------------------------
    @bot.message_handler(commands=['start'])
    def command_start_handler(message):
        uid = message.chat.id
        
        # ពិនិត្យមើលថាតើគាត់ជា User ថ្មីឬទេ
        db_user = DatabaseEngine.execute_query("SELECT role FROM users WHERE id=? AND bot_token=?", (uid, bot_token), fetchone=True)
        
        if not db_user:
            if not is_main:
                # បើជាកូន Bot សូមឆែកមើលថាតើមានអេតមីនហើយឬនៅ
                admin_count = DatabaseEngine.execute_query("SELECT COUNT(*) as c FROM users WHERE bot_token=? AND role IN ('admin', 'super_admin')", (bot_token,), fetchone=True)['c']
                if admin_count == 0:
                    # អ្នកចូលដំបូងគេក្លាយជា Admin ធម្មតា (មិនមែន Super Admin ទេ)
                    DatabaseEngine.execute_query("INSERT INTO users (id, bot_token, role) VALUES (?, ?, ?)", (uid, bot_token, 'admin'), commit=True)
                    bot.send_message(uid, "🎉 អបអរសាទរ! ដោយសារអ្នកជាអ្នកដំណើរការ Bot នេះមុនគេ អ្នកទទួលបានសិទ្ធិជា អេតមីន ដោយស្វ័យប្រវត្តិ។")
                else:
                    DatabaseEngine.execute_query("INSERT INTO users (id, bot_token, role) VALUES (?, ?, ?)", (uid, bot_token, 'user'), commit=True)
            else:
                DatabaseEngine.execute_query("INSERT INTO users (id, bot_token, role) VALUES (?, ?, ?)", (uid, bot_token, 'user'), commit=True)
                
        SessionMemory.clear_state(uid, bot_token)
        role = SecurityManager.get_user_role(uid, bot_token)
        
        photo = DatabaseEngine.execute_query("SELECT value FROM settings WHERE key='welcome_photo' AND bot_token=?", (bot_token,), fetchone=True)
        welcome_txt = "Welcome! Tap 🛒 Buy to start."
        
        # អ្នកប្រើធម្មតាឃើញតែប៊ូតុង User ទេ
        if role in ['admin', 'super_admin']:
            kb = KeyboardBuilder.admin_dashboard(role)
        else:
            kb = KeyboardBuilder.user_home()
            
        try:
            if photo:
                bot.send_photo(uid, photo['value'], caption=welcome_txt, reply_markup=kb)
            else:
                bot.send_message(uid, welcome_txt, reply_markup=kb)
        except Exception as e:
            bot.send_message(uid, welcome_txt, reply_markup=kb)

    @bot.message_handler(commands=['abmin'])
    def command_abmin_login(message):
        uid = message.chat.id
        args = message.text.split()
        if len(args) == 2:
            code = args[1]
            valid_code = DatabaseEngine.execute_query("SELECT code FROM admin_codes WHERE code=? AND bot_token=?", (code, bot_token), fetchone=True)
            if valid_code:
                DatabaseEngine.execute_query("DELETE FROM admin_codes WHERE code=? AND bot_token=?", (code, bot_token), commit=True)
                DatabaseEngine.execute_query("INSERT OR REPLACE INTO users (id, bot_token, role) VALUES (?, ?, ?)", (uid, bot_token, 'admin'), commit=True)
                bot.send_message(uid, "✅ អ្នកបានក្លាយជា អេតមីន របស់ Bot នេះដោយជោគជ័យ!", reply_markup=KeyboardBuilder.admin_dashboard('admin'))
            else:
                bot.send_message(uid, "❌ កូតមិនត្រឹមត្រូវ ឬកូតនេះត្រូវបានប្រើប្រាស់រួចហើយ!")

    # --------------------------------------------------------------------------
    # 🛒 ដំណើរការទិញទំនិញ (BUYING ENGINE - SKIP QUANTITY)
    # --------------------------------------------------------------------------
    @bot.message_handler(func=lambda msg: msg.text == "🛒 Buy")
    def buy_trigger(message):
        uid = message.chat.id
        SessionMemory.set_state(uid, bot_token, 'navigating', {'path': []})
        bot.send_message(uid, "🛒 Buy. Please select the game/product you want:", reply_markup=KeyboardBuilder.store_navigation(bot_token, None))

    @bot.message_handler(func=lambda msg: SessionMemory.get_state(msg.chat.id, bot_token)['state'] == 'navigating' and msg.text not in ["🛒 Buy", "➡️Back", "❌ បោះបង់ (Cancel)", "បោះបង់"])
    def navigate_store_folders(message):
        uid = message.chat.id
        txt = message.text.strip()
        sess = SessionMemory.get_state(uid, bot_token)
        path = sess['data'].get('path', [])
        parent_id = path[-1] if len(path) > 0 else None

        # [ករណីទី១] ចុចលើ កញ្ចប់ទំនិញ (Package)
        if txt.startswith("📦 ") and " | 💰 $" in txt:
            pkg_name = txt.split(" | 💰 $")[0].replace("📦 ", "").strip()
            
            # ទាញយកទិន្នន័យកញ្ចប់
            if parent_id is None:
                pkg = DatabaseEngine.execute_query("SELECT * FROM packages WHERE name=? AND button_id IS NULL AND bot_token=?", (pkg_name, bot_token), fetchone=True)
            else:
                pkg = DatabaseEngine.execute_query("SELECT * FROM packages WHERE name=? AND button_id=? AND bot_token=?", (pkg_name, parent_id, bot_token), fetchone=True)
                
            if pkg:
                # ឆែកមើលស្តុកសិន
                stock_check = DatabaseEngine.execute_query("SELECT COUNT(*) as c FROM stocks WHERE package_id=? AND bot_token=?", (pkg['id'], bot_token), fetchone=True)['c']
                if stock_check < 1:
                    return bot.send_message(uid, "⚠️ សុំទោស! កញ្ចប់នេះត្រូវបានលក់អស់ស្តុកហើយ។", reply_markup=KeyboardBuilder.store_navigation(bot_token, parent_id))
                    
                # រកឈ្មោះហ្គេម ដើម្បីចេញវិក្កយបត្រឲ្យស្អាត
                game_name = pkg['name']
                if parent_id:
                    btn_info = DatabaseEngine.execute_query("SELECT name FROM buttons WHERE id=? AND bot_token=?", (parent_id, bot_token), fetchone=True)
                    if btn_info: game_name = btn_info['name']

                # រំលងការបូកដក ចូលជ្រើសរើសការបង់ប្រាក់
                t_data = {
                    'pkg_id': pkg['id'], 
                    'pkg_name': pkg['name'], 
                    'game_name': game_name, 
                    'duration': pkg['duration'], 
                    'price': pkg['price']
                }
                SessionMemory.set_state(uid, bot_token, 'choose_payment', t_data)
                bot.send_message(uid, "Choose payment method:", reply_markup=KeyboardBuilder.payment_methods_menu())
            return

        # [ករណីទី២] ចុចលើ ប៊ូតុងរុករកធម្មតា (Folder Button)
        if parent_id is None:
            btn = DatabaseEngine.execute_query("SELECT * FROM buttons WHERE name=? AND parent_id IS NULL AND bot_token=?", (txt, bot_token), fetchone=True)
        else:
            btn = DatabaseEngine.execute_query("SELECT * FROM buttons WHERE name=? AND parent_id=? AND bot_token=?", (txt, parent_id, bot_token), fetchone=True)

        if btn:
            path.append(btn['id'])
            SessionMemory.set_state(uid, bot_token, 'navigating', {'path': path})
            if btn['text_msg']: 
                bot.send_message(uid, btn['text_msg'])
            bot.send_message(uid, f"📂 កំពុងបើក {btn['name']}:", reply_markup=KeyboardBuilder.store_navigation(bot_token, btn['id']))
        else:
            # ការពារបញ្ហា 'ប៊ូតុងមិនត្រឹមត្រូវ'
            bot.send_message(uid, "⚠️ ជម្រើសមិនត្រឹមត្រូវ ឬទំនិញត្រូវបានផ្លាស់ប្តូរទីតាំង។", reply_markup=KeyboardBuilder.store_navigation(bot_token, parent_id))

    # --------------------------------------------------------------------------
    # 💳 ចេញវិក្កយបត្រ និងការទូទាត់ (INVOICE & PAYMENT)
    # --------------------------------------------------------------------------
    @bot.message_handler(func=lambda msg: SessionMemory.get_state(msg.chat.id, bot_token)['state'] == 'choose_payment' and msg.text in ["🏦 ABA MOBILE", "🧡QR Code"])
    def process_payment_method(message):
        uid = message.chat.id
        method = message.text
        data = SessionMemory.get_state(uid, bot_token)['data']
        price = data['price']
        
        db_qr_key = 'qr_aba' if method == "🏦 ABA MOBILE" else 'qr_generic'
        qr_data = DatabaseEngine.execute_query("SELECT value FROM settings WHERE key=? AND bot_token=?", (db_qr_key, bot_token), fetchone=True)
        
        # ទម្រង់វិក្កយបត្រត្រឹមត្រូវតាមអ្វីដែលអ្នកស្នើសុំ
        invoice_text = f"""Game/Product: {data['game_name']}
Duration/Type: {data['duration']}
Level: Normal
Payment Method: {method}
Price: ${price}

Scan this QR code to pay.
🔴🔴🔴 សូមកុំបង់លុយម្តងទៀតលើ QR កូដចាស់។ សូមប្រើ QR កូដថ្មីដែលបូតផ្ញើប៉ុណ្ណោះ។
•បព្ជាក់ពេលបាញ់លុយរួចសូមអ្នកថតវិក្កិយបត្រធ្ញើមកbotវិញផង ដើម្បីអោយ Abmin ពិនិត្យមើលសិន 

Then tap ✅ Verify Payment.

Invoice expires in 5:00min."""

        trx_id = f"{random.randint(10000, 99999)}"
        DatabaseEngine.execute_query(
            "INSERT INTO transactions (id, bot_token, user_id, package_id, price, method, status) VALUES (?, ?, ?, ?, ?, ?, 'pending')",
            (trx_id, bot_token, uid, data['pkg_id'], price, method), commit=True
        )

        data['trx_id'] = trx_id
        SessionMemory.set_state(uid, bot_token, 'waiting_slip', data)
        
        try:
            if qr_data: 
                bot.send_photo(uid, qr_data['value'], caption=invoice_text, reply_markup=KeyboardBuilder.cancel_payment())
            else: 
                bot.send_message(uid, invoice_text, reply_markup=KeyboardBuilder.cancel_payment())
        except Exception as e:
            bot.send_message(uid, invoice_text, reply_markup=KeyboardBuilder.cancel_payment())

    # --------------------------------------------------------------------------
    # 📸 ទទួលវិក្កយបត្រ និងបញ្ជូនទៅអេតមីន (RECEIVE SLIP)
    # --------------------------------------------------------------------------
    @bot.message_handler(content_types=['photo'], func=lambda msg: SessionMemory.get_state(msg.chat.id, bot_token)['state'] == 'waiting_slip')
    def process_slip_upload(message):
        uid = message.chat.id
        data = SessionMemory.get_state(uid, bot_token)['data']
        trx_id = data['trx_id']
        price = data['price']
        
        SessionMemory.clear_state(uid, bot_token)
        role = SecurityManager.get_user_role(uid, bot_token)
        
        kb = KeyboardBuilder.admin_dashboard(role) if role in ['admin', 'super_admin'] else KeyboardBuilder.user_home()
        bot.send_message(uid, "✅ វិក្កយបត្រត្រូវបានបញ្ជូន! សូមរង់ចាំ Abmin ពិនិត្យមើលសិន...", reply_markup=kb)
        
        # ទាញយកអេតមីនទាំងអស់របស់ Bot នេះ
        admins = DatabaseEngine.execute_query("SELECT id FROM users WHERE role IN ('admin', 'super_admin') AND bot_token=?", (bot_token,), fetchall=True)
        caption = f"🔔 <b>មានការបង់ប្រាក់ថ្មីចូល!</b>\n\n👤 អ្នកទិញ ID: <code>{uid}</code>\n🧾 វិក្កយបត្រ: TRX-{trx_id}\n🛍 ទំនិញ: {data['pkg_name']}\n💰 សរុប: <b>${price}</b>\n💳 វិធីទូទាត់: {data.get('method', 'QR')}"
        
        for ad in admins:
            try: 
                bot.send_photo(ad['id'], message.photo[-1].file_id, caption=caption, parse_mode="HTML", reply_markup=KeyboardBuilder.approval_keypad(trx_id))
            except Exception: 
                pass

    # ==========================================================================
    # 🛡 [ADMIN CONTROL PANEL] អេតមីនបញ្ជាក់ និងរៀបចំទំនិញ
    # ==========================================================================

    @bot.message_handler(func=lambda msg: (msg.text.startswith("✅ យល់ព្រម TRX-") or msg.text.startswith("❌ បដិសេធ TRX-")) and SecurityManager.is_admin(msg.chat.id, bot_token))
    def admin_approval_system(message):
        admin_id = message.chat.id
        txt = message.text
        action = "approve" if "✅ យល់ព្រម" in txt else "reject"
        trx_id = txt.split("-")[-1]
        
        trx = DatabaseEngine.execute_query("SELECT * FROM transactions WHERE id=? AND bot_token=?", (trx_id, bot_token), fetchone=True)
        if not trx: 
            return bot.send_message(admin_id, "⚠️ រកមិនឃើញលេខវិក្កយបត្រនេះក្នុងប្រព័ន្ធទេ!")
        if trx['status'] != 'pending': 
            return bot.send_message(admin_id, "⚠️ វិក្កយបត្រនេះត្រូវបានចាត់ការរួចរាល់ហើយ!", reply_markup=KeyboardBuilder.admin_dashboard(SecurityManager.get_user_role(admin_id, bot_token)))
            
        DatabaseEngine.execute_query("UPDATE transactions SET status=? WHERE id=? AND bot_token=?", (action, trx_id, bot_token), commit=True)
        buyer_id = trx['user_id']
        
        if action == "approve":
            pkg_id = trx['package_id']
            # ដកស្តុក ១ ឯកតា ជានិច្ច
            stocks = DatabaseEngine.execute_query("SELECT id, content FROM stocks WHERE package_id=? AND bot_token=? LIMIT 1", (pkg_id, bot_token), fetchall=True)
            
            for st in stocks: 
                DatabaseEngine.execute_query("DELETE FROM stocks WHERE id=? AND bot_token=?", (st['id'], bot_token), commit=True)
                
            contents = "\n\n".join([st['content'] for st in stocks])
            link_record = DatabaseEngine.execute_query("SELECT value FROM settings WHERE key='tutorial_link' AND bot_token=?", (bot_token,), fetchone=True)
            
            success_msg = f"🎉 ការទូទាត់ត្រូវបានអនុម័តដោយជោគជ័យ!\n\n📦 ខាងក្រោមនេះជាទំនិញរបស់អ្នក៖\n\n{contents}"
            if link_record: 
                success_msg += f"\n\n📺 របៀបប្រើប្រាស់ ឬទាញយក៖ {link_record['value']}"
                
            try: 
                bot.send_message(buyer_id, success_msg)
            except: 
                pass
            bot.send_message(admin_id, f"✅ បានយល់ព្រម និងទម្លាក់អីវ៉ាន់ឲ្យភ្ញៀវរួចរាល់!", reply_markup=KeyboardBuilder.admin_dashboard(SecurityManager.get_user_role(admin_id, bot_token)))
        else:
            try: 
                bot.send_message(buyer_id, f"❌ វិក្កយបត្រលេខ `TRX-{trx_id}` របស់អ្នកត្រូវបានបដិសេធដោយអេតមីន។", parse_mode="Markdown")
            except: 
                pass
            bot.send_message(admin_id, "❌ បានបដិសេធវិក្កយបត្ររួចរាល់!", reply_markup=KeyboardBuilder.admin_dashboard(SecurityManager.get_user_role(admin_id, bot_token)))

    # --- Decorator សម្រាប់តម្រូវសិទ្ធិ Admin ធម្មតា ---
    def restrict_to_admin(func):
        def wrapper(message):
            if SecurityManager.is_admin(message.chat.id, bot_token): return func(message)
        return wrapper

    # [១] ✏️អេត Button
    @bot.message_handler(func=lambda m: m.text == "✏️អេត Button")
    @restrict_to_admin
    def admin_add_btn_step1(message):
        SessionMemory.set_state(message.chat.id, bot_token, 'add_btn_name')
        bot.send_message(message.chat.id, "សូមវាយបញ្ចូលឈ្មោះប៊ូតុងថ្មី (ឧ. ហ្គេមបាញ់សត្វ)៖", reply_markup=KeyboardBuilder.cancel_only())

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'add_btn_name')
    def admin_add_btn_step2(message):
        uid = message.chat.id
        name = message.text.strip()
        
        # ឆែកមើលឈ្មោះកុំឲ្យជាន់គ្នា
        if DatabaseEngine.execute_query("SELECT id FROM buttons WHERE name=? AND bot_token=?", (name, bot_token), fetchone=True):
            return bot.send_message(uid, "⚠️ ឈ្មោះនេះមានរួចហើយ! សូមវាយឈ្មោះផ្សេង៖", reply_markup=KeyboardBuilder.cancel_only())
            
        SessionMemory.set_state(uid, bot_token, 'add_btn_parent', {'name': name})
        
        # ទាញយក Folder ទាំងអស់
        btns = DatabaseEngine.execute_query("SELECT name FROM buttons WHERE bot_token=?", (bot_token,), fetchall=True)
        opts = ["🌟 ខាងក្រៅបំផុត (ROOT)"] + [b['name'] for b in btns] if btns else ["🌟 ខាងក្រៅបំផុត (ROOT)"]
        bot.send_message(uid, "ជ្រើសរើសទីតាំង (Folder) ដែលត្រូវដាក់ប៊ូតុងនេះចូល៖", reply_markup=KeyboardBuilder.list_dynamic_options(opts))

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'add_btn_parent')
    def admin_add_btn_step3(message):
        uid = message.chat.id
        parent_name = message.text
        new_name = SessionMemory.get_state(uid, bot_token)['data']['name']
        parent_id = None
        
        if parent_name != "🌟 ខាងក្រៅបំផុត (ROOT)":
            p = DatabaseEngine.execute_query("SELECT id FROM buttons WHERE name=? AND bot_token=?", (parent_name, bot_token), fetchone=True)
            if not p: return bot.send_message(uid, "⚠️ រកទីតាំងមិនឃើញទេ!")
            parent_id = p['id']
            
        # ស្វែងរកលេខរៀងខ្ពស់បំផុតដើម្បីរៀបចុះក្រោមគេ
        idx_query = "SELECT MAX(order_idx) as m FROM buttons WHERE parent_id IS NULL AND bot_token=?" if parent_id is None else f"SELECT MAX(order_idx) as m FROM buttons WHERE parent_id={parent_id} AND bot_token=?"
        max_idx = DatabaseEngine.execute_query(idx_query, (bot_token,), fetchone=True)['m']
        new_idx = (max_idx or 0) + 1
        
        DatabaseEngine.execute_query(
            "INSERT INTO buttons (bot_token, name, parent_id, order_idx) VALUES (?, ?, ?, ?)", 
            (bot_token, new_name, parent_id, new_idx), commit=True
        )
        SessionMemory.clear_state(uid, bot_token)
        bot.send_message(uid, f"✅ បានបង្កើតប៊ូតុង '{new_name}' រួចរាល់!", reply_markup=KeyboardBuilder.admin_dashboard(SecurityManager.get_user_role(uid, bot_token)))

    # [២] 🗑លុប Button
    @bot.message_handler(func=lambda m: m.text == "🗑លុប Button")
    @restrict_to_admin
    def admin_del_btn_step1(message):
        btns = DatabaseEngine.execute_query("SELECT name FROM buttons WHERE bot_token=?", (bot_token,), fetchall=True)
        if not btns: return bot.send_message(message.chat.id, "⚠️ មិនមានប៊ូតុងណាមួយឡើយ!")
        SessionMemory.set_state(message.chat.id, bot_token, 'del_btn')
        bot.send_message(message.chat.id, "សូមជ្រើសរើសប៊ូតុងដែលចង់លុបចោល (ការលុបនេះនឹងលុបអ្វីៗដែលនៅខាងក្នុងវាផងដែរ)៖", reply_markup=KeyboardBuilder.list_dynamic_options([b['name'] for b in btns]))

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'del_btn')
    def admin_del_btn_step2(message):
        uid = message.chat.id
        DatabaseEngine.execute_query("DELETE FROM buttons WHERE name=? AND bot_token=?", (message.text, bot_token), commit=True)
        SessionMemory.clear_state(uid, bot_token)
        bot.send_message(uid, f"✅ បានលុបប៊ូតុង '{message.text}' រួចរាល់!", reply_markup=KeyboardBuilder.admin_dashboard(SecurityManager.get_user_role(uid, bot_token)))

    # [៣] 📝ដាក់អក្សរ & 🗑លុបអក្សរ
    @bot.message_handler(func=lambda m: m.text in ["📝ដាក់អក្សរ", "🗑លុបអក្សរ"])
    @restrict_to_admin
    def admin_text_msg_step1(message):
        act = message.text
        btns = DatabaseEngine.execute_query("SELECT name FROM buttons WHERE bot_token=?", (bot_token,), fetchall=True)
        if not btns: return bot.send_message(message.chat.id, "⚠️ មិនមានប៊ូតុងទេ!")
        SessionMemory.set_state(message.chat.id, bot_token, 'txt_msg_btn', {'act': act})
        bot.send_message(message.chat.id, "សូមជ្រើសរើសប៊ូតុងដែលចង់រៀបចំអក្សរ៖", reply_markup=KeyboardBuilder.list_dynamic_options([b['name'] for b in btns]))

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'txt_msg_btn')
    def admin_text_msg_step2(message):
        uid = message.chat.id
        act = SessionMemory.get_state(uid, bot_token)['data']['act']
        btn_name = message.text
        
        if act == "🗑លុបអក្សរ":
            DatabaseEngine.execute_query("UPDATE buttons SET text_msg=NULL WHERE name=? AND bot_token=?", (btn_name, bot_token), commit=True)
            SessionMemory.clear_state(uid, bot_token)
            bot.send_message(uid, "✅ បានលុបអក្សរចេញពីប៊ូតុងរួចរាល់!", reply_markup=KeyboardBuilder.admin_dashboard(SecurityManager.get_user_role(uid, bot_token)))
        else:
            SessionMemory.set_state(uid, bot_token, 'txt_msg_input', {'btn': btn_name})
            bot.send_message(uid, "សូមវាយបញ្ចូលអក្សរដែលអ្នកចង់បង្ហាញនៅពេលគេចុចប៊ូតុងនេះ៖", reply_markup=KeyboardBuilder.cancel_only())

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'txt_msg_input')
    def admin_text_msg_step3(message):
        uid = message.chat.id
        btn_name = SessionMemory.get_state(uid, bot_token)['data']['btn']
        DatabaseEngine.execute_query("UPDATE buttons SET text_msg=? WHERE name=? AND bot_token=?", (message.text, btn_name, bot_token), commit=True)
        SessionMemory.clear_state(uid, bot_token)
        bot.send_message(uid, "✅ បានដាក់អក្សរចូលប៊ូតុងរួចរាល់!", reply_markup=KeyboardBuilder.admin_dashboard(SecurityManager.get_user_role(uid, bot_token)))

    # [៤] រៀបចំបូតុង (REARRANGE BUTTONS - SUPER FEATURE)
    @bot.message_handler(func=lambda m: m.text == "រៀបចំបូតុង")
    @restrict_to_admin
    def admin_rearrange_step1(message):
        btns = DatabaseEngine.execute_query("SELECT name FROM buttons WHERE bot_token=?", (bot_token,), fetchall=True)
        pkgs = DatabaseEngine.execute_query("SELECT name FROM packages WHERE bot_token=?", (bot_token,), fetchall=True)
        items = [b['name'] for b in btns] + [p['name'] for p in pkgs]
        
        if not items: return bot.send_message(message.chat.id, "⚠️ មិនមានទិន្នន័យដើម្បីរៀបចំទេ!")
        
        SessionMemory.set_state(message.chat.id, bot_token, 'arrange_select')
        bot.send_message(message.chat.id, "ជ្រើសរើសប៊ូតុង ឬ កញ្ចប់លក់ ដែលអ្នកចង់រុញទីតាំង៖", reply_markup=KeyboardBuilder.list_dynamic_options(items))

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'arrange_select')
    def admin_rearrange_step2(message):
        uid = message.chat.id
        name = message.text
        
        item = DatabaseEngine.execute_query("SELECT id, order_idx FROM buttons WHERE name=? AND bot_token=?", (name, bot_token), fetchone=True)
        tb_type = 'buttons'
        if not item:
            item = DatabaseEngine.execute_query("SELECT id, order_idx FROM packages WHERE name=? AND bot_token=?", (name, bot_token), fetchone=True)
            tb_type = 'packages'
            
        if not item: return bot.send_message(uid, "⚠️ រកមិនឃើញទិន្នន័យនេះទេ!")
        
        SessionMemory.set_state(uid, bot_token, 'arrange_move', {'id': item['id'], 'tb': tb_type, 'idx': item['order_idx']})
        bot.send_message(uid, f"កំពុងរៀបចំ៖ <b>{name}</b>\nសូមចុចប៊ូតុងសញ្ញាព្រួញខាងក្រោមដើម្បីរុញទីតាំង៖", parse_mode="HTML", reply_markup=KeyboardBuilder.rearrange_keypad())

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'arrange_move' and m.text in ["⬅️ឆ្វេង", "➡️ស្ដាំ", "⬆️លើ", "⬇️ក្រោម", "✅ រក្សាទុក"])
    def admin_rearrange_step3(message):
        uid = message.chat.id
        if message.text == "✅ រក្សាទុក":
            SessionMemory.clear_state(uid, bot_token)
            return bot.send_message(uid, "✅ ការរៀបចំប៊ូតុងត្រូវបានរក្សាទុកដោយជោគជ័យ!", reply_markup=KeyboardBuilder.admin_dashboard(SecurityManager.get_user_role(uid, bot_token)))
            
        data = SessionMemory.get_state(uid, bot_token)['data']
        # ⬅️/⬆️ បន្ថយលេខរៀង, ➡️/⬇️ តំឡើងលេខរៀង
        shift = -1 if message.text in ["⬅️ឆ្វេង", "⬆️លើ"] else 1
        new_idx = data['idx'] + shift
        
        DatabaseEngine.execute_query(f"UPDATE {data['tb']} SET order_idx=? WHERE id=? AND bot_token=?", (new_idx, data['id'], bot_token), commit=True)
        data['idx'] = new_idx
        SessionMemory.set_state(uid, bot_token, 'arrange_move', data)
        bot.send_message(uid, f"រុញទៅ {message.text} រួចរាល់។ សូមចុចបន្ត ឬ ចុច Save៖", reply_markup=KeyboardBuilder.rearrange_keypad())

    # [៥] ✏️អេតកព្ចាប់ Button & 🗑លុប កព្ចាប់
    @bot.message_handler(func=lambda m: m.text == "✏️អេតកព្ចាប់ Button")
    @restrict_to_admin
    def admin_add_pkg_step1(message):
        btns = DatabaseEngine.execute_query("SELECT name FROM buttons WHERE bot_token=?", (bot_token,), fetchall=True)
        opts = ["🌟 ខាងក្រៅបំផុត (ROOT)"] + [b['name'] for b in btns] if btns else ["🌟 ខាងក្រៅបំផុត (ROOT)"]
        SessionMemory.set_state(message.chat.id, bot_token, 'add_pkg_btn')
        bot.send_message(message.chat.id, "សូមជ្រើសរើសទីតាំង (Folder) ដែលអ្នកចង់ដាក់កញ្ចប់នេះលក់៖", reply_markup=KeyboardBuilder.list_dynamic_options(opts))

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'add_pkg_btn')
    def admin_add_pkg_step2(message):
        uid = message.chat.id
        parent_name = message.text
        parent_id = None
        if parent_name != "🌟 ខាងក្រៅបំផុត (ROOT)":
            p = DatabaseEngine.execute_query("SELECT id FROM buttons WHERE name=? AND bot_token=?", (parent_name, bot_token), fetchone=True)
            if p: parent_id = p['id']
            
        SessionMemory.set_state(uid, bot_token, 'add_pkg_name', {'pid': parent_id})
        bot.send_message(uid, "សូមវាយបញ្ចូលឈ្មោះកញ្ចប់ (ឧ. កញ្ចប់ម៉ូតឡាន, Key VIP)៖", reply_markup=KeyboardBuilder.cancel_only())

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'add_pkg_name')
    def admin_add_pkg_step3(message):
        uid = message.chat.id
        data = SessionMemory.get_state(uid, bot_token)['data']
        data['name'] = message.text
        SessionMemory.set_state(uid, bot_token, 'add_pkg_dur', data)
        bot.send_message(uid, "សូមវាយបញ្ចូលរយៈពេល ឬប្រភេទ (ឧ. 1 អាទិត្យ, លេងម៉ាសេរី)៖")

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'add_pkg_dur')
    def admin_add_pkg_step4(message):
        uid = message.chat.id
        data = SessionMemory.get_state(uid, bot_token)['data']
        data['dur'] = message.text
        SessionMemory.set_state(uid, bot_token, 'add_pkg_price', data)
        bot.send_message(uid, "សូមវាយតម្លៃគិតជាដុល្លារ (ឧ. 5.50) [បញ្ជាក់៖ ដាក់តែលេខប៉ុណ្ណោះ]៖")

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'add_pkg_price')
    def admin_add_pkg_step5(message):
        uid = message.chat.id
        try:
            price = float(message.text)
            data = SessionMemory.get_state(uid, bot_token)['data']
            pid = data['pid']
            
            idx_q = "SELECT MAX(order_idx) as m FROM packages WHERE button_id IS NULL AND bot_token=?" if pid is None else f"SELECT MAX(order_idx) as m FROM packages WHERE button_id={pid} AND bot_token=?"
            max_idx = DatabaseEngine.execute_query(idx_q, (bot_token,), fetchone=True)['m']
            new_idx = (max_idx or 0) + 1
            
            DatabaseEngine.execute_query(
                "INSERT INTO packages (bot_token, button_id, name, duration, price, order_idx) VALUES (?, ?, ?, ?, ?, ?)", 
                (bot_token, pid, data['name'], data['dur'], price, new_idx), commit=True
            )
            SessionMemory.clear_state(uid, bot_token)
            bot.send_message(uid, "✅ អេតកញ្ចប់សម្រាប់លក់បានជោគជ័យ!", reply_markup=KeyboardBuilder.admin_dashboard(SecurityManager.get_user_role(uid, bot_token)))
        except ValueError:
            bot.send_message(uid, "❌ តម្លៃត្រូវតែជាលេខសុទ្ធ! សូមវាយម្តងទៀត (ឧ. 5 ឬ 5.5)៖")

    @bot.message_handler(func=lambda m: m.text == "🗑លុប កព្ចាប់")
    @restrict_to_admin
    def admin_del_pkg_step1(message):
        pkgs = DatabaseEngine.execute_query("SELECT name FROM packages WHERE bot_token=?", (bot_token,), fetchall=True)
        if not pkgs: return bot.send_message(message.chat.id, "⚠️ មិនមានកញ្ចប់លក់ទេ!")
        SessionMemory.set_state(message.chat.id, bot_token, 'del_pkg')
        bot.send_message(message.chat.id, "សូមជ្រើសរើសកញ្ចប់ដែលអ្នកចង់លុបចោល៖", reply_markup=KeyboardBuilder.list_dynamic_options([p['name'] for p in pkgs]))

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'del_pkg')
    def admin_del_pkg_step2(message):
        uid = message.chat.id
        DatabaseEngine.execute_query("DELETE FROM packages WHERE name=? AND bot_token=?", (message.text, bot_token), commit=True)
        SessionMemory.clear_state(uid, bot_token)
        bot.send_message(uid, "✅ បានលុបកញ្ចប់ចេញពីប្រព័ន្ធដោយជោគជ័យ!", reply_markup=KeyboardBuilder.admin_dashboard(SecurityManager.get_user_role(uid, bot_token)))

    # [៦] 📦អេតស្តុកកព្ចាប់ & 🗑លុប ស្តុក (បង្ហាញចំនួនស្តុក)
    @bot.message_handler(func=lambda m: m.text in ["📦អេតស្តុកកព្ចាប់", "🗑លុប ស្តុក"])
    @restrict_to_admin
    def admin_stock_step1(message):
        uid = message.chat.id
        act = 'add_stock' if "អេត" in message.text else 'del_stock'
        pkgs = DatabaseEngine.execute_query("SELECT id, name FROM packages WHERE bot_token=?", (bot_token,), fetchall=True)
        if not pkgs: return bot.send_message(uid, "⚠️ អត់ទាន់មានកញ្ចប់លក់ទេ! សូមអេតកញ្ចប់ជាមុនសិន។")
        
        SessionMemory.set_state(uid, bot_token, 'select_stock_pkg', {'act': act})
        opts = []
        for p in pkgs:
            c = DatabaseEngine.execute_query("SELECT COUNT(*) as c FROM stocks WHERE package_id=? AND bot_token=?", (p['id'], bot_token), fetchone=True)['c']
            opts.append(f"{p['name']} (មាន {c} ស្តុក)")
            
        bot.send_message(uid, "សូមជ្រើសរើសកញ្ចប់៖", reply_markup=KeyboardBuilder.list_dynamic_options(opts))

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'select_stock_pkg')
    def admin_stock_step2(message):
        uid = message.chat.id
        pkg_name = message.text.split(" (មាន")[0]
        pkg = DatabaseEngine.execute_query("SELECT id FROM packages WHERE name=? AND bot_token=?", (pkg_name, bot_token), fetchone=True)
        if not pkg: return bot.send_message(uid, "⚠️ រកមិនឃើញកញ្ចប់នេះទេ! សូមជ្រើសរើសឲ្យបានត្រឹមត្រូវ។")
        
        act = SessionMemory.get_state(uid, bot_token)['data']['act']
        if act == 'del_stock':
            DatabaseEngine.execute_query("DELETE FROM stocks WHERE package_id=? AND bot_token=?", (pkg['id'], bot_token), commit=True)
            SessionMemory.clear_state(uid, bot_token)
            bot.send_message(uid, f"✅ បានលុបស្តុកទាំងអស់ចេញពីកញ្ចប់ '{pkg_name}' រួចរាល់!", reply_markup=KeyboardBuilder.admin_dashboard(SecurityManager.get_user_role(uid, bot_token)))
        else:
            SessionMemory.set_state(uid, bot_token, 'add_stock_input', {'pid': pkg['id']})
            txt = "សូមផ្ញើ Key ឬ File (ជាទម្រង់អក្សរ) មកកាន់ទីនេះ។\n\n*(ចំណាំ៖ ១ បន្ទាត់ចុះក្រោម = ១ ស្តុក ។ អ្នកអាចផ្ញើម្ដង ១០០បន្ទាត់ វានឹងលោតជាស្តុក ១០០ អូតូ!)*"
            bot.send_message(uid, txt, parse_mode="Markdown", reply_markup=KeyboardBuilder.cancel_only())

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'add_stock_input')
    def admin_stock_step3(message):
        uid = message.chat.id
        pid = SessionMemory.get_state(uid, bot_token)['data']['pid']
        keys = [k.strip() for k in message.text.split('\n') if k.strip()]
        
        count = 0
        for k in keys:
            DatabaseEngine.execute_query("INSERT INTO stocks (bot_token, package_id, content) VALUES (?, ?, ?)", (bot_token, pid, k), commit=True)
            count += 1
            
        SessionMemory.clear_state(uid, bot_token)
        bot.send_message(uid, f"✅ បានអេតបញ្ចូលចំនួន {count} ស្តុកទៅក្នុងកញ្ចប់ដោយជោគជ័យ!", reply_markup=KeyboardBuilder.admin_dashboard(SecurityManager.get_user_role(uid, bot_token)))

    # [៧] 💬ធ្ញើសារ (Broadcast)
    @bot.message_handler(func=lambda m: m.text == "💬ធ្ញើសារ")
    @restrict_to_admin
    def admin_broadcast_step1(message):
        SessionMemory.set_state(message.chat.id, bot_token, 'broadcast')
        bot.send_message(message.chat.id, "សូមវាយបញ្ចូលសារដែលអ្នកត្រូវផ្ញើទៅកាន់ Users ទាំងអស់៖", reply_markup=KeyboardBuilder.cancel_only())

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'broadcast')
    def admin_broadcast_step2(message):
        uid = message.chat.id
        b_msg = f"📣សារថ្មីពីរ Abmin\n\n{message.text}"
        bot.send_message(uid, "⏳ កំពុងដំណើរការផ្ញើសារ...")
        
        users = DatabaseEngine.execute_query("SELECT id FROM users WHERE bot_token=?", (bot_token,), fetchall=True)
        s, f = 0, 0
        
        for u in users:
            try: 
                bot.send_message(u['id'], b_msg)
                s += 1
            except: 
                f += 1
                
        SessionMemory.clear_state(uid, bot_token)
        bot.send_message(uid, f"✅ ការផ្ញើបានបញ្ចប់ដោយជោគជ័យ៖\n- ផ្ញើបានសម្រេច: {s} នាក់\n- បរាជ័យ: {f} នាក់", reply_markup=KeyboardBuilder.admin_dashboard(SecurityManager.get_user_role(uid, bot_token)))

    # [៨] ការកំណត់ទូទៅ (QR, ABA, Welcome, Links)
    @bot.message_handler(func=lambda m: m.text in ["🖼ដាក់QRcode", "✏️ដាក់ABA", "🖼Wellcome Photo", "✏️អេតលីង/វីដេអូ"])
    @restrict_to_admin
    def admin_settings_step1(message):
        SessionMemory.set_state(message.chat.id, bot_token, 'settings_input', {'act': message.text})
        bot.send_message(message.chat.id, f"សូមបញ្ជូន រូបភាព ឬ លីង សម្រាប់ [{message.text}] មកកាន់ទីនេះ៖", reply_markup=KeyboardBuilder.cancel_only())

    @bot.message_handler(content_types=['text', 'photo'], func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'settings_input')
    def admin_settings_step2(message):
        uid = message.chat.id
        act = SessionMemory.get_state(uid, bot_token)['data']['act']
        
        key_db = 'qr_generic' if act == "🖼ដាក់QRcode" else 'qr_aba' if act == "✏️ដាក់ABA" else 'welcome_photo' if act == "🖼Wellcome Photo" else 'tutorial_link'
        val = message.photo[-1].file_id if message.photo else message.text
        
        DatabaseEngine.execute_query("REPLACE INTO settings (key, bot_token, value) VALUES (?, ?, ?)", (key_db, bot_token, val), commit=True)
        SessionMemory.clear_state(uid, bot_token)
        bot.send_message(uid, "✅ បានរក្សាទុករួចរាល់!", reply_markup=KeyboardBuilder.admin_dashboard(SecurityManager.get_user_role(uid, bot_token)))

    @bot.message_handler(func=lambda m: m.text in ["🗑លុប QRcode", "🗑លុបABA", "🗑លុប Welcome Photo", "🗑លុបលីង/វីដេអូ"])
    @restrict_to_admin
    def admin_settings_del(message):
        txt = message.text
        key_db = 'qr_generic' if "QR" in txt else 'qr_aba' if "ABA" in txt else 'welcome_photo' if "Welcome" in txt else 'tutorial_link'
        DatabaseEngine.execute_query("DELETE FROM settings WHERE key=? AND bot_token=?", (key_db, bot_token), commit=True)
        bot.send_message(message.chat.id, "✅ បានលុបការកំណត់នេះរួចរាល់!", reply_markup=KeyboardBuilder.admin_dashboard(SecurityManager.get_user_role(message.chat.id, bot_token)))

    # ==========================================================================
    # 👑 [SUPER ADMIN] មុខងារមេធំគ្រប់គ្រងកូន Bot
    # ==========================================================================
    def restrict_to_super_admin(func):
        def wrapper(message):
            if SecurityManager.is_super_admin(message.chat.id, bot_token): return func(message)
        return wrapper

    @bot.message_handler(func=lambda m: m.text == "🔐បង្កើតកូតអេតមីន")
    @restrict_to_super_admin
    def super_gen_admin_code(message):
        code = f"BABY-{random.randint(1000, 9999)}"
        DatabaseEngine.execute_query("INSERT INTO admin_codes (code, bot_token) VALUES (?, ?)", (code, bot_token), commit=True)
        bot.send_message(message.chat.id, f"✅ កូតអេតមីនត្រូវបានបង្កើតជោគជ័យ។\n\nឲ្យកូតនេះទៅអ្នកដែលអ្នកចង់ឲ្យធ្វើជាអេតមីន ដើម្បីឲ្យគាត់វាយបញ្ជូនមកកាន់ Bot៖\n\n`/abmin {code}`", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text == "🤖Abb Bot")
    @restrict_to_super_admin
    def super_add_bot_step1(message):
        SessionMemory.set_state(message.chat.id, bot_token, 'add_bot_token')
        bot.send_message(message.chat.id, "សូមបញ្ជូន Bot Token ដែលយកពី @BotFather មកកាន់ទីនេះ៖", reply_markup=KeyboardBuilder.cancel_only())

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'add_bot_token')
    def super_add_bot_step2(message):
        uid = message.chat.id
        token_child = message.text.strip()
        bot.send_message(uid, "⏳ កំពុងភ្ជាប់ទៅកាន់ Telegram Server...")
        try:
            import requests
            r = requests.get(f"https://api.telegram.org/bot{token_child}/getMe").json()
            if r.get('ok'):
                username = "@" + r['result']['username']
                DatabaseEngine.execute_query("INSERT INTO child_bots (token, username) VALUES (?, ?)", (token_child, username), commit=True)
                
                # បញ្ឆេះ Bot ភ្លាមៗដោយប្រើ Thread ថ្មីការពារគាំង
                threading.Thread(target=SystemRunner.run_single_bot_instance, args=(token_child,), daemon=True).start()
                
                SessionMemory.clear_state(uid, bot_token)
                bot.send_message(uid, f"✅ អស្ចារ្យណាស់! កូន Bot ថ្មី {username} កំពុងដំណើរការហើយ។\n*(បញ្ជាក់៖ អ្នកដែលវាយ /start ក្នុង Bot នោះដំបូងគេបំផុត នឹងក្លាយជា Admin អូតូ)*", reply_markup=KeyboardBuilder.admin_dashboard('super_admin'))
            else:
                bot.send_message(uid, "❌ Token មិនត្រឹមត្រូវទេ! សូមពិនិត្យមើលម្ដងទៀត។")
        except Exception as e: 
            bot.send_message(uid, f"❌ មានបញ្ហាភ្ជាប់ API: {e}")

    @bot.message_handler(func=lambda m: m.text == "📊មើលចំនួនBot")
    @restrict_to_super_admin
    def super_view_bots(message):
        bots = DatabaseEngine.execute_query("SELECT username FROM child_bots", fetchall=True)
        txt = f"📊 ចំនួន Bot សរុបមាន: {len(bots)}\n\n" + "\n".join([f"- {b['username']}" for b in bots])
        bot.send_message(message.chat.id, txt)

    @bot.message_handler(func=lambda m: m.text == "🗑លុប Bot")
    @restrict_to_super_admin
    def super_del_bot_step1(message):
        bots = DatabaseEngine.execute_query("SELECT username FROM child_bots", fetchall=True)
        if not bots: return bot.send_message(message.chat.id, "⚠️ មិនមានកូន Bot នៅក្នុងប្រព័ន្ធទេ!")
        SessionMemory.set_state(message.chat.id, bot_token, 'del_bot')
        bot.send_message(message.chat.id, "សូមជ្រើសរើសឈ្មោះ Bot ដែលអ្នកចង់លុបចោល៖", reply_markup=KeyboardBuilder.list_dynamic_options([b['username'] for b in bots]))

    @bot.message_handler(func=lambda m: SessionMemory.get_state(m.chat.id, bot_token)['state'] == 'del_bot')
    def super_del_bot_step2(message):
        DatabaseEngine.execute_query("DELETE FROM child_bots WHERE username=?", (message.text,), commit=True)
        SessionMemory.clear_state(message.chat.id, bot_token)
        bot.send_message(message.chat.id, f"✅ បានលុប Bot {message.text} ជោគជ័យ! (Bot នេះនឹងឈប់ដំណើរការពេលអ្នក Restart Server)", reply_markup=KeyboardBuilder.admin_dashboard('super_admin'))

# ==============================================================================
# ♾️ [៦] MULTI-THREADING BOT RUNNER (បញ្ឆេះប្រព័ន្ធធានាមិនគាំងដាច់ខាត)
# ==============================================================================
class SystemRunner:
    @staticmethod
    def run_single_bot_instance(token, is_main=False):
        if token in active_bots: return
        active_bots[token] = True
        
        while True:
            try:
                # Threaded=True និង num_threads ធំ ជួយឱ្យ bot ឆ្លើយតបមនុស្សច្រើនក្នុងពេលតែមួយបាន
                bot_instance = telebot.TeleBot(token, threaded=True, num_threads=50)
                create_bot_handlers(bot_instance, token, is_main)
                bot_info = bot_instance.get_me()
                logger.info(f"🟢 Started Bot Process: {bot_info.username}")
                
                # Infinity Polling ជាមួយនឹងការគ្រប់គ្រង Error ការពារការដាច់
                bot_instance.infinity_polling(timeout=90, long_polling_timeout=90, logger_level=logging.ERROR)
            except Exception as e:
                logger.error(f"🔴 Bot Auto Restarting to prevent Crash... Reason: {e}")
                time.sleep(3)

    @staticmethod
    def boot_entire_system():
        logger.info(f"🚀 កំពុងបញ្ឆេះប្រព័ន្ធ {VERSION} ខ្នាតយក្ស...")
        
        # បញ្ឆេះកូន Bot ទាំងអស់ដែលមានក្នុង Database ជា Threads ដាច់ដោយឡែក
        child_bots = DatabaseEngine.execute_query("SELECT token FROM child_bots", fetchall=True)
        if child_bots:
            for cb in child_bots: 
                threading.Thread(target=SystemRunner.run_single_bot_instance, args=(cb['token'],), daemon=True).start()
                
        # បញ្ឆេះ Bot មេធំ នៅក្នុង Main Thread ដើម្បីទប់កុំឲ្យកម្មវិធីបិទ
        SystemRunner.run_single_bot_instance(MAIN_BOT_TOKEN, is_main=True)

if __name__ == '__main__':
    SystemRunner.boot_entire_system()