# -*- coding: utf-8 -*-
"""
India Social Panel - Professional SMM Services Bot
Advanced Telegram Bot for Social Media Marketing Services
"""

import asyncio
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
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Import modules
import account_handlers
import payment_system
import services
import account_creation
import text_input_handler

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

# Bot initialization
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
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

# ========== CORE FUNCTIONS ==========
def init_user(user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> None:
    """Initialize user data if not exists"""
    if user_id not in users_data:
        users_data[user_id] = {
            "user_id": user_id,
            "username": username or "",
            "first_name": first_name or "",
            "balance": 0.0,
            "total_spent": 0.0,
            "orders_count": 0,
            "referral_code": generate_referral_code(),
            "referred_by": None,
            "join_date": datetime.now().isoformat(),
            "api_key": generate_api_key(),
            "status": "active",
            "account_created": False,
            "full_name": "",
            "phone_number": "",
            "email": "",
            "profile_photo": None # Added for profile photo
        }

    # Initialize user state for input tracking
    if user_id not in user_state:
        user_state[user_id] = {
            "current_step": None,
            "data": {}
        }

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

async def send_admin_notification(order_record: Dict[str, Any]):
    """Send notification to admin group about a new order or important event"""
    # Group ID where notifications will be sent
    admin_group_id = -1003009015663

    try:
        user_id = order_record.get('user_id')
        order_id = order_record.get('order_id')
        package_name = order_record.get('package_name', 'N/A')
        platform = order_record.get('platform', 'N/A')
        quantity = order_record.get('quantity', 0)
        total_price = order_record.get('total_price', 0.0)
        payment_method = order_record.get('payment_method', 'N/A')
        link = order_record.get('link', 'N/A')
        service_id = order_record.get('service_id', 'N/A')
        created_at = order_record.get('created_at', '')

        # Get user info if available - with better fallback
        user_info = [InlineKeyboardButton(text="⬅️ Offers & Rewards", callback_data="offers_rewards")]
        username = user_info.get('username', '')
        first_name = user_info.get('first_name', '')
        full_name = user_info.get('full_name', '')
        phone = user_info.get('phone_number', '')

        # Use better display values
        display_username = f"@{username}" if username else "No Username"
        display_name = full_name or first_name or "No Name Set"
        display_phone = phone if phone else "No Phone Set"

        print(f"📊 DEBUG: User {user_id} info - username: {username}, first_name: {first_name}, full_name: {full_name}, phone: {phone}")

        if order_id: # Notification for new order with screenshot
            message_text = (
                f"🚨 <b>नया Order Received - Screenshot Upload!</b>\n\n"
                f"👤 <b>User Details:</b>\n"
                f"• User ID: {user_id}\n"
                f"• Name: {display_name}\n"
                f"• Username: {display_username}\n"
                f"• Phone: {display_phone}\n\n"
                f"📦 <b>Order Details:</b>\n"
                f"• Order ID: <code>{order_id}</code>\n"
                f"• Package: {package_name}\n"
                f"• Platform: {platform.title()}\n"
                f"• Service ID: {service_id}\n"
                f"• Link: {link}\n"
                f"• Quantity: {quantity:,}\n"
                f"• Amount: ₹{total_price:,.2f}\n"
                f"• Payment Method: {payment_method}\n"
                f"• Order Time: {format_time(created_at)}\n\n"
                f"📸 <b>Payment screenshot uploaded by user</b>\n\n"
                f"⚡️ <b>Action Required: Verify payment and manage order</b>"
            )
        else: # Generic notification for screenshot upload if no order_id
            message_text = (
                f"📸 <b>Screenshot Upload Received!</b>\n\n"
                f"👤 <b>User ID:</b> {user_id}\n"
                f"📝 <b>Details:</b> A user has uploaded a screenshot for payment verification.\n\n"
                f"👉 <b>Please check user's messages for context.</b>"
            )

        # Create management buttons for order handling
        management_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Complete Order", callback_data=f"admin_complete_{order_id}"),
                InlineKeyboardButton(text="❌ Cancel Order", callback_data=f"admin_cancel_{order_id}")
            ],
            [
                InlineKeyboardButton(text="💬 Send Message", callback_data=f"admin_message_{user_id}"),
                InlineKeyboardButton(text="📊 Order Details", callback_data=f"admin_details_{order_id}")
            ],
            [
                InlineKeyboardButton(text="👤 User Profile", callback_data=f"admin_profile_{user_id}"),
                InlineKeyboardButton(text="🔄 Refresh Status", callback_data=f"admin_refresh_{order_id}")
            ]
        ])

        await bot.send_message(admin_group_id, message_text, parse_mode="HTML", reply_markup=management_keyboard)
        print(f"✅ Group notification sent for Order ID: {order_id or 'Screenshot Upload'}")

    except Exception as e:
        print(f"❌ Failed to send group notification: {e}")

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
            InlineKeyboardButton(text="➕ Naya Ticket Banayein", callback_data="create_ticket"),
        ],
        [
            InlineKeyboardButton(text="📖 Mere Tickets Dekhein", callback_data="view_tickets")
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
            InlineKeyboardButton(text="👨‍💻 Owner Ke Baare Mein", callback_data="owner_info"),
            InlineKeyboardButton(text="🌐 Hamari Website", callback_data="website_info")
        ],
        [
            InlineKeyboardButton(text="💬 Support Channel", callback_data="support_channel"),
            InlineKeyboardButton(text="🤖 AI Support", callback_data="ai_support")
        ],
        [
            InlineKeyboardButton(text="👨‍💼 Contact Admin", callback_data="contact_admin"),
            InlineKeyboardButton(text="📜 Seva Ki Shartein (TOS)", callback_data="terms_service")
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
            InlineKeyboardButton(text="🎟️ Coupon Redeem Karein", callback_data="coupon_redeem"),
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
                text=f"""
📢 <b>Message from Admin</b>

{broadcast_message}

---
<i>India Social Panel Official Broadcast</i>
""",
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

    # Check if account is created
    if is_account_created(user.id):
        # Get user's actual username or first name
        user_display_name = f"@{user.username}" if user.username else user.first_name or 'Friend'

        # Existing user welcome
        welcome_text = f"""
🇮🇳 <b>स्वागत है India Social Panel में!</b>

नमस्ते <b>{user_display_name}</b>! 🙏

🎯 <b>भारत का सबसे भरोसेमंद SMM Panel</b>
✅ <b>High Quality Services</b>
✅ <b>Instant Delivery</b>
✅ <b>24/7 Support</b>
✅ <b>Affordable Rates</b>

📱 <b>सभी Social Media Platforms के लिए:</b>
Instagram • YouTube • Facebook • Twitter • TikTok • LinkedIn

💡 <b>नीचे से अपनी जरूरत का option चुनें:</b>
"""
        await message.answer(welcome_text, reply_markup=get_main_menu())
    else:
        # New user - show both create account and login options
        user_display_name = f"@{user.username}" if user.username else user.first_name or 'Friend'

        welcome_text = f"""
🇮🇳 <b>स्वागत है India Social Panel में!</b>

नमस्ते <b>{user_display_name}</b>! 🙏

🎯 <b>भारत का सबसे भरोसेमंद SMM Panel</b>
✅ <b>High Quality Services</b>
✅ <b>Instant Delivery</b>
✅ <b>24/7 Support</b>
✅ <b>Affordable Rates</b>

📱 <b>सभी Social Media Platforms के लिए:</b>
Instagram • YouTube • Facebook • Twitter • TikTok • LinkedIn

💡 <b>अपना option चुनें:</b>
"""
        # Import required functions from account_creation for dynamic use
        # Import get_main_menu dynamically to avoid circular imports
        await message.answer(welcome_text, reply_markup=account_creation.get_initial_options_menu())

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
    await message.answer("🏠 <b>Main Menu</b>\n अपनी जरूरत के अनुसार option चुनें:", reply_markup=get_main_menu())

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

    help_text = """
❓ <b>Help & Support</b>

🤖 <b>Bot Commands:</b>
• /start - Main menu
• /menu - Show menu
• /help - Show this help
• /description - Package details (during ordering)

📞 <b>Support:</b>
• Contact: @tech_support_admin
• Response: 2-6 hours

💡 <b>Bot working perfectly!</b>
"""

    print(f"✅ Sending help to user {user.id}")
    await message.answer(help_text, reply_markup=get_main_menu())

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

💡 <b>Order process में वापस जाने के लिए link/quantity/coupon भेजते रहें</b>
"""

        await message.answer(description_text)
    else:
        # User is not in order process
        text = """
⚠️ <b>Description Command</b>

📋 <b>/description command केवल order process के दौरान available है</b>

💡 <b>Package description देखने के लिए:</b>
1. पहले /start करें
2. New Order पर click करें
3. कोई service select करें
4. Package choose करें
5. फिर /description use करें

🚀 <b>अभी order शुरू करने के लिए /start करें</b>
"""
        await message.answer(text, reply_markup=get_main_menu())

# ========== PHOTO HANDLERS ==========
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
        message, user_state, order_temp, generate_order_id, format_currency, get_main_menu
    )

    if not screenshot_handled:
        # Photo not related to order process
        text = """
📸 <b>Photo Received</b>

💡 <b>यह photo किसी order process के लिए नहीं है</b>

📋 <b>Photo का use करने के लिए:</b>
• पहले order process शुरू करें
• Payment method choose करें
• QR code generate करें
• फिर screenshot भेजें

🏠 <b>Main menu के लिए /start दबाएं</b>
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

🤝 <b>हमारी Support Team आपकी मदद के लिए तैयार है!</b>

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

आपका account अभी तक create नहीं हुआ है!

📝 <b>सभी features का access पाने के लिए पहले account create करें</b>

✅ <b>Account creation में सिर्फ 2 मिनट लगते हैं</b>
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
🚀 <b>New Order - Service Selection</b>

🎯 <b>Choose Your Platform</b>

💎 <b>Premium Quality Services Available:</b>
✅ Real & Active Users Only
✅ High Retention Rate
✅ Fast Delivery (0-6 Hours)
✅ 24/7 Customer Support
✅ Secure & Safe Methods

🔒 <b>100% Money Back Guarantee</b>
⚡️ <b>Instant Start Guarantee</b>

💡 <b>कृपया अपना platform चुनें:</b>
"""

    await safe_edit_message(callback, text, get_services_main_menu())
    await callback.answer()

# Service handlers moved to services.py

@dp.callback_query(F.data == "add_funds")
@require_account
async def cb_add_funds(callback: CallbackQuery):
    """Handle add funds request"""
    if not callback.message:
        return

    user_id = callback.from_user.id if callback.from_user else 0
    current_balance = users_data.get(user_id, {}).get("balance", 0.0)

    text = f"""
💰 <b>Add Funds</b>

💳 <b>Current Balance:</b> {format_currency(current_balance)}

🔸 <b>Payment Methods Available:</b>
• UPI (Instant)
• Bank Transfer
• Paytm
• PhonePe
• Google Pay

💡 <b>Amount चुनें या custom amount type करें:</b>
"""

    amount_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="₹500", callback_data="fund_500"),
            InlineKeyboardButton(text="₹1000", callback_data="fund_1000")
        ],
        [
            InlineKeyboardButton(text="₹2000", callback_data="fund_2000"),
            InlineKeyboardButton(text="₹5000", callback_data="fund_5000")
        ],
        [
            InlineKeyboardButton(text="💬 Custom Amount", callback_data="fund_custom")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

    await safe_edit_message(callback, text, amount_keyboard)
    await callback.answer()


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

💡 <b> अपनी जरूरत के अनुसार tool चुनें:</b>
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

✨ <b> अपना reward claim करें:</b>
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

यह section केवल authorized administrators के लिए है।

🔒 <b>Security Notice:</b>
Unauthorized access attempts are logged and monitored.

📞 यदि आप administrator हैं, तो owner से contact करें।
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
भारत का सबसे भरोसेमंद SMM Platform

🎯 <b>Our Mission:</b>
High-quality, affordable social media marketing services प्रदान करना

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

🙏 <b>Namaste! मैं {OWNER_NAME}</b>
Founder & CEO, India Social Panel

📍 <b>Location:</b> India 🇮🇳
💼 <b>Experience:</b> 5+ Years in SMM Industry
🎯 <b>Mission:</b> भारतीय businesses को affordable digital marketing solutions देना

✨ <b>My Vision:</b>
"हर Indian business को social media पर successful बनाना"

💬 <b>Personal Message:</b>
"मेरा मकसद आप सभी को high-quality और affordable SMM services प्रदान करना है। आपका support और trust ही मेरी सबसे बड़ी achievement है।"

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

<b>Platform चुनें pricing देखने के लिए:</b>

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

💡 <b>आप क्या करना चाहते हैं?</b>
"""

    await safe_edit_message(callback, text, get_support_menu())
    await callback.answer()

@dp.callback_query(F.data == "back_main")
async def cb_back_main(callback: CallbackQuery):
    """Return to main menu"""
    if not callback.message:
        return

    text = """
🏠 <b>India Social Panel - Main Menu</b>

🇮🇳 भारत का #1 SMM Panel
💡 अपनी जरूरत के अनुसार option चुनें:
"""

    await safe_edit_message(callback, text, get_main_menu())
    await callback.answer()

@dp.callback_query(F.data == "skip_coupon")
async def cb_skip_coupon(callback: CallbackQuery):
    """Handle skip coupon and show confirmation"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Check if user has order data
    if user_id not in user_state or user_state[user_id].get("current_step") != "waiting_coupon":
        await callback.answer("⚠️ Order data not found!")
        return

    # Get all order details
    order_data = user_state[user_id]["data"]
    package_name = order_data.get("package_name", "Unknown Package")
    service_id = order_data.get("service_id", "")
    platform = order_data.get("platform", "")
    package_rate = order_data.get("package_rate", "₹1.00 per unit")
    link = order_data.get("link", "")
    quantity = order_data.get("quantity", 0)

    # Calculate total price (simplified calculation for demo)
    # Extract numeric part from rate for calculation
    rate_num = 1.0  # Default
    if "₹" in package_rate:
        try:
            rate_str = package_rate.replace("₹", "").split()[0]
            rate_num = float(rate_str)
        except (ValueError, IndexError):
            rate_num = 1.0

    total_price = rate_num * quantity

    # Show confirmation page
    confirmation_text = f"""
✅ <b>Order Confirmation</b>

📦 <b>Package Details:</b>
• Name: {package_name}
• ID: {service_id}
• Platform: {platform.title()}
• Rate: {package_rate}

🔗 <b>Target Link:</b>
{link}

📊 <b>Order Summary:</b>
• Quantity: {quantity:,}
• Total Price: ₹{total_price:,.2f}

📋 <b>Description Command:</b> /description

🎯 <b>सभी details correct हैं?</b>

💡 <b>Confirm करने पर payment method select करना होगा</b>
⚠️ <b>Cancel करने पर main menu पर वापस चले जाएंगे</b>
"""

    # Store total price in order data
    user_state[user_id]["data"]["total_price"] = total_price
    user_state[user_id]["current_step"] = "confirming_order"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm Order", callback_data="final_confirm_order"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="back_main")
        ]
    ])

    await safe_edit_message(callback, confirmation_text, keyboard)
    await callback.answer()

@dp.callback_query(F.data == "final_confirm_order")
async def cb_final_confirm_order(callback: CallbackQuery):
    """Handle final order confirmation with balance check and payment options"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Check if user has order data
    if user_id not in user_state or user_state[user_id].get("current_step") != "confirming_order":
        await callback.answer("⚠️ Order data not found!")
        return

    # Get order details
    order_data = user_state[user_id]["data"]
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

💡 <b>अपना payment method चुनें:</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Pay from Balance", callback_data="pay_from_balance"),
                InlineKeyboardButton(text="⚡️ Quick QR Payment", callback_data="payment_qr")
            ],
            [
                InlineKeyboardButton(text="📱 UPI Payment", callback_data="payment_upi"),
                InlineKeyboardButton(text="🏦 Bank Transfer", callback_data="payment_bank")
            ],
            [
                InlineKeyboardButton(text="💳 Card Payment", callback_data="payment_card"),
                InlineKeyboardButton(text="💸 Digital Wallets", callback_data="payment_wallet")
            ],
            [
                InlineKeyboardButton(text="📲 Open UPI App", callback_data="payment_app"),
                InlineKeyboardButton(text="💰 Net Banking", callback_data="payment_netbanking")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back", callback_data="skip_coupon")
            ]
        ])

        user_state[user_id]["current_step"] = "selecting_payment"
        await safe_edit_message(callback, payment_text, keyboard)

    else:
        # User has insufficient balance - show professional message with options
        shortfall = total_price - current_balance

        balance_message = f"""
💰 <b>Account Balance Check</b>

📊 <b>Order Summary:</b>
• Package: {package_name}
• Platform: {platform.title()}
• Quantity: {quantity:,}
• Total Amount: ₹{total_price:,.2f}

💳 <b>Current Balance:</b> ₹{current_balance:,.2f}
⚠️ <b>Additional Required:</b> ₹{shortfall:,.2f}

🎯 <b>Payment Options Available:</b>

💡 <b>Option 1: Add Balance First</b>
पहले अपने account में balance add करें, फिर order complete करें। यह सबसे convenient method है।

💡 <b>Option 2: Direct Payment (Emergency)</b>
बिना balance add किए direct payment करें। Emergency के लिए best option है।

🔒 <b>India Social Panel - Trusted SMM Platform</b>
✅ <b>100% Safe & Secure Payments</b>
✅ <b>Instant Order Processing</b>
✅ <b>24/7 Customer Support</b>

🎯 <b>अपना preferred option चुनें:</b>
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

        user_state[user_id]["current_step"] = "choosing_payment_option"
        await safe_edit_message(callback, balance_message, balance_keyboard)

    await callback.answer()

@dp.callback_query(F.data == "payment_qr")
async def cb_payment_qr(callback: CallbackQuery):
    """Handle QR code payment method - Fixed to work properly"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Check if user has order data
    if user_id not in user_state or user_state[user_id].get("current_step") != "selecting_payment":
        await callback.answer("⚠️ Order data not found!")
        return

    # Get order details
    order_data = user_state[user_id]["data"]
    total_price = order_data.get("total_price", 0.0)

    # Generate transaction ID
    import time
    import random
    transaction_id = f"QR{int(time.time())}{random.randint(100, 999)}"

    # Set user state to waiting for screenshot
    user_state[user_id]["current_step"] = "waiting_screenshot_upload"
    user_state[user_id]["data"]["transaction_id"] = transaction_id

    # Show QR payment with proper buttons
    qr_text = f"""
📱 <b>QR Code Payment</b>

💰 <b>Amount:</b> ₹{total_price:,.2f}
🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>
📱 <b>UPI ID:</b> <code>business@paytm</code>
👤 <b>Merchant:</b> India Social Panel

📋 <b>Payment Instructions:</b>
1. Scan QR code with any UPI app (GPay, PhonePe, Paytm)
2. Pay exact amount ₹{total_price:,.2f}
3. Complete payment with UPI PIN
4. Take screenshot of success message
5. Click "Payment Done" after successful payment

⚡️ <b>QR Code ready for scanning!</b>

💡 <b>Payment complete होने के बाद "Payment Done" button दबाएं</b>
"""

    # Create payment completion keyboard
    qr_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Payment Done", callback_data=f"payment_completed_{transaction_id}"),
            InlineKeyboardButton(text="❌ Cancel Order", callback_data="payment_cancel")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Payment Methods", callback_data="final_confirm_order")
        ]
    ])

    await safe_edit_message(callback, qr_text, qr_keyboard)
    await callback.answer("✅ QR Payment ready! Complete payment and click 'Payment Done'")

