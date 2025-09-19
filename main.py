# -*- coding: utf-8 -*-
"""
India Social Panel - Professional SMM Services Bot
Advanced Telegram Bot for Social Media Marketing Services
"""

import asyncio
import json
import os
import random
import string
import time
from datetime import datetime
from typing import Dict, Any, Optional

from aiohttp import web
from aiohttp.web import Application
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Import modules
import account_handlers
import payment_system
import services
import account_creation
import text_input_handler

from states import OrderStates, CreateOfferStates, AdminSendOfferStates, OfferOrderStates, AdminCreateUserStates, AdminDirectMessageStates
from fsm_handlers import handle_link_input, handle_quantity_input, handle_coupon_input

# ========== CONFIGURATION ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing. Set it in Environment.")

# Get base URL from environment or use the Replit provided URL
BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL")
if not BASE_WEBHOOK_URL:
    # Auto-detect Replit URL if available
    repl_url = os.getenv("REPLIT_URL")
    if repl_url:
        BASE_WEBHOOK_URL = repl_url
    else:
        print("⚠️ BASE_WEBHOOK_URL not set. Bot will run in polling mode.")

OWNER_NAME = os.getenv("OWNER_NAME", "Panel Owner")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "tech_support_admin")

# Webhook settings
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "india_social_panel_secret_2025"
WEBHOOK_URL = f"{BASE_WEBHOOK_URL.rstrip('/')}{WEBHOOK_PATH}" if BASE_WEBHOOK_URL else None
WEBHOOK_MODE = bool(BASE_WEBHOOK_URL)  # True if webhook URL available, False for polling

# Server settings
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))

# Bot initialization with FSM storage
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
START_TIME = time.time()

# Webhook handler setup
webhook_requests_handler = SimpleRequestHandler(
    dispatcher=dp,
    bot=bot,
    secret_token=WEBHOOK_SECRET
)

# Bot restart tracking
BOT_RESTART_TIME = datetime.now()
# Simple admin notification on startup
# Simple admin notification on startup
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "7437014244"))  # Consistent admin ID

# Set to store users to be notified after a restart
users_to_notify = set()

# ========== DATA STORAGE ==========
# In-memory storage (will be replaced with database later)
users_data: Dict[int, Dict[str, Any]] = {}
orders_data: Dict[str, Dict[str, Any]] = {}
tickets_data: Dict[str, Dict[str, Any]] = {}
user_state: Dict[int, Dict[str, Any]] = {}  # For tracking user input states
order_temp: Dict[int, Dict[str, Any]] = {}  # For temporary order data
admin_users = {ADMIN_USER_ID}  # Use consistent admin user ID

# Handler registration flag - not needed
# _handlers_registered = False

# ========== PERSISTENT STORAGE FUNCTIONS ==========
def save_data_to_json(data: Dict, filename: str) -> None:
    """Save data dictionary to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ Data saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving data to {filename}: {e}")

def load_data_from_json(filename: str) -> Dict:
    """Load data from JSON file, return empty dict if file doesn't exist"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Data loaded from {filename}")
            return data
        else:
            print(f"📄 File {filename} not found, starting with empty data")
            return {}
    except Exception as e:
        print(f"❌ Error loading data from {filename}: {e}")
        return {}

def load_users_data_from_json() -> Dict:
    """Load users data from JSON file with string-to-int key conversion"""
    try:
        if os.path.exists("users.json"):
            with open("users.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Convert string keys to integers for memory consistency
            users_data_with_int_keys = {}
            for str_key, value in data.items():
                try:
                    int_key = int(str_key)
                    users_data_with_int_keys[int_key] = value
                except ValueError:
                    # If conversion fails, skip this entry
                    print(f"⚠️ Skipping invalid user ID key: {str_key}")
                    continue
            print(f"✅ Users data loaded from users.json with {len(users_data_with_int_keys)} users")
            return users_data_with_int_keys
        else:
            print(f"📄 File users.json not found, starting with empty users data")
            return {}
    except Exception as e:
        print(f"❌ Error loading users data from users.json: {e}")
        return {}

# ========== CORE FUNCTIONS ==========
def init_user(user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> None:
    """Initialize minimal user data if not exists. Full profile completed during account creation."""
    global users_data
    
    # Only create if user doesn't exist in memory (use integer keys for consistency)
    if user_id not in users_data:
        # Create minimal user record - full profile will be completed during account creation
        users_data[user_id] = {
            "user_id": user_id,
            "username": username or "",
            "first_name": first_name or "",
            "join_date": datetime.now().isoformat(),
            "account_created": False
        }
        # Save minimal record immediately with key conversion
        save_users_data()
        print(f"✅ Minimal user record created for {user_id} - full profile will be completed during account creation")

    # Initialize user state for input tracking
    if user_id not in user_state:
        user_state[user_id] = {
            "current_step": None,
            "data": {}
        }

def save_users_data():
    """Save users_data to JSON with string key conversion"""
    # Convert integer keys to strings for JSON compatibility
    users_data_with_str_keys = {str(k): v for k, v in users_data.items()}
    save_data_to_json(users_data_with_str_keys, "users.json")

def generate_referral_code() -> str:
    """Generate unique referral code"""
    return f"ISP{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

def generate_api_key() -> str:
    """Generate API key for user"""
    return f"ISP-{''.join(random.choices(string.ascii_letters + string.digits, k=32))}"

def generate_order_id() -> str:
    """Generate unique professional order ID"""
    import secrets
    import string

    # Generate timestamp part
    timestamp = str(int(time.time()))[-6:]  # Last 6 digits

    # Generate random part with letters and numbers
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

    # Create professional format: ISP-XXXXXX-YYYYYY
    order_id = f"ISP-{timestamp}-{random_part}"
    return order_id

def generate_ticket_id() -> str:
    """Generate unique ticket ID"""
    return f"TKT{int(time.time())}{random.randint(10, 99)}"

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in admin_users

def is_message_old(message: Message) -> bool:
    """Check if message was sent before bot restart"""
    if not message.date:
        return False

    # Convert message date to timestamp and compare with bot start time
    message_timestamp = message.date.timestamp()
    return message_timestamp < START_TIME

async def send_admin_notification(order_record: Dict[str, Any], photo_file_id: Optional[str] = None):
    """Send enhanced notification to admin group about a new order"""
    # Group ID where notifications will be sent
    admin_group_id = -1003009015663

    try:
        user_id = order_record.get('user_id')
        order_id = order_record.get('order_id')
        package_name = order_record.get('package_name', 'N/A')
        platform = order_record.get('platform') or 'N/A'
        quantity = order_record.get('quantity', 0)
        total_price = order_record.get('total_price', 0.0)
        payment_method = order_record.get('payment_method') or 'N/A'
        link = order_record.get('link') or 'N/A'
        service_id = order_record.get('service_id') or 'N/A'
        created_at = order_record.get('created_at', '')

        # Get complete user information from users_data
        # Ensure user_id is valid integer before using as key
        if user_id and isinstance(user_id, (int, str)):
            try:
                user_id_int = int(user_id) if isinstance(user_id, str) else user_id
                user_info = users_data.get(user_id_int, {})
            except (ValueError, TypeError):
                user_info = {}
        else:
            user_info = {}
        username = user_info.get('username', '')
        first_name = user_info.get('first_name', '')
        full_name = user_info.get('full_name', '')
        phone = user_info.get('phone_number', '')
        email = user_info.get('email', '')
        balance = user_info.get('balance', 0.0)
        total_spent = user_info.get('total_spent', 0.0)
        orders_count = user_info.get('orders_count', 0)
        join_date = user_info.get('join_date', '')
        referral_code = user_info.get('referral_code', '')

        # Format display values
        display_username = f"@{username}" if username else "Not Set"
        display_name = full_name or first_name or "Not Set"
        display_phone = phone if phone else "Not Set"
        display_email = email if email else "Not Set"

        print(f"📊 DEBUG: Enhanced user {user_id} info loaded successfully")

        if order_id: # Enhanced notification for new order with screenshot
            message_text = f"""
🚨 <b>New Order Received - Payment Screenshot!</b>

👤 <b>Customer Information:</b>
• 🆔 <b>User ID:</b> <code>{user_id}</code>
• 👤 <b>Name:</b> {display_name}
• 📱 <b>Username:</b> {display_username}
• 📞 <b>Phone:</b> {display_phone}
• 📧 <b>Email:</b> {display_email}
• 💰 <b>Balance:</b> ₹{balance:,.2f}
• 💸 <b>Total Spent:</b> ₹{total_spent:,.2f}
• 📦 <b>Previous Orders:</b> {orders_count}
• 📅 <b>Member Since:</b> {format_time(join_date)}
• 🔗 <b>Referral Code:</b> {referral_code}

📦 <b>Order Information:</b>
• 🆔 <b>Order ID:</b> <code>{order_id}</code>
• 📦 <b>Package:</b> {package_name}
• 📱 <b>Platform:</b> {platform.title()}
• 🔧 <b>Service ID:</b> <code>{service_id}</code>
• 🔗 <b>Target Link:</b> {link}
• 🔢 <b>Quantity:</b> {quantity:,}
• 💰 <b>Amount:</b> ₹{total_price:,.2f}
• 💳 <b>Payment Method:</b> {payment_method}
• 🕐 <b>Order Time:</b> {format_time(created_at)}

📸 <b>Payment screenshot uploaded - Verification Required!</b>

⚡️ <b>Quick Actions Available Below</b>
"""
        else: # Generic notification for screenshot upload if no order_id
            message_text = f"""
📸 <b>Screenshot Upload Received!</b>

👤 <b>User ID:</b> {user_id}
📝 <b>Details:</b> Payment screenshot uploaded

👉 <b>Please check for context</b>
"""

        # Enhanced management buttons for professional order handling
        keyboard_rows = []

        # Only add Complete/Cancel buttons when order_id is present and valid
        if order_id and order_id != "None":
            keyboard_rows.append([
                InlineKeyboardButton(text="✅ Complete Order", callback_data=f"admin_complete_{order_id}_{user_id}"),
                InlineKeyboardButton(text="❌ Cancel Order", callback_data=f"admin_cancel_{order_id}_{user_id}")
            ])

        # Always add user management buttons
        keyboard_rows.append([
            InlineKeyboardButton(text="💬 Send Message", callback_data=f"admin_message_{user_id}"),
            InlineKeyboardButton(text="👤 User Details", callback_data=f"admin_profile_{user_id}")
        ])

        # Add order-specific buttons only when order_id is present and valid
        if order_id and order_id != "None":
            keyboard_rows.append([
                InlineKeyboardButton(text="📊 Order Details", callback_data=f"admin_details_{order_id}"),
                InlineKeyboardButton(text="🔄 Refresh Status", callback_data=f"admin_refresh_{order_id}")
            ])

        management_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

        await bot.send_message(admin_group_id, message_text, parse_mode="HTML", reply_markup=management_keyboard)

        # If a photo_file_id is provided, send the photo as well
        if photo_file_id:
            await bot.send_photo(
                chat_id=admin_group_id,
                photo=photo_file_id,
                caption=f"📸 Payment Screenshot for Order ID: <code>{order_record.get('order_id')}</code>",
                parse_mode="HTML"
            )

        print(f"✅ Enhanced group notification sent for Order ID: {order_id or 'Screenshot Upload'}")

    except Exception as e:
        print(f"❌ Failed to send enhanced group notification: {e}")
        import traceback
        traceback.print_exc()

async def send_first_interaction_notification(user_id: int, first_name: str = "", username: str = ""):
    """Send notification to user on first interaction after restart"""

    try:
        # Get display name with username preference
        user_display_name = f"@{username}" if username else first_name or 'Friend'

        alive_text = f"""
🟢 <b>Bot is Live!</b>

Hello <b>{user_display_name}</b>! 👋

✅ <b>India Social Panel is now Online and Ready!</b>

💡 <b>All services are working perfectly</b>
🚀 <b>Ready to process your requests</b>

📱 <b>Available Services:</b>
• Instagram • YouTube • Facebook • Twitter • TikTok

🎯 Use <b>/start</b> to access all features!
"""
        await bot.send_message(user_id, alive_text)
        return True
    except Exception as e:
        print(f"❌ Failed to send first interaction notification to {user_id}: {e}")
        return False

async def send_new_user_notification_to_admin(user):
    """Send notification to admin group when a new user starts the bot for the first time"""
    admin_group_id = -1003009015663

    try:
        user_id = user.id
        first_name = user.first_name or "N/A"
        username = f"@{user.username}" if user.username else "N/A"

        notification_text = f"""
🆕 <b>New User Alert!</b>

👤 <b>User Details:</b>
• 🆔 <b>User ID:</b> <code>{user_id}</code>
• 👤 <b>First Name:</b> {first_name}
• 📱 <b>Username:</b> {username}
• 🕐 <b>Joined:</b> {datetime.now().strftime("%d %b %Y, %I:%M %p")}

🎉 <b>A new user has started the bot!</b>
"""

        await bot.send_message(admin_group_id, notification_text, parse_mode="HTML")
        print(f"✅ New user notification sent to admin group for user {user_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to send new user notification to admin group: {e}")
        return False

async def send_token_notification_to_admin(user_id: int, full_name: str, username: str, access_token: str):
    """Send notification to admin group with new user account details and access token"""
    admin_group_id = -1003009015663

    try:
        # Get additional user details if available
        user_info = users_data.get(user_id, {})
        phone_number = user_info.get('phone_number', 'N/A')
        email = user_info.get('email', 'N/A')

        # Format username display
        display_username = f"@{username}" if username else "N/A"

        notification_text = f"""
🎉 <b>NEW ACCOUNT CREATED!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 <b>USER DETAILS:</b>
• 🆔 <b>User ID:</b> <code>{user_id}</code>
• 👤 <b>Name:</b> {full_name}
• 📱 <b>Username:</b> {display_username}
• 📞 <b>Phone:</b> {phone_number}
• 📧 <b>Email:</b> {email}
• 🕐 <b>Created:</b> {datetime.now().strftime("%d %b %Y, %I:%M %p")}

🔐 <b>ACCESS TOKEN:</b>
<code>{access_token}</code>

✅ <b>Account successfully created and activated!</b>
💡 <b>User can now access all premium features</b>
"""

        await bot.send_message(admin_group_id, notification_text, parse_mode="HTML")
        print(f"✅ Token notification sent to admin group for user {user_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to send token notification to admin group: {e}")
        return False

def mark_user_for_notification(user_id: int):
    """Mark user for bot alive notification"""
    users_to_notify.add(user_id)

def format_currency(amount: float) -> str:
    """Format currency in Indian Rupees"""
    return f"₹{amount:,.2f}"

def format_time(timestamp: str) -> str:
    """Format datetime string"""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except (ValueError, TypeError):
        return "N/A"

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup: Optional[InlineKeyboardMarkup] = None) -> bool:
    """Safely edit callback message with comprehensive error handling"""
    if not callback.message:
        return False

    try:
        # Check if message is editable (not InaccessibleMessage)
        if (hasattr(callback.message, 'edit_text') and
            hasattr(callback.message, 'message_id') and
            hasattr(callback.message, 'text') and
            not callback.message.__class__.__name__ == 'InaccessibleMessage'):
            if reply_markup:
                await callback.message.edit_text(text, reply_markup=reply_markup)  # type: ignore
            else:
                await callback.message.edit_text(text)  # type: ignore
            return True
        else:
            # Message is inaccessible, send new message
            if hasattr(callback.message, 'chat') and hasattr(callback.message.chat, 'id'):
                if reply_markup:
                    await bot.send_message(callback.message.chat.id, text, reply_markup=reply_markup)
                else:
                    await bot.send_message(callback.message.chat.id, text)
                return True
            return False
    except Exception as e:
        print(f"Error editing message: {e}")
        # Try sending new message as fallback
        try:
            if hasattr(callback.message, 'chat') and hasattr(callback.message.chat, 'id'):
                if reply_markup:
                    await bot.send_message(callback.message.chat.id, text, reply_markup=reply_markup)
                else:
                    await bot.send_message(callback.message.chat.id, text)
                return True
        except Exception as fallback_error:
            print(f"Fallback message send failed: {fallback_error}")
        return False

def is_account_created(user_id: int) -> bool:
    """Check if user has completed account creation"""
    return users_data.get(user_id, {}).get("account_created", False)

# Menu functions moved to account_creation.py

def get_account_complete_menu() -> InlineKeyboardMarkup:
    """Build menu after account creation"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 My Account", callback_data="my_account"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

def get_amount_selection_menu() -> InlineKeyboardMarkup:
    """Build amount selection menu for add funds"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="₹500", callback_data="amount_500"),
            InlineKeyboardButton(text="₹1000", callback_data="amount_1000")
        ],
        [
            InlineKeyboardButton(text="₹2000", callback_data="amount_2000"),
            InlineKeyboardButton(text="₹5000", callback_data="amount_5000")
        ],
        [
            InlineKeyboardButton(text="💬 Custom Amount", callback_data="amount_custom")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

def get_support_menu() -> InlineKeyboardMarkup:
    """Build support tickets menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Create New Ticket", callback_data="create_ticket"),
        ],
        [
            InlineKeyboardButton(text="📖 View My Tickets", callback_data="view_tickets")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

def get_order_confirm_menu(price: float) -> InlineKeyboardMarkup:
    """Build order confirmation menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm Order", callback_data="confirm_order"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_order")
        ]
    ])

# ========== MENU BUILDERS ==========
def get_main_menu() -> InlineKeyboardMarkup:
    """Build main menu with all core features"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚀 New Order", callback_data="new_order"),
            InlineKeyboardButton(text="💰 Add Funds", callback_data="add_funds")
        ],
        [
            InlineKeyboardButton(text="👤 My Account", callback_data="my_account"),
            InlineKeyboardButton(text="⚙️ Services & Tools", callback_data="services_tools")
        ],
        [
            InlineKeyboardButton(text="📈 Service List", callback_data="service_list"),
            InlineKeyboardButton(text="🎫 Support Tickets", callback_data="support_tickets")
        ],
        [
            InlineKeyboardButton(text="🎁 Offers & Rewards", callback_data="offers_rewards"),
            InlineKeyboardButton(text="👑 Admin Panel", callback_data="admin_panel")
        ],
        [
            InlineKeyboardButton(text="📞 Contact & About", callback_data="contact_about")
        ]
    ])

def get_category_menu() -> InlineKeyboardMarkup:
    """Build social media category menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📷 Instagram", callback_data="cat_instagram"),
            InlineKeyboardButton(text="🎥 YouTube", callback_data="cat_youtube")
        ],
        [
            InlineKeyboardButton(text="📘 Facebook", callback_data="cat_facebook"),
            InlineKeyboardButton(text="🐦 Twitter", callback_data="cat_twitter")
        ],
        [
            InlineKeyboardButton(text="💼 LinkedIn", callback_data="cat_linkedin"),
            InlineKeyboardButton(text="🎵 TikTok", callback_data="cat_tiktok")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_main")
        ]
    ])

def get_service_menu(category: str) -> InlineKeyboardMarkup:
    """Build service menu for specific category"""
    services = {
        "instagram": [
            ("👥 Followers", "ig_followers"),
            ("❤️ Likes", "ig_likes"),
            ("👁️ Views", "ig_views"),
            ("💬 Comments", "ig_comments")
        ],
        "youtube": [
            ("👥 Subscribers", "yt_subscribers"),
            ("❤️ Likes", "yt_likes"),
            ("👁️ Views", "yt_views"),
            ("💬 Comments", "yt_comments")
        ],
        "facebook": [
            ("👥 Page Likes", "fb_likes"),
            ("👁️ Post Views", "fb_views"),
            ("💬 Comments", "fb_comments"),
            ("↗️ Shares", "fb_shares")
        ]
    }

    keyboard = []
    for name, data in services.get(category, []):
        keyboard.append([InlineKeyboardButton(text=name, callback_data=f"service_{data}")])

    keyboard.append([InlineKeyboardButton(text="⬅️ Back", callback_data="new_order")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_contact_menu() -> InlineKeyboardMarkup:
    """Build contact & about menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨‍💻 About Owner", callback_data="owner_info"),
            InlineKeyboardButton(text="🌐 Our Website", callback_data="website_info")
        ],
        [
            InlineKeyboardButton(text="💬 Support Channel", callback_data="support_channel"),
            InlineKeyboardButton(text="🤖 AI Support", callback_data="ai_support")
        ],
        [
            InlineKeyboardButton(text="👨‍💼 Contact Admin", callback_data="contact_admin"),
            InlineKeyboardButton(text="📜 Terms of Service", callback_data="terms_service")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

def get_services_tools_menu() -> InlineKeyboardMarkup:
    """Build services & tools menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 Mass Order", callback_data="mass_order"),
            InlineKeyboardButton(text="🔄 Subscriptions", callback_data="subscriptions")
        ],
        [
            InlineKeyboardButton(text="📊 Profile Analyzer", callback_data="profile_analyzer"),
            InlineKeyboardButton(text="## Hashtag Generator", callback_data="hashtag_generator")
        ],
        [
            InlineKeyboardButton(text="✨ Free Trial Service", callback_data="free_trial")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

def get_offers_rewards_menu() -> InlineKeyboardMarkup:
    """Build offers & rewards menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎟️ Redeem Coupon", callback_data="coupon_redeem"),
            InlineKeyboardButton(text="🤝 Partner Program", callback_data="partner_program")
        ],
        [
            InlineKeyboardButton(text="🏆 Loyalty Program", callback_data="loyalty_program"),
            InlineKeyboardButton(text="🎉 Daily Reward", callback_data="daily_reward")
        ],
        [
            InlineKeyboardButton(text="🥇 Leaderboard", callback_data="leaderboard"),
            InlineKeyboardButton(text="📝 Community Polls", callback_data="community_polls")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

# ========== BOT HANDLERS ==========

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    """Simple admin broadcast command - NO STATE MANAGEMENT NEEDED"""
    user = message.from_user
    if not user or not is_admin(user.id):
        await message.answer("⚠️ This command is for admins only!")
        return

    # Get broadcast message from command
    if not message.text:
        await message.answer("❌ Please provide a message to broadcast!")
        return
    command_parts = message.text.split(' ', 1)
    if len(command_parts) < 2:
        await message.answer("""
📢 <b>Broadcast Command Usage:</b>

💬 <b>Format:</b> /broadcast your message here

📝 <b>Example:</b> /broadcast Hello all users! New features available.

⚠️ <b>This will send to ALL registered users!</b>
""")
        return

    broadcast_message = command_parts[1]

    # Get all registered users DIRECTLY from users_data
    target_users = list(users_data.keys())
    print(f"📢 BROADCAST: Admin {user.id} sending to {len(target_users)} users")

    if not target_users:
        await message.answer("❌ No registered users found!")
        return

    # Send confirmation to admin
    await message.answer(f"""
📢 <b>Broadcasting Message...</b>

📊 <b>Target Users:</b> {len(target_users)}
📝 <b>Message:</b> {broadcast_message}

🔄 <b>Sending now...</b>
""")

    # Send broadcast messages DIRECTLY
    sent_count = 0
    failed_count = 0

    for user_id in target_users:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=broadcast_message,
                parse_mode="HTML"
            )
            sent_count += 1
            print(f"✅ Broadcast sent to user {user_id}")

            # Rate limiting
            import asyncio
            await asyncio.sleep(0.5)  # 0.5 second delay

        except Exception as e:
            failed_count += 1
            print(f"❌ Failed to send to user {user_id}: {e}")

    # Send final report to admin
    await message.answer(f"""
✅ <b>Broadcast Complete!</b>

📊 <b>Results:</b>
• ✅ Successfully sent: {sent_count}
• ❌ Failed: {failed_count}
• 👥 Total attempted: {len(target_users)}

🎯 <b>Broadcast finished!</b>
""")

@dp.message(Command("restoreuser"))
async def cmd_restoreuser(message: Message):
    """Admin command to restore a user back into memory after bot restart"""
    user = message.from_user
    if not user or not is_admin(user.id):
        await message.answer("⚠️ This command is for admins only!")
        return

    # Parse the command to extract USER_ID
    if not message.text:
        await message.answer("❌ Please provide a user ID to restore!")
        return
    command_parts = message.text.split(' ', 1)
    if len(command_parts) < 2:
        await message.answer("""
🔧 <b>Restore User Command Usage:</b>

💬 <b>Format:</b> /restoreuser USER_ID

📝 <b>Example:</b> /restoreuser 123456789

💡 <b>This will restore the user back into bot memory</b>
""")
        return

    try:
        user_id = int(command_parts[1].strip())
    except ValueError:
        await message.answer("❌ Invalid USER_ID! Please provide a valid numeric user ID.")
        return

    # Check if user is already in memory
    if user_id in users_data:
        await message.answer(f"⚠️ User {user_id} is already in memory!")
        return

    # Use the existing init_user function to create identical user record
    init_user(user_id)

    print(f"🔧 RESTORE: Admin {user.id} restored user {user_id} to memory")

    # Send confirmation message
    await message.answer(f"✅ User {user_id} has been successfully restored to memory.")

@dp.message(Command("sendtouser"))
async def cmd_sendtouser(message: Message):
    """Admin command to send a message to a specific user"""
    user = message.from_user
    if not user or not is_admin(user.id):
        await message.answer("⚠️ This command is for admins only!")
        return

    # Parse the command to extract USER_ID and message
    if not message.text:
        await message.answer("❌ Please provide user ID and message!")
        return
    command_parts = message.text.split(' ', 2)
    if len(command_parts) < 3:
        await message.answer("""
💬 <b>Send to User Command Usage:</b>

💬 <b>Format:</b> /sendtouser <USER_ID> <The message to send>

📝 <b>Example:</b> /sendtouser 123456789 Hello, your order is being processed.

💡 <b>This will send a direct message to the specified user</b>
""")
        return

    try:
        target_user_id = int(command_parts[1].strip())
    except ValueError:
        await message.answer("❌ Invalid USER_ID! Please provide a valid numeric user ID.")
        return

    message_text = command_parts[2]

    # Try to send message to the target user
    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=f"""
💬 <b>Message from Admin</b>

{message_text}

---
<i>India Social Panel Administration</i>
""",
            parse_mode="HTML"
        )

        print(f"💬 SEND_TO_USER: Admin {user.id} sent message to user {target_user_id}")
        await message.answer(f"✅ Message sent successfully to user {target_user_id}.")

    except Exception as e:
        print(f"❌ Failed to send message to user {target_user_id}: {e}")
        await message.answer(f"❌ Failed to send message to user {target_user_id}. Error: {str(e)}")

# ========== OFFERS SYSTEM ==========

def load_offers_from_json() -> list:
    """Load offers from offers.json file, return empty list if file doesn't exist"""
    try:
        if os.path.exists("offers.json"):
            with open("offers.json", 'r', encoding='utf-8') as f:
                offers = json.load(f)
            print(f"✅ Offers loaded from offers.json")
            return offers
        else:
            print(f"📄 File offers.json not found, starting with empty offers list")
            return []
    except Exception as e:
        print(f"❌ Error loading offers from offers.json: {e}")
        return []

def save_offers_to_json(offers: list) -> None:
    """Save offers list to offers.json file"""
    try:
        with open("offers.json", 'w', encoding='utf-8') as f:
            json.dump(offers, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ Offers saved to offers.json")
    except Exception as e:
        print(f"❌ Error saving offers to offers.json: {e}")

def generate_offer_id() -> str:
    """Generate unique offer ID"""
    return f"OFFER-{int(time.time())}-{random.randint(1000, 9999)}"

@dp.message(Command("create_offer"))
async def cmd_create_offer(message: Message, state: FSMContext):
    """Admin command to start offer creation process"""
    user = message.from_user
    if not user or not is_admin(user.id):
        await message.answer("⚠️ This command is for admins only!")
        return

    # Start the offer creation FSM flow
    await state.set_state(CreateOfferStates.getting_message)

    text = """
🎯 <b>Create New Offer - Step 1/5</b>

📝 <b>Offer Message Entry</b>

💡 <b>Please send the offer message that will be shown to users:</b>

📋 <b>Example Messages:</b>
• "🎉 Special Discount! Get 50% OFF on all Instagram packages!"
• "💸 Limited Time Offer: Buy 1000 followers, get 500 free!"
• "🔥 Flash Sale: All YouTube services at half price!"

⚠️ <b>Guidelines:</b>
• Write a clear and attractive message
• Use emojis
• Highlight the benefits
• Include call-to-action

📤 <b>Type and send your offer message:</b>
"""

    await message.answer(text)
    print(f"🎯 CREATE_OFFER: Admin {user.id} started offer creation process")

@dp.message(Command("delete_offer"))
async def cmd_delete_offer(message: Message):
    """Admin command to permanently delete an offer from offers.json"""
    user = message.from_user
    if not user or not is_admin(user.id):
        await message.answer("⚠️ This command is for admins only!")
        return

    # Parse the command to extract OFFER_ID
    if not message.text:
        await message.answer("❌ Please provide an offer ID to delete!")
        return
    command_parts = message.text.split(' ', 1)
    if len(command_parts) < 2:
        await message.answer("""
🗑️ <b>Delete Offer Command Usage:</b>

💬 <b>Format:</b> /delete_offer <OFFER_ID>

📝 <b>Example:</b> /delete_offer OFFER-1758164130-3130

⚠️ <b>This will permanently delete the offer!</b>
""")
        return

    offer_id = command_parts[1].strip()

    # Load current offers from offers.json
    offers = load_offers_from_json()
    
    if not offers:
        await message.answer("❌ No offers found in the system!")
        return

    # Find and remove the offer with matching OFFER_ID
    offer_found = False
    updated_offers = []
    removed_offer = None
    
    for offer in offers:
        if offer.get("offer_id") == offer_id:
            offer_found = True
            removed_offer = offer
            print(f"🗑️ DELETE_OFFER: Admin {user.id} deleting offer {offer_id}")
        else:
            updated_offers.append(offer)

    # Error handling for cases where the Offer ID is not found
    if not offer_found:
        await message.answer(f"""
❌ <b>Offer Not Found!</b>

🔍 <b>Offer ID "{offer_id}" does not exist</b>

💡 <b>Please check:</b>
• Offer ID is correct (case-sensitive)
• Offer hasn't been deleted already
• Use the exact Offer ID format

🔧 <b>Tip:</b> Check existing offers in the admin panel
""")
        return

    # Save the updated offers list back to offers.json
    save_offers_to_json(updated_offers)

    # Send confirmation message to admin
    if removed_offer:
        confirmation_text = f"""
✅ <b>Offer [{offer_id}] has been successfully deleted.</b>

🗑️ <b>Deleted Offer Details:</b>

🆔 <b>Offer ID:</b> <code>{removed_offer.get('offer_id', 'N/A')}</code>
📝 <b>Message:</b> {removed_offer.get('offer_message', 'N/A')}
📦 <b>Package:</b> {removed_offer.get('package_name', 'N/A')}
💰 <b>Rate:</b> {removed_offer.get('rate', 'N/A')}
📅 <b>Created:</b> {removed_offer.get('created_at', 'N/A')}

🎯 <b>The offer has been permanently removed from offers.json</b>

📊 <b>Remaining Offers:</b> {len(updated_offers)}
"""
    else:
        # This should not happen due to earlier validation, but add safety
        confirmation_text = f"""
❌ <b>Offer Not Found!</b>

🔍 <b>Offer ID "{offer_id}" was not found in the system</b>

📊 <b>Current Offers Count:</b> {len(updated_offers)}
"""

    await message.answer(confirmation_text)
    print(f"✅ DELETE_OFFER: Admin {user.id} successfully deleted offer {offer_id}")

@dp.message(CreateOfferStates.getting_message)
async def handle_offer_message(message: Message, state: FSMContext):
    """Handle offer message input in getting_message state"""
    if not message.text:
        await message.answer("⚠️ Please send a text message for the offer.")
        return

    offer_message = message.text.strip()

    # Store the offer message and move to next step
    await state.update_data(offer_message=offer_message)
    await state.set_state(CreateOfferStates.getting_package_name)

    text = f"""
✅ <b>Offer Message Saved!</b>

📝 <b>Message:</b> {offer_message}

🎯 <b>Create New Offer - Step 2/5</b>

📦 <b>Package Name Entry</b>

💡 <b>Send the package name for this offer:</b>

📋 <b>Example Package Names:</b>
• "Special Instagram Followers"
• "Premium YouTube Views"
• "Mega Facebook Likes Package"
• "Ultimate TikTok Growth Pack"

⚠️ <b>Guidelines:</b>
• Give a descriptive and attractive name
• Mention the platform
• Clearly mention service type

📤 <b>Type and send the package name:</b>
"""

    await message.answer(text)

@dp.message(CreateOfferStates.getting_package_name)
async def handle_package_name(message: Message, state: FSMContext):
    """Handle package name input in getting_package_name state"""
    if not message.text:
        await message.answer("⚠️ Please send a text message for the package name.")
        return

    package_name = message.text.strip()

    # Store the package name and move to next step
    await state.update_data(package_name=package_name)
    await state.set_state(CreateOfferStates.getting_rate)

    text = f"""
✅ <b>Package Name Saved!</b>

📦 <b>Package:</b> {package_name}

🎯 <b>Create New Offer - Step 3/5</b>

💰 <b>Rate Entry</b>

💡 <b>Send the rate for this package:</b>

📋 <b>Example Rates:</b>
• "₹100 per 1000"
• "₹50 per 500 followers"
• "₹200 per 10K views"
• "₹25 per 100 likes"

⚠️ <b>Guidelines:</b>
• Include currency symbol (₹)
• Clearly mention per unit rate
• Keep attractive pricing

📤 <b>Type and send the rate:</b>
"""

    await message.answer(text)

@dp.message(CreateOfferStates.getting_rate)
async def handle_rate(message: Message, state: FSMContext):
    """Handle rate input in getting_rate state"""
    if not message.text:
        await message.answer("⚠️ Please send a text message for the rate.")
        return

    rate = message.text.strip()

    # Store the rate and move to next step
    await state.update_data(rate=rate)
    await state.set_state(CreateOfferStates.asking_fixed_quantity)

    text = f"""
✅ <b>Rate Saved!</b>

💰 <b>Rate:</b> {rate}

🎯 <b>Create New Offer - Step 4/5</b>

🔢 <b>Fixed Quantity Setting</b>

💡 <b>Should this offer have a fixed quantity?</b>

📋 <b>Options:</b>
• <b>Yes:</b> Users will get a fixed quantity (e.g., exactly 1000 followers)
• <b>No:</b> Users can choose their preferred quantity

⚠️ <b>Choose wisely:</b>
• Fixed quantity is better for special offers
• Variable quantity provides flexibility

📤 <b>Reply with "Yes" or "No":</b>
"""

    await message.answer(text)

@dp.message(CreateOfferStates.asking_fixed_quantity)
async def handle_fixed_quantity_choice(message: Message, state: FSMContext):
    """Handle fixed quantity choice in asking_fixed_quantity state"""
    if not message.text:
        await message.answer("⚠️ Please reply with 'Yes' or 'No'.")
        return

    choice = message.text.strip().lower()

    if choice in ['yes', 'y', 'हां', 'हाँ']:
        # Ask for fixed quantity amount
        await state.update_data(has_fixed_quantity=True)
        await state.set_state(CreateOfferStates.getting_fixed_quantity)

        text = """
🔢 <b>Fixed Quantity Amount</b>

💡 <b>Send the fixed quantity amount:</b>

📋 <b>Examples:</b>
• 1000 (for 1000 followers)
• 5000 (for 5000 views)
• 500 (for 500 likes)

⚠️ <b>Guidelines:</b>
• Send only numbers
• Keep realistic quantity
• Choose popular quantities

📤 <b>Send the quantity number:</b>
"""

        await message.answer(text)

    elif choice in ['no', 'n', 'नहीं', 'nahi']:
        # Complete the offer creation
        await state.update_data(has_fixed_quantity=False, fixed_quantity=None)
        await complete_offer_creation(message, state)

    else:
        await message.answer("⚠️ Please reply with 'Yes' or 'No' only.")

@dp.message(CreateOfferStates.getting_fixed_quantity)
async def handle_fixed_quantity_amount(message: Message, state: FSMContext):
    """Handle fixed quantity amount input in getting_fixed_quantity state"""
    if not message.text:
        await message.answer("⚠️ Please send a number for the fixed quantity.")
        return

    try:
        fixed_quantity = int(message.text.strip())
        if fixed_quantity <= 0:
            await message.answer("⚠️ Quantity must be greater than 0. Please send a valid number.")
            return
    except ValueError:
        await message.answer("⚠️ Please send a valid number only.")
        return

    # Store the fixed quantity and complete offer creation
    await state.update_data(fixed_quantity=fixed_quantity)
    await complete_offer_creation(message, state)

async def complete_offer_creation(message: Message, state: FSMContext):
    """Complete the offer creation process and save to JSON"""
    # Get all collected data
    data = await state.get_data()

    # Create the offer dictionary
    offer = {
        "offer_id": generate_offer_id(),
        "offer_message": data.get("offer_message", ""),
        "package_name": data.get("package_name", ""),
        "rate": data.get("rate", ""),
        "has_fixed_quantity": data.get("has_fixed_quantity", False),
        "fixed_quantity": data.get("fixed_quantity"),
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "created_by": message.from_user.id if message.from_user else 0
    }

    # Load existing offers and add new one
    offers = load_offers_from_json()
    offers.append(offer)

    # Save updated offers list
    save_offers_to_json(offers)

    # Clear FSM state
    await state.clear()

    # Send confirmation message
    text = f"""
✅ <b>Offer Created Successfully!</b>

🎯 <b>Offer Details:</b>

🆔 <b>Offer ID:</b> <code>{offer['offer_id']}</code>
📝 <b>Message:</b> {offer['offer_message']}
📦 <b>Package:</b> {offer['package_name']}
💰 <b>Rate:</b> {offer['rate']}
🔢 <b>Fixed Quantity:</b> {"Yes (" + str(offer['fixed_quantity']) + ")" if offer['has_fixed_quantity'] else "No"}
🟢 <b>Status:</b> Active
📅 <b>Created:</b> {format_time(offer['created_at'])}

🎉 <b>The offer has been saved to offers.json and is ready to use!</b>
"""

    await message.answer(text)
    print(f"✅ CREATE_OFFER: Admin {message.from_user.id if message.from_user else 'Unknown'} created offer {offer['offer_id']}")

# ========== SEND OFFER SYSTEM ==========

async def send_offer_to_user(user_id: int, offer: dict, bot: Bot) -> bool:
    """Send offer message with Order Now button to a specific user"""
    try:
        offer_text = f"""
🎉 <b>Special Offer for You!</b>

{offer['offer_message']}

📦 <b>Package:</b> {offer['package_name']}
💰 <b>Rate:</b> {offer['rate']}
"""

        if offer.get('has_fixed_quantity') and offer.get('fixed_quantity'):
            offer_text += f"🔢 <b>Quantity:</b> {offer['fixed_quantity']}\n"

        offer_text += """
⚡ <b>Limited Time Offer!</b>
🛒 <b>Click below to order now!</b>
"""

        # Create Order Now button with offer_id in callback_data
        order_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🛒 Order Now", 
                callback_data=f"order_offer_{offer['offer_id']}"
            )]
        ])

        await bot.send_message(
            chat_id=user_id,
            text=offer_text,
            reply_markup=order_button,
            parse_mode="HTML"
        )
        return True
    except Exception as e:
        print(f"❌ Failed to send offer to user {user_id}: {e}")
        return False

@dp.message(Command("send_offer"))
async def cmd_send_offer(message: Message, state: FSMContext):
    """Admin command to start offer sending process"""
    user = message.from_user
    if not user or not is_admin(user.id):
        await message.answer("⚠️ This command is for admins only!")
        return

    # Start the offer sending FSM flow
    await state.set_state(AdminSendOfferStates.getting_offer_id)

    # Load and display available offers
    offers = load_offers_from_json()

    if not offers:
        await message.answer("❌ No offers found! Please create offers first using /create_offer")
        await state.clear()
        return

    offer_list = "\n".join([
        f"🆔 <code>{offer['offer_id']}</code> - {offer['package_name']}"
        for offer in offers if offer.get('is_active', True)
    ])

    text = f"""
📤 <b>Send Offer to Users - Step 1/3</b>

🎯 <b>Available Offers:</b>

{offer_list}

💡 <b>Please copy and send the offer ID you want to send:</b>

📋 <b>Example:</b>
<code>OFFER-1234567890-5678</code>

📤 <b>Send the Offer ID:</b>
"""

    await message.answer(text)
    print(f"📤 SEND_OFFER: Admin {user.id} started offer sending process")

@dp.message(AdminSendOfferStates.getting_offer_id)
async def handle_offer_id_input(message: Message, state: FSMContext):
    """Handle offer ID input in getting_offer_id state"""
    if not message.text:
        await message.answer("⚠️ Please send the Offer ID as text.")
        return

    offer_id = message.text.strip()

    # Load offers and validate offer_id
    offers = load_offers_from_json()
    selected_offer = None

    for offer in offers:
        if offer.get('offer_id') == offer_id and offer.get('is_active', True):
            selected_offer = offer
            break

    if not selected_offer:
        await message.answer(
            "❌ <b>Invalid Offer ID!</b>\n\n"
            "🔍 <b>Please check the Offer ID and try again</b>\n"
            "💡 <b>Make sure to copy the exact ID from the list</b>\n\n"
            "📤 <b>Send correct Offer ID:</b>"
        )
        return

    # Store selected offer and move to target selection
    await state.update_data(offer_id=offer_id, selected_offer=selected_offer)
    await state.set_state(AdminSendOfferStates.choosing_target)

    text = f"""
✅ <b>Offer Selected Successfully!</b>

🎯 <b>Selected Offer:</b>
🆔 <b>ID:</b> <code>{selected_offer['offer_id']}</code>
📦 <b>Package:</b> {selected_offer['package_name']}
💰 <b>Rate:</b> {selected_offer['rate']}

📤 <b>Send Offer to Users - Step 2/3</b>

👥 <b>Target Selection</b>

💡 <b>Who do you want to send this offer to?</b>

🌍 <b>All Users:</b> Send to all registered users
👤 <b>Specific User:</b> Send to a particular user

📤 <b>Choose your target audience:</b>
"""

    # Create target selection buttons
    target_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌍 All Users", callback_data="send_to_all_users"),
            InlineKeyboardButton(text="👤 Specific User", callback_data="send_to_specific_user")
        ]
    ])

    await message.answer(text, reply_markup=target_buttons)

@dp.callback_query(AdminSendOfferStates.choosing_target)
async def handle_target_choice(callback: CallbackQuery, state: FSMContext):
    """Handle target choice in choosing_target state"""
    if not callback.data:
        await callback.answer("❌ Invalid selection!")
        return

    # Get stored offer data
    data = await state.get_data()
    selected_offer = data.get('selected_offer')

    if not selected_offer:
        await callback.answer("❌ Offer data lost! Please start again.")
        await state.clear()
        return

    if callback.data == "send_to_all_users":
        # Send to all users
        await callback.answer("📤 Sending to all users...")

        # Use global users_data (already loaded with proper key conversion)
        if not users_data:
            if callback.message and hasattr(callback.message, 'edit_text'):
                await callback.message.edit_text(
                    "❌ <b>No users found!</b>\n\n"
                    "🔍 <b>No registered users available to send offers</b>"
                )
            await state.clear()
            return

        # Send offer to all users
        success_count = 0
        total_users = len(users_data)

        for user_id in users_data:
            if await send_offer_to_user(int(user_id), selected_offer, bot):
                success_count += 1

        # Report results and clear state
        if callback.message and hasattr(callback.message, 'edit_text'):
            await callback.message.edit_text(
                f"✅ <b>Offer Sent Successfully!</b>\n\n"
                f"📊 <b>Delivery Report:</b>\n"
                f"👥 <b>Total Users:</b> {total_users}\n"
                f"✅ <b>Successfully Sent:</b> {success_count}\n"
                f"❌ <b>Failed:</b> {total_users - success_count}\n\n"
                f"🎯 <b>Offer:</b> {selected_offer['package_name']}\n"
                f"🎉 <b>Campaign completed!</b>"
            )
        await state.clear()
        print(f"📤 SEND_OFFER: Admin sent offer {selected_offer['offer_id']} to all {total_users} users")

    elif callback.data == "send_to_specific_user":
        # Ask for specific user ID
        await state.set_state(AdminSendOfferStates.getting_specific_user_id)

        if callback.message and hasattr(callback.message, 'edit_text'):
            await callback.message.edit_text(
                f"👤 <b>Send to Specific User - Step 3/3</b>\n\n"
                f"🎯 <b>Selected Offer:</b> {selected_offer['package_name']}\n\n"
                f"💡 <b>Please send the target user's ID:</b>\n\n"
                f"📋 <b>How to find User ID:</b>\n"
                f"• When user messages the bot, ID shows in console\n"
                f"• User IDs are shown in admin commands\n\n"
                f"📤 <b>Send the User ID number:</b>"
            )
        await callback.answer()

    else:
        await callback.answer("❌ Invalid option!")

@dp.message(AdminSendOfferStates.getting_specific_user_id)
async def handle_specific_user_id(message: Message, state: FSMContext):
    """Handle specific user ID input in getting_specific_user_id state"""
    if not message.text:
        await message.answer("⚠️ Please send a user ID number.")
        return

    try:
        target_user_id = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Please send a valid user ID number.")
        return

    # Get stored offer data
    data = await state.get_data()
    selected_offer = data.get('selected_offer')

    if not selected_offer:
        await message.answer("❌ Offer data lost! Please start again with /send_offer")
        await state.clear()
        return

    # Check if user exists in global users_data
    if target_user_id not in users_data:
        await message.answer(
            f"❌ <b>User not found!</b>\n\n"
            f"👤 <b>User ID {target_user_id} is not registered with the bot</b>\n\n"
            f"💡 <b>Please check the user ID and try again</b>\n"
            f"📤 <b>Send correct User ID:</b>"
        )
        return

    # Send offer to specific user
    if await send_offer_to_user(target_user_id, selected_offer, bot):
        # Success - clear state and report
        await message.answer(
            f"✅ <b>Offer Sent Successfully!</b>\n\n"
            f"👤 <b>Target User:</b> {target_user_id}\n"
            f"🎯 <b>Offer:</b> {selected_offer['package_name']}\n"
            f"💰 <b>Rate:</b> {selected_offer['rate']}\n\n"
            f"🎉 <b>User will receive the offer with Order Now button!</b>"
        )
        await state.clear()
        print(f"📤 SEND_OFFER: Admin sent offer {selected_offer['offer_id']} to user {target_user_id}")
    else:
        await message.answer(
            f"❌ <b>Failed to send offer!</b>\n\n"
            f"⚠️ <b>Could not deliver offer to user {target_user_id}</b>\n"
            f"💡 <b>User might have blocked the bot or have privacy settings</b>\n\n"
            f"🔄 <b>Try again or choose a different user</b>"
        )

# Handle offer QR generation callback
@dp.callback_query(F.data == "offer_generate_qr_btn")
async def cb_offer_generate_qr(callback: CallbackQuery, state: FSMContext):
    """Handle offer QR code generation button"""
    from fsm_handlers import handle_offer_generate_qr
    await handle_offer_generate_qr(callback, state)

# Handle offer payment completion callback  
@dp.callback_query(F.data == "offer_payment_done")
async def cb_offer_payment_done(callback: CallbackQuery, state: FSMContext):
    """Handle offer payment done button"""
    from fsm_handlers import handle_offer_payment_done
    await handle_offer_payment_done(callback, state)

# Handle offer add fund callback
@dp.callback_query(F.data == "offer_add_fund_btn")
async def cb_offer_add_fund(callback: CallbackQuery, state: FSMContext):
    """Handle offer add fund button"""
    from fsm_handlers import handle_offer_add_fund
    await handle_offer_add_fund(callback, state)

# Handle offer direct payment callback
@dp.callback_query(F.data == "offer_direct_payment_btn")
async def cb_offer_direct_payment(callback: CallbackQuery, state: FSMContext):
    """Handle offer direct payment button"""
    from fsm_handlers import handle_offer_direct_payment
    await handle_offer_direct_payment(callback, state)

# Handle "Order Now" button clicks from sent offers - New Simplified Flow
@dp.callback_query(F.data.startswith("order_offer_"))
async def handle_order_offer(callback: CallbackQuery, state: FSMContext):
    """Handle Order Now button clicks from offers using simplified OfferOrderStates flow"""
    print(f"🔥 ORDER OFFER BUTTON: User {callback.from_user.id if callback.from_user else 'Unknown'} clicked Order Now button")
    print(f"🔥 ORDER OFFER BUTTON: Callback data: {callback.data}")

    if not callback.data:
        await callback.answer("❌ Invalid offer!")
        return

    # Extract offer_id from callback_data: "order_offer_OFFER-123456789-1234"
    offer_id = callback.data.replace("order_offer_", "")
    print(f"🔥 ORDER OFFER BUTTON: Extracted offer ID: {offer_id}")

    # Load offers and find the selected offer
    offers = load_offers_from_json()
    selected_offer = None

    for offer in offers:
        if offer.get('offer_id') == offer_id and offer.get('is_active', True):
            selected_offer = offer
            break

    if not selected_offer:
        print(f"❌ ORDER OFFER BUTTON: Offer {offer_id} not found or inactive")
        await callback.answer(
            "⚠️ Offer Expired!\n\n"
            "This special offer has ended or is no longer available.\n\n"
            "💡 Please check our latest offers or contact support for new deals.",
            show_alert=True
        )
        return

    user = callback.from_user
    if not user:
        print(f"❌ ORDER OFFER BUTTON: No user found in callback")
        await callback.answer("❌ User not found!")
        return

    print(f"✅ ORDER OFFER BUTTON: Found offer: {selected_offer['package_name']} for user {user.id}")

    # Check if user account is created
    if not is_account_created(user.id):
        print(f"⚠️ ORDER OFFER BUTTON: User {user.id} account not created")
        await callback.answer("⚠️ Please complete your account setup first!")
        if callback.message and hasattr(callback.message, 'edit_text'):
            await callback.message.edit_text(
                "⚠️ <b>Account Setup Required</b>\n\n"
                "🔐 <b>To place orders, you need to complete account creation first</b>\n\n"
                "💡 <b>Please start by sending /start command</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🚀 Start Account Setup", url="https://t.me/your_bot_username")]
                ])
            )
        return

    print(f"✅ ORDER OFFER BUTTON: User {user.id} account verified, starting offer order flow")

    # Store all offer details in FSM state for the new simplified flow
    await state.update_data(
        offer_id=offer_id,
        offer_message=selected_offer.get("offer_message", ""),
        package_name=selected_offer.get("package_name", ""),
        rate=selected_offer.get("rate", ""),
        has_fixed_quantity=selected_offer.get("has_fixed_quantity", False),
        fixed_quantity=selected_offer.get("fixed_quantity")
    )

    # Set the new OfferOrderStates.getting_link state
    await state.set_state(OfferOrderStates.getting_link)
    print(f"🔥 ORDER OFFER BUTTON: Set FSM state to OfferOrderStates.getting_link for user {user.id}")

    # Send simple message asking for link
    link_request_text = f"""
🚀 <b>Order Started - {selected_offer['package_name']}</b>

💰 <b>Rate:</b> {selected_offer['rate']}
{f"🔢 <b>Quantity:</b> {selected_offer['fixed_quantity']}" if selected_offer.get('has_fixed_quantity') and selected_offer.get('fixed_quantity') else ""}

🔗 <b>Send your profile link:</b>

💡 <b>Example:</b> https://instagram.com/yourprofile

📤 <b>Type your link now</b>
"""

    await callback.answer("🛒 Starting your order...")

    if callback.message and hasattr(callback.message, 'edit_text'):
        await callback.message.edit_text(link_request_text)
        print(f"✅ ORDER OFFER BUTTON: Link request message sent to user {user.id}")
    else:
        print(f"❌ ORDER OFFER BUTTON: No callback.message found to edit")

    print(f"🛒 OFFER_ORDER: User {user.id} started offer order for {offer_id} - waiting for link")

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command with professional welcome"""
    print(f"📨 Received /start command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        print("❌ No user found in message")
        return

    print(f"👤 Processing /start for user: {user.id} (@{user.username})")

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        print(f"⏰ Message is old, marking user {user.id} for notification")
        mark_user_for_notification(user.id)
        return  # Ignore old messages

    init_user(user.id, user.username or "", user.first_name or "")

    # Auto-complete account for admin users to avoid conflicts
    if is_admin(user.id) and not is_account_created(user.id):
        users_data[user.id]['account_created'] = True
        users_data[user.id]['full_name'] = user.first_name or "Admin"
        users_data[user.id]['email'] = "admin@indiasocialpanel.com"
        users_data[user.id]['phone_number'] = "+91XXXXXXXXXX"
        print(f"🔧 Auto-completed admin account for user {user.id}")
        # Save admin account data to persistent storage
        save_users_data()

    # Check if account is created
    if is_account_created(user.id):
        # Get user's actual username or first name
        user_display_name = f"@{user.username}" if user.username else user.first_name or 'Friend'

        # Existing user welcome - professional English message
        welcome_text = f"""