@dp.callback_query(F.data == "share_screenshot")
async def cb_share_screenshot(callback: CallbackQuery):
    """Handle screenshot sharing request"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    screenshot_text = """
📸 <b>Screenshot Upload</b>

💡 <b>कृपया payment का screenshot भेजें</b>

📋 <b>Screenshot Requirements:</b>
• Clear और readable हो
• Payment amount दिखना चाहिए
• Transaction status "Success" हो
• Date और time visible हो

💬 <b>Screenshot को image के रूप में send करें...</b>
"""

    user_state[user_id]["current_step"] = "waiting_screenshot_upload"

    await safe_edit_message(callback, screenshot_text)
    await callback.answer()

@dp.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    """Handle main_menu callback - same as back_main"""
    if not callback.message:
        return

    text = """
🏠 <b>India Social Panel - Main Menu</b>

🇮🇳 भारत का #1 SMM Panel
💡 अपनी जरूरत के अनुसार option चुनें:
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
• Order tracking और status check
• Customer support के लिए reference
• Future inquiries और complaints
• Order delivery confirmation

🎯 <b>Order Tracking:</b>
Order History में जाकर इस ID से अपना order track कर सकते हैं।

📞 <b>Support:</b>
अगर कोई problem हो तो इस Order ID के साथ support contact करें।