🚀 <b>Welcome Back to India Social Panel</b>
<b>Your Premium SMM Growth Partner</b>

Hello, <b>{user_display_name}</b>! Ready to accelerate your social media success?

✨ <b>What makes us special:</b>
📈 <b>Guaranteed Results:</b> Real growth you can measure and trust
⚡ <b>Lightning Speed:</b> Most services start within 0-6 hours  
🛡️ <b>100% Safe:</b> No bans, only secure growth methods
💎 <b>Premium Quality:</b> Real, active users - not bots
🎯 <b>Best Prices:</b> Unbeatable rates in the Indian market

🎪 <b>Choose your action below:</b>
"""
        await message.answer(welcome_text, reply_markup=get_main_menu())
    else:
        # NEW USER - Account creation focused welcome message
        user_display_name = f"@{user.username}" if user.username else user.first_name or 'Friend'

        # Send notification to admin group about new user
        await send_new_user_notification_to_admin(user)

        # Professional welcome message - designed for conversion
        new_user_welcome = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 🇮🇳 <b>INDIA SOCIAL PANEL</b>
┃ <i>Professional SMM Growth Partner</i>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🙏 <b>Namaste {user_display_name}!</b>

🚀 <b>Transform your social media presence with India's most trusted SMM platform</b>

✨ <b>What makes us special:</b>
📈 <b>50,000+ Happy Customers</b> - Join the success story
⚡ <b>60 Seconds Setup</b> - Quick account creation process  
🛡️ <b>100% Safe Methods</b> - Zero risk, maximum results
💎 <b>Premium Quality</b> - Real users, genuine engagement

🎯 <b>Ready to dominate social media?</b>

💡 <b>Create your free account in just 60 seconds!</b>
"""
        # Import required functions from account_creation for dynamic use
        await message.answer(new_user_welcome, reply_markup=account_creation.get_initial_options_menu())

@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    """Show main menu"""
    print(f"📨 Received /menu command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        print("❌ No user found in message")
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        print(f"⏰ Message is old, marking user {user.id} for notification")
        mark_user_for_notification(user.id)
        return  # Ignore old messages

    print(f"✅ Sending menu to user {user.id}")
    await message.answer("🏠 <b>Main Menu</b>\nSelect your preferred option below:", reply_markup=get_main_menu())

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    print(f"📨 Received /help command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        print("❌ No user found in message")
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        print(f"⏰ Message is old, marking user {user.id} for notification")
        mark_user_for_notification(user.id)
        return  # Ignore old messages

    help_text = f"""
❓ <b>Help & Support - India Social Panel</b>

🚀 <b>Welcome to India's Most Trusted SMM Platform!</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 <b>AVAILABLE BOT COMMANDS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• <b>/start</b> - Show main menu and start the bot
• <b>/menu</b> - Main menu for all services
• <b>/help</b> - Show this help message
• <b>/about</b> - Complete information about India Social Panel
• <b>/description</b> - Package details during order process

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <b>HOW TO USE THE BOT</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ <b>New User:</b> Use /start to create account
2️⃣ <b>Service Order:</b> Choose platform from menu → select service
3️⃣ <b>Payment:</b> Make payment via UPI, Bank Transfer, or Digital Wallet
4️⃣ <b>Tracking:</b> Track your orders from Order History

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 <b>SUPPORTED PLATFORMS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• 📷 <b>Instagram:</b> Followers, Likes, Views, Comments, Reels
• 🎥 <b>YouTube:</b> Subscribers, Views, Likes, Comments
• 📘 <b>Facebook:</b> Page Likes, Post Likes, Views, Shares  
• 🐦 <b>Twitter:</b> Followers, Likes, Retweets, Views
• 💼 <b>LinkedIn:</b> Connections, Post Engagement
• 🎵 <b>TikTok:</b> Followers, Likes, Views, Shares

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 <b>PAYMENT METHODS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ <b>UPI Payments:</b> Google Pay, PhonePe, Paytm
✅ <b>Bank Transfer:</b> NEFT, RTGS, IMPS  
✅ <b>Digital Wallets:</b> All major wallets
✅ <b>QR Code:</b> Instant payment via QR scan

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📞 <b>CUSTOMER SUPPORT</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 <b>Owner Contact:</b> @{OWNER_USERNAME}
⏰ <b>Response Time:</b> 2-6 hours
🕐 <b>Available:</b> 9 AM - 11 PM IST
📧 <b>Email:</b> support@indiasocialpanel.com

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ <b>IMPORTANT GUIDELINES</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• ✅ All services are 100% safe and secure
• ✅ No account bans will occur  
• ✅ You get real and active users
• ✅ 24/7 customer support is available
• ✅ Fast delivery guarantee (0-6 hours)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>QUICK TIPS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 <b>First Time:</b> You can place orders only after creating an account
💡 <b>Links:</b> Provide only correct and working links  
💡 <b>Payment:</b> Must share screenshot for verification
💡 <b>Support:</b> Contact us if you have any problems

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌟 <b>Thank you for choosing India Social Panel!</b>
🚀 <b>Press /start to begin your social media growth journey!</b>

💙 <b>Bot is working perfectly and ready for your service!</b>
"""

    print(f"✅ Sending help to user {user.id}")
    await message.answer(help_text)

@dp.message(Command("about"))
async def cmd_about(message: Message):
    """Handle /about command - Complete India Social Panel information"""
    print(f"📨 Received /about command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        print("❌ No user found in message")
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        print(f"⏰ Message is old, marking user {user.id} for notification")
        mark_user_for_notification(user.id)
        return  # Ignore old messages

    about_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 🇮🇳 <b>INDIA SOCIAL PANEL</b>
┃ <i>India's Most Trusted SMM Platform</i>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>OUR MISSION</b>
To provide affordable, high-quality social media marketing services to Indian businesses and individuals and help them succeed in the digital world.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌟 <b>WHY CHOOSE US?</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ <b>100% Real & Active Users</b>
• No bots, no fake accounts
• Genuine engagement guaranteed
• Long-lasting results

⚡ <b>Lightning Fast Delivery</b>
• Services start within 0-6 hours
• Real-time order tracking
• Instant notifications

🔒 <b>100% Safe & Secure</b>
• No account bans guaranteed
• SSL encrypted transactions
• Privacy protection assured

💰 <b>Best Prices in Market</b>
• Wholesale rates available
• Bulk order discounts
• No hidden charges

🎯 <b>Premium Quality Services</b>
• High retention guarantee
• Lifetime refill warranty
• Professional support team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 <b>SUPPORTED PLATFORMS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📷 <b>Instagram:</b> Followers, Likes, Views, Comments, Reels
🎥 <b>YouTube:</b> Subscribers, Views, Likes, Comments, Watch Time
📘 <b>Facebook:</b> Page Likes, Post Likes, Views, Shares
🐦 <b>Twitter:</b> Followers, Likes, Retweets, Views
💼 <b>LinkedIn:</b> Connections, Post Likes, Company Followers
🎵 <b>TikTok:</b> Followers, Likes, Views, Shares

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 <b>PREMIUM FEATURES</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎁 <b>For Our Valued Customers:</b>
• 24/7 Customer Support
• Real-time Order Tracking
• Multiple Payment Methods
• Instant Refund Policy
• Loyalty Rewards Program
• VIP Customer Benefits
• API Access for Resellers
• White-label Solutions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>OUR ACHIEVEMENTS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 <b>Trusted by 10,000+ Happy Customers</b>
📈 <b>5 Million+ Services Delivered</b>
⭐ <b>4.9/5 Average Customer Rating</b>
🚀 <b>99.9% Service Success Rate</b>
🌍 <b>Serving 50+ Countries Worldwide</b>
🇮🇳 <b>#1 SMM Panel in India</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 <b>PAYMENT METHODS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 <b>UPI Payments:</b> Google Pay, PhonePe, Paytm
🏦 <b>Bank Transfer:</b> NEFT, RTGS, IMPS
💳 <b>Digital Wallets:</b> All major wallets supported
💰 <b>Account Balance:</b> Instant order processing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍💻 <b>ABOUT THE FOUNDER</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🙏 <b>Name:</b> {OWNER_NAME}
📱 <b>Contact:</b> @{OWNER_USERNAME}
💼 <b>Experience:</b> 5+ Years in SMM Industry
🎯 <b>Vision:</b> "Making every Indian business successful on social media"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📞 <b>CUSTOMER SUPPORT</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💬 <b>Telegram:</b> @{OWNER_USERNAME}
📧 <b>Email:</b> support@indiasocialpanel.com
⏰ <b>Response Time:</b> 2-6 hours
🕐 <b>Available:</b> 9 AM - 11 PM IST

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌟 <b>JOIN OUR COMMUNITY</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📢 <b>Official Channel:</b> @IndiaSocialPanelOfficial
👥 <b>Support Group:</b> @IndiaSocialPanelSupport
📱 <b>Updates & Offers:</b> Daily notifications
🎁 <b>Exclusive Benefits:</b> Member-only discounts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💙 <b>Thank you for choosing India Social Panel!</b>
🚀 <b>Let's grow together on social media!</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 <b>Ready to get started? Use /start command!</b>
"""

    about_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚀 Get Started", callback_data="back_main"),
            InlineKeyboardButton(text="📞 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")
        ],
        [
            InlineKeyboardButton(text="💬 Join Channel", url="https://t.me/IndiaSocialPanelOfficial"),
            InlineKeyboardButton(text="👥 Support Group", url="https://t.me/IndiaSocialPanelSupport")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    print(f"✅ Sending about info to user {user.id}")
    await message.answer(about_text, reply_markup=about_keyboard)

@dp.message(Command("description"))
async def cmd_description(message: Message):
    """Handle /description command during order process"""
    print(f"📨 Received /description command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        print("❌ No user found in message")
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        print(f"⏰ Message is old, marking user {user.id} for notification")
        mark_user_for_notification(user.id)
        return  # Ignore old messages

    user_id = user.id

    # Check if user is in order process
    current_step = user_state.get(user_id, {}).get("current_step")

    if current_step in ["waiting_link", "waiting_quantity", "waiting_coupon"]:
        # User is in order process, show package description
        platform = user_state[user_id]["data"].get("platform", "")
        service_id = user_state[user_id]["data"].get("service_id", "")
        package_name = user_state[user_id]["data"].get("package_name", "Unknown Package")
        package_rate = user_state[user_id]["data"].get("package_rate", "₹1.00 per unit")

        # Get detailed package description from services.py
        from services import get_package_description
        description = get_package_description(platform, service_id)

        description_text = f"""
📋 <b>Detailed Package Description</b>

📦 <b>Package:</b> {package_name}
🆔 <b>ID:</b> {service_id}
💰 <b>Rate:</b> {package_rate}
🎯 <b>Platform:</b> {platform.title()}

{description['text']}

💡 <b>Continue sending link/quantity/coupon to return to the order process</b>
"""

        await message.answer(description_text)
    else:
        # User is not in order process
        text = """
⚠️ <b>Description Command</b>

📋 <b>/description command is only available during the order process</b>

💡 <b>To view package description:</b>
1. First use /start
2. Click on New Order
3. Select any service
4. Choose a package
5. Then use /description

🚀 <b>Use /start to begin placing an order now</b>
"""
        await message.answer(text, reply_markup=get_main_menu())

@dp.message(Command("account"))
async def cmd_account(message: Message):
    """Handle /account command"""
    print(f"📨 Received /account command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        return

    if is_message_old(message):
        mark_user_for_notification(user.id)
        return

    if not is_account_created(user.id):
        await message.answer("⚠️ Please create your account first using /start command!")
        return

    text = """
👤 <b>My Account Dashboard</b>

🎯 <b>Quick access to your account settings and information</b>

💡 <b>Use the menu below to navigate to your account:</b>
"""
    await message.answer(text, reply_markup=get_main_menu())

@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    """Handle /balance command"""
    print(f"📨 Received /balance command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        return

    if is_message_old(message):
        mark_user_for_notification(user.id)
        return

    if not is_account_created(user.id):
        await message.answer("⚠️ Please create your account first using /start command!")
        return

    user_id = user.id
    current_balance = users_data.get(user_id, {}).get("balance", 0.0)
    total_spent = users_data.get(user_id, {}).get("total_spent", 0.0)

    text = f"""
💰 <b>Account Balance Information</b>

💳 <b>Current Balance:</b> ₹{current_balance:,.2f}
💸 <b>Total Spent:</b> ₹{total_spent:,.2f}
📊 <b>Account Status:</b> ✅ Active

💡 <b>Use Add Funds button below to recharge your account</b>
"""

    balance_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Add Funds", callback_data="add_funds"),
            InlineKeyboardButton(text="📜 Payment History", callback_data="payment_history")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await message.answer(text, reply_markup=balance_keyboard)

@dp.message(Command("orders"))
async def cmd_orders(message: Message):
    """Handle /orders command"""
    print(f"📨 Received /orders command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        return

    if is_message_old(message):
        mark_user_for_notification(user.id)
        return

    if not is_account_created(user.id):
        await message.answer("⚠️ Please create your account first using /start command!")
        return

    text = """
📦 <b>Order History & Tracking</b>

🎯 <b>View all your orders and track their progress</b>

💡 <b>Use the menu below to access your order history:</b>
"""

    orders_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📜 Order History", callback_data="order_history"),
            InlineKeyboardButton(text="🔍 Track Order", callback_data="track_order")
        ],
        [
            InlineKeyboardButton(text="🚀 New Order", callback_data="new_order"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await message.answer(text, reply_markup=orders_keyboard)

@dp.message(Command("services"))
async def cmd_services(message: Message):
    """Handle /services command"""
    print(f"📨 Received /services command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        return

    if is_message_old(message):
        mark_user_for_notification(user.id)
        return

    text = """
📈 <b>SMM Services & Pricing</b>

🎯 <b>Browse all available social media marketing services</b>

💡 <b>Use the menu below to explore our services:</b>
"""
    await message.answer(text, reply_markup=get_category_menu())

@dp.message(Command("support"))
async def cmd_support(message: Message):
    """Handle /support command"""
    print(f"📨 Received /support command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        return

    if is_message_old(message):
        mark_user_for_notification(user.id)
        return

    text = f"""
🎫 <b>Customer Support Center</b>

💬 <b>Get help from our professional support team</b>

📞 <b>Support Options:</b>
• Live chat with support team
• Create support tickets
• Direct contact with admin
• FAQ and help guides

⏰ <b>Response Time:</b> 2-6 hours
🕐 <b>Available:</b> 9 AM - 11 PM IST

💡 <b>Choose your preferred support method:</b>
"""

    support_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎫 Create Ticket", callback_data="create_ticket"),
            InlineKeyboardButton(text="💬 Live Chat", url=f"https://t.me/{OWNER_USERNAME}")
        ],
        [
            InlineKeyboardButton(text="📞 Contact Admin", url=f"https://t.me/{OWNER_USERNAME}"),
            InlineKeyboardButton(text="❓ Help Guide", callback_data="help_support")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await message.answer(text, reply_markup=support_keyboard)

@dp.message(Command("offers"))
async def cmd_offers(message: Message):
    """Handle /offers command"""
    print(f"📨 Received /offers command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        return

    if is_message_old(message):
        mark_user_for_notification(user.id)
        return

    text = """
🎁 <b>Special Offers & Discounts</b>

🔥 <b>Exclusive deals and limited-time offers</b>

💡 <b>Access all available offers and rewards:</b>
"""
    await message.answer(text, reply_markup=get_offers_rewards_menu())

@dp.message(Command("referral"))
async def cmd_referral(message: Message):
    """Handle /referral command"""
    print(f"📨 Received /referral command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        return

    if is_message_old(message):
        mark_user_for_notification(user.id)
        return

    if not is_account_created(user.id):
        await message.answer("⚠️ Please create your account first using /start command!")
        return

    user_id = user.id
    referral_code = users_data.get(user_id, {}).get('referral_code', 'Not Generated')

    text = f"""
🤝 <b>Referral Program</b>

💰 <b>Earn rewards by referring friends!</b>

🔗 <b>Your Referral Code:</b> <code>{referral_code}</code>

🎁 <b>Referral Benefits:</b>
• 15% commission on friend's first order
• Bonus points for every successful referral
• Monthly referral contests with prizes
• Exclusive referral-only offers

💡 <b>How to refer:</b>
1. Share your referral code with friends
2. They use your code during signup
3. You earn rewards instantly

🚀 <b>Start earning today!</b>
"""

    referral_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Copy Referral Code", callback_data=f"copy_referral_{referral_code}"),
            InlineKeyboardButton(text="📊 Referral Stats", callback_data="referral_stats")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await message.answer(text, reply_markup=referral_keyboard)

@dp.message(Command("api"))
async def cmd_api(message: Message):
    """Handle /api command"""
    print(f"📨 Received /api command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        return

    if is_message_old(message):
        mark_user_for_notification(user.id)
        return

    if not is_account_created(user.id):
        await message.answer("⚠️ Please create your account first using /start command!")
        return

    text = """
🔧 <b>API Access & Integration</b>

💻 <b>Integrate our services with your applications</b>

📋 <b>API Features:</b>
• RESTful API endpoints
• Real-time order tracking
• Automated service delivery
• Comprehensive documentation

💡 <b>Access your API dashboard:</b>
"""

    api_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔑 Generate API Key", callback_data="api_key"),
            InlineKeyboardButton(text="📚 API Documentation", callback_data="api_docs")
        ],
        [
            InlineKeyboardButton(text="🧪 Test API", callback_data="api_testing"),
            InlineKeyboardButton(text="📝 Code Examples", callback_data="api_examples")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await message.answer(text, reply_markup=api_keyboard)

@dp.message(Command("status"))
async def cmd_status(message: Message):
    """Handle /status command"""
    print(f"📨 Received /status command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        return

    if is_message_old(message):
        mark_user_for_notification(user.id)
        return

    # Calculate uptime
    uptime_seconds = int(time.time() - START_TIME)
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60

    text = f"""
⚡ <b>Bot Status & Health Check</b>

🟢 <b>Bot Status:</b> Online & Operational
⏰ <b>Uptime:</b> {uptime_hours}h {uptime_minutes}m
📊 <b>System Health:</b> Excellent
🔄 <b>Last Update:</b> {datetime.now().strftime("%d %b %Y, %I:%M %p")}

💻 <b>System Information:</b>
• 📱 <b>Active Users:</b> {len(users_data)}
• 📦 <b>Total Orders:</b> {len(orders_data)}
• ⚡ <b>Response Time:</b> < 100ms
• 🔒 <b>Security:</b> SSL Encrypted

✅ <b>All systems are running perfectly!</b>
"""

    status_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Refresh Status", callback_data="refresh_status"),
            InlineKeyboardButton(text="📊 Statistics", callback_data="bot_statistics")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await message.answer(text, reply_markup=status_keyboard)

@dp.message(Command("contact"))
async def cmd_contact(message: Message):
    """Handle /contact command"""
    print(f"📨 Received /contact command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        return

    if is_message_old(message):
        mark_user_for_notification(user.id)
        return

    text = """
📞 <b>Contact & Business Information</b>

🎯 <b>Get in touch with our team</b>

💡 <b>Choose your contact preference:</b>
"""
    await message.answer(text, reply_markup=get_contact_menu())

@dp.message(Command("language"))
async def cmd_language(message: Message):
    """Handle /language command"""
    print(f"📨 Received /language command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        return

    if is_message_old(message):
        mark_user_for_notification(user.id)
        return

    text = """
🌐 <b>Language & Regional Settings</b>

🗣️ <b>Currently Available Languages:</b>
• 🇮🇳 English (Default)
• 🇮🇳 हिंदी (Hindi) - Coming Soon
• 🇮🇳 मराठी (Marathi) - Coming Soon

🎯 <b>Regional Features:</b>
• Local payment methods
• Regional pricing
• Cultural customization
• Local support hours

💡 <b>Language selection feature coming soon!</b>
📞 <b>For language support:</b> @{OWNER_USERNAME}
"""

    language_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📞 Request Language", url=f"https://t.me/{OWNER_USERNAME}"),
            InlineKeyboardButton(text="🔔 Get Notified", callback_data="notify_language")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await message.answer(text, reply_markup=language_keyboard)

@dp.message(Command("notifications"))
async def cmd_notifications(message: Message):
    """Handle /notifications command"""
    print(f"📨 Received /notifications command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        return

    if is_message_old(message):
        mark_user_for_notification(user.id)
        return

    text = """
🔔 <b>Notification Settings</b>

📱 <b>Manage your alert preferences</b>

💡 <b>Notification Types:</b>
• Order status updates
• Payment confirmations
• Special offers & deals
• Account security alerts
• System maintenance notices

⚙️ <b>Notification Preferences:</b>
• Telegram messages (Current)
• Email notifications (Coming Soon)
• SMS alerts (Premium Feature)

🔧 <b>Notification management coming soon!</b>
"""

    notifications_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📧 Email Setup", callback_data="email_notifications"),
            InlineKeyboardButton(text="📱 SMS Setup", callback_data="sms_notifications")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await message.answer(text, reply_markup=notifications_keyboard)

@dp.message(Command("premium"))
async def cmd_premium(message: Message):
    """Handle /premium command"""
    print(f"📨 Received /premium command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        return

    if is_message_old(message):
        mark_user_for_notification(user.id)
        return

    text = """
👑 <b>Premium Features & VIP Membership</b>

✨ <b>Unlock exclusive premium benefits!</b>

💎 <b>Premium Benefits:</b>
• Priority customer support
• Exclusive premium services
• Advanced analytics dashboard
• API access with higher limits
• Special pricing discounts
• Early access to new features

🏆 <b>VIP Membership Tiers:</b>
• 🥉 Bronze: ₹5,000+ spent
• 🥈 Silver: ₹15,000+ spent  
• 🥇 Gold: ₹50,000+ spent
• 💎 Diamond: ₹1,00,000+ spent

🚀 <b>Premium features launching soon!</b>
"""

    premium_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👑 Upgrade Now", callback_data="upgrade_premium"),
            InlineKeyboardButton(text="📊 Check Eligibility", callback_data="check_premium")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await message.answer(text, reply_markup=premium_keyboard)

@dp.message(Command("analytics"))
async def cmd_analytics(message: Message):
    """Handle /analytics command"""
    print(f"📨 Received /analytics command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        return

    if is_message_old(message):
        mark_user_for_notification(user.id)
        return

    if not is_account_created(user.id):
        await message.answer("⚠️ Please create your account first using /start command!")
        return

    user_id = user.id
    user_data = users_data.get(user_id, {})
    user_orders = [order for order in orders_data.values() if order.get('user_id') == user_id]

    text = f"""
📊 <b>Account Analytics & Statistics</b>

💰 <b>Financial Summary:</b>
• Total Spent: ₹{user_data.get('total_spent', 0.0):,.2f}
• Current Balance: ₹{user_data.get('balance', 0.0):,.2f}
• Total Orders: {len(user_orders)}

📈 <b>Growth Metrics:</b>
• Account Age: {format_time(user_data.get('join_date', ''))}
• Order Success Rate: 95%+
• Average Order Value: ₹{(user_data.get('total_spent', 0.0) / max(len(user_orders), 1)):,.2f}

📊 <b>Advanced analytics dashboard coming soon!</b>
"""

    analytics_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📈 Growth Chart", callback_data="growth_chart"),
            InlineKeyboardButton(text="💰 Spending Analysis", callback_data="spending_analysis")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await message.answer(text, reply_markup=analytics_keyboard)

@dp.message(Command("feedback"))
async def cmd_feedback(message: Message):
    """Handle /feedback command"""
    print(f"📨 Received /feedback command from user {message.from_user.id if message.from_user else 'Unknown'}")

    user = message.from_user
    if not user:
        return

    if is_message_old(message):
        mark_user_for_notification(user.id)
        return

    text = f"""
⭐ <b>Rate Our Service & Share Feedback</b>

💝 <b>Your opinion matters to us!</b>

📝 <b>Feedback Options:</b>
• Rate our service quality
• Share your experience
• Suggest improvements
• Report any issues

🎁 <b>Feedback Rewards:</b>
• Bonus points for detailed reviews
• Special discounts for constructive feedback
• Recognition in our testimonials
• Priority support for regular reviewers

💬 <b>How to share feedback:</b>
"""

    feedback_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐ Rate 5 Stars", callback_data="rate_5_stars"),
            InlineKeyboardButton(text="📝 Write Review", url=f"https://t.me/{OWNER_USERNAME}")
        ],
        [
            InlineKeyboardButton(text="💡 Suggest Feature", callback_data="suggest_feature"),
            InlineKeyboardButton(text="🐛 Report Issue", callback_data="report_issue")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await message.answer(text, reply_markup=feedback_keyboard)

@dp.message(Command("viewuser"))
async def cmd_viewuser(message: Message):
    """Handle /viewuser <USER_ID> command for admin user profile viewing"""
    print(f"📨 Received /viewuser command from user {message.from_user.id if message.from_user else 'Unknown'}")

    # Import log_activity function
    from services import log_activity

    user = message.from_user
    if not user:
        print("❌ No user found in message")
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        print(f"⏰ Message is old, marking user {user.id} for notification")
        mark_user_for_notification(user.id)
        return  # Ignore old messages

    # Verify admin access
    if not is_admin(user.id):
        await message.answer("⚠️ Access denied. This command is for administrators only.")
        return

    # Parse command arguments
    if not message.text:
        await message.answer("❌ Please provide a command with text!")
        return
    command_text = message.text.strip()
    parts = command_text.split()

    # Check command format
    if len(parts) != 2:
        error_text = """
❌ <b>Invalid Command Format</b>

📋 <b>Usage:</b> <code>/viewuser &lt;USER_ID&gt;</code>

💡 <b>Examples:</b>
• <code>/viewuser 7437014244</code>
• <code>/viewuser 1234567890</code>

⚠️ <b>Please provide exactly one User ID</b>
"""
        await message.answer(error_text, parse_mode="HTML")
        return

    user_id_input = parts[1].strip()

    # Validate the user ID is numeric
    if not user_id_input.isdigit():
        error_text = """
❌ <b>Invalid User ID Format</b>

🔍 <b>User ID must be numeric</b>

💡 <b>Examples:</b>
• <code>/viewuser 7437014244</code>
• <code>/viewuser 1234567890</code>

⚠️ <b>Send only numbers, no extra text</b>
"""
        await message.answer(error_text, parse_mode="HTML")
        return

    # Convert to integer
    target_user_id = int(user_id_input)

    # Access current users_data (don't overwrite global state)
    # users_data is already loaded and maintained globally

    # Check if user exists
    if str(target_user_id) not in users_data and target_user_id not in users_data:
        not_found_text = f"""
❌ <b>User Not Found</b>

🔍 <b>User ID {target_user_id} does not exist in our database</b>

💡 <b>Please check:</b>
• User ID is correct
• User has registered with the bot
• Check the User Management dashboard for valid IDs

🔧 <b>Try:</b> /start → Admin Panel → Users → View recent users
"""
        await message.answer(not_found_text, parse_mode="HTML")
        return

    # Get user data (handle both string and int keys)
    try:
        user_data = users_data.get(str(target_user_id)) or users_data.get(target_user_id, {})
    except (KeyError, TypeError):
        user_data = {}

    # Format detailed user profile
    full_name = user_data.get('full_name', 'N/A')
    username = user_data.get('username', 'N/A')
    phone_number = user_data.get('phone_number', 'N/A')
    email = user_data.get('email', 'N/A')
    balance = user_data.get('balance', 0)
    total_spent = user_data.get('total_spent', 0)
    join_date = user_data.get('created_at', user_data.get('join_date', 'N/A'))
    api_key = user_data.get('access_token', 'Not generated')
    account_created = user_data.get('account_created', False)

    display_username = f"@{username}" if username and username != 'N/A' else 'Not set'


    profile_text = f"""
👤 <b>User Profile Details</b>

🔍 <b>User ID:</b> <code>{target_user_id}</code>

👤 <b>Personal Information:</b>
• <b>Full Name:</b> {full_name}
• <b>Username:</b> {display_username}
• <b>Phone:</b> <tg-spoiler>{phone_number}</tg-spoiler>
• <b>Email:</b> <tg-spoiler>{email}</tg-spoiler>

💰 <b>Account Information:</b>
• <b>Balance:</b> ₹{balance:.2f}
• <b>Total Spent:</b> ₹{total_spent:.2f}
• <b>Account Status:</b> {'✅ Active' if account_created else '❌ Incomplete'}

📅 <b>Activity:</b>
• <b>Joined:</b> {join_date}

🔐 <b>Security:</b>
• <b>Access Token:</b> <tg-spoiler><code>{api_key}</code></tg-spoiler>

💡 <b>Privacy Protected:</b> Sensitive data hidden - tap to reveal!
⚡ <b>Command executed successfully!</b>
"""

    # Create keyboard with admin options
    keyboard_buttons = [
        [InlineKeyboardButton(
            text="💬 Send Message", 
            callback_data=f"admin_msg_user_{target_user_id}"
        )]
    ]
    
    # Add conditional button for incomplete accounts
    if not account_created:
        keyboard_buttons.append([InlineKeyboardButton(
            text="➕ Create Account via Token", 
            callback_data=f"admin_create_token_{target_user_id}"
        )])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    log_activity(user.id, f"Viewed profile for user {target_user_id}")
    await message.answer(profile_text, parse_mode="HTML", reply_markup=keyboard)

# ========== PHOTO HANDLERS ==========
@dp.message(OrderStates.waiting_screenshot, F.photo)
async def handle_screenshot_fsm(message: Message, state: FSMContext):
    """Handle the screenshot sent by the user using FSM."""
    if not message.from_user or not message.photo:
        await state.clear()
        return

    try:
        user_id = message.from_user.id
        order_data = await state.get_data()

        if not order_data.get("service_id"):
            await message.answer("⚠️ Order data could not be found. Please start a new order.")
            await state.clear()
            return

        # Generate order ID
        order_id = generate_order_id() # Assumes this function is available in the file

        # Create final order record from FSM data
        order_record = {
            'order_id': order_id,
            'user_id': user_id,
            'package_name': order_data.get("package_name", "N/A"),
            'service_id': order_data.get("service_id", "N/A"),
            'platform': order_data.get("platform", "N/A"),
            'link': order_data.get("link", "N/A"),
            'quantity': order_data.get("quantity", 0),
            'total_price': order_data.get("total_price", 0.0),
            'status': 'processing',
            'created_at': datetime.now().isoformat(),
            'payment_method': 'QR Code Screenshot',
            'payment_status': 'pending_verification'
        }

        # Store the final order
        # orders_data and send_admin_notification are already available in this module
        orders_data[order_id] = order_record

        # Send notification to admin group
        photo_file_id = None
        if message.photo and len(message.photo) > 0:
            photo_file_id = message.photo[-1].file_id
        await send_admin_notification(order_record, photo_file_id)

        # Send confirmation to user
        success_text = f"""
🎉 <b>Order Successfully Placed!</b>

✅ <b>Payment Screenshot Received!</b>

🆔 <b>Order ID:</b> <code>{order_id}</code>
📦 <b>Package:</b> {order_record['package_name']}
🔢 <b>Quantity:</b> {order_record['quantity']:,}
💰 <b>Amount:</b> {format_currency(order_record['total_price'])}

📋 <b>Order Status:</b> ⏳ Processing
🔄 <b>Payment Status:</b> Pending Verification

💡 <b>Your order will be completed after verification.</b>
"""

        success_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📜 Order History", callback_data="order_history"),
                InlineKeyboardButton(text="🚀 New Order", callback_data="new_order")
            ]
        ])

        await message.answer(success_text, reply_markup=success_keyboard)

    except Exception as e:
        print(f"CRITICAL ERROR in handle_screenshot_fsm: {e}")
        await message.answer("An error occurred while processing your order. Please contact support.")

    finally:
        # Clear the state to finish the conversation
        await state.clear()

@dp.message(F.photo)
async def handle_photo_message(message: Message):
    """Handle photo uploads (for screenshots, etc.)"""
    if not message.from_user:
        return

    user_id = message.from_user.id

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        mark_user_for_notification(user_id)
        return  # Ignore old messages

    # Try to handle as screenshot upload
    from text_input_handler import handle_screenshot_upload
    screenshot_handled = await handle_screenshot_upload(
        message, order_temp, generate_order_id, format_currency, get_main_menu
    )

    if not screenshot_handled:
        # Photo not related to order process
        text = """
📸 <b>Photo Received</b>

💡 <b>This photo is not for any order process</b>

📋 <b>To use photos:</b>
• First start the order process
• Choose payment method
• Generate QR code
• Then send the screenshot

🏠 <b>Press /start for main menu</b>
"""
        await message.answer(text, reply_markup=get_main_menu())

# ========== ACCOUNT CREATION AND LOGIN HANDLERS (MOVED TO account_creation.py) ==========
# All account creation handlers have been moved to account_creation.py for better code organization

@dp.callback_query(F.data == "help_support")
async def cb_help_support(callback: CallbackQuery):
    """Handle help and support for new users"""
    if not callback.message:
        return

    text = f"""
❓ <b>Help & Support</b>

🤝 <b>Our Support Team is ready to help you!</b>

📞 <b>Contact Options:</b>
• Telegram: @{OWNER_USERNAME}
• Support Chat: Direct message
• Response Time: 2-6 hours

💡 <b>Common Questions:</b>
• Account creation issues
• Payment problems
• Service inquiries
• Technical difficulties

🎯 <b>Quick Solutions:</b>
• Create Account - New users
• Login Account - Existing users
• Check our service list
• Contact support for help

🔒 <b>Safe & Secure Platform</b>
✅ <b>Trusted by thousands of users</b>
"""

    help_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📞 Contact Support", url=f"https://t.me/{OWNER_USERNAME}"),
            InlineKeyboardButton(text="📝 Create Account", callback_data="create_account")
        ],
        [
            InlineKeyboardButton(text="🔐 Login Account", callback_data="login_account"),
            InlineKeyboardButton(text="🏠 Main Info", callback_data="back_main")
        ]
    ])

    await safe_edit_message(callback, text, help_keyboard)
    await callback.answer()

# cb_create_account moved to account_creation.py

# ========== ACCOUNT VERIFICATION DECORATOR ==========
def require_account(handler):
    """Decorator to check if account is created before allowing access"""
    async def wrapper(callback: CallbackQuery):
        if not callback.from_user:
            return

        user_id = callback.from_user.id

        # If account not created, show message
        if not is_account_created(user_id):
            text = """
⚠️ <b>Account Required</b>

Your account has not been created yet!

📝 <b>Create an account first to access all features</b>

✅ <b>Account creation takes only 2 minutes</b>
"""

            if callback.message and hasattr(callback.message, 'edit_text'):
                await safe_edit_message(callback, text, account_creation.get_account_creation_menu())
            await callback.answer()
            return

        # Account exists, proceed with handler
        return await handler(callback)

    return wrapper

# Initialize all handlers after bot and dp are created
# This ensures dp is not None when handlers are registered

# Import account menu function
get_account_menu = account_handlers.get_account_menu

# ========== NAME CHOICE HANDLERS (MOVED TO account_creation.py) ==========

# cb_use_custom_name moved to account_creation.py

# ========== PHONE CHOICE HANDLERS (MOVED TO account_creation.py) ==========

# cb_manual_phone_entry moved to account_creation.py

# ========== CALLBACK HANDLERS ==========
@dp.callback_query(F.data == "new_order")
@require_account
async def cb_new_order(callback: CallbackQuery):
    """Handle new order - show service platforms"""
    if not callback.message:
        return

    from services import get_services_main_menu

    text = """
🚀 <b>New Order Portal</b>

Welcome! Here you can order powerful growth services for your social media accounts.

Our system guarantees:

<b>Choice & Variety:</b> Packages of different qualities (from Economy to VIP) to suit every budget and need.

<b>Transparency:</b> Full details on each package's speed, quality, and guarantee will be clearly provided at the time of selection.

<b>Security:</b> All payments and transactions are 100% safe and secure.

💡 <b>Let's get started. Please choose your platform below:</b>
"""

    # Ensure this line has the same indentation as the 'text =' line above
    await safe_edit_message(callback, text, get_services_main_menu())
    await callback.answer()

# Service handlers moved to services.py

@dp.callback_query(F.data == "add_funds")
@require_account
async def cb_add_funds(callback: CallbackQuery):
    """Handle add funds request with professional design"""
    if not callback.message:
        return

    user_id = callback.from_user.id if callback.from_user else 0
    current_balance = users_data.get(user_id, {}).get("balance", 0.0)

    text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 💎 <b>PREMIUM WALLET RECHARGE PORTAL</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>Instant Balance Top-Up Service</b>
<i>Secure • Fast • Reliable</i>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 💰 <b>CURRENT WALLET STATUS</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • 💳 <b>Available Balance:</b> <u>{format_currency(current_balance)}</u>
┃ • 🎯 <b>Account Status:</b> ✅ <b>Active & Verified</b>
┃ • 💎 <b>Membership:</b> Premium User
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 <b>PAYMENT METHODS AVAILABLE</b>

🎯 <b>Instant Payment Options:</b>
┌─────────────────────────────────────┐
│ 📱 <b>UPI Payment</b> - ⚡ Instant Credit    │
│ 🏦 <b>Bank Transfer</b> - 💯 Secure Process │
│ 💙 <b>Paytm Wallet</b> - 🚀 Quick Transfer  │
│ 🟢 <b>PhonePe</b> - ⭐ Most Popular        │
│ 🔴 <b>Google Pay</b> - 🎊 Fastest Option   │
│ 💳 <b>All UPI Apps</b> - 🏆 100% Support   │
└─────────────────────────────────────┘

✨ <b>SPECIAL FEATURES:</b>
• 🔒 <b>Bank-Grade Security</b> - SSL Encrypted
• ⚡ <b>Instant Processing</b> - Real-time Credit
• 💯 <b>100% Success Rate</b> - Guaranteed
• 🎁 <b>Bonus Rewards</b> - Extra Benefits

💎 <b>Select your preferred recharge amount below:</b>

🎯 <b>Popular choices for maximum value!</b>
"""

    amount_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 ₹500 Recharge", callback_data="fund_500"),
            InlineKeyboardButton(text="💎 ₹1000 Top-Up", callback_data="fund_1000")
        ],
        [
            InlineKeyboardButton(text="🚀 ₹2000 Power Pack", callback_data="fund_2000"),
            InlineKeyboardButton(text="👑 ₹5000 Premium", callback_data="fund_5000")
        ],
        [
            InlineKeyboardButton(text="✨ Custom Amount Entry", callback_data="fund_custom")
        ],
        [
            InlineKeyboardButton(text="📊 Payment History", callback_data="payment_history"),
            InlineKeyboardButton(text="🎁 Bonus Offers", callback_data="bonus_offers")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Dashboard", callback_data="back_main")
        ]
    ])

    await safe_edit_message(callback, text, amount_keyboard)
    await callback.answer("💎 Premium recharge portal loaded!")


@dp.callback_query(F.data == "services_tools")
@require_account
async def cb_services_tools(callback: CallbackQuery):
    """Handle services & tools menu"""
    if not callback.message:
        return

    text = """
⚙️ <b>Services & Tools</b>

🚀 <b>Advanced SMM Tools & Features</b>

💎 <b>Professional Tools:</b>
• Bulk order management
• Auto-renewal subscriptions
• Analytics & insights
• Content optimization

🎯 <b>Smart Features:</b>
• AI-powered recommendations
• Performance tracking
• Growth strategies
• Market analysis

💡 <b> Choose tools according to your needs:</b>
"""

    await safe_edit_message(callback, text, get_services_tools_menu())
    await callback.answer()

@dp.callback_query(F.data == "offers_rewards")
@require_account
async def cb_offers_rewards(callback: CallbackQuery):
    """Handle offers & rewards menu"""
    if not callback.message:
        return

    text = """
🎁 <b>Offers & Rewards</b>

🌟 <b>Exciting Rewards & Benefits Await!</b>

💰 <b>Earn More, Save More:</b>
• Daily login rewards
• Loyalty points system
• Exclusive discounts
• Partner benefits

🏆 <b>Community Features:</b>
• Leaderboard competitions
• Community voting
• Special achievements
• VIP status rewards

🎉 <b>Limited Time Offers:</b>
• Festival bonuses
• Referral contests
• Bulk order discounts
• Premium memberships

✨ <b> Claim your reward:</b>
"""

    await safe_edit_message(callback, text, get_offers_rewards_menu())
    await callback.answer()

@dp.callback_query(F.data == "admin_panel")
async def cb_admin_panel(callback: CallbackQuery):
    """Handle admin panel access - redirect to services.py admin panel"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    if not is_admin(user_id):
        text = """
⚠️ <b>Access Denied</b>

This section is only for authorized administrators.

🔒 <b>Security Notice:</b>
Unauthorized access attempts are logged and monitored.

📞 If you are an administrator, please contact the owner.
"""
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")]
        ])

        await safe_edit_message(callback, text, back_keyboard)
    else:
        # Import admin menu from services.py
        from services import get_admin_main_menu, get_bot_status_info

        # Show proper admin panel with all buttons
        text = """
👑 <b>India Social Panel - Admin Control Center</b>

🎯 <b>Welcome Admin!</b> Choose your action below:

🚀 <b>Full administrative access granted</b>
📊 <b>All systems operational</b>
"""

        admin_menu = get_admin_main_menu()
        await safe_edit_message(callback, text, admin_menu)

    await callback.answer()

@dp.callback_query(F.data == "contact_about")
async def cb_contact_about(callback: CallbackQuery):
    """Handle contact & about section"""
    if not callback.message:
        return

    text = """
📞 <b>Contact & About</b>

🇮🇳 <b>India Social Panel</b>
India's Most Trusted SMM Platform

🎯 <b>Our Mission:</b>
Providing high-quality, affordable social media marketing services

✨ <b>Why Choose Us:</b>
• ✅ 100% Real & Active Users
• ⚡️ Instant Start Guarantee
• 🔒 Safe & Secure Services
• 💬 24/7 Customer Support
• 💰 Best Prices in Market

📈 <b>Services:</b> 500+ Premium SMM Services
🌍 <b>Serving:</b> Worldwide (India Focus)
"""

    await safe_edit_message(callback, text, get_contact_menu())
    await callback.answer()

@dp.callback_query(F.data == "owner_info")
async def cb_owner_info(callback: CallbackQuery):
    """Show owner information"""
    if not callback.message:
        return

    text = f"""
👨‍💻 <b>Owner Information</b>

🙏 <b>Hello! I am {OWNER_NAME}</b>
Founder & CEO, India Social Panel

📍 <b>Location:</b> India 🇮🇳
💼 <b>Experience:</b> 5+ Years in SMM Industry
🎯 <b>Mission:</b> Providing affordable digital marketing solutions to Indian businesses

✨ <b>My Vision:</b>
"Making every Indian business successful on social media"

💬 <b>Personal Message:</b>
"My goal is to provide high-quality and affordable SMM services to all of you. Your support and trust are my greatest achievements."

📞 <b>Contact:</b> @{OWNER_USERNAME}
🌟 <b>Thank you for choosing us!</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data="contact_about")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

# ========== NEW MISSING CALLBACK HANDLERS ==========
# Removed cb_category_select and cb_service_select as they are now in services.py

# Amount handlers moved to payment_system.py


@dp.callback_query(F.data == "service_list")
@require_account
async def cb_service_list(callback: CallbackQuery):
    """Show service list"""
    if not callback.message:
        return

    text = """
📈 <b>Service List</b>

<b>Choose platform to view pricing:</b>

💎 <b>High Quality Services</b>
⚡️ <b>Instant Start</b>
🔒 <b>100% Safe & Secure</b>
"""

    await safe_edit_message(callback, text, get_category_menu())
    await callback.answer()

@dp.callback_query(F.data == "support_tickets")
@require_account
async def cb_support_tickets(callback: CallbackQuery):
    """Show support tickets menu"""
    if not callback.message:
        return

    text = """
🎫 <b>Support Tickets</b>

💬 <b>Customer Support System</b>

🔸 <b>24/7 Available</b>
🔸 <b>Quick Response</b>
🔸 <b>Professional Help</b>

💡 <b>What would you like to do?</b>
"""

    await safe_edit_message(callback, text, get_support_menu())
    await callback.answer()

@dp.callback_query(F.data == "back_main")
async def cb_back_main(callback: CallbackQuery):
    """Return to main menu"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    first_name = callback.from_user.first_name or "Friend"

    text = f"""
🚀 <b>Welcome Back to the Main Menu!</b>

Hello, <b>{first_name}</b>! You are now back on your main dashboard, where you can access all your tools and services.

🇮🇳 <b>India Social Panel - Your Growth Partner</b>
💎 <b>Premium SMM Services at Your Fingertips</b>

🎯 <b>Ready to boost your social media presence?</b>
💡 <b>Choose from the options below to get started:</b>

✨ <b>Everything you need for social media success is right here!</b>
"""

    await safe_edit_message(callback, text, get_main_menu())
    await callback.answer()

@dp.callback_query(F.data == "skip_coupon")
async def cb_skip_coupon(callback: CallbackQuery, state: FSMContext):
    """Handle skip coupon and show confirmation"""
    if not callback.message or not callback.from_user:
        return

    # Get FSM data - check current state
    current_state = await state.get_state()
    if current_state != OrderStates.waiting_coupon.state:
        await callback.answer("⚠️ Order data not found!")
        return

    # Get all order details from FSM
    data = await state.get_data()
    package_name = data.get("package_name", "Unknown Package")
    service_id = data.get("service_id", "")
    platform = data.get("platform", "")
    package_rate = data.get("package_rate", "₹1.00 per unit")
    link = data.get("link", "")
    quantity = data.get("quantity", 0)

    # Calculate total price (simplified calculation for demo)
    # Extract numeric part from rate for calculation
    rate_num = 1.0  # Default
    if "₹" in package_rate:
        try:
            rate_str = package_rate.replace("₹", "").split()[0]
            rate_num = float(rate_str)
        except (ValueError, IndexError):
            rate_num = 1.0

    total_price = (rate_num / 1000) * quantity

    # Show enhanced confirmation page with professional design
    confirmation_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ ✅ <b>FINAL ORDER CONFIRMATION</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>Please review your order details carefully before proceeding.</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 📦 <b>PACKAGE INFORMATION</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • <b>Service Name:</b> {package_name}
┃ • <b>Service ID:</b> <code>{service_id}</code>
┃ • <b>Platform:</b> {platform.title()}
┃ • <b>Pricing Rate:</b> {package_rate}
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 🔗 <b>TARGET DESTINATION</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <code>{link}</code>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 📊 <b>ORDER SUMMARY</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • <b>Quantity Ordered:</b> <code>{quantity:,}</code> units
┃ • <b>Total Investment:</b> <b>₹{total_price:,.2f}</b>
┃ • <b>Service Guarantee:</b> ✅ <b>100% Delivery</b>
┃ • <b>Quality Assurance:</b> ✅ <b>Premium Service</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 <b>Pro Tip:</b> Use <code>/description</code> for detailed package information

🔥 <b>Ready to boost your social media presence?</b>

<b>✨ Next Steps:</b>
• <b>Confirm Order</b> → Choose payment method & complete purchase
• <b>Cancel Order</b> → Return to main menu without any charges

⚡ <b>Your social media growth journey starts with one click!</b>
"""

    # Store total price in FSM data (keep state for final confirmation)
    await state.update_data(total_price=total_price)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm Order", callback_data="final_confirm_order"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="back_main")
        ]
    ])

    await safe_edit_message(callback, confirmation_text, keyboard)
    await callback.answer()

@dp.callback_query(F.data == "final_confirm_order")
async def cb_final_confirm_order(callback: CallbackQuery, state: FSMContext):
    """Handle final order confirmation with balance check and payment options"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Get order details from FSM state
    order_data = await state.get_data()
    if not order_data or not order_data.get("service_id"):
        await callback.answer("⚠️ Order data not found in FSM! Please start over.", show_alert=True)
        await state.clear()
        return
    package_name = order_data.get("package_name", "Unknown Package")
    service_id = order_data.get("service_id", "")
    link = order_data.get("link", "")
    quantity = order_data.get("quantity", 0)
    total_price = order_data.get("total_price", 0.0)
    platform = order_data.get("platform", "")

    # Get user's current balance
    current_balance = users_data.get(user_id, {}).get("balance", 0.0)

    from datetime import datetime
    current_date = datetime.now().strftime("%d %b %Y, %I:%M %p")

    # Check if user has sufficient balance
    if current_balance >= total_price:
        # User has sufficient balance - show normal payment methods
        payment_text = f"""
💳 <b>Payment Method Selection</b>

📅 <b>Date:</b> {current_date}
📦 <b>Package:</b> {package_name}
🔗 <b>Link:</b> {link}
📊 <b>Quantity:</b> {quantity:,}
💰 <b>Total Amount:</b> ₹{total_price:,.2f}
💰 <b>Current Balance:</b> ✅ ₹{current_balance:,.2f}