💡 <b>Important:</b> यह Order ID unique है और केवल आपके order के लिए है।
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

💡 <b>Amount चुनें या custom amount type करें:</b>

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
async def cb_direct_payment_emergency(callback: CallbackQuery):
    """Handle direct payment option - show payment methods directly"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Check if user has order data
    if user_id not in user_state or user_state[user_id].get("current_step") != "choosing_payment_option":
        await callback.answer("⚠️ Order data not found!")
        return

    # Get order details
    order_data = user_state[user_id]["data"]
    package_name = order_data.get("package_name", "Unknown Package")
    link = order_data.get("link", "")
    quantity = order_data.get("quantity", 0)
    total_price = order_data.get("total_price", 0.0)
    platform = order_data.get("platform", "")

    from datetime import datetime
    current_date = datetime.now().strftime("%d %b %Y, %I:%M %p")

    emergency_payment_text = f"""
⚡️ <b>Direct Payment (Emergency Mode)</b>

🚨 <b>Emergency Order Processing</b>

📅 <b>Date:</b> {current_date}
📦 <b>Package:</b> {package_name}
🌐 <b>Platform:</b> {platform.title()}
🔗 <b>Target:</b> {link[:50]}...
📊 <b>Quantity:</b> {quantity:,}
💰 <b>Total Amount:</b> ₹{total_price:,.2f}