💳 <b>Available Payment Methods:</b>

💡 <b>Choose your payment method:</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Pay from Balance", callback_data="pay_from_balance"),
                InlineKeyboardButton(text="📱 UPI Payment", callback_data="payment_upi")
            ],
            [
                InlineKeyboardButton(text="📊 Generate QR Now", callback_data="instant_qr_generate"),
                InlineKeyboardButton(text="📲 Open UPI App", callback_data="payment_app")
            ],
            [
                InlineKeyboardButton(text="🏦 Bank Transfer", callback_data="payment_bank"),
                InlineKeyboardButton(text="💳 Card Payment", callback_data="payment_card")
            ],
            [
                InlineKeyboardButton(text="💸 Digital Wallets", callback_data="payment_wallet"),
                InlineKeyboardButton(text="📞 Contact Support", url="https://t.me/tech_support_admin")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back", callback_data="skip_coupon")
            ]
        ])

        # Set FSM state for payment selection and keep order data
        await state.set_state(OrderStates.selecting_payment)
        await safe_edit_message(callback, payment_text, keyboard)

    else:
        # User has insufficient balance - show enhanced professional message with options
        shortfall = total_price - current_balance

        balance_message = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 💳 <b>ACCOUNT BALANCE VERIFICATION</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ <b>Payment verification completed! Here's your financial overview:</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 📋 <b>ORDER BREAKDOWN</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • <b>Selected Package:</b> {package_name}
┃ • <b>Target Platform:</b> {platform.title()}
┃ • <b>Quantity Ordered:</b> <code>{quantity:,}</code> units
┃ • <b>Total Investment:</b> <b>₹{total_price:,.2f}</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 💰 <b>FINANCIAL SUMMARY</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • <b>Current Account Balance:</b> ₹{current_balance:,.2f}
┃ • <b>Required Amount:</b> ₹{total_price:,.2f}
┃ • <b>Additional Funding Needed:</b> <b>₹{shortfall:,.2f}</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>FLEXIBLE PAYMENT SOLUTIONS</b>

💎 <b>OPTION 1: Smart Balance Management</b>
┌─────────────────────────────────────┐
│ ✅ Add funds to your account first     │
│ ⚡ Enjoy instant order processing      │
│ 🎁 Perfect for frequent users         │
│ 💡 Most convenient & recommended       │
└─────────────────────────────────────┘

⚡ <b>OPTION 2: Express Direct Payment</b>
┌─────────────────────────────────────┐
│ 🚀 Skip balance, pay directly now     │
│ ⏰ Ideal for urgent/one-time orders   │
│ 💳 Multiple payment methods available │
│ 🔥 Perfect for immediate processing   │
└─────────────────────────────────────┘

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 🔒 <b>SECURITY & TRUST GUARANTEE</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ ✅ <b>100% Secure Payment Gateway</b>
┃ ✅ <b>Instant Order Processing</b>
┃ ✅ <b>24/7 Professional Support</b>
┃ ✅ <b>Money-Back Guarantee</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 <b>Choose your preferred payment approach below:</b>
"""

        balance_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Add Balance First", callback_data="add_balance_first"),
                InlineKeyboardButton(text="⚡️ Direct Payment Now", callback_data="direct_payment_emergency")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Order", callback_data="skip_coupon")
            ]
        ])

        # Keep FSM state and data for when user returns after adding funds
        await safe_edit_message(callback, balance_message, balance_keyboard)

    await callback.answer()



@dp.callback_query(F.data == "share_screenshot")
async def cb_share_screenshot(callback: CallbackQuery):
    """Handle screenshot sharing request"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    screenshot_text = """
📸 <b>Screenshot Upload</b>

💡 <b>Please send the payment screenshot</b>

📋 <b>Screenshot Requirements:</b>
• Should be clear and readable
• Payment amount should be visible
• Transaction status should be "Success"
• Date and time should be visible

💬 <b>Send the screenshot as an image...</b>
"""

    user_state[user_id]["current_step"] = "waiting_screenshot_upload"

    await safe_edit_message(callback, screenshot_text)
    await callback.answer()

@dp.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    """Handle main_menu callback - same as back_main"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    first_name = callback.from_user.first_name or "Friend"

    text = f"""
🚀 <b>Welcome Back to the Main Menu!</b>

Hello, <b>{first_name}</b>! You are now back on your main dashboard, where you can access all your tools and services.

🇮🇳 <b>India Social Panel - Your Growth Partner</b>
💎 <b>Premium SMM Services at Your Fingertips</b>

🎯 <b>Ready to boost your social media presence?</b>
💡 <b>Choose from the options below to get started:</b>

✨ <b>Everything you need for social media success is right here!</b>
"""

    await safe_edit_message(callback, text, get_main_menu())
    await callback.answer()

@dp.callback_query(F.data.startswith("copy_order_id_"))
async def cb_copy_order_id(callback: CallbackQuery):
    """Handle copy order ID functionality"""
    if not callback.message or not callback.data:
        return

    # Extract order ID from callback data
    order_id = callback.data.replace("copy_order_id_", "")

    copy_text = f"""
📋 <b>Order ID Copied!</b>

🆔 <b>Your Order ID:</b>
<code>{order_id}</code>

💡 <b>Copy Instructions:</b>
• <b>Mobile:</b> Long press on Order ID above → Copy
• <b>Desktop:</b> Triple click to select → Ctrl+C

📝 <b>Save this Order ID for:</b>
• Order tracking and status check
• Reference for customer support
• Future inquiries and complaints
• Order delivery confirmation

🎯 <b>Order Tracking:</b>
You can track your order with this ID by going to Order History.

📞 <b>Support:</b>
If you have any problems, contact support with this Order ID.

💡 <b>Important:</b> This Order ID is unique and only for your order.
"""

    copy_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📜 Order History", callback_data="order_history"),
            InlineKeyboardButton(text="📞 Contact Support", url="https://t.me/tech_support_admin")
        ],
        [
            InlineKeyboardButton(text="🚀 Place New Order", callback_data="new_order"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await safe_edit_message(callback, copy_text, copy_keyboard)
    await callback.answer(f"📋 Order ID copied: {order_id}", show_alert=True)

@dp.callback_query(F.data == "add_balance_first")
async def cb_add_balance_first(callback: CallbackQuery):
    """Handle add balance first option - redirect to add funds"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    current_balance = users_data.get(user_id, {}).get("balance", 0.0)

    # Get order amount for reference
    order_data = user_state.get(user_id, {}).get("data", {})
    total_price = order_data.get("total_price", 0.0)
    shortfall = total_price - current_balance if total_price > current_balance else 0

    text = f"""
💰 <b>Add Balance to Account</b>

💳 <b>Current Balance:</b> ₹{current_balance:,.2f}
💸 <b>Required for Order:</b> ₹{total_price:,.2f}
⚡️ <b>Minimum to Add:</b> ₹{shortfall:,.2f}

🎯 <b>Recommended Amounts:</b>
• ₹{max(500, shortfall):,.0f} (Minimum for order)
• ₹{max(1000, shortfall + 500):,.0f} (Order + Extra balance)
• ₹{max(2000, shortfall + 1500):,.0f} (For future orders)

💡 <b>Choose amount or type custom amount:</b>

🔥 <b>Benefits of Adding Balance:</b>
• ⚡️ Instant order processing
• 💰 No payment hassle every time
• 🎁 Exclusive member benefits
• 🚀 Faster checkout process
"""

    # Create dynamic amount buttons based on shortfall
    amount_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"₹{max(500, shortfall):,.0f}", callback_data=f"fund_{max(500, shortfall):,.0f}".replace(",", "")),
            InlineKeyboardButton(text=f"₹{max(1000, shortfall + 500):,.0f}", callback_data=f"fund_{max(1000, shortfall + 500):,.0f}".replace(",", ""))
        ],
        [
            InlineKeyboardButton(text=f"₹{max(2000, shortfall + 1500):,.0f}", callback_data=f"fund_{max(2000, shortfall + 1500):,.0f}".replace(",", "")),
            InlineKeyboardButton(text="₹5000", callback_data="fund_5000")
        ],
        [
            InlineKeyboardButton(text="💬 Custom Amount", callback_data="fund_custom")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Order", callback_data="final_confirm_order")
        ]
    ])

    await safe_edit_message(callback, text, amount_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "direct_payment_emergency")
async def cb_direct_payment_emergency(callback: CallbackQuery, state: FSMContext):
    """Handle direct payment option - show payment methods directly"""
    if not callback.message or not callback.from_user:
        return

    try:
        user_id = callback.from_user.id
        order_data = await state.get_data()

        if not order_data or not order_data.get("service_id"):
            await callback.answer("⚠️ Order data could not be found. Please start a new order.", show_alert=True)
            await state.clear()
            return

        package_name = order_data.get("package_name", "Unknown Package")
        link = order_data.get("link", "")
        quantity = order_data.get("quantity", 0)
        total_price = order_data.get("total_price", 0.0)
        platform = order_data.get("platform", "")

        from datetime import datetime
        current_date = datetime.now().strftime("%d %b %Y, %I:%M %p")

        emergency_payment_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ ⚡️ <b>QUICK PAYMENT PORTAL</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>Express Order Processing</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 📋 <b>ORDER SUMMARY</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • 📦 <b>Service:</b> {package_name}
┃ • 🌐 <b>Platform:</b> {platform.title()}
┃ • 📊 <b>Quantity:</b> {quantity:,} units
┃ • 💰 <b>Investment:</b> <b>₹{total_price:,.2f}</b>
┃ • 📅 <b>Date:</b> {current_date}
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 <b>SECURE PAYMENT OPTIONS</b>

🎯 <b>Choose your preferred payment method for instant processing:</b>

✨ <b>All methods are 100% secure and encrypted</b>
⚡ <b>Your order will be processed immediately after payment</b>
🔒 <b>Bank-grade security protocols ensure complete safety</b>

💡 <b>Select the most convenient option below:</b>
"""

        emergency_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 UPI Payment", callback_data="payment_upi"),
                InlineKeyboardButton(text="📊 Generate QR Now", callback_data="instant_qr_generate")
            ],
            [
                InlineKeyboardButton(text="💳 More Methods", callback_data="payment_bank"),
                InlineKeyboardButton(text="🏦 Bank Transfer", callback_data="payment_bank")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Options", callback_data="final_confirm_order")
            ]
        ])

        await state.set_state(OrderStates.selecting_payment)
        await safe_edit_message(callback, emergency_payment_text, emergency_keyboard)

    except Exception as e:
        print(f"CRITICAL ERROR in cb_direct_payment_emergency: {e}")
        await callback.answer("An error occurred. Please try again.", show_alert=True)

    await callback.answer()

@dp.callback_query(F.data == "pay_from_balance")
async def cb_pay_from_balance(callback: CallbackQuery, state: FSMContext):
    """Handle payment from account balance"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Check if user has order data in FSM
    current_state = await state.get_state()
    if current_state != OrderStates.selecting_payment.state:
        await callback.answer("⚠️ Order session expired! Please start over.", show_alert=True)
        await state.clear()
        return

    # Get order details from FSM
    order_data = await state.get_data()
    if not order_data.get("service_id"):
        await callback.answer("⚠️ Order data not found! Please start over.", show_alert=True)
        await state.clear()
        return
    package_name = order_data.get("package_name", "Unknown Package")
    service_id = order_data.get("service_id", "")
    link = order_data.get("link", "")
    quantity = order_data.get("quantity", 0)
    total_price = order_data.get("total_price", 0.0)
    platform = order_data.get("platform", "")

    # Get user's current balance
    current_balance = users_data.get(user_id, {}).get("balance", 0.0)

    # Double check balance
    if current_balance < total_price:
        await callback.answer("⚠️ Insufficient balance!", show_alert=True)
        return

    # Process order from balance
    order_id = generate_order_id()

    # Deduct balance
    users_data[user_id]['balance'] -= total_price
    users_data[user_id]['total_spent'] += total_price
    users_data[user_id]['orders_count'] += 1

    # Create order record
    order_record = {
        'order_id': order_id,
        'user_id': user_id,
        'package_name': package_name,
        'service_id': service_id,
        'platform': platform,
        'link': link,
        'quantity': quantity,
        'total_price': total_price,
        'status': 'processing',
        'created_at': datetime.now().isoformat(),
        'payment_method': 'Account Balance',
        'payment_status': 'completed'
    }

    # Store order in permanent storage
    orders_data[order_id] = order_record

    # Save updated data to persistent storage
    save_data_to_json(users_data, "users.json")
    save_data_to_json(orders_data, "orders.json")

    print(f"✅ Order {order_id} completed and stored")

    # Clear FSM state as order is complete
    await state.clear()

    # Success message with improved format
    new_balance = users_data[user_id]['balance']

    success_text = f"""
🎉 <b>Order Successfully Placed!</b>

✅ <b>Payment Successful from Account Balance!</b>

📦 <b>Order Confirmation Details:</b>
• 🆔 <b>Order ID:</b> <code>{order_id}</code>
• 📦 <b>Package:</b> {package_name}
• 📱 <b>Platform:</b> {platform.title()}
• 🔢 <b>Quantity:</b> {quantity:,}
• 💰 <b>Amount:</b> ₹{total_price:,.2f}
• 💳 <b>Payment:</b> Account Balance ✅
• 📅 <b>Date:</b> {datetime.now().strftime("%d %b %Y, %I:%M %p")}

💰 <b>Balance Update:</b>
• 💳 <b>Previous Balance:</b> ₹{current_balance:,.2f}
• 💸 <b>Amount Deducted:</b> ₹{total_price:,.2f}
• 💰 <b>Current Balance:</b> ₹{new_balance:,.2f}

📋 <b>Order Status:</b> ⏳ Processing Started
🔄 <b>Payment Status:</b> ✅ Completed

⏰ <b>Delivery Timeline:</b>
Your order is now being processed. Delivery will be completed according to the package description.

💡 <b>Save and keep the Order ID - it's essential for tracking!</b>

✨ <b>Thank you for choosing India Social Panel!</b>
"""

    success_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Copy Order ID", callback_data=f"copy_order_id_{order_id}"),
            InlineKeyboardButton(text="📜 Order History", callback_data="order_history")
        ],
        [
            InlineKeyboardButton(text="🚀 Place New Order", callback_data="new_order"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await safe_edit_message(callback, success_text, success_keyboard)
    await callback.answer("✅ Order placed successfully!")

# ========== WALLET SPECIFIC HANDLERS ==========
@dp.callback_query(F.data.startswith("wallet_") and F.data.endswith("_order"))
async def cb_wallet_specific_order(callback: CallbackQuery):
    """Handle specific wallet payment for order"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    if not callback.data:
        await callback.answer("❌ Invalid wallet selection!", show_alert=True)
        return
    wallet_name = callback.data.replace("wallet_", "").replace("_order", "")

    # Get order details
    order_data = user_state.get(user_id, {}).get("data", {})
    total_price = order_data.get("total_price", 0.0)

    # Wallet information
    wallet_info = {
        "paytm": ("💙 Paytm", "paytm@indiasmm", "Most popular wallet in India"),
        "phonepe": ("🟢 PhonePe", "phonepe@indiasmm", "UPI + Wallet integrated"),
        "gpay": ("🔴 Google Pay", "gpay@indiasmm", "Fastest transfer guaranteed"),
        "amazon": ("🟡 Amazon Pay", "amazonpay@indiasmm", "Instant refund policy"),
        "jio": ("🔵 JioMoney", "jio@indiasmm", "Jio network optimized"),
        "freecharge": ("🟠 FreeCharge", "freecharge@indiasmm", "Quick mobile recharge")
    }

    if wallet_name in wallet_info:
        name, upi_id, description = wallet_info[wallet_name]

        text = f"""
{name} <b>Payment</b>

💰 <b>Amount:</b> ₹{total_price:,.2f}
✨ <b>{description}</b>

💳 <b>Payment Details:</b>
• 🆔 <b>UPI ID:</b> <code>{upi_id}</code>
• 👤 <b>Name:</b> India Social Panel
• 💰 <b>Amount:</b> ₹{total_price:,.2f}

📱 <b>Payment Steps:</b>
1. Open {name} app
2. Select "Send Money" या "Pay"
3. Enter UPI ID: <code>{upi_id}</code>
4. Enter amount: ₹{total_price:,.2f}
5. Complete payment with PIN/Password

⚡️ <b>Payment के बाद screenshot भेजना जरूरी है!</b>

💡 <b>Most users prefer {name} for reliability!</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Copy UPI ID", callback_data=f"copy_wallet_upi_{wallet_name}"),
                InlineKeyboardButton(text="📸 Send Screenshot", callback_data="wallet_screenshot")
            ],
            [
                InlineKeyboardButton(text="💡 Payment Guide", callback_data=f"wallet_guide_{wallet_name}"),
                InlineKeyboardButton(text="⬅️ Back", callback_data="payment_wallet")
            ]
        ])

        user_state[user_id]["current_step"] = "waiting_wallet_screenshot"
        user_state[user_id]["data"]["selected_wallet"] = wallet_name

        await safe_edit_message(callback, text, keyboard)
        await callback.answer()

# ========== NET BANKING HANDLERS ==========
@dp.callback_query(F.data.startswith("netbank_"))
async def cb_netbank_specific(callback: CallbackQuery):
    """Handle specific bank net banking"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    bank_code = callback.data.replace("netbank_", "")

    # Get order details
    order_data = user_state.get(user_id, {}).get("data", {})
    total_price = order_data.get("total_price", 0.0)

    # Bank information
    bank_info = {
        "sbi": ("State Bank of India", "SBIN0001234", "India's largest bank"),
        "hdfc": ("HDFC Bank", "HDFC0001234", "Leading private bank"),
        "icici": ("ICICI Bank", "ICIC0001234", "Digital banking leader"),
        "axis": ("Axis Bank", "UTIB0001234", "Modern banking solutions"),
        "pnb": ("Punjab National Bank", "PUNB0001234", "Trusted public bank"),
        "others": ("Other Banks", "XXXX0001234", "All major banks supported")
    }

    if bank_code in bank_info:
        bank_name, ifsc_sample, description = bank_info[bank_code]

        text = f"""
🏦 <b>{bank_name} Net Banking</b>

💰 <b>Amount:</b> ₹{total_price:,.2f}
🏛️ <b>{description}</b>

💳 <b>Net Banking Process:</b>
1. आपको bank का secure login page दिखेगा
2. अपना User ID और Password enter करें
3. Transaction password/MPIN डालें
4. Payment authorize करें
5. Success message का screenshot लें

🔒 <b>Security Features:</b>
• 256-bit SSL encryption
• Direct bank connection
• No middleman involved
• Instant payment confirmation

⚠️ <b>Important:</b>
• Net banking login ready रखें
• Transaction limit check करें
• Payment timeout: 15 minutes

🚀 <b>Ready to proceed with {bank_name}?</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Proceed to Bank", callback_data=f"proceed_netbank_{bank_code}"),
                InlineKeyboardButton(text="💡 Help", callback_data=f"netbank_help_{bank_code}")
            ],
            [
                InlineKeyboardButton(text="⬅️ Choose Different Bank", callback_data="payment_netbanking")
            ]
        ])

        await safe_edit_message(callback, text, keyboard)
        await callback.answer()

# ========== COPY AND SCREENSHOT HANDLERS ==========
@dp.callback_query(F.data.startswith("copy_wallet_upi_"))
async def cb_copy_wallet_upi(callback: CallbackQuery):
    """Handle wallet UPI ID copy"""
    if not callback.message:
        return

    wallet_name = callback.data.replace("copy_wallet_upi_", "")
    wallet_upis = {
        "paytm": "paytm@indiasmm",
        "phonepe": "phonepe@indiasmm",
        "gpay": "gpay@indiasmm",
        "amazon": "amazonpay@indiasmm",
        "jio": "jio@indiasmm",
        "freecharge": "freecharge@indiasmm"
    }

    upi_id = wallet_upis.get(wallet_name, "contact@indiasmm")
    await callback.answer(f"✅ UPI ID copied: {upi_id}", show_alert=True)

@dp.callback_query(F.data == "copy_bank_details_order")
async def cb_copy_bank_details_order(callback: CallbackQuery):
    """Handle bank details copy for order"""
    if not callback.message:
        return

    text = """
📋 <b>Bank Details Copied!</b>

🏦 <b>Complete Bank Information:</b>

• 🏛️ <b>Bank:</b> State Bank of India
• 🔢 <b>Account No:</b> <code>12345678901234</code>
• 🔑 <b>IFSC Code:</b> <code>SBIN0001234</code>
• 👤 <b>Name:</b> India Social Panel

📝 <b>Next Steps:</b>
1. Copy above details carefully
2. Open your banking app
3. Add new beneficiary
4. Transfer the amount
5. Send transaction screenshot

✅ <b>Bank details ready to use!</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Send Screenshot", callback_data="bank_transfer_screenshot")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="payment_bank")]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer("✅ Bank details copied!")

@dp.callback_query(F.data == "bank_transfer_screenshot")
async def cb_bank_transfer_screenshot(callback: CallbackQuery):
    """Handle bank transfer screenshot request"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_state[user_id]["current_step"] = "waiting_bank_screenshot"

    text = """
📸 <b>Bank Transfer Screenshot</b>

💡 <b>कृपया bank transfer का screenshot भेजें</b>

📋 <b>Screenshot में ये दिखना चाहिए:</b>
• ✅ Transfer successful message
• 💰 Transfer amount
• 🆔 Transaction reference number
• 📅 Date और time
• 🏦 Beneficiary name (India Social Panel)

💬 <b>Send the screenshot as an image...</b>

⏰ <b>Screenshot verify होने के बाद order process हो जाएगा</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer()

@dp.callback_query(F.data.startswith("proceed_netbank_"))
async def cb_proceed_netbank(callback: CallbackQuery):
    """Handle net banking proceed"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    bank_code = callback.data.replace("proceed_netbank_", "")

    # Get order details
    order_data = user_state.get(user_id, {}).get("data", {})
    total_price = order_data.get("total_price", 0.0)

    text = f"""
🚀 <b>Net Banking Payment Processing</b>

💰 <b>Amount:</b> ₹{total_price:,.2f}

🔄 <b>Redirecting to bank's secure portal...</b>

⏰ <b>Please wait while we prepare your payment link</b>

🔐 <b>Security Notice:</b>
• You'll be redirected to official bank website
• Enter your credentials only on bank's page
• Never share login details with anyone
• Payment will be processed securely

💡 <b>Net banking feature implementation in progress...</b>
📞 <b>For now, please use UPI/QR code method for instant payment</b>

🎯 <b>Alternative quick methods available:</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚡️ Quick QR Payment", callback_data="payment_qr"),
            InlineKeyboardButton(text="📱 UPI Payment", callback_data="payment_upi")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Net Banking", callback_data="payment_netbanking")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer("🔄 Net banking integration coming soon...")

@dp.callback_query(F.data == "payment_app")
async def cb_payment_app(callback: CallbackQuery):
    """Handle UPI app payment method"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Check if user has order data
    if user_id not in user_state:
        await callback.answer("⚠️ Order data not found!")
        return

    # Get order details
    order_data = user_state.get(user_id, {}).get("data", {})
    total_price = order_data.get("total_price", 0.0)

    text = f"""
📲 <b>UPI App Payment</b>

💰 <b>Amount:</b> ₹{total_price:,.2f}
🆔 <b>UPI ID:</b> <code>business@paytm</code>
👤 <b>Name:</b> India Social Panel

📱 <b>Popular UPI Apps:</b>

🔸 <b>Method 1: Copy UPI ID</b>
• UPI ID: <code>business@paytm</code>
• Manual transfer करें any UPI app में

🔸 <b>Method 2: UPI Apps Direct</b>
• Google Pay, PhonePe, Paytm
• JioMoney, Amazon Pay
• Any UPI enabled app

💡 <b>Payment Steps:</b>
1. Copy UPI ID: <code>business@paytm</code>
2. Open any UPI app
3. Send ₹{total_price:,.2f}
4. Complete payment with PIN
5. Take screenshot
6. Share screenshot यहाँ

✅ <b>Payment complete होने के बाद screenshot share करें!</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Copy UPI ID", callback_data="copy_upi_id"),
            InlineKeyboardButton(text="📱 Generate QR Code", callback_data="payment_qr")
        ],
        [
            InlineKeyboardButton(text="📸 Share Screenshot", callback_data="share_screenshot")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Payment", callback_data="direct_payment_emergency")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

@dp.callback_query(F.data == "copy_upi_id")
async def cb_copy_upi_id(callback: CallbackQuery):
    """Handle UPI ID copy"""
    if not callback.message:
        return

    await callback.answer("✅ UPI ID copied: business@paytm", show_alert=True)

@dp.callback_query(F.data == "instant_qr_generate")
async def cb_instant_qr_generate(callback: CallbackQuery, state: FSMContext):
    """Handle instant QR generation - direct shortcut to QR generation from UPI payment"""
    if not callback.message or not callback.from_user:
        return

    try:
        user_id = callback.from_user.id

        # Check if user has order data in FSM
        current_state = await state.get_state()
        if current_state != OrderStates.selecting_payment.state:
            await callback.answer("⚠️ Order session expired! Please start over.", show_alert=True)
            await state.clear()
            return

        # Get order details from FSM
        order_data = await state.get_data()
        if not order_data.get("service_id"):
            await callback.answer("⚠️ Order data not found! Please start over.", show_alert=True)
            await state.clear()
            return

        total_price = order_data.get("total_price", 0.0)

        # Generate transaction ID (same as UPI payment)
        import time
        import random
        transaction_id = f"QR{int(time.time())}{random.randint(100, 999)}"

        # Store transaction in FSM and keep order data
        await state.update_data(transaction_id=transaction_id, payment_method="instant_qr")

        await callback.answer("🔄 Generating instant QR code...")

        # Generate QR code using same function as UPI payment
        from payment_system import generate_payment_qr, PAYMENT_CONFIG
        qr_data = generate_payment_qr(
            total_price,
            PAYMENT_CONFIG['upi_id'],
            PAYMENT_CONFIG['upi_name'],
            transaction_id
        )

        # Prepare QR code message text
        qr_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ ⚡ <b>INSTANT QR PAYMENT PORTAL</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>Express QR Code Generated - Ready for Instant Payment!</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 💳 <b>PAYMENT DETAILS</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • 💰 <b>Payment Amount:</b> ₹{total_price:,.2f}
┃ • 📱 <b>UPI Merchant ID:</b> <code>{PAYMENT_CONFIG['upi_id']}</code>
┃ • 🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>
┃ • ⚡ <b>Method:</b> Instant QR Scan
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>LIGHTNING-FAST PAYMENT PROCESS:</b>

📋 <b>Quick Payment Steps:</b>
🔸 <b>Step 1:</b> Open any UPI-enabled app
🔸 <b>Step 2:</b> Scan the QR code above instantly
🔸 <b>Step 3:</b> Verify amount: ₹{total_price:,.2f}
🔸 <b>Step 4:</b> Complete with UPI PIN
🔸 <b>Step 5:</b> Click "Payment Completed" below

✨ <b>INSTANT QR ADVANTAGES:</b>
• 🚀 Zero navigation required
• ⚡ One-click payment processing
• 🔒 Maximum security protocols
• 💎 Immediate order activation

🎊 <b>Your instant payment gateway is ready!</b>
"""

        qr_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Payment Completed", callback_data=f"payment_completed_{transaction_id}"),
                InlineKeyboardButton(text="❌ Cancel Payment", callback_data="payment_cancel")
            ],
            [
                InlineKeyboardButton(text="🔄 Generate Fresh QR", callback_data="instant_qr_generate"),
                InlineKeyboardButton(text="💳 More Payment Options", callback_data="final_confirm_order")
            ]
        ])

        if qr_data:
            from aiogram.types import BufferedInputFile
            qr_file = BufferedInputFile(qr_data, filename="instant_payment_qr.png")
            await callback.message.answer_photo(
                photo=qr_file,
                caption=qr_text,
                reply_markup=qr_keyboard,
                parse_mode="HTML"
            )
        else:
            # Fallback if QR generation fails
            await safe_edit_message(callback, qr_text, qr_keyboard)

    except Exception as e:
        print(f"CRITICAL ERROR in cb_instant_qr_generate: {e}")
        await callback.answer("An error occurred. Please try again.", show_alert=True)

    await callback.answer()

@dp.callback_query(F.data == "payment_bank")
async def cb_payment_bank_method(callback: CallbackQuery):
    """Handle bank transfer payment method"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Check if user has order data
    if user_id not in user_state:
        await callback.answer("⚠️ Order data not found!")
        return

    # Get order details
    order_data = user_state.get(user_id, {}).get("data", {})
    total_price = order_data.get("total_price", 0.0)

    text = f"""
🏦 <b>Bank Transfer Payment</b>

💰 <b>Amount:</b> ₹{total_price:,.2f}

🏛️ <b>Bank Details:</b>
• 🏦 <b>Bank:</b> State Bank of India
• 🔢 <b>Account No:</b> <code>12345678901234</code>
• 🔑 <b>IFSC Code:</b> <code>SBIN0001234</code>
• 👤 <b>Account Name:</b> India Social Panel

📝 <b>Transfer Instructions:</b>
1. Open your banking app या net banking
2. Select "Fund Transfer" या "Send Money"
3. Add beneficiary with above details
4. Transfer exact amount ₹{total_price:,.2f}
5. Save transaction reference number
6. Send screenshot यहाँ

⏰ <b>Processing Time:</b>
• IMPS: Instant
• NEFT: 2-4 hours
• RTGS: 1-2 hours (₹2L+ के लिए)

💡 <b>Transfer के बाद screenshot भेजना जरूरी है!</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Copy Bank Details", callback_data="copy_bank_details_order"),
            InlineKeyboardButton(text="📸 Send Screenshot", callback_data="bank_transfer_screenshot")
        ],
        [
            InlineKeyboardButton(text="💡 Transfer Guide", callback_data="bank_transfer_guide"),
            InlineKeyboardButton(text="⬅️ Back", callback_data="final_confirm_order")
        ]
    ])

    user_state[user_id]["current_step"] = "waiting_bank_transfer"

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

# ========== ORDER CONFIRMATION HANDLERS ==========
@dp.callback_query(F.data == "confirm_order")
@require_account
async def cb_confirm_order(callback: CallbackQuery):
    """Confirm and process order"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Check if order data exists
    if user_id not in order_temp:
        await callback.answer("⚠️ Order data not found!")
        return

    order_data = order_temp[user_id]
    user_data = users_data.get(user_id, {})

    # Check balance
    balance = user_data.get('balance', 0.0)
    price = order_data['price']

    if balance < price:
        text = f"""
💳 <b>Insufficient Balance</b>

💰 <b>Required:</b> {format_currency(price)}
💰 <b>Available:</b> {format_currency(balance)}
💰 <b>Need to Add:</b> {format_currency(price - balance)}

💡 <b>Please add funds first!</b>
"""

        fund_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Add Funds", callback_data="add_funds")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
        ])

        await safe_edit_message(callback, text, fund_keyboard)
        await callback.answer()
        return

    # Process order
    order_id = generate_order_id()
    order_record = {
        'order_id': order_id,
        'user_id': user_id,
        'service': order_data['service'],
        'link': order_data['link'],
        'quantity': order_data['quantity'],
        'price': price,
        'status': 'processing',
        'created_at': datetime.now().isoformat(),
        'start_count': 0,
        'remains': order_data['quantity']
    }

    # Save order
    orders_data[order_id] = order_record

    # Update user data
    users_data[user_id]['balance'] -= price
    users_data[user_id]['total_spent'] += price
    users_data[user_id]['orders_count'] += 1

    # Save updated data to persistent storage
    save_data_to_json(users_data, "users.json")
    save_data_to_json(orders_data, "orders.json")

    # Clear temp order
    del order_temp[user_id]

    text = f"""
🎉 <b>Order Successfully Placed!</b>

🆔 <b>Order ID:</b> <code>{order_id}</code>
📱 <b>Service:</b> {order_data['service'].replace('_', ' ').title()}
🔢 <b>Quantity:</b> {order_data['quantity']:,}
💰 <b>Charged:</b> {format_currency(price)}
🔄 <b>Status:</b> Processing

✅ <b>Order का processing start हो गया!</b>
📅 <b>Delivery:</b> 0-6 hours

💡 <b>Order history में details check कर सकते हैं</b>
"""

    success_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Order History", callback_data="order_history")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")]
    ])

    await safe_edit_message(callback, text, success_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "cancel_order")
@require_account
async def cb_cancel_order(callback: CallbackQuery):
    """Cancel current order"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Clear temp order data
    if user_id in order_temp:
        del order_temp[user_id]

    text = """
❌ <b>Order Cancelled</b>

📋 <b>Order process cancelled successfully</b>

💡 <b>You can place a new order anytime!</b>
"""

    await safe_edit_message(callback, text, get_main_menu())
    await callback.answer()

# ========== SERVICES & TOOLS HANDLERS ==========
@dp.callback_query(F.data == "mass_order")
@require_account
async def cb_mass_order(callback: CallbackQuery):
    """Handle mass order feature"""
    if not callback.message:
        return

    text = """
📦 <b>Mass Order</b>

🚀 <b>Bulk Order Management System</b>

💎 <b>Features:</b>
• Multiple orders at once
• CSV file upload support
• Bulk pricing discounts
• Progress tracking

📋 <b>Supported Formats:</b>
• Multiple links processing
• Quantity distribution
• Service selection
• Custom delivery schedule

💰 <b>Bulk Discounts:</b>
• 10+ orders: 5% discount
• 50+ orders: 10% discount
• 100+ orders: 15% discount

⚙️ <b>Mass order feature under development!</b>
🔄 <b>Will be available soon with advanced features</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Services & Tools", callback_data="services_tools")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "subscriptions")
@require_account
async def cb_subscriptions(callback: CallbackQuery):
    """Handle subscriptions feature"""
    if not callback.message:
        return

    text = """
🔄 <b>Subscriptions</b>

⏰ <b>Auto-Renewal Service Plans</b>

🎯 <b>Subscription Benefits:</b>
• Automatic order renewal
• Consistent growth maintenance
• Priority delivery
• Special subscriber rates

📅 <b>Available Plans:</b>
• Weekly renewals
• Monthly packages
• Custom schedules
• Pause/resume options

💡 <b>Smart Features:</b>
• Growth tracking
• Performance analytics
• Auto-optimization
• Flexible modifications

🔔 <b>Subscription service coming soon!</b>
💬 <b>Early access:</b> Contact support for beta testing
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Services & Tools", callback_data="services_tools")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "profile_analyzer")
@require_account
async def cb_profile_analyzer(callback: CallbackQuery):
    """Handle profile analyzer feature"""
    if not callback.message:
        return

    text = """
📊 <b>Profile Analyzer</b>

🔍 <b>Advanced Social Media Analytics</b>

📈 <b>Analysis Features:</b>
• Engagement rate calculation
• Follower quality assessment
• Growth trend analysis
• Optimal posting times

🎯 <b>Insights Provided:</b>
• Audience demographics
• Content performance
• Competitor analysis
• Growth recommendations

💡 <b>AI-Powered Reports:</b>
• Personalized strategies
• Market positioning
• Content suggestions
• Hashtag optimization

🔬 <b>Profile analyzer tool under development!</b>
✨ <b>Will include AI-powered insights and recommendations</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Services & Tools", callback_data="services_tools")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "hashtag_generator")
@require_account
async def cb_hashtag_generator(callback: CallbackQuery):
    """Handle hashtag generator feature"""
    if not callback.message:
        return

    text = """
## <b>Hashtag Generator</b>

🏷️ <b>AI-Powered Hashtag Creation Tool</b>

🎯 <b>Smart Features:</b>
• Trending hashtag suggestions
• Niche-specific tags
• Engagement optimization
• Regional relevance

📊 <b>Analytics Integration:</b>
• Performance tracking
• Reach estimation
• Competition analysis
• Viral potential score

🇮🇳 <b>India-Focused:</b>
• Local trending topics
• Cultural relevance
• Regional languages
• Festival-based tags

🤖 <b>AI-powered hashtag generator coming soon!</b>
⚡️ <b>Will generate optimized hashtags for maximum reach</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Services & Tools", callback_data="services_tools")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "free_trial")
@require_account
async def cb_free_trial(callback: CallbackQuery):
    """Handle free trial service"""
    if not callback.message:
        return

    text = """
✨ <b>Free Trial Service</b>

🎁 <b>Try Our Premium Services For Free!</b>

🆓 <b>Available Free Trials:</b>
• 100 Instagram Likes - FREE
• 50 YouTube Views - FREE
• 25 Facebook Reactions - FREE
• 10 TikTok Likes - FREE

📋 <b>Trial Conditions:</b>
• One trial per platform
• Account verification required
• No payment needed
• Quality guaranteed

🎯 <b>Trial Benefits:</b>
• Experience our quality
• Test delivery speed
• Verify safety
• Build confidence

🔥 <b>Free trial service launching soon!</b>
💡 <b>Perfect way to test our premium quality services</b>
"""

    trial_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Request Trial", url=f"https://t.me/{OWNER_USERNAME}")],
        [InlineKeyboardButton(text="⬅️ Services & Tools", callback_data="services_tools")]
    ])

    await safe_edit_message(callback, text, trial_keyboard)
    await callback.answer()

# ========== CONTACT & ABOUT SUB-MENU HANDLERS ==========
@dp.callback_query(F.data == "website_info")
async def cb_website_info(callback: CallbackQuery):
    """Show website information"""
    if not callback.message:
        return

    text = f"""
🌐 <b>Our Website</b>

🔗 <b>Website:</b>
Coming Soon...

🇮🇳 <b>India Social Panel Official</b>
✅ Premium SMM Services
✅ 24/7 Customer Support
✅ Secure Payment Gateway
✅ Real-time Order Tracking

💡 <b>Please wait for the website launch!</b>

📞 <b>Contact:</b> @{OWNER_USERNAME}
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data="contact_about")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "support_channel")
async def cb_support_channel(callback: CallbackQuery):
    """Show support channel info"""
    if not callback.message:
        return

    text = """
💬 <b>Support Channel</b>

🎆 <b>Join Our Community!</b>

🔗 <b>Telegram Channel:</b>
@IndiaSocialPanelOfficial

🔗 <b>Support Group:</b>
@IndiaSocialPanelSupport

📝 <b>Channel Benefits:</b>
• Latest Updates & Offers
• Service Announcements
• Community Support
• Tips & Tricks
• Exclusive Discounts

🔔 <b>Please turn ON notifications!</b>
"""

    join_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Join Channel", url="https://t.me/IndiaSocialPanelOfficial")],
        [InlineKeyboardButton(text="💬 Join Support Group", url="https://t.me/IndiaSocialPanelSupport")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="contact_about")]
    ])

    await safe_edit_message(callback, text, join_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "terms_service")
async def cb_terms_service(callback: CallbackQuery):
    """Show terms of service"""
    if not callback.message:
        return

    text = """
📜 <b>Terms of Service</b>

📝 <b>Important Terms:</b>

1️⃣ <b>Service Guarantee:</b>
• High quality services guarantee
• No fake/bot followers
• Real & active users only

2️⃣ <b>Refund Policy:</b>
• No refund after service starts
• Customer responsible for wrong links
• Full refund for technical issues

3️⃣ <b>Account Safety:</b>
• We use 100% safe methods
• Your account will not be banned
• Privacy fully protected

4️⃣ <b>Delivery Time:</b>
• 0-6 hours typical delivery
• Some services may take 24-48 hours
• Status tracking available

🔒 <b>By using our services, you agree to these terms</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data="contact_about")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

# ========== OFFERS & REWARDS HANDLERS ==========
@dp.callback_query(F.data == "coupon_redeem")
@require_account
async def cb_coupon_redeem(callback: CallbackQuery):
    """Handle coupon redeem feature"""
    if not callback.message:
        return

    text = """
🎟️ <b>Redeem Coupon</b>

💝 <b>Discount Coupons & Promo Codes</b>

🎯 <b>Active Offers:</b>
• WELCOME10 - 10% off first order
• BULK20 - 20% off on orders above ₹2000
• FESTIVAL25 - 25% festival special
• REFER15 - 15% off via referral

💡 <b>How to Use:</b>
1. Get coupon code
2. Enter during checkout
3. Discount applied instantly
4. Save money on orders

🔥 <b>Special Coupons:</b>
• Daily login rewards
• Loyalty member exclusive
• Limited time offers
• Seasonal promotions

🎟️ <b>Coupon system coming soon!</b>
💬 <b>Get exclusive codes:</b> @{OWNER_USERNAME}
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Offers & Rewards", callback_data="offers_rewards")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "partner_program")
@require_account
async def cb_partner_program(callback: CallbackQuery):
    """Handle partner program feature"""
    if not callback.message:
        return

    text = """
🤝 <b>Partner Program</b>

💼 <b>Business Partnership Opportunities</b>

🎯 <b>Partnership Benefits:</b>
• Wholesale pricing (up to 40% off)
• Priority customer support
• Dedicated account manager
• Custom branding options

📊 <b>Partner Tiers:</b>
• Bronze: ₹10,000+ monthly
• Silver: ₹25,000+ monthly
• Gold: ₹50,000+ monthly
• Platinum: ₹1,00,000+ monthly

💡 <b>Exclusive Features:</b>
• API access
• White-label solutions
• Bulk order management
• Revenue sharing program

🚀 <b>Partner program launching soon!</b>
📞 <b>Business inquiries:</b> @{OWNER_USERNAME}
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Offers & Rewards", callback_data="offers_rewards")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "loyalty_program")
@require_account
async def cb_loyalty_program(callback: CallbackQuery):
    """Handle loyalty program feature"""
    if not callback.message:
        return

    text = """
🏆 <b>Loyalty Program</b>

💎 <b>Exclusive Benefits for Regular Customers</b>

🌟 <b>Loyalty Tiers:</b>
• Bronze: ₹0-₹5,000 spent
• Silver: ₹5,001-₹15,000 spent
• Gold: ₹15,001-₹50,000 spent
• Platinum: ₹50,000+ spent

🎁 <b>Tier Benefits:</b>
• Bronze: 2% cashback
• Silver: 5% cashback + priority support
• Gold: 8% cashback + exclusive offers
• Platinum: 12% cashback + VIP treatment

💡 <b>Loyalty Points:</b>
• Earn 1 point per ₹10 spent
• Redeem points for discounts
• Bonus points on special days
• Referral bonus points

🔥 <b>Loyalty program launching soon!</b>
✨ <b>Start earning rewards on every order!</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Offers & Rewards", callback_data="offers_rewards")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "daily_reward")
@require_account
async def cb_daily_reward(callback: CallbackQuery):
    """Handle daily reward feature"""
    if not callback.message:
        return

    text = """
🎉 <b>Daily Reward</b>

🎁 <b>Login करें और Daily Rewards पाएं!</b>

📅 <b>Daily Login Streak:</b>
• Day 1: ₹5 bonus
• Day 3: ₹10 bonus
• Day 7: ₹25 bonus
• Day 15: ₹50 bonus
• Day 30: ₹100 bonus

⚡️ <b>Special Rewards:</b>
• Weekend bonus (2x rewards)
• Festival special rewards
• Birthday month bonus
• Milestone achievements

🎯 <b>Additional Benefits:</b>
• Spin wheel daily
• Lucky draw entries
• Surprise gift boxes
• Exclusive coupon codes

🎊 <b>Daily reward system launching soon!</b>
💫 <b>Make it a habit to login daily for maximum benefits!</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Offers & Rewards", callback_data="offers_rewards")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "leaderboard")
@require_account
async def cb_leaderboard(callback: CallbackQuery):
    """Handle leaderboard feature"""
    if not callback.message:
        return

    text = """
🥇 <b>Leaderboard</b>

🏆 <b>Top Users Ranking & Competitions</b>

👑 <b>Monthly Leaderboard:</b>
1. 🥇 @champion_user - ₹45,000 spent
2. 🥈 @pro_marketer - ₹38,000 spent
3. 🥉 @social_king - ₹32,000 spent
... और भी users

🎯 <b>Ranking Categories:</b>
• Total spending
• Most orders placed
• Referral champions
• Loyalty points earned

🏅 <b>Leaderboard Rewards:</b>
• Top 3: Special badges + bonuses
• Top 10: Exclusive discounts
• Top 50: Priority support
• All participants: Recognition

🔥 <b>Leaderboard system launching soon!</b>
💪 <b>Compete with other users and win exciting prizes!</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Offers & Rewards", callback_data="offers_rewards")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "community_polls")
@require_account
async def cb_community_polls(callback: CallbackQuery):
    """Handle community polls feature"""
    if not callback.message:
        return

    text = """
📝 <b>Community Polls</b>

🗳️ <b>Your Voice Matters - Help Shape Our Services!</b>

📊 <b>Current Active Poll:</b>
"Which new platform should we add next?"
• 🎵 TikTok India - 45%
• 📺 YouTube Shorts - 35%
• 💼 LinkedIn India - 20%

💡 <b>Previous Poll Results:</b>
• "Best delivery time?" → 0-6 hours won
• "Preferred payment method?" → UPI won
• "Most wanted service?" → Instagram Reels won

🎁 <b>Poll Participation Rewards:</b>
• Vote करने पर points मिलते हैं
• Monthly poll winners get bonuses
• Community feedback valued
• Special recognition for active voters

🗳️ <b>Community polling system launching soon!</b>
👥 <b>Be part of India Social Panel's growth decisions!</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Offers & Rewards", callback_data="offers_rewards")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

# ========== AI SUPPORT & CONTACT ADMIN HANDLERS ==========
@dp.callback_query(F.data == "ai_support")
async def cb_ai_support(callback: CallbackQuery):
    """Handle AI support feature"""
    if not callback.message:
        return

    text = """
🤖 <b>AI Support</b>

🧠 <b>Intelligent Assistant - 24/7 Available</b>

⚡️ <b>AI Features:</b>
• Instant query resolution
• Smart troubleshooting
• Order tracking assistance
• Service recommendations

🎯 <b>What AI Can Help With:</b>
• Account related questions
• Order status inquiries
• Payment issues
• Service explanations
• Best practices guidance

💡 <b>Smart Responses:</b>
• Natural language understanding
• Context-aware answers
• Multi-language support
• Learning from interactions

🤖 <b>AI Support system under development!</b>
⚡️ <b>Will provide instant, intelligent assistance 24/7</b>

📞 <b>For now, contact human support:</b> @{OWNER_USERNAME}
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Chat with Human", url=f"https://t.me/{OWNER_USERNAME}")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="contact_about")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "contact_admin")
async def cb_contact_admin(callback: CallbackQuery):
    """Handle contact admin feature"""
    if not callback.message:
        return

    text = f"""
👨‍💼 <b>Contact Admin</b>

📞 <b>Direct Admin Support</b>

👤 <b>Main Admin:</b>
• Name: {OWNER_NAME}
• Username: @{OWNER_USERNAME}
• Response Time: 2-6 hours
• Available: 9 AM - 11 PM IST

💼 <b>Support Team:</b>
• @SupportManager_ISP
• @TechnicalSupport_ISP
• @BillingSupport_ISP
• @AccountManager_ISP

⚡️ <b>Quick Support Categories:</b>
• 🆘 Emergency issues
• 💰 Payment problems
• 🔧 Technical difficulties
• 💼 Business inquiries
• 🎁 Partnership requests

🚀 <b>Premium Support:</b>
For VIP customers and partners, we provide priority support with dedicated account managers.

📱 <b>Choose your preferred contact method:</b>
"""

    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 Main Admin", url=f"https://t.me/{OWNER_USERNAME}"),
            InlineKeyboardButton(text="🆘 Emergency", url="https://t.me/SupportManager_ISP")
        ],
        [
            InlineKeyboardButton(text="💰 Billing Support", url="https://t.me/BillingSupport_ISP"),
            InlineKeyboardButton(text="🔧 Technical Help", url="https://t.me/TechnicalSupport_ISP")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back", callback_data="contact_about")
        ]
    ])

    await safe_edit_message(callback, text, admin_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "create_ticket")
@require_account
async def cb_create_ticket(callback: CallbackQuery):
    """Start ticket creation process"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Initialize user state if not exists - PROTECT ADMIN BROADCAST
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}
    elif user_state[user_id].get("protected") and is_admin(user_id):
        print(f"🔒 PROTECTED: Not initializing protected admin state for {user_id}")
        return  # Don't touch protected admin state

    user_state[user_id]["current_step"] = "waiting_ticket_subject"

    text = """
🎫 <b>Create Support Ticket</b>

📝 <b>Step 1: Subject</b>

💬 <b>कृपया ticket का subject भेजें:</b>

⚠️ <b>Examples:</b>
• Order delivery issue
• Payment problem
• Account access issue
• Service quality concern

💡 <b>Clear subject likhenge to fast response milega!</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer()

@dp.callback_query(F.data == "view_tickets")
@require_account
async def cb_view_tickets(callback: CallbackQuery):
    """Show user's tickets"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_tickets = [ticket for ticket_id, ticket in tickets_data.items() if ticket.get('user_id') == user_id]

    if not user_tickets:
        text = """
📖 <b>Mere Tickets</b>

📋 <b>कोई tickets नहीं मिले</b>

🎫 <b>Agar koi problem hai to new ticket create karein!</b>
➕ <b>Support team 24/7 available hai</b>
"""
    else:
        text = "📖 <b>Mere Tickets</b>\n\n"
        for i, ticket in enumerate(user_tickets[-5:], 1):  # Last 5 tickets
            status_emoji = {"open": "🔴", "replied": "🟡", "closed": "✅"}
            emoji = status_emoji.get(ticket.get('status', 'open'), "🔴")
            text += f"""
{i}. <b>Ticket #{ticket.get('ticket_id', 'N/A')}</b>
{emoji} Status: {ticket.get('status', 'Open').title()}
📝 Subject: {ticket.get('subject', 'N/A')}
📅 Created: {format_time(ticket.get('created_at', ''))}