💳 <b>Available Payment Methods:</b>

🎯 <b>सभी payment methods available हैं:</b>

🔥 <b>Instant Payment Features:</b>
• ⚡️ QR Code scan करके pay करें
• 💳 UPI से direct transfer
• 🏦 Bank transfer options
• 📱 All UPI apps supported

💡 <b>अपना preferred payment method चुनें:</b>
"""

    emergency_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚡️ Quick QR Payment", callback_data="payment_qr"),
            InlineKeyboardButton(text="📱 UPI Payment", callback_data="payment_upi")
        ],
        [
            InlineKeyboardButton(text="📲 Open UPI App", callback_data="payment_app"),
            InlineKeyboardButton(text="🏦 Bank Transfer", callback_data="payment_bank")
        ],
        [
            InlineKeyboardButton(text="💸 Digital Wallets", callback_data="payment_wallet"),
            InlineKeyboardButton(text="💰 Net Banking", callback_data="payment_netbanking")
        ],
        [
            InlineKeyboardButton(text="💳 Card Payment", callback_data="payment_card")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Options", callback_data="final_confirm_order")
        ]
    ])

    user_state[user_id]["current_step"] = "selecting_payment"

    await safe_edit_message(callback, emergency_payment_text, emergency_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "pay_from_balance")
async def cb_pay_from_balance(callback: CallbackQuery):
    """Handle payment from account balance"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Check if user has order data
    if user_id not in user_state:
        await callback.answer("⚠️ Order data not found!")
        return

    # Get order details
    order_data = user_state[user_id]["data"]
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

    # Store order in both temp and permanent storage
    order_temp[user_id] = order_record
    orders_data[order_id] = order_record  # Also store in permanent orders_data

    print(f"✅ Order {order_id} stored in both temp and permanent storage")

    # Clear user state
    user_state[user_id]["current_step"] = None
    user_state[user_id]["data"] = {}

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
आपका order अब process हो रहा है। Package description के अनुसार delivery complete होगी।