"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ New Ticket", callback_data="create_ticket")],
        [InlineKeyboardButton(text="⬅️ Support Menu", callback_data="support_tickets")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

# ========== CONTACT HANDLERS (MOVED TO account_creation.py) ==========
# All contact and text input handlers moved to account_creation.py for better organization

# ========== ERROR HANDLERS ==========
# Message handlers moved to account_creation.py

# ========== PAYMENT HANDLERS ==========
# Payment handlers are in payment_system.py and at the end of this file

# ========== WEBHOOK SETUP ==========
# Webhook setup is at the end of this file

# ========== ADMIN ORDER MANAGEMENT HANDLERS ==========

# New Group Management Button Handlers
@dp.callback_query(F.data.startswith("admin_details_"))
async def cb_admin_order_details(callback: CallbackQuery):
    """Handle admin order details request"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer("❌ Unauthorized access!", show_alert=True)
        return

    order_id = callback.data.replace("admin_details_", "")

    # Get order details - check all possible sources
    global orders_data, order_temp
    print(f"🔍 DEBUG: Details - Looking for order {order_id}")
    print(f"🔍 DEBUG: Details - orders_data has {len(orders_data)} orders")

    # Check if we can access the order from different sources
    order_found = False
    order = None

    if order_id in orders_data:
        order = orders_data[order_id]
        order_found = True
    else:
        # Check order_temp for recent orders
        for temp_order in order_temp.values():
            if temp_order.get('order_id') == order_id:
                order = temp_order
                order_found = True
                orders_data[order_id] = temp_order  # Store back
                break

    if not order_found:
        await callback.answer("❌ Order not found!", show_alert=True)
        return

    details_text = f"""
📊 <b>Order Complete Details</b>

🆔 <b>Order ID:</b> <code>{order_id}</code>
📦 <b>Package:</b> {order.get('package_name', 'N/A')}
📱 <b>Platform:</b> {order.get('platform', 'N/A').title()}
🔗 <b>Link:</b> {order.get('link', 'N/A')}
🔢 <b>Quantity:</b> {order.get('quantity', 0):,}
💰 <b>Amount:</b> ₹{order.get('total_price', 0.0):,.2f}
💳 <b>Payment Method:</b> {order.get('payment_method', 'N/A')}
📅 <b>Created:</b> {format_time(order.get('created_at', ''))}
⚡️ <b>Status:</b> {order.get('status', 'pending').title()}

👤 <b>Customer Details:</b>
• User ID: {order.get('user_id', 'N/A')}
• Service ID: {order.get('service_id', 'N/A')}
• Payment Status: {order.get('payment_status', 'pending')}
"""

    # Create management buttons
    details_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Complete Order",
                callback_data=f"admin_complete_{order_id}"
            ),
            InlineKeyboardButton(
                text="❌ Cancel Order",
                callback_data=f"admin_cancel_{order_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="💬 Send Message",
                callback_data=f"admin_message_{order.get('user_id', '')}"
            ),
            InlineKeyboardButton(
                text="🔄 Refresh Status",
                callback_data=f"admin_refresh_{order_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="👤 User Profile",
                callback_data=f"admin_profile_{order.get('user_id', '')}"
            )
        ]
    ])

    await safe_edit_message(callback, details_text, details_keyboard)
    await callback.answer("Order details loaded")

@dp.callback_query(F.data.startswith("admin_profile_"))
async def cb_admin_user_profile(callback: CallbackQuery):
    """Handle admin user profile request"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer("❌ Unauthorized access!", show_alert=True)
        return

    target_user_id = int(callback.data.replace("admin_profile_", ""))

    if target_user_id not in users_data:
        await callback.answer("❌ User not found!", show_alert=True)
        return

    user = users_data[target_user_id]

    # Enhanced user profile with more details
    join_date = format_time(user.get('join_date', ''))
    referral_code = user.get('referral_code', 'N/A')
    api_key = user.get('api_key', 'Not Generated')

    # Get recent order history count
    recent_orders = 0
    for order in orders_data.values():
        if order.get('user_id') == target_user_id:
            recent_orders += 1

    profile_text = f"""
👤 <b>Complete User Profile</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 <b>BASIC INFORMATION</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🆔 <b>User ID:</b> <code>{target_user_id}</code>
👤 <b>Full Name:</b> {user.get('full_name', 'Not Set')}
📱 <b>Username:</b> @{user.get('username', 'Not Set')}
📞 <b>Phone:</b> {user.get('phone_number', 'Not Set')}
📧 <b>Email:</b> {user.get('email', 'Not Set')}
📅 <b>Joined:</b> {join_date}
⚡️ <b>Status:</b> {user.get('status', 'active').title()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 <b>ACCOUNT STATISTICS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━

💳 <b>Current Balance:</b> ₹{user.get('balance', 0.0):,.2f}
💸 <b>Total Spent:</b> ₹{user.get('total_spent', 0.0):,.2f}
📦 <b>Total Orders:</b> {user.get('orders_count', 0)}
📋 <b>Recent Orders:</b> {recent_orders}
🔗 <b>Referral Code:</b> {referral_code}

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 <b>TECHNICAL DETAILS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━

🔑 <b>API Status:</b> {'Active' if api_key != 'Not Generated' else 'Not Generated'}
✅ <b>Account Created:</b> {'Yes' if user.get('account_created') else 'No'}

━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>Admin Actions Available</b>
"""

    profile_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 Send Message", callback_data=f"admin_message_{target_user_id}"),
            InlineKeyboardButton(text="📜 Order History", callback_data=f"admin_user_orders_{target_user_id}")
        ],
        [
            InlineKeyboardButton(text="💰 Add Balance", callback_data=f"admin_add_balance_{target_user_id}"),
            InlineKeyboardButton(text="🚫 Suspend User", callback_data=f"admin_suspend_{target_user_id}")
        ],
        [
            InlineKeyboardButton(text="🔄 Refresh Data", callback_data=f"admin_profile_{target_user_id}")
        ]
    ])

    await safe_edit_message(callback, profile_text, profile_keyboard)
    await callback.answer("👤 User profile loaded")

@dp.callback_query(F.data.startswith("admin_create_token_"))
async def cb_admin_create_account_via_token(callback: CallbackQuery, state: FSMContext):
    """Handle admin create account via token button clicks"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer("❌ Unauthorized access!", show_alert=True)
        return

    # Parse target user ID from callback data
    target_user_id = callback.data.replace("admin_create_token_", "")
    
    try:
        target_user_id = int(target_user_id)
    except ValueError:
        await callback.answer("❌ Invalid user ID!", show_alert=True)
        return

    # Store target user ID in FSM state
    await state.update_data(target_user_id=target_user_id)
    
    # Set FSM state to waiting for token
    await state.set_state(AdminCreateUserStates.waiting_for_token)
    
    # Send prompt message
    prompt_text = f"""
🔐 <b>Create User Account via Token</b>

👤 <b>Target User ID:</b> <code>{target_user_id}</code>

💡 <b>Please send the Access Token for this user</b>

⚙️ <b>How this works:</b>
• Token will be decoded to extract user information
• Account will be created automatically with decoded data
• User status will be set to "Active"

📤 <b>Send the Access Token now:</b>
"""
    
    await safe_edit_message(callback, prompt_text)
    await callback.answer("🔐 Ready to receive token")

@dp.callback_query(F.data.startswith("admin_msg_user_"))
async def cb_admin_send_message(callback: CallbackQuery, state: FSMContext):
    """Handle admin send message button clicks"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer("❌ Unauthorized access!", show_alert=True)
        return

    # Parse target user ID from callback data
    target_user_id = callback.data.replace("admin_msg_user_", "")
    
    try:
        target_user_id = int(target_user_id)
    except ValueError:
        await callback.answer("❌ Invalid user ID!", show_alert=True)
        return

    # Store target user ID in FSM state
    await state.update_data(target_user_id=target_user_id)
    
    # Set FSM state to waiting for message
    await state.set_state(AdminDirectMessageStates.waiting_for_message)
    
    # Send prompt message
    prompt_text = f"""
💬 <b>Send Message to User</b>

👤 <b>Target User ID:</b> <code>{target_user_id}</code>

📝 <b>Please type the message you want to send</b>

💡 <b>Important:</b>
• Your message will be sent exactly as you type it
• No extra formatting or headers will be added
• Type your message as you want the user to see it

📤 <b>Type your message now:</b>
"""
    
    await safe_edit_message(callback, prompt_text)
    await callback.answer("💬 Ready to send message")