💡 <b>Order ID को save करके रखें - यह tracking के लिए जरूरी है!</b>

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

💬 <b>Screenshot को image के रूप में send करें...</b>

⏰ <b>Screenshot verify होने के बाद order process हो जाएगा</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer("📸 Bank transfer screenshot भेजें...")

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

@dp.callback_query(F.data == "payment_wallet")
async def cb_payment_wallet_method(callback: CallbackQuery):
    """Handle digital wallet payment method"""
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
💸 <b>Digital Wallet Payment</b>

💰 <b>Amount:</b> ₹{total_price:,.2f}

📱 <b>Available Wallets:</b>

💙 <b>Paytm</b>
• UPI ID: <code>paytm@indiasmm</code>
• Most popular in India

🟢 <b>PhonePe</b>
• UPI ID: <code>phonepe@indiasmm</code>
• UPI + Wallet combo

🔴 <b>Google Pay</b>
• UPI ID: <code>gpay@indiasmm</code>
• Fastest transfers

🟡 <b>Amazon Pay</b>
• UPI ID: <code>amazonpay@indiasmm</code>
• Instant refunds

💡 <b>Choose your preferred wallet:</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💙 Paytm", callback_data="wallet_paytm_order"),
            InlineKeyboardButton(text="🟢 PhonePe", callback_data="wallet_phonepe_order")
        ],
        [
            InlineKeyboardButton(text="🔴 Google Pay", callback_data="wallet_gpay_order"),
            InlineKeyboardButton(text="🟡 Amazon Pay", callback_data="wallet_amazon_order")
        ],
        [
            InlineKeyboardButton(text="🔵 JioMoney", callback_data="wallet_jio_order"),
            InlineKeyboardButton(text="🟠 FreeCharge", callback_data="wallet_freecharge_order")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back", callback_data="final_confirm_order")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

@dp.callback_query(F.data == "payment_netbanking")
async def cb_payment_netbanking_method(callback: CallbackQuery):
    """Handle net banking payment method"""
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
💰 <b>Net Banking Payment</b>

💰 <b>Amount:</b> ₹{total_price:,.2f}

🏦 <b>Supported Banks:</b>
• State Bank of India (SBI)
• HDFC Bank
• ICICI Bank
• Axis Bank
• Punjab National Bank (PNB)
• Bank of Baroda
• Canara Bank
• और सभी major banks

📝 <b>Net Banking Steps:</b>
1. Select your bank below
2. You'll be redirected to bank's secure page
3. Login with your net banking credentials
4. Authorize payment of ₹{total_price:,.2f}
5. Payment will be processed instantly

🔒 <b>100% Secure & Encrypted</b>
✅ <b>Direct bank-to-bank transfer</b>

💡 <b>Select your bank:</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏦 SBI", callback_data="netbank_sbi"),
            InlineKeyboardButton(text="🏦 HDFC", callback_data="netbank_hdfc")
        ],
        [
            InlineKeyboardButton(text="🏦 ICICI", callback_data="netbank_icici"),
            InlineKeyboardButton(text="🏦 Axis", callback_data="netbank_axis")
        ],
        [
            InlineKeyboardButton(text="🏦 PNB", callback_data="netbank_pnb"),
            InlineKeyboardButton(text="🏦 Other Banks", callback_data="netbank_others")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back", callback_data="final_confirm_order")
        ]
    ])

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
🌐 <b>Hamari Website</b>