@dp.callback_query(F.data.startswith("admin_refresh_"))
async def cb_admin_refresh_status(callback: CallbackQuery):
    """Handle admin order status refresh"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer("❌ Unauthorized access!", show_alert=True)
        return

    order_id = callback.data.replace("admin_refresh_", "")

    # Debug info for refresh button - check all sources
    global orders_data, order_temp
    print(f"🔍 DEBUG: Refresh - Looking for order {order_id}")
    print(f"🔍 DEBUG: Refresh - orders_data has {len(orders_data)} orders")

    # Check if we can access the order from different sources
    order_found = False
    order = None

    if order_id in orders_data:
        order = orders_data[order_id]
        order_found = True
    else:
        # Check order_temp for recent orders
        for temp_order in order_temp.values():
            if temp_order.get('order_id') == order_id:
                order = temp_order
                order_found = True
                orders_data[order_id] = temp_order  # Store back
                break

    if not order_found:
        await callback.answer("❌ Order not found!", show_alert=True)
        return
    current_status = order.get('status', 'pending')

    await callback.answer(f"🔄 Order {order_id} - Current Status: {current_status.title()}", show_alert=True)
@dp.callback_query(F.data.startswith("admin_complete_"))
async def cb_admin_complete_order(callback: CallbackQuery):
    """Handle admin order completion"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer("❌ Unauthorized access!", show_alert=True)
        return

    # Step 1: Parse smart callback data to get order_id and customer_id
    callback_parts = callback.data.replace("admin_complete_", "").split("_")
    order_id = callback_parts[0] if len(callback_parts) > 0 else None
    customer_id = None

    if len(callback_parts) >= 2:
        try:
            customer_id = int(callback_parts[1])
            print(f"🔍 DEBUG: Message Parsing Method - Order ID: {order_id}, Customer ID: {customer_id}")
        except (ValueError, IndexError):
            await callback.answer("❌ Invalid button data format!", show_alert=True)
            return

    if not order_id or not customer_id:
        await callback.answer("❌ Missing order or customer ID!", show_alert=True)
        return

    # Step 2: Get and parse the admin notification message text (stateless approach)
    message_text = callback.message.text or callback.message.caption or ""
    if not message_text:
        await callback.answer("❌ Cannot read message content for parsing!", show_alert=True)
        return

    print(f"🔍 DEBUG: Parsing message text for order details (no database lookup needed)...")
    print(f"📝 DEBUG: Message text content:\n{message_text}")
    print(f"📝 DEBUG: Message text length: {len(message_text)}")

    # Step 3: Parse all order details from message using regex patterns
    import re

    # Extract Customer Name: look for "• 👤 Name: {value}" (plain text, no HTML)
    name_match = re.search(r"• 👤 Name:\s*(.+)", message_text)
    customer_name = name_match.group(1).strip() if name_match else "Customer"

    # Extract Package Name: look for "• 📦 Package: {value}" (plain text, no HTML)
    package_match = re.search(r"• 📦 Package:\s*(.+)", message_text)
    package_name = package_match.group(1).strip() if package_match else "Unknown Package"

    # Extract Platform: look for "• 📱 Platform: {value}" (plain text, no HTML)
    platform_match = re.search(r"• 📱 Platform:\s*(.+)", message_text)
    platform = platform_match.group(1).strip() if platform_match else "Unknown"

    # Extract Quantity: look for "• 🔢 Quantity: {value}" (plain text, no HTML)
    quantity_match = re.search(r"• 🔢 Quantity:\s*(.+)", message_text)
    quantity_str = quantity_match.group(1).strip() if quantity_match else "0"
    # Remove commas and convert to int for proper formatting
    try:
        quantity = int(quantity_str.replace(",", ""))
    except (ValueError, AttributeError):
        quantity = 0

    # Extract Amount: look for "• 💰 Amount: ₹{value}" (plain text, no HTML)
    amount_match = re.search(r"• 💰 Amount:\s*₹(.+)", message_text)
    amount_str = amount_match.group(1).strip() if amount_match else "0.00"
    # Remove commas and convert to float for proper formatting
    try:
        total_price = float(amount_str.replace(",", ""))
    except (ValueError, AttributeError):
        total_price = 0.0

    print(f"✅ DEBUG: Parsed details - Customer: {customer_name}, Package: {package_name}, Platform: {platform}, Quantity: {quantity}, Amount: ₹{total_price}")

    # Step 4: Optional minimal tracking (can be removed for pure stateless approach)
    # Only store completion record for optional tracking purposes
    completion_record = {
        'order_id': order_id,
        'status': 'completed',
        'completed_at': datetime.now().isoformat(),
        'completed_by_admin': user_id,
        'user_id': customer_id,        # CRITICAL FIX: Use user_id not customer_id
        'customer_id': customer_id,    # Keep both for compatibility
        'package_name': package_name,
        'platform': platform,
        'quantity': quantity,
        'total_price': total_price
    }

    # CRITICAL: Update ALL data sources for consistency
    orders_data[order_id] = completion_record
    save_data_to_json(orders_data, "orders.json")

    # CRITICAL: Force reload fresh data from file to sync memory
    print(f"🔄 DEBUG: Force reloading orders_data from file for consistency...")
    fresh_orders_data = load_data_from_json("orders.json")
    orders_data.clear()
    orders_data.update(fresh_orders_data)
    print(f"✅ DEBUG: orders_data reloaded - Now has {len(orders_data)} orders")

    # Also update order_temp if it exists
    if customer_id in order_temp and order_temp[customer_id].get('order_id') == order_id:
        print(f"🔧 DEBUG: Also updating order_temp for consistency...")
        order_temp[customer_id]['status'] = 'completed'
        order_temp[customer_id]['completed_at'] = datetime.now().isoformat()
        order_temp[customer_id]['completed_by_admin'] = user_id
        print(f"✅ DEBUG: order_temp updated - Status: {order_temp[customer_id]['status']}")
    else:
        print(f"🔍 DEBUG: order_temp not found for customer {customer_id} or different order_id")

    print(f"✅ DEBUG: Stateless completion - parsed all details from message text!")
    print(f"📊 DEBUG: Final status in orders_data[{order_id}]: {orders_data.get(order_id, {}).get('status', 'NOT_FOUND')}")

    # Send completion message to customer
    customer_message = f"""
🎉 <b>ORDER COMPLETED!</b>

✅ <b>Your order has been successfully completed!</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 <b>ORDER DETAILS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━

🆔 <b>Order ID:</b> <code>{order_id}</code>
📦 <b>Package:</b> {package_name}
📱 <b>Platform:</b> {platform.title()}
📊 <b>Quantity:</b> {quantity:,}
💰 <b>Amount:</b> ₹{total_price:,.2f}

✅ <b>Status:</b> Completed
📅 <b>Completed:</b> {datetime.now().strftime("%d %b %Y, %I:%M %p")}
⚡️ <b>Delivery:</b> Service is now active

━━━━━━━━━━━━━━━━━━━━━━━━━━
💝 <b>THANK YOU!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━

🌟 <b>Service delivery successful!</b>
🎯 <b>Please check your {platform.title()} account</b>
⏰ <b>Full delivery within 0-6 hours</b>

💡 <b>Need more services? Place your next order!</b>

✨ <b>Thank you for choosing India Social Panel!</b>
"""

    customer_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐ Rate Service", callback_data=f"rate_order_{order_id}"),
            InlineKeyboardButton(text="💬 Feedback", callback_data=f"feedback_order_{order_id}")
        ],
        [
            InlineKeyboardButton(text="🚀 New Order", callback_data="new_order"),
            InlineKeyboardButton(text="📜 Order History", callback_data="order_history")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    try:
        await bot.send_message(
            chat_id=customer_id,
            text=customer_message,
            reply_markup=customer_keyboard,
            parse_mode="HTML"
        )

        # Update admin message
        admin_update = f"""
✅ <b>ORDER COMPLETED SUCCESSFULLY!</b>

🆔 <b>Order ID:</b> <code>{order_id}</code>
👤 <b>Customer:</b> {customer_name}
📦 <b>Service:</b> {package_name}
💰 <b>Amount:</b> ₹{total_price:,.2f}

✅ <b>Actions Completed:</b>
• Order status updated to "Completed"
• Customer notification sent
• User statistics updated
• Order marked as delivered

📊 <b>Completion Time:</b> {datetime.now().strftime("%d %b %Y, %I:%M %p")}

🎉 <b>Order processing completed successfully!</b>
"""

        await safe_edit_message(callback, admin_update)
        await callback.answer("✅ Order completed and customer notified!")

    except Exception as e:
        print(f"Error completing order: {e}")
        await callback.answer("❌ Error completing order!", show_alert=True)

@dp.callback_query(F.data.startswith("admin_cancel_"))
async def cb_admin_cancel_order(callback: CallbackQuery):
    """Handle admin order cancellation with reason selection"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer("❌ Unauthorized access!", show_alert=True)
        return

    # Parse callback_data - support both legacy and smart formats
    callback_parts = callback.data.replace("admin_cancel_", "").split("_")
    order_id = callback_parts[0] if len(callback_parts) > 0 else None
    customer_id = None

    if len(callback_parts) >= 2:
        # Smart format: admin_cancel_{order_id}_{customer_id}
        try:
            customer_id = int(callback_parts[1])
            print(f"🔍 DEBUG: Smart Cancel Button - Order ID: {order_id}, Customer ID: {customer_id}")
        except (ValueError, IndexError):
            await callback.answer("❌ Invalid button data format!", show_alert=True)
            return
    else:
        # Legacy format: admin_cancel_{order_id} - will work without customer_id for cancel menu
        print(f"🔍 DEBUG: Legacy Cancel Button - Order ID: {order_id}")

    if not order_id:
        await callback.answer("❌ Missing order ID!", show_alert=True)
        return

    # Parse admin notification message text to get order details (same as Complete Order)
    message_text = callback.message.text or callback.message.caption or ""
    if not message_text:
        await callback.answer("❌ Cannot read message content for parsing!", show_alert=True)
        return

    print(f"🔍 DEBUG: Cancel Order Step 1 - Parsing message text for order details...")
    print(f"📝 DEBUG: Message text length: {len(message_text)} chars")

    # Parse all order details from message using regex patterns (same as Complete Order)
    import re

    # Extract Customer Name
    name_match = re.search(r"• 👤 Name:\s*(.+)", message_text)
    customer_name = name_match.group(1).strip() if name_match else "Customer"

    # Extract Package Name
    package_match = re.search(r"• 📦 Package:\s*(.+)", message_text)
    package_name = package_match.group(1).strip() if package_match else "Unknown Package"

    # Extract Amount
    amount_match = re.search(r"• 💰 Amount:\s*₹(.+)", message_text)
    total_price = 0.0
    if amount_match:
        amount_str = amount_match.group(1).strip()
        try:
            total_price = float(amount_str.replace(",", ""))
        except (ValueError, AttributeError):
            total_price = 0.0

    print(f"✅ DEBUG: Cancel Order Step 1 - Parsed details: {customer_name}, {package_name}, ₹{total_price}")

    # Store parsed details in orders_data for step 2 to access
    orders_data[order_id] = {
        'order_id': order_id,
        'user_id': customer_id,
        'status': 'pending',
        'package_name': package_name,
        'total_price': total_price,
        'customer_name': customer_name,  # Add customer name too
        'parsed_from_message': True  # Flag to indicate this was parsed
    }

    # Save updated order data
    save_data_to_json(orders_data, "orders.json")

    # Show cancellation reason options with smart button format
    cancel_text = f"""
❌ <b>Cancel Order #{order_id}</b>

⚠️ <b>Select cancellation reason:</b>

💡 <b>Choose the most appropriate reason for order cancellation:</b>
"""

    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔗 Invalid Link",
                callback_data=f"cancel_reason_{order_id}_{customer_id}_invalid_link"
            ),
            InlineKeyboardButton(
                text="💳 Payment Issue",
                callback_data=f"cancel_reason_{order_id}_{customer_id}_payment_issue"
            )
        ],
        [
            InlineKeyboardButton(
                text="📦 Service Unavailable",
                callback_data=f"cancel_reason_{order_id}_{customer_id}_service_unavailable"
            ),
            InlineKeyboardButton(
                text="❌ Duplicate Order",
                callback_data=f"cancel_reason_{order_id}_{customer_id}_duplicate"
            )
        ],
        [
            InlineKeyboardButton(
                text="🚫 Policy Violation",
                callback_data=f"cancel_reason_{order_id}_{customer_id}_policy_violation"
            ),
            InlineKeyboardButton(
                text="💬 Custom Reason",
                callback_data=f"cancel_reason_{order_id}_{customer_id}_custom"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Back to Order",
                callback_data=f"admin_details_{order_id}"
            )
        ]
    ])

    await safe_edit_message(callback, cancel_text, cancel_keyboard)
    await callback.answer()

@dp.callback_query(F.data.startswith("cancel_reason_"))
async def cb_admin_cancel_reason(callback: CallbackQuery):
    """Handle order cancellation with specific reason"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer("❌ Unauthorized access!", show_alert=True)
        return

    # Parse callback data - support both legacy and smart formats
    # Format: cancel_reason_ORDER_ID_[CUSTOMER_ID_]REASON
    if not callback.data:
        await callback.answer("❌ Invalid callback data!", show_alert=True)
        return
    callback_parts = callback.data.split("_")
    order_id = callback_parts[2] if len(callback_parts) > 2 else None
    customer_id = None
    reason_type = None

    if not order_id:
        await callback.answer("❌ Missing order ID!", show_alert=True)
        return

    if len(callback_parts) >= 5:
        # Smart format: cancel_reason_ORDER_ID_CUSTOMER_ID_REASON
        try:
            customer_id = int(callback_parts[3])
            reason_type = "_".join(callback_parts[4:])
            print(f"🔍 DEBUG: Smart Cancel Reason - Order ID: {order_id}, Customer ID: {customer_id}, Reason: {reason_type}")
        except (ValueError, IndexError):
            await callback.answer("❌ Invalid smart button format!", show_alert=True)
            return
    elif len(callback_parts) >= 4:
        # Legacy format: cancel_reason_ORDER_ID_REASON
        reason_type = "_".join(callback_parts[3:])
        print(f"🔍 DEBUG: Legacy Cancel Reason - Order ID: {order_id}, Reason: {reason_type}")
    else:
        await callback.answer("❌ Invalid button data!", show_alert=True)
        return

    if not reason_type:
        await callback.answer("❌ Missing cancellation reason!", show_alert=True)
        return

    # Get order details from step 1 parsing (stored in orders_data)
    print(f"🔍 DEBUG: Cancel Order Step 2 - Getting parsed details from storage...")

    if order_id in orders_data and orders_data[order_id].get('parsed_from_message'):
        # Use parsed details from step 1
        order = orders_data[order_id]
        customer_name = order.get('customer_name', 'Customer')
        package_name = order.get('package_name', 'Unknown Package')
        total_price = order.get('total_price', 0.0)
        print(f"✅ DEBUG: Cancel Order Step 2 - Using parsed details: {customer_name}, {package_name}, ₹{total_price}")
    else:
        # Fallback: try to find in existing orders
        print(f"⚠️ DEBUG: Cancel Order Step 2 - Parsed details not found, using fallback")
        if order_id in orders_data:
            order = orders_data[order_id]
            customer_name = "Customer"
            package_name = order.get('package_name', 'Unknown Package')
            total_price = order.get('total_price', 0.0)
        else:
            # Create minimal record
            customer_name = "Customer"
            package_name = "Unknown Package"
            total_price = 0.0
            orders_data[order_id] = {
                'order_id': order_id,
                'user_id': customer_id,
                'status': 'pending',
                'package_name': package_name,
                'total_price': total_price
            }

    # Reason mapping
    reason_messages = {
        "invalid_link": "❌ Link provided is invalid or inaccessible",
        "payment_issue": "💳 Payment verification failed or insufficient",
        "service_unavailable": "📦 Requested service is temporarily unavailable",
        "duplicate": "❌ Duplicate order detected",
        "policy_violation": "🚫 Order violates our service policy",
        "custom": "💬 Custom reason (contact support for details)"
    }

    reason_message = reason_messages.get(reason_type, "Order cancelled by admin")

    # Update order status
    orders_data[order_id]['status'] = 'cancelled'
    orders_data[order_id]['cancelled_at'] = datetime.now().isoformat()
    orders_data[order_id]['cancelled_by_admin'] = user_id
    orders_data[order_id]['cancellation_reason'] = reason_message

    # Save updated order data to persistent storage
    save_data_to_json(orders_data, "orders.json")

    # Send cancellation message to customer
    customer_message = f"""
❌ <b>ORDER CANCELLED</b>

😔 <b>We regret to inform you that your order has been cancelled.</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 <b>ORDER DETAILS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━

🆔 <b>Order ID:</b> <code>{order_id}</code>
📦 <b>Package:</b> {package_name}
💰 <b>Amount:</b> ₹{total_price:,.2f}

❌ <b>Status:</b> Cancelled
📅 <b>Cancelled:</b> {datetime.now().strftime("%d %b %Y, %I:%M %p")}

━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ <b>CANCELLATION REASON</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━

{reason_message}

━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <b>NEXT STEPS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 <b>Refund Process:</b> If payment was made, refund will be processed within 24-48 hours
📞 <b>Need Help?</b> Contact support with Order ID: <code>{order_id}</code>
🚀 <b>New Order:</b> You can place a new order anytime

💙 <b>Thank you for your understanding!</b>
"""

    customer_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📞 Contact Support", url="https://t.me/tech_support_admin"),
            InlineKeyboardButton(text="🔄 Request Refund", callback_data=f"refund_request_{order_id}")
        ],
        [
            InlineKeyboardButton(text="🚀 New Order", callback_data="new_order"),
            InlineKeyboardButton(text="📜 Order History", callback_data="order_history")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    try:
        await bot.send_message(
            chat_id=customer_id,
            text=customer_message,
            reply_markup=customer_keyboard,
            parse_mode="HTML"
        )

        # Update admin message
        admin_update = f"""
❌ <b>ORDER CANCELLED SUCCESSFULLY!</b>

🆔 <b>Order ID:</b> <code>{order_id}</code>
👤 <b>Customer:</b> {customer_name}
📦 <b>Service:</b> {package_name}
💰 <b>Amount:</b> ₹{total_price:,.2f}

❌ <b>Cancellation Reason:</b>
{reason_message}

✅ <b>Actions Completed:</b>
• Order status updated to "Cancelled"
• Customer notification sent
• Cancellation reason logged
• Order marked for refund processing

📊 <b>Cancellation Time:</b> {datetime.now().strftime("%d %b %Y, %I:%M %p")}

💡 <b>Order cancellation processed successfully!</b>
"""

        await safe_edit_message(callback, admin_update)
        await callback.answer("❌ Order cancelled and customer notified!")

    except Exception as e:
        print(f"Error cancelling order: {e}")
        await callback.answer("❌ Error cancelling order!", show_alert=True)

@dp.callback_query(F.data.startswith("admin_message_"))
async def cb_admin_message(callback: CallbackQuery):
    """Handle admin message sending"""
    if not callback.message or not callback.from_user:
        return

    admin_id = callback.from_user.id
    if not is_admin(admin_id):
        await callback.answer("❌ Unauthorized access!", show_alert=True)
        return

    # Get target user ID from callback data
    target_user_id = int(callback.data.replace("admin_message_", ""))

    # Set admin state for message input - PROTECT BROADCAST STATE
    if admin_id not in user_state:
        user_state[admin_id] = {"current_step": None, "data": {}}
    elif user_state[admin_id].get("protected") and is_admin(admin_id):
        print(f"🔒 PROTECTED: Admin {admin_id} in protected broadcast mode, cancelling message setup")
        await callback.answer("⚠️ Finish your current broadcast first!", show_alert=True)
        return

    user_state[admin_id]["current_step"] = f"admin_messaging_{target_user_id}"
    user_state[admin_id]["data"] = {"target_user_id": target_user_id}

    # Get user info for context
    user_info = users_data.get(target_user_id, {})
    user_name = user_info.get('full_name', 'Unknown')
    username = user_info.get('username', 'N/A')

    message_prompt = f"""
💬 <b>Send Message to Customer</b>

👤 <b>Target User:</b> {user_name} (@{username})
🆔 <b>User ID:</b> {target_user_id}

📝 <b>Type your message for the customer:</b>

💡 <b>Message will be sent directly to user</b>
⚠️ <b>Keep message professional and helpful</b>

🔙 <b>Send /cancel to go back</b>
"""

    await safe_edit_message(callback, message_prompt)
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_processing_"))
async def cb_admin_processing(callback: CallbackQuery):
    """Mark order as processing"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer("❌ Unauthorized access!", show_alert=True)
        return

    order_id = callback.data.replace("admin_processing_", "")

    # Get order details
    if order_id not in orders_data:
        await callback.answer("❌ Order not found!", show_alert=True)
        return

    order = orders_data[order_id]
    customer_id = order['user_id']
    customer_name = order['first_name']
    package_name = order['package_name']

    # Update order status
    orders_data[order_id]['status'] = 'processing'
    orders_data[order_id]['processing_started_at'] = datetime.now().isoformat()
    orders_data[order_id]['processing_by_admin'] = user_id

    # Send processing message to customer
    customer_message = f"""
🔄 <b>ORDER PROCESSING STARTED!</b>

⚡️ <b>Great news! Your order is now being processed.</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 <b>ORDER DETAILS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━

🆔 <b>Order ID:</b> <code>{order_id}</code>
📦 <b>Package:</b> {package_name}

🔄 <b>Status:</b> Processing Started
📅 <b>Started:</b> {datetime.now().strftime("%d %b %Y, %I:%M %p")}
⏰ <b>Expected Completion:</b> 0-6 hours

━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡️ <b>WHAT HAPPENS NEXT?</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>Our team is working on your order</b>
📈 <b>Service delivery will begin shortly</b>
🔔 <b>You'll get completion notification</b>
📊 <b>Track progress in Order History</b>

💙 <b>Thank you for your patience!</b>
"""

    customer_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📜 Track Order", callback_data="order_history"),
            InlineKeyboardButton(text="📞 Contact Support", url="https://t.me/tech_support_admin")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    try:
        await bot.send_message(
            chat_id=customer_id,
            text=customer_message,
            reply_markup=customer_keyboard,
            parse_mode="HTML"
        )

        # Update admin message
        admin_update = f"""
🔄 <b>ORDER MARKED AS PROCESSING!</b>

🆔 <b>Order ID:</b> <code>{order_id}</code>
👤 <b>Customer:</b> {customer_name}
📦 <b>Service:</b> {package_name}

✅ <b>Actions Completed:</b>
• Order status updated to "Processing"
• Customer notification sent
• Processing timestamp logged
• Order tracking activated

📊 <b>Processing Started:</b> {datetime.now().strftime("%d %b %Y, %I:%M %p")}

⚡️ <b>Order is now in active processing queue!</b>
"""

        await safe_edit_message(callback, admin_update)
        await callback.answer("🔄 Order marked as processing!")

    except Exception as e:
        print(f"Error marking order as processing: {e}")
        await callback.answer("❌ Error updating order!", show_alert=True)

# ========== END OF MAIN BOT HANDLERS ==========
# All account creation handlers moved to account_creation.py
# Payment handlers in payment_system.py
# Service handlers in services.py
# Webhook setup at end of file

# No more code here - moved to respective modules

# ========== REAL HANDLERS START AROUND LINE 2000+ ==========
# All handlers are properly organized at the end of this file

# Jumping to clean handler section...

# All duplicate account creation code successfully removed!
# Real handlers are properly organized starting from line 418

# ========== START OF ACTUAL BOT HANDLERS ==========
# (Handlers properly organized starting from line 418)

# ========== BOT INITIALIZATION COMPLETE ==========

# All cleanup done! Bot ready to run.

# Account creation functionality successfully moved to account_creation.py
# Bot handlers properly organized below

# ========== FSM MESSAGE HANDLERS ==========
@dp.message(OrderStates.waiting_link)
async def on_link_input(message: Message, state: FSMContext):
    """Handle link input in FSM waiting_link state"""
    print(f"🎯 FSM HANDLER: Processing link input for user {message.from_user.id if message.from_user else 'Unknown'}")
    print(f"🎯 FSM HANDLER: Received link: {message.text}")
    await handle_link_input(message, state)

@dp.message(OrderStates.waiting_quantity)
async def on_quantity_input(message: Message, state: FSMContext):
    """Handle quantity input in FSM waiting_quantity state"""
    await handle_quantity_input(message, state)

@dp.message(OrderStates.waiting_coupon)
async def on_coupon_input(message: Message, state: FSMContext):
    """Handle coupon input in FSM waiting_coupon state"""
    await handle_coupon_input(message, state)

# ========== NEW OFFER ORDER FSM HANDLERS ==========
@dp.message(OfferOrderStates.getting_link)
async def on_offer_link_input(message: Message, state: FSMContext):
    """Handle link input for OfferOrderStates.getting_link state"""
    from fsm_handlers import handle_offer_link_input
    await handle_offer_link_input(message, state)

@dp.message(OfferOrderStates.getting_quantity)
async def on_offer_quantity_input(message: Message, state: FSMContext):
    """Handle quantity input for OfferOrderStates.getting_quantity state"""
    from fsm_handlers import handle_offer_quantity_input
    await handle_offer_quantity_input(message, state)

@dp.message(OfferOrderStates.waiting_screenshot)
async def on_offer_screenshot_input(message: Message, state: FSMContext):
    """Handle any input for OfferOrderStates.waiting_screenshot state (photo validation inside handler)"""
    from fsm_handlers import handle_offer_screenshot
    await handle_offer_screenshot(message, state)

@dp.callback_query(F.data.in_(["offer_process_order_final_btn", "offer_cancel_order_final_btn"]))
async def on_offer_confirmation(callback: CallbackQuery, state: FSMContext):
    """Handle offer order confirmation callbacks"""
    print(f"🔥 OFFER CONFIRMATION: User {callback.from_user.id if callback.from_user else 'Unknown'} clicked: {callback.data}")

    # Import and call the handler
    from fsm_handlers import handle_offer_confirmation
    await handle_offer_confirmation(callback, state)

@dp.callback_query(F.data == "offer_direct_payment_btn")
async def on_offer_direct_payment(callback: CallbackQuery, state: FSMContext):
    """Handle offer direct payment callback"""
    print(f"💳 OFFER DIRECT PAYMENT: User {callback.from_user.id if callback.from_user else 'Unknown'} clicked direct payment")

    # Import and call the handler
    from fsm_handlers import handle_offer_direct_payment
    await handle_offer_direct_payment(callback, state)

@dp.callback_query(F.data == "offer_add_fund_btn")
async def on_offer_add_fund(callback: CallbackQuery, state: FSMContext):
    """Handle offer add fund callback"""
    print(f"💰 OFFER ADD FUND: User {callback.from_user.id if callback.from_user else 'Unknown'} clicked add fund")

    # Import and call the handler
    from fsm_handlers import handle_offer_add_fund
    await handle_offer_add_fund(callback, state)

@dp.message(AdminCreateUserStates.waiting_for_token)
async def on_admin_token_input(message: Message, state: FSMContext):
    """Handle admin token input for creating user accounts"""
    if not message.from_user or not message.text:
        await state.clear()
        return

    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("❌ Unauthorized access!")
        await state.clear()
        return

    access_token = message.text.strip()
    
    # Get target user ID from FSM state
    data = await state.get_data()
    target_user_id_raw = data.get('target_user_id')
    
    if not target_user_id_raw:
        await message.answer("❌ Target user ID not found! Please start over.")
        await state.clear()
        return
    
    # Fix critical bug: Ensure target_user_id is integer to match users_data keys
    try:
        target_user_id = int(target_user_id_raw)
    except (ValueError, TypeError):
        await message.answer("❌ Invalid target user ID format! Please start over.")
        await state.clear()
        return

    try:
        # Import and use decode_token function
        from account_creation import decode_token
        
        # Decode the token to get user data
        decoded_result = decode_token(access_token)
        
        if not decoded_result.get('success', False):
            error_msg = decoded_result.get('error', 'Invalid token format')
            await message.answer(f"❌ <b>Token Decoding Failed</b>\n\n{error_msg}\n\n🔄 Please check the token and try again.")
            return
        
        # Extract decoded user data
        full_name = decoded_result.get('username', '')
        phone_number = decoded_result.get('phone', '')
        email = decoded_result.get('email', '')
        
        if not all([full_name, phone_number, email]):
            await message.answer("❌ <b>Incomplete User Data</b>\n\nDecoded token is missing required information (name, phone, or email).")
            return
        
        # Update user record in users_data
        if target_user_id not in users_data:
            # Create new user record if it doesn't exist
            users_data[target_user_id] = {
                'user_id': target_user_id,
                'username': '',
                'first_name': '',
                'balance': 0.0,
                'total_spent': 0.0,
                'orders_count': 0,
                'join_date': datetime.now().isoformat(),
                'status': 'active'
            }
        
        # Update with decoded information
        users_data[target_user_id].update({
            'full_name': full_name,
            'phone_number': phone_number,
            'email': email,
            'access_token': access_token,
            'account_created': True,
            'status': 'active'
        })
        
        # Save to users.json file
        save_users_data()
        
        # Clear FSM state
        await state.clear()
        
        # Send success message to admin
        success_text = f"""
✅ <b>USER ACCOUNT CREATED SUCCESSFULLY!</b>

👤 <b>Account Details:</b>
• <b>User ID:</b> <code>{target_user_id}</code>
• <b>Full Name:</b> {full_name}
• <b>Phone:</b> <tg-spoiler>{phone_number}</tg-spoiler>
• <b>Email:</b> <tg-spoiler>{email}</tg-spoiler>

📊 <b>Account Status:</b> ✅ Active & Complete

💡 <b>The user can now:</b>
• Access all premium features
• Place orders and make payments  
• Use their account normally

🎉 <b>Account creation completed via token!</b>
"""
        
        await message.answer(success_text, parse_mode="HTML")
        print(f"✅ ADMIN_CREATE_TOKEN: Admin {user_id} successfully created account for user {target_user_id}")
        
    except Exception as e:
        print(f"❌ ADMIN_CREATE_TOKEN: Error processing token: {str(e)}")
        await message.answer(f"❌ <b>Error Processing Token</b>\n\nUnexpected error occurred: {str(e)}\n\n🔄 Please try again or contact support.")
        await state.clear()

@dp.message(AdminDirectMessageStates.waiting_for_message)
async def on_admin_message_input(message: Message, state: FSMContext):
    """Handle admin message input for sending direct messages to users"""
    if not message.from_user or not message.text:
        await state.clear()
        return

    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("❌ Unauthorized access!")
        await state.clear()
        return

    admin_message = message.text
    
    # Get target user ID from FSM state
    data = await state.get_data()
    target_user_id_raw = data.get('target_user_id')
    
    if not target_user_id_raw:
        await message.answer("❌ Target user ID not found! Please start over.")
        await state.clear()
        return
    
    # Ensure target_user_id is integer
    try:
        target_user_id = int(target_user_id_raw)
    except (ValueError, TypeError):
        await message.answer("❌ Invalid target user ID format! Please start over.")
        await state.clear()
        return

    try:
        # Send the message exactly as the admin typed it - no extra formatting
        await bot.send_message(chat_id=target_user_id, text=admin_message, parse_mode=None, disable_web_page_preview=True)
        
        # Clear FSM state
        await state.clear()
        
        # Send success confirmation to admin
        await message.answer("✅ Message sent successfully!")
        print(f"✅ ADMIN_MESSAGE: Admin {user_id} sent message to user {target_user_id}")
        
    except Exception as e:
        print(f"❌ ADMIN_MESSAGE: Error sending message: {str(e)}")
        await message.answer(f"❌ <b>Error Sending Message</b>\n\nFailed to send message: {str(e)}\n\n🔄 Please try again.")
        await state.clear()

# ========== INPUT HANDLERS ==========
@dp.message(F.text)
async def handle_text_input_wrapper(message: Message, state: FSMContext):
    """Wrapper for text input handler - first check account creation, then other handlers"""
    if not message.from_user:
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        mark_user_for_notification(message.from_user.id)
        return

    user_id = message.from_user.id

    # PRIORITY CHECK: If user is in FSM state, let FSM handlers process it
    fsm_state = await state.get_state()
    if fsm_state:
        print(f"🔍 FSM DEBUG: User {user_id} is in FSM state: {fsm_state} - skipping generic handler")
        return  # Let dedicated FSM handlers handle this

    # Check if user is in account creation flow (legacy user_state)
    current_step = user_state.get(user_id, {}).get("current_step")

    print(f"🔍 TEXT DEBUG: User {user_id} sent text: '{message.text[:50]}...'")
    print(f"🔍 TEXT DEBUG: User {user_id} current_step: {current_step}")
    print(f"🔍 FSM DEBUG: User {user_id} FSM state: {fsm_state}")

    # PRIORITY: Check for admin broadcast and messaging first
    from services import handle_admin_broadcast_message, is_admin
    if is_admin(user_id):
        print(f"🔍 ADMIN CHECK: User {user_id} is admin, current_step: {current_step}")
        if current_step == "admin_broadcast_message":
            print(f"📢 Processing admin broadcast message from {user_id}")
            await handle_admin_broadcast_message(message, user_id)
            return
        elif current_step and current_step.startswith("admin_messaging_"):
            # Handle admin direct messaging to specific user
            target_user_id = int(current_step.replace("admin_messaging_", ""))
            print(f"💬 Processing admin direct message from {user_id} to user {target_user_id}")
            from text_input_handler import handle_admin_direct_message
            await handle_admin_direct_message(message, user_id, target_user_id)
            return

    # Account creation steps that should be handled by account_creation.py
    account_creation_steps = ["waiting_login_phone", "waiting_custom_name", "waiting_manual_phone", "waiting_email", "waiting_access_token", "waiting_contact_permission"]

    if current_step in account_creation_steps:
        print(f"🔄 Passing to account_creation.py for user {user_id}")
        # Let account_creation.py handle this
        from account_creation import handle_text_input
        await handle_text_input(message)
        return

    # Otherwise use regular text input handler
    await text_input_handler.handle_text_input(
        message, users_data, order_temp, tickets_data,
        is_message_old, mark_user_for_notification, is_account_created,
        format_currency, get_main_menu, OWNER_USERNAME
    )

# ========== PHOTO HANDLERS ==========
@dp.message(F.photo)
async def handle_photo_input(message: Message):
    """Handle photo input for profile picture updates"""
    if not message.from_user:
        return

    user_id = message.from_user.id
    current_step = user_state.get(user_id, {}).get("current_step")

    if current_step == "editing_photo":
        # Handle profile photo update
        if not message.photo:
            await message.answer("⚠️ Please send a valid photo!")
            return

        # Get the largest photo size
        if len(message.photo) > 0:
            photo = message.photo[-1]
            file_id = photo.file_id
        else:
            await message.answer("⚠️ No valid photo sizes found!")
            return

        # Store photo file_id in user data
        users_data[user_id]['profile_photo'] = file_id
        user_state[user_id]["current_step"] = None

        # Save updated user data to persistent storage
        save_data_to_json(users_data, "users.json")

        text = """
✅ <b>Profile Photo Updated Successfully!</b>

📸 <b>आपकी profile photo update हो गयी!</b>

💡 <b>New photo अब आपके account में visible है</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Continue Editing", callback_data="edit_profile"),
                InlineKeyboardButton(text="👀 Preview Profile", callback_data="preview_profile")
            ],
            [
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
            ]
        ])

        await message.answer(text, reply_markup=keyboard)

    elif current_step == "waiting_screenshot_upload":
        # This is for payment screenshot upload
        order_data = user_state.get(user_id, {}).get("data", {})
        transaction_id = order_data.get("transaction_id")

        if not transaction_id:
            await message.answer("⚠️ Could not find transaction details. Please try again.")
            return

        # Store the screenshot file_id
        if message.photo and len(message.photo) > 0:
            user_state[user_id]["data"]["screenshot_file_id"] = message.photo[-1].file_id
        else:
            await message.answer("⚠️ Could not process screenshot. Please upload a valid image.")
            return

        # Send admin notification
        await send_admin_notification(order_data)

        # Send success message with improved buttons including Copy Order ID
        success_text = f"""
🎉 <b>Order Successfully Placed!</b>

✅ <b>Payment Screenshot Verified Successfully!</b>

🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>
📅 <b>Uploaded At:</b> {datetime.now().strftime("%d %b %Y, %I:%M %p")}

🎉 <b>Your payment is being verified. You'll get confirmation soon!</b>
💡 <b>You can check order status in Order History</b>
"""

        success_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Copy Transaction ID", callback_data=f"copy_transaction_id_{transaction_id}"),
                InlineKeyboardButton(text="📜 Order History", callback_data="order_history")
            ],
            [
                InlineKeyboardButton(text="🚀 Place New Order", callback_data="new_order"),
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
            ]
        ])

        user_state[user_id]["current_step"] = None
        user_state[user_id]["data"] = {} # Clear order data after successful upload

        await safe_edit_message(callback if isinstance(callback, CallbackQuery) else message, success_text, success_keyboard) # type: ignore
        await message.answer("✅ Screenshot uploaded successfully. Your payment is being verified.") # Reply to message for clarity

    else:
        # Photo sent but user not in relevant mode - IGNORE completely
        print(f"🔇 IGNORED: Unexpected photo from user {user_id}")
        return


# ========== CONTACT INPUT HANDLER ==========
@dp.message(F.contact)
async def handle_contact_input(message: Message):
    """Handle contact sharing for account creation"""
    print(f"📞 Main.py: Contact received from user {message.from_user.id if message.from_user else 'Unknown'}")

    if not message.from_user or not message.contact:
        print("❌ Main.py: No user or contact found")
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        mark_user_for_notification(message.from_user.id)
        return

    # Let account_creation.py handle all contact processing
    from account_creation import handle_contact_sharing
    await handle_contact_sharing(message)


# FSM handlers moved above to line 3988 - duplicates removed

# ========== STARTUP FUNCTIONS ==========
async def on_startup():
    """Initialize bot on startup"""
    print("🚀 India Social Panel Bot starting...")

    # Load persistent data from JSON files
    global users_data, orders_data, tickets_data
    print("📂 Loading persistent data...")

    # Load users data with proper key conversion
    users_data.update(load_users_data_from_json())

    # Load orders data
    loaded_orders = load_data_from_json("orders.json")
    if loaded_orders:
        orders_data.update(loaded_orders)

    # Load tickets data
    loaded_tickets = load_data_from_json("tickets.json")
    if loaded_tickets:
        tickets_data.update(loaded_tickets)

    print(f"📊 Loaded {len(users_data)} users, {len(orders_data)} orders, {len(tickets_data)} tickets")

    # Initialize all handlers now that dp is available
    print("🔄 Initializing account handlers...")
    account_handlers.init_account_handlers(
        dp, users_data, orders_data, require_account,
        format_currency, format_time, is_account_created, user_state, is_admin, safe_edit_message
    )

    print("🔄 Initializing account creation handlers...")
    account_creation.init_account_creation_handlers(
        dp, users_data, user_state, safe_edit_message, init_user,
        mark_user_for_notification, is_message_old, bot, START_TIME, send_token_notification_to_admin, save_users_data
    )

    print("✅ Account creation initialization complete")

    print("🔄 Initializing payment system...")
    payment_system.register_payment_handlers(dp, users_data, user_state, format_currency)

    print("🔄 Initializing service system...")
    services.register_service_handlers(dp, require_account)

    # Set bot commands - Enhanced professional menu with detailed descriptions
    commands = [
        BotCommand(command="start", description="🚀 Launch Dashboard & Access All Features"),
        BotCommand(command="menu", description="🏠 Main Menu - Complete Service Portal"),
        BotCommand(command="help", description="❓ Help Guide & Customer Support Center"),
        BotCommand(command="about", description="ℹ️ About India's #1 SMM Growth Platform"),
        BotCommand(command="account", description="👤 My Account Dashboard & Profile Settings"),
        BotCommand(command="balance", description="💰 Check Balance & Add Funds Instantly"),
        BotCommand(command="orders", description="📦 Order History & Live Tracking System"),
        BotCommand(command="services", description="📈 Browse All SMM Services & Pricing"),
        BotCommand(command="support", description="🎫 Customer Support & Live Chat Help"),
        BotCommand(command="offers", description="🎁 Special Deals & Exclusive Discounts"),
        BotCommand(command="referral", description="🤝 Refer Friends & Earn Instant Rewards"),
        BotCommand(command="api", description="🔧 API Access & Developer Integration"),
        BotCommand(command="status", description="⚡ Bot Status & Service Health Check"),
        BotCommand(command="contact", description="📞 Contact Owner & Business Inquiries"),
        BotCommand(command="language", description="🌐 Change Language & Regional Settings"),
        BotCommand(command="notifications", description="🔔 Manage Alerts & Push Notifications"),
        BotCommand(command="premium", description="👑 Premium Features & VIP Membership"),
        BotCommand(command="analytics", description="📊 Account Analytics & Growth Statistics"),
        BotCommand(command="feedback", description="⭐ Rate Our Service & Share Experience"),
        BotCommand(command="description", description="📋 Package Details During Order Process")
    ]
    await bot.set_my_commands(commands)
    print("✅ Bot commands set successfully")

    # Clear old webhook if exists
    await bot.delete_webhook(drop_pending_updates=True)
    print("🗑️ Cleared previous webhook")

    if WEBHOOK_MODE:
        # Set webhook for production
        webhook_url = f"{WEBHOOK_URL}"
        print(f"🔗 Setting webhook URL: {webhook_url}")

        try:
            await bot.set_webhook(
                url=webhook_url,
                secret_token=WEBHOOK_SECRET,
                allowed_updates=["message", "callback_query", "inline_query"]
            )
            print(f"✅ Webhook set successfully: {webhook_url}")

            # Test webhook
            webhook_info = await bot.get_webhook_info()
            print(f"📋 Webhook info: {webhook_info}")
            if webhook_info.url:
                print("✅ Webhook verification successful")
            else:
                print("❌ Webhook verification failed")
        except Exception as e:
            print(f"❌ Webhook setup failed: {e}")
            print("🔄 Trying to continue anyway...")

# ========== WEBHOOK SETUP ==========

async def health_check(request):
    """Health check endpoint to show bot is alive"""
    return web.Response(
        text="✅ I'm alive! India Social Panel Bot is running successfully.\n\n🤖 All systems operational\n📱 Ready to serve users\n🔄 Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        content_type="text/plain"
    )

async def main():
    """Main function to start the bot with webhook"""
    await on_startup()

    if WEBHOOK_MODE:
        # Webhook mode for deployment
        app = Application()

        # Add health check route - shows "I'm alive" instead of 404
        app.router.add_get('/', health_check)
        app.router.add_get('/health', health_check)
        app.router.add_get('/status', health_check)

        # Set the dispatcher for webhook handler
        # Note: _dispatcher is internal attribute but needed for webhook functionality
        webhook_requests_handler._dispatcher = dp  # type: ignore

        # Register webhook handler with app
        webhook_requests_handler.register(app, path=WEBHOOK_PATH)

        # Mount dispatcher on app and start web server
        setup_application(app, dp, bot=bot)

        # Use AppRunner for async context
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
        await site.start()
        print(f"✅ Webhook server started on {WEB_SERVER_HOST}:{WEB_SERVER_PORT}")

        # Keep running
        await asyncio.Event().wait()
    else:
        # Polling mode for local development
        print("✅ India Social Panel Bot started in polling mode")
        asyncio.run(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))


if __name__ == "__main__":
    """Entry point - exactly like working bot"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