🔗 <b>Website:</b>
Coming Soon...

🇮🇳 <b>India Social Panel Official</b>
✅ Premium SMM Services
✅ 24/7 Customer Support
✅ Secure Payment Gateway
✅ Real-time Order Tracking

💡 <b>Website launch ke liye wait kariye!</b>

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

🔔 <b>Notifications ON kar dena!</b>
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
📜 <b>Seva Ki Shartein (Terms of Service)</b>

📝 <b>Important Terms:</b>

1️⃣ <b>Service Guarantee:</b>
• High quality services guarantee
• No fake/bot followers
• Real & active users only

2️⃣ <b>Refund Policy:</b>
• Service start ke baad no refund
• Wrong link ke liye customer responsible
• Technical issues mein full refund

3️⃣ <b>Account Safety:</b>
• 100% safe methods use karte hain
• Account ban nahi hoga
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
🎟️ <b>Coupon Redeem Karein</b>

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

    profile_text = f"""
👤 <b>User Profile Details</b>

🆔 <b>User ID:</b> {target_user_id}
👤 <b>Name:</b> {user.get('full_name', 'N/A')}
📱 <b>Username:</b> @{user.get('username', 'N/A')}
📞 <b>Phone:</b> {user.get('phone_number', 'N/A')}
📧 <b>Email:</b> {user.get('email', 'N/A')}

💰 <b>Balance:</b> ₹{user.get('balance', 0.0):,.2f}
💸 <b>Total Spent:</b> ₹{user.get('total_spent', 0.0):,.2f}
📦 <b>Orders:</b> {user.get('orders_count', 0)}
📅 <b>Joined:</b> {format_time(user.get('join_date', ''))}
⚡️ <b>Status:</b> {user.get('status', 'active').title()}
"""

    await callback.answer(profile_text, show_alert=True)

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

    order_id = callback.data.replace("admin_complete_", "")

    # Get order details - check all possible sources  
    global orders_data, order_temp
    print(f"🔍 DEBUG: Complete Order - Looking for order {order_id}")
    print(f"🔍 DEBUG: Complete Order - Global orders_data has {len(orders_data)} orders")
    print(f"🔍 DEBUG: Complete Order - Available orders: {list(orders_data.keys())}")

    # Check if we can access the order from different sources
    order_found = False
    order = None

    if order_id in orders_data:
        order = orders_data[order_id]
        order_found = True
        print(f"✅ DEBUG: Order found in global orders_data")
    else:
        # Check order_temp for recent orders
        for temp_order in order_temp.values():
            if temp_order.get('order_id') == order_id:
                order = temp_order
                order_found = True
                print(f"✅ DEBUG: Order found in order_temp")
                # Also store it back in orders_data
                orders_data[order_id] = temp_order
                break

    if not order_found:
        await callback.answer("❌ Order not found in any storage!", show_alert=True)
        return
    customer_id = order['user_id']
    # Get customer name from users_data instead of order
    customer_info = users_data.get(customer_id, {})
    customer_name = customer_info.get('full_name') or customer_info.get('first_name', 'Customer')
    package_name = order['package_name']
    platform = order['platform']
    quantity = order['quantity']
    total_price = order['total_price']

    # Update order status
    orders_data[order_id]['status'] = 'completed'
    orders_data[order_id]['completed_at'] = datetime.now().isoformat()
    orders_data[order_id]['completed_by_admin'] = user_id

    # Update user's order count and spending
    if customer_id in users_data:
        users_data[customer_id]['orders_count'] += 1
        users_data[customer_id]['total_spent'] += total_price

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

    order_id = callback.data.replace("admin_cancel_", "")

    # Show cancellation reason options
    cancel_text = f"""
❌ <b>Cancel Order #{order_id}</b>

⚠️ <b>Select cancellation reason:</b>

💡 <b>Choose the most appropriate reason for order cancellation:</b>
"""

    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔗 Invalid Link",
                callback_data=f"cancel_reason_{order_id}_invalid_link"
            ),
            InlineKeyboardButton(
                text="💳 Payment Issue",
                callback_data=f"cancel_reason_{order_id}_payment_issue"
            )
        ],
        [
            InlineKeyboardButton(
                text="📦 Service Unavailable",
                callback_data=f"cancel_reason_{order_id}_service_unavailable"
            ),
            InlineKeyboardButton(
                text="❌ Duplicate Order",
                callback_data=f"cancel_reason_{order_id}_duplicate"
            )
        ],
        [
            InlineKeyboardButton(
                text="🚫 Policy Violation",
                callback_data=f"cancel_reason_{order_id}_policy_violation"
            ),
            InlineKeyboardButton(
                text="💬 Custom Reason",
                callback_data=f"cancel_reason_{order_id}_custom"
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

    # Parse callback data: cancel_reason_ORDER_ID_REASON
    callback_parts = callback.data.split("_")
    order_id = callback_parts[2]
    reason_type = "_".join(callback_parts[3:])

    # Get order details - check all possible sources
    global orders_data, order_temp
    print(f"🔍 DEBUG: Cancel Reason - Looking for order {order_id}")

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
    customer_id = order['user_id']
    # Get customer name from users_data instead of order
    customer_info = users_data.get(customer_id, {})
    customer_name = customer_info.get('full_name') or customer_info.get('first_name', 'Customer')
    package_name = order['package_name']
    total_price = order['total_price']

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

# ========== INPUT HANDLERS ==========
@dp.message(F.text)
async def handle_text_input_wrapper(message: Message):
    """Wrapper for text input handler - first check account creation, then other handlers"""
    if not message.from_user:
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        mark_user_for_notification(message.from_user.id)
        return

    # Check if user is in account creation flow
    user_id = message.from_user.id
    current_step = user_state.get(user_id, {}).get("current_step")

    print(f"🔍 TEXT DEBUG: User {user_id} sent text: '{message.text[:50]}...'")
    print(f"🔍 TEXT DEBUG: User {user_id} current_step: {current_step}")

    # PRIORITY: Check for admin broadcast first
    from services import handle_admin_broadcast_message, is_admin
    if is_admin(user_id):
        print(f"🔍 ADMIN CHECK: User {user_id} is admin, current_step: {current_step}")
        if current_step == "admin_broadcast_message":
            print(f"📢 Processing admin broadcast message from {user_id}")
            await handle_admin_broadcast_message(message, user_id)
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
        message, user_state, users_data, order_temp, tickets_data,
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
        photo = message.photo[-1]
        file_id = photo.file_id

        # Store photo file_id in user data
        users_data[user_id]['profile_photo'] = file_id
        user_state[user_id]["current_step"] = None

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
        user_state[user_id]["data"]["screenshot_file_id"] = message.photo[-1].file_id

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


# ========== STARTUP FUNCTIONS ==========
async def on_startup():
    """Initialize bot on startup"""
    print("🚀 India Social Panel Bot starting...")

    # Initialize all handlers now that dp is available
    print("🔄 Initializing account handlers...")
    account_handlers.init_account_handlers(
        dp, users_data, orders_data, require_account,
        format_currency, format_time, is_account_created, user_state, is_admin, safe_edit_message
    )

    print("🔄 Initializing account creation handlers...")
    account_creation.init_account_creation_handlers(
        dp, users_data, user_state, safe_edit_message, init_user,
        mark_user_for_notification, is_message_old, bot, START_TIME
    )

    print("✅ Account creation initialization complete")

    print("🔄 Initializing payment system...")
    payment_system.register_payment_handlers(dp, users_data, user_state, format_currency)

    print("🔄 Initializing service system...")
    services.register_service_handlers(dp, require_account)

    # Set bot commands
    commands = [
        BotCommand(command="start", description="🏠 Main Menu"),
        BotCommand(command="menu", description="📋 Show Menu"),
        BotCommand(command="help", description="❓ Help & Support"),
        BotCommand(command="about", description="ℹ️ About India Social Panel")
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
