# -*- coding: utf-8 -*-
"""
My Account Handlers - India Social Panel
All account-related functionality and handlers
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import pytz

# Global variables (will be initialized from main.py)
from typing import Dict, Any, Callable, Optional, Union

# Initialize with proper default values to avoid None type errors
dp: Any = None
users_data: Dict[int, Dict[str, Any]] = {}
orders_data: Dict[str, Dict[str, Any]] = {}
user_state: Dict[int, Dict[str, Any]] = {}  # Fixed type to match main.py
format_currency: Optional[Callable[[float], str]] = None
format_time: Optional[Callable[[str], str]] = None
safe_edit_message: Optional[Callable] = None
require_account: Optional[Callable] = None
is_account_created: Optional[Callable[[int], bool]] = None
is_admin: Optional[Callable[[int], bool]] = None

def format_join_date_with_timezone(join_date_str: str, user_timezone: str = "Asia/Kolkata") -> str:
    """Format join date with timezone information"""
    try:
        # Parse the ISO format date
        if join_date_str:
            join_dt = datetime.fromisoformat(join_date_str.replace('Z', '+00:00'))

            # Convert to user's timezone (default: India)
            user_tz = pytz.timezone(user_timezone)
            local_dt = join_dt.astimezone(user_tz)

            # Format with timezone info
            formatted_date = local_dt.strftime("%d %B %Y")
            formatted_time = local_dt.strftime("%I:%M %p")
            timezone_name = local_dt.strftime("%Z")

            return f"{formatted_date} at {formatted_time} {timezone_name}"
        return "Unknown"
    except Exception as e:
        print(f"Error formatting join date: {e}")
        return join_date_str or "Unknown"

def get_user_timezone_info(user_language: str = "en") -> dict:
    """Get timezone information based on user preferences"""
    timezone_map = {
        "hi": "Asia/Kolkata",  # Hindi - India
        "en": "Asia/Kolkata",  # English - Default to India
        "bn": "Asia/Kolkata",  # Bengali - India
        "te": "Asia/Kolkata",  # Telugu - India
        "mr": "Asia/Kolkata",  # Marathi - India
        "ta": "Asia/Kolkata",  # Tamil - India
        "gu": "Asia/Kolkata",  # Gujarati - India
        "kn": "Asia/Kolkata",  # Kannada - India
        "ml": "Asia/Kolkata",  # Malayalam - India
        "or": "Asia/Kolkata",  # Odia - India
        "pa": "Asia/Kolkata",  # Punjabi - India
        "ur": "Asia/Kolkata",  # Urdu - India/Pakistan
        "as": "Asia/Kolkata",  # Assamese - India
        "zh": "Asia/Shanghai", # Chinese
        "ja": "Asia/Tokyo",    # Japanese
        "ko": "Asia/Seoul",    # Korean
        "ar": "Asia/Riyadh",   # Arabic
        "ru": "Europe/Moscow", # Russian
        "es": "Europe/Madrid", # Spanish
        "fr": "Europe/Paris",  # French
        "de": "Europe/Berlin", # German
        "pt": "America/Sao_Paulo", # Portuguese
        "it": "Europe/Rome",   # Italian
    }

    timezone_str = timezone_map.get(user_language[:2], "Asia/Kolkata")
    tz = pytz.timezone(timezone_str)
    current_time = datetime.now(tz)

    return {
        "timezone": timezone_str,
        "name": current_time.strftime("%Z"),
        "offset": current_time.strftime("%z"),
        "current_time": current_time.strftime("%d %B %Y, %I:%M %p %Z")
    }

# Safe edit message function is passed from main.py - no need to define here

def init_account_handlers(main_dp, main_users_data, main_orders_data, main_require_account,
                         main_format_currency, main_format_time, main_is_account_created, main_user_state, main_is_admin, main_safe_edit_message):
    """Initialize account handlers with references from main.py"""
    global dp, users_data, orders_data, require_account, format_currency, format_time, is_account_created, user_state, is_admin, safe_edit_message

    # Initialize all global variables
    dp = main_dp
    users_data = main_users_data if main_users_data is not None else {}
    orders_data = main_orders_data if main_orders_data is not None else {}
    require_account = main_require_account
    format_currency = main_format_currency
    format_time = main_format_time
    is_account_created = main_is_account_created
    user_state = main_user_state if main_user_state is not None else {}
    is_admin = main_is_admin
    safe_edit_message = main_safe_edit_message

    # Only register handlers if all required components are available
    if dp and require_account:
        # Register handlers after initialization
        dp.callback_query.register(require_account(cb_my_account), F.data == "my_account")
        dp.callback_query.register(require_account(cb_order_history), F.data == "order_history")
        dp.callback_query.register(require_account(cb_refill_history), F.data == "refill_history")
        dp.callback_query.register(require_account(cb_api_key), F.data == "api_key")
        dp.callback_query.register(require_account(cb_edit_profile), F.data == "edit_profile")
        dp.callback_query.register(require_account(cb_user_stats), F.data == "user_stats")
        dp.callback_query.register(require_account(cb_smart_alerts), F.data == "smart_alerts")
        dp.callback_query.register(require_account(cb_language_settings), F.data == "language_settings")
        dp.callback_query.register(require_account(cb_account_preferences), F.data == "account_preferences")
        dp.callback_query.register(require_account(cb_security_settings), F.data == "security_settings")
        dp.callback_query.register(require_account(cb_payment_methods), F.data == "payment_methods")

        # Register language region handlers
        dp.callback_query.register(require_account(cb_language_regions), F.data == "language_regions")
        dp.callback_query.register(require_account(cb_lang_region_indian), F.data == "lang_region_indian")
        dp.callback_query.register(require_account(cb_lang_region_international), F.data == "lang_region_international")
        dp.callback_query.register(require_account(cb_lang_region_european), F.data == "lang_region_european")
        dp.callback_query.register(require_account(cb_lang_region_asian), F.data == "lang_region_asian")
        dp.callback_query.register(require_account(cb_lang_region_middle_east), F.data == "lang_region_middle_east")
        dp.callback_query.register(require_account(cb_lang_region_americas), F.data == "lang_region_americas")
        dp.callback_query.register(require_account(cb_lang_region_popular), F.data == "lang_region_popular")

        # Register individual language selection handlers
        dp.callback_query.register(require_account(cb_language_select), F.data.startswith("select_lang_"))

        # Register new API management handlers
        dp.callback_query.register(require_account(cb_create_api_key), F.data == "create_api_key")
        dp.callback_query.register(require_account(cb_view_api_key), F.data == "view_api_key")
        dp.callback_query.register(require_account(cb_regenerate_api), F.data == "regenerate_api")
        dp.callback_query.register(require_account(cb_confirm_regenerate_api), F.data == "confirm_regenerate_api")
        dp.callback_query.register(require_account(cb_delete_api_key), F.data == "delete_api_key")
        dp.callback_query.register(require_account(cb_api_stats), F.data == "api_stats")
        dp.callback_query.register(require_account(cb_api_docs), F.data == "api_docs")
        dp.callback_query.register(require_account(cb_api_security), F.data == "api_security")
        dp.callback_query.register(require_account(cb_test_api), F.data == "test_api")
        dp.callback_query.register(require_account(cb_api_examples), F.data == "api_examples")
        dp.callback_query.register(require_account(cb_copy_api_key), F.data == "copy_api_key")
        dp.callback_query.register(require_account(cb_copy_test_commands), F.data == "copy_test_commands")

        # Register edit profile handlers
        dp.callback_query.register(require_account(cb_edit_name), F.data == "edit_name")
        dp.callback_query.register(require_account(cb_edit_phone), F.data == "edit_phone")
        dp.callback_query.register(require_account(cb_edit_email), F.data == "edit_email")
        dp.callback_query.register(require_account(cb_edit_bio), F.data == "edit_bio")
        dp.callback_query.register(require_account(cb_edit_username), F.data == "edit_username")
        dp.callback_query.register(require_account(cb_edit_location), F.data == "edit_location")
        dp.callback_query.register(require_account(cb_edit_birthday), F.data == "edit_birthday")
        dp.callback_query.register(require_account(cb_edit_photo), F.data == "edit_photo")
        dp.callback_query.register(require_account(cb_sync_telegram_data), F.data == "sync_telegram_data")
        dp.callback_query.register(require_account(cb_preview_profile), F.data == "preview_profile")

        # Register new access token and logout handlers
        dp.callback_query.register(require_account(cb_copy_access_token_myaccount), F.data == "copy_access_token")
        dp.callback_query.register(require_account(cb_logout_account), F.data == "logout_account")
        dp.callback_query.register(require_account(cb_confirm_logout), F.data == "confirm_logout")
        dp.callback_query.register(require_account(cb_regenerate_access_token), F.data == "regenerate_access_token")


# ========== ACCOUNT MENU BUILDERS ==========
def get_account_menu() -> InlineKeyboardMarkup:
    """Build my account sub-menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Refill History", callback_data="refill_history"),
            InlineKeyboardButton(text="🔑 API Key", callback_data="api_key")
        ],
        [
            InlineKeyboardButton(text="✏️ Edit Profile", callback_data="edit_profile"),
            InlineKeyboardButton(text="📊 Statistics", callback_data="user_stats")
        ],
        [
            InlineKeyboardButton(text="📜 Order History", callback_data="order_history"),
            InlineKeyboardButton(text="🔔 Smart Alerts", callback_data="smart_alerts")
        ],
        [
            InlineKeyboardButton(text="🌐 Language / भाषा", callback_data="language_settings"),
            InlineKeyboardButton(text="🎯 Preferences", callback_data="account_preferences")
        ],
        [
            InlineKeyboardButton(text="🔐 Security Settings", callback_data="security_settings"),
            InlineKeyboardButton(text="💳 Payment Methods", callback_data="payment_methods")
        ],
        [
            InlineKeyboardButton(text="🔑 Copy Access Token", callback_data="copy_access_token"),
            InlineKeyboardButton(text="🚪 Logout Account", callback_data="logout_account")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

def get_back_to_account_keyboard() -> InlineKeyboardMarkup:
    """Common keyboard to go back to account menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ My Account", callback_data="my_account")]
    ])

# ========== ACCOUNT DASHBOARD ==========
async def cb_my_account(callback: CallbackQuery):
    """Handle my account dashboard"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})

    # Get user display name
    telegram_user = callback.from_user
    user_display_name = f"@{telegram_user.username}" if telegram_user.username else user_data.get('full_name', user_data.get('first_name', 'User'))

    # Get user language for timezone
    user_language = getattr(telegram_user, 'language_code', 'en') or user_data.get('language_code', 'en')
    timezone_info = get_user_timezone_info(user_language)

    # Format join date with timezone
    join_date_formatted = format_join_date_with_timezone(
        user_data.get('join_date', ''), 
        timezone_info['timezone']
    )

    text = f"""
👤 <b>My Account Dashboard</b>

👋 <b>Welcome back, {user_display_name}!</b>

📱 <b>Phone:</b> {user_data.get('phone_number', 'Not set')}
📧 <b>Email:</b> {user_data.get('email', 'Not set')}

💰 <b>Balance:</b> {format_currency(user_data.get('balance', 0.0)) if format_currency else f"₹{user_data.get('balance', 0.0):.2f}"}
📊 <b>Total Spent:</b> {format_currency(user_data.get('total_spent', 0.0)) if format_currency else f"₹{user_data.get('total_spent', 0.0):.2f}"}
🛒 <b>Total Orders:</b> {user_data.get('orders_count', 0)}
📅 <b>Member Since:</b> {join_date_formatted}
🌍 <b>Your Timezone:</b> {timezone_info['name']} ({timezone_info['offset']})
🕐 <b>Current Time:</b> {timezone_info['current_time']}

🔸 <b>Account Status:</b> ✅ Active
🔸 <b>User ID:</b> <code>{user_id}</code>

💡 <b>Choose an option below to manage your account:</b>
"""

    if safe_edit_message:
        await safe_edit_message(callback, text, get_account_menu())
    await callback.answer()

# ========== ORDER HISTORY ==========
async def cb_order_history(callback: CallbackQuery):
    """Show user's order history with proper details"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Get orders from multiple sources
    from main import order_temp, orders_data as main_orders_data
    user_orders = []

    print(f"🔍 DEBUG: Checking order history for user {user_id}")
    print(f"🔍 DEBUG: main_orders_data has {len(main_orders_data)} orders")
    print(f"🔍 DEBUG: order_temp has user {user_id}: {user_id in order_temp}")
    print(f"🔍 DEBUG: local orders_data has {len(orders_data)} orders")

    # Get from main orders_data
    for order_id, order in main_orders_data.items():
        if order.get('user_id') == user_id:
            print(f"🔍 Found order in main_orders_data: {order_id}")
            user_orders.append(order)

    # Get from order_temp (recent orders) 
    if user_id in order_temp:
        temp_order = order_temp[user_id].copy()
        temp_order['is_recent'] = True
        print(f"🔍 Found recent order in order_temp: {temp_order.get('order_id', 'NO_ID')}")
        user_orders.append(temp_order)

    # Also get from local orders_data if it exists
    if orders_data:
        for order_id, order in orders_data.items():
            if order.get('user_id') == user_id:
                # Check if not already added
                existing_ids = [o.get('order_id') for o in user_orders]
                if order.get('order_id') not in existing_ids:
                    print(f"🔍 Found order in local orders_data: {order_id}")
                    user_orders.append(order)

    print(f"🔍 DEBUG: Total orders found for user {user_id}: {len(user_orders)}")

    if not user_orders:
        text = """
📜 <b>Order History</b>

📋 <b>अभी तक कोई orders नहीं हैं</b>

🚀 <b>आपने अभी तक कोई orders place नहीं किए हैं!</b>

💡 <b>First order करने के लिए:</b>
• "New Order" पर click करें
• अपना platform choose करें  
• Package select करें
• Order place करें

✨ <b>India Social Panel में आपका स्वागत है!</b>
"""
    else:
        text = f"""
📜 <b>Order History</b>

📊 <b>Total Orders Found:</b> {len(user_orders)}

📋 <b>Recent Orders (Latest First):</b>

"""
        # Sort orders by created_at (newest first)
        sorted_orders = sorted(user_orders, key=lambda x: x.get('created_at', ''), reverse=True)

        for i, order in enumerate(sorted_orders[:15], 1):  # Show last 15 orders
            status_emoji = {"processing": "⏳", "completed": "✅", "failed": "❌", "pending": "🔄", "cancelled": "❌"}
            emoji = status_emoji.get(order.get('status', 'processing'), "⏳")

            # Handle different order data formats
            order_id = order.get('order_id', f'ORDER-{i}')
            package_name = order.get('package_name', order.get('service', 'Unknown Package'))
            platform = order.get('platform', 'Unknown Platform').title()
            quantity = order.get('quantity', 0)
            amount = order.get('total_price', order.get('price', 0))
            created_at = order.get('created_at', '')
            payment_status = order.get('payment_status', 'completed')
            payment_method = order.get('payment_method', 'Unknown')

            # Recent order indicator
            recent_indicator = " 🔥" if order.get('is_recent') else ""

            # Format date properly
            try:
                if created_at:
                    from datetime import datetime
                    if isinstance(created_at, str):
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        formatted_date = dt.strftime("%d %b %Y, %I:%M %p")
                    else:
                        formatted_date = str(created_at)
                else:
                    formatted_date = "Just now"
            except:
                formatted_date = "Recent"

            text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>{i}. Order #{order_id}</b>{recent_indicator}
━━━━━━━━━━━━━━━━━━━━━━━━━━━

{emoji} <b>Status:</b> {order.get('status', 'Processing').title()}
📦 <b>Package:</b> {package_name}
📱 <b>Platform:</b> {platform}
🔢 <b>Quantity:</b> {quantity:,}
💰 <b>Amount:</b> {format_currency(amount) if format_currency else f"₹{amount:,.2f}"}
💳 <b>Payment:</b> {payment_method} - {payment_status.title()}
📅 <b>Date:</b> {formatted_date}

"""

        text += """
💡 <b>Order Details देखने के लिए:</b>
• Order ID copy करें
• Support को भेजें detailed info के लिए

📞 <b>Order में problem है?</b>
• Support contact करें: @tech_support_admin
• Order ID mention करना न भूलें
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚀 New Order", callback_data="new_order"),
            InlineKeyboardButton(text="📞 Contact Support", url="https://t.me/tech_support_admin")
        ],
        [
            InlineKeyboardButton(text="👤 My Account", callback_data="my_account"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

# ========== REFILL HISTORY ==========
async def cb_refill_history(callback: CallbackQuery):
    """Handle refill/payment history"""
    if not callback.message:
        return

    text = """
🔄 <b>Refill History</b>

💳 <b>Payment History Empty</b>

आपने अभी तक कोई payment नहीं किया है।

💰 <b>Add funds करने के लिए:</b>
• Main menu → Add Funds पर click करें
• Amount select करें या custom amount enter करें
• Payment method choose करें
• Payment complete करें

🔐 <b>All transactions are secure and encrypted</b>
"""

    await safe_edit_message(callback, text, get_back_to_account_keyboard())
    await callback.answer()

# ========== API KEY MANAGEMENT ==========
def get_api_management_menu(has_api: bool = False) -> InlineKeyboardMarkup:
    """Build API management menu"""
    if has_api:
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 View API Key", callback_data="view_api_key"),
                InlineKeyboardButton(text="📊 API Usage Stats", callback_data="api_stats")
            ],
            [
                InlineKeyboardButton(text="🔄 Regenerate Key", callback_data="regenerate_api"),
                InlineKeyboardButton(text="🗑️ Delete API Key", callback_data="delete_api_key")
            ],
            [
                InlineKeyboardButton(text="📚 Documentation", callback_data="api_docs"),
                InlineKeyboardButton(text="🔐 Security Settings", callback_data="api_security")
            ],
            [
                InlineKeyboardButton(text="💻 Test API", callback_data="test_api"),
                InlineKeyboardButton(text="📋 Code Examples", callback_data="api_examples")
            ],
            [
                InlineKeyboardButton(text="⬅️ My Account", callback_data="my_account")
            ]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Create API Key", callback_data="create_api_key")],
            [InlineKeyboardButton(text="📚 API Documentation", callback_data="api_docs")],
            [InlineKeyboardButton(text="⬅️ My Account", callback_data="my_account")]
        ])

async def cb_api_key(callback: CallbackQuery):
    """Handle API key main dashboard"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})
    api_key = user_data.get('api_key', None)
    has_api = bool(api_key and api_key != 'Not generated')

    if has_api:
        # User has API key - show management dashboard
        masked_key = f"{api_key[:8]}...{api_key[-8:]}" if len(api_key) > 16 else api_key

        text = f"""
🔑 <b>API Key Management Dashboard</b>

✅ <b>API Status:</b> Active & Ready
🆔 <b>Key ID:</b> <code>{masked_key}</code>
📅 <b>Created:</b> {format_time(user_data.get('join_date', ''))}
🔄 <b>Last Used:</b> Never (Coming Soon)

📊 <b>Quick Stats:</b>
• 🚀 <b>Requests Today:</b> 0/1,000
• ⚡ <b>Success Rate:</b> 100%
• 🔒 <b>Security Status:</b> Secure
• 💰 <b>Credits Used:</b> ₹0.00

🌟 <b>API Features Available:</b>
✅ All SMM Services Access
✅ Real-time Order Tracking  
✅ Balance Management
✅ Service Status Monitoring
✅ Webhook Notifications

💡 <b>Choose an action below:</b>
"""
    else:
        # User doesn't have API key - show creation option
        text = f"""
🔑 <b>API Key Management</b>

🚀 <b>Professional API Integration</b>

🌟 <b>India Social Panel API Features:</b>
✅ <b>Complete SMM Service Access</b>
✅ <b>Real-time Order Processing</b>
✅ <b>Advanced Analytics & Reporting</b>
✅ <b>Webhook Integration Support</b>
✅ <b>Enterprise-grade Security</b>

📈 <b>API Capabilities:</b>
• 🔄 Automated order placement
• 📊 Real-time status tracking
• 💰 Balance & transaction management
• 📋 Service catalog access
• 🔔 Instant notifications

🔒 <b>Security & Reliability:</b>
• 🛡️ OAuth 2.0 + JWT Authentication
• 🌐 99.9% Uptime Guarantee
• 🔐 AES-256 Encryption
• 📝 Comprehensive logging
• ⚡ Rate limiting protection

💼 <b>Perfect for:</b>
• SMM Panel Resellers
• Digital Marketing Agencies
• Automated Social Media Tools
• Custom Application Integration

⚠️ <b>Important:</b> प्रत्येक account में केवल एक ही API key create कर सकते हैं।

💡 <b>Ready to create your professional API key?</b>
"""

    await safe_edit_message(callback, text, get_api_management_menu(has_api))
    await callback.answer()

async def cb_create_api_key(callback: CallbackQuery):
    """Handle API key creation"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})

    # Check if user already has API key
    existing_api = user_data.get('api_key')
    if existing_api and existing_api != 'Not generated':
        text = """
⚠️ <b>API Key Already Exists</b>

🔑 <b>आपके पास पहले से API key है!</b>

📋 <b>Options:</b>
• API key देखने के लिए "View API Key" click करें
• नई key चाहिए तो पहले current key को regenerate करें
• API key delete करने के लिए support contact करें

💡 <b>Security reason से एक account में केवल एक API key allow है</b>
"""

        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 View Current Key", callback_data="view_api_key")],
            [InlineKeyboardButton(text="⬅️ Back to API", callback_data="api_key")]
        ])

        await safe_edit_message(callback, text, back_keyboard)
        await callback.answer()
        return

    # Generate new API key
    import secrets
    import string
    import time

    # Generate secure API key
    timestamp = str(int(time.time()))
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    new_api_key = f"ISP_{timestamp}_{random_part}"

    # Store API key
    users_data[user_id]['api_key'] = new_api_key
    users_data[user_id]['api_created_at'] = timestamp

    text = f"""
🎉 <b>API Key Successfully Created!</b>

🔑 <b>Your New API Key:</b>
<code>{new_api_key}</code>

✅ <b>API Key Features Activated:</b>
• 🚀 Full service access
• 📊 Real-time monitoring
• 🔔 Webhook support
• 💰 Balance management
• 📈 Analytics access

🔒 <b>Security Information:</b>
• 🆔 <b>Key ID:</b> {new_api_key[:16]}...
• 📅 <b>Created:</b> Just now
• ⏰ <b>Valid:</b> Forever (until regenerated)
• 🛡️ <b>Encryption:</b> AES-256

⚠️ <b>Important Security Notes:</b>
• API key को किसी के साथ share न करें
• Secure environment में store करें
• Regular monitoring करते रहें
• Suspicious activity पर तुरंत regenerate करें

💡 <b>API key को copy करने के लिए above text को tap करें</b>

🎯 <b>Next Steps:</b>
• Documentation पढ़ें
• Test API calls करें
• Integration start करें
"""

    success_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Copy Key", callback_data="copy_api_key"),
            InlineKeyboardButton(text="📚 Documentation", callback_data="api_docs")
        ],
        [
            InlineKeyboardButton(text="💻 Test API", callback_data="test_api"),
            InlineKeyboardButton(text="📊 View Dashboard", callback_data="api_key")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await safe_edit_message(callback, text, success_keyboard)
    await callback.answer()  # Remove popup alert

async def cb_view_api_key(callback: CallbackQuery):
    """Handle viewing API key"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})
    api_key = user_data.get('api_key')

    if not api_key or api_key == 'Not generated':
        text = """
⚠️ <b>No API Key Found</b>

🔑 <b>आपके पास अभी तक कोई API key नहीं है</b>

💡 <b>Create करने के लिए "Create API Key" button click करें</b>
"""

        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Create API Key", callback_data="create_api_key")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="api_key")]
        ])

        await safe_edit_message(callback, text, back_keyboard)
        await callback.answer()
        return

    text = f"""
🔑 <b>Your API Key</b>

🔐 <b>Full API Key:</b>
<code>{api_key}</code>

📊 <b>Key Information:</b>
• 🆔 <b>Key ID:</b> {api_key[:16]}...
• 📅 <b>Created:</b> {format_time(user_data.get('join_date', ''))}
• 🔄 <b>Last Used:</b> Coming Soon
• 🔒 <b>Status:</b> ✅ Active

🌐 <b>API Base URL:</b>
<code>https://api.indiasocialpanel.com/v1</code>

🔑 <b>Authentication Header:</b>
<code>Authorization: Bearer {api_key}</code>

⚠️ <b>Security Warning:</b>
• API key को कभी भी public repositories में store न करें
• Environment variables का use करें
• Regular basis पर key को regenerate करें
• Unauthorized access monitor करते रहें

💡 <b>Tap on API key to copy it</b>
"""

    view_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Copy Full Key", callback_data="copy_api_key"),
            InlineKeyboardButton(text="🔄 Regenerate", callback_data="regenerate_api")
        ],
        [
            InlineKeyboardButton(text="📚 Documentation", callback_data="api_docs"),
            InlineKeyboardButton(text="💻 Test API", callback_data="test_api")
        ],
        [
            InlineKeyboardButton(text="⬅️ API Dashboard", callback_data="api_key")
        ]
    ])

    await safe_edit_message(callback, text, view_keyboard)
    await callback.answer()

async def cb_regenerate_api(callback: CallbackQuery):
    """Handle API key regeneration with confirmation"""
    if not callback.message or not callback.from_user:
        return

    text = """
⚠️ <b>Regenerate API Key</b>

🔄 <b>API Key Regeneration Confirmation</b>

⚠️ <b>Important Warning:</b>
• Current API key will be permanently deleted
• All applications using old key will stop working
• आपको सभी applications में new key update करना होगा
• यह action undo नहीं हो सकता

🔒 <b>Security Benefits:</b>
• Fresh new secure key generation
• Previous key immediately invalidated  
• Enhanced security protection
• Clean slate for API access

💡 <b>क्या आप वाकई API key regenerate करना चाहते हैं?</b>
"""

    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yes, Regenerate", callback_data="confirm_regenerate_api"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="api_key")
        ]
    ])

    await safe_edit_message(callback, text, confirm_keyboard)
    await callback.answer()

async def cb_confirm_regenerate_api(callback: CallbackQuery):
    """Confirm and regenerate API key"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Generate new API key
    import secrets
    import string
    import time

    timestamp = str(int(time.time()))
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    new_api_key = f"ISP_{timestamp}_{random_part}"

    # Store new API key
    old_key = users_data.get(user_id, {}).get('api_key', 'N/A')
    users_data[user_id]['api_key'] = new_api_key
    users_data[user_id]['api_regenerated_at'] = timestamp

    text = f"""
🎉 <b>API Key Successfully Regenerated!</b>

🔑 <b>Your New API Key:</b>
<code>{new_api_key}</code>

✅ <b>Regeneration Complete:</b>
• 🗑️ Old key permanently deleted
• 🔒 New key activated instantly
• 🛡️ Enhanced security applied
• 📅 Timestamp: Just now

⚠️ <b>Action Required:</b>
• Update all applications with new key
• Test API connections
• Verify all integrations working
• Monitor for any authentication errors

🔒 <b>Security Enhancement:</b>
• Previous access tokens invalidated
• All active sessions terminated
• Fresh authentication required
• Clean security slate established

💡 <b>Copy new API key और applications में update करें</b>
"""

    success_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Copy New Key", callback_data="copy_api_key"),
            InlineKeyboardButton(text="💻 Test New Key", callback_data="test_api")
        ],
        [
            InlineKeyboardButton(text="📚 Update Guide", callback_data="api_docs"),
            InlineKeyboardButton(text="📊 API Dashboard", callback_data="api_key")
        ]
    ])

    await safe_edit_message(callback, text, success_keyboard)
    await callback.answer("🔄 API Key successfully regenerated!", show_alert=True)

async def cb_delete_api_key(callback: CallbackQuery):
    """Handle API key deletion"""
    if not callback.message:
        return

    text = """
🗑️ <b>Delete API Key</b>

⚠️ <b>Permanent Deletion Warning</b>

🔴 <b>This action will:</b>
• Permanently delete your API key
• Stop all API access immediately
• Cannot be undone
• Require creating new key for future use

💡 <b>API key deletion feature coming soon!</b>
📞 <b>For now, contact support for deletion:</b> @tech_support_admin
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back to API", callback_data="api_key")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

async def cb_api_stats(callback: CallbackQuery):
    """Handle API usage statistics"""
    if not callback.message:
        return

    text = """
📊 <b>API Usage Statistics</b>

📈 <b>Usage Analytics Dashboard</b>

📊 <b>Today's Usage:</b>
• 🚀 <b>Requests:</b> 0/1,000
• ✅ <b>Success Rate:</b> 100%
• ⚡ <b>Avg Response:</b> 150ms
• 💰 <b>Cost:</b> ₹0.00

📅 <b>This Month:</b>
• 📈 <b>Total Requests:</b> 0
• 🎯 <b>Success Rate:</b> N/A
• 🕐 <b>Peak Hour:</b> N/A
• 💳 <b>Total Cost:</b> ₹0.00

🏆 <b>All Time Stats:</b>
• 📊 <b>Total Requests:</b> 0
• 🥇 <b>Best Day:</b> N/A
• 📈 <b>Growth Rate:</b> N/A

🔧 <b>Advanced analytics coming soon!</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ API Dashboard", callback_data="api_key")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

async def cb_api_docs(callback: CallbackQuery):
    """Handle API documentation"""
    if not callback.message:
        return

    text = """
📚 <b>API Documentation</b>

🌟 <b>India Social Panel API v1.0</b>

🔗 <b>Base URL:</b>
<code>https://api.indiasocialpanel.com/v1</code>

🔑 <b>Authentication:</b>
<code>Authorization: Bearer YOUR_API_KEY</code>

📋 <b>Main Endpoints:</b>

🔸 <b>Services:</b>
• <code>GET /services</code> - List all services
• <code>GET /services/{id}</code> - Service details

🔸 <b>Orders:</b>
• <code>POST /orders</code> - Create new order
• <code>GET /orders/{id}</code> - Order status
• <code>GET /orders</code> - Order history

🔸 <b>Account:</b>
• <code>GET /balance</code> - Check balance
• <code>GET /profile</code> - User profile

📖 <b>Request Example:</b>
<code>
curl -X POST \
  https://api.indiasocialpanel.com/v1/orders \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "service": 1,
    "link": "https://instagram.com/user",
    "quantity": 1000
  }'
</code>

🔔 <b>Response Codes:</b>
• 200 - Success
• 400 - Bad Request
• 401 - Unauthorized
• 429 - Rate Limited
• 500 - Server Error

💡 <b>Full documentation coming soon!</b>
"""

    docs_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Code Examples", callback_data="api_examples"),
            InlineKeyboardButton(text="💻 Test API", callback_data="test_api")
        ],
        [
            InlineKeyboardButton(text="⬅️ API Dashboard", callback_data="api_key")
        ]
    ])

    await safe_edit_message(callback, text, docs_keyboard)
    await callback.answer()

async def cb_api_security(callback: CallbackQuery):
    """Handle API security settings"""
    if not callback.message:
        return

    text = """
🔐 <b>API Security Settings</b>

🛡️ <b>Advanced Security Configuration</b>

🔒 <b>Current Security Status:</b>
• ✅ <b>Encryption:</b> AES-256 Active
• ✅ <b>Rate Limiting:</b> 1000/hour
• ✅ <b>IP Filtering:</b> Disabled
• ✅ <b>Request Logging:</b> Enabled

🌐 <b>Access Control:</b>
• 🔓 <b>IP Whitelist:</b> Not configured
• 🔄 <b>Allowed Methods:</b> GET, POST
• 📊 <b>CORS:</b> Enabled
• 🕐 <b>Token Expiry:</b> Never

🔔 <b>Security Alerts:</b>
• ✅ Suspicious activity monitoring
• ✅ Failed login attempt alerts
• ✅ Rate limit breach notifications
• ✅ Unusual pattern detection

⚙️ <b>Security Features Coming Soon:</b>
• IP-based access control
• Custom rate limiting
• Two-factor authentication
• Advanced threat detection

🔧 <b>Advanced security configuration under development!</b>
"""

    security_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Regenerate Key", callback_data="regenerate_api"),
            InlineKeyboardButton(text="📊 View Logs", callback_data="api_logs")
        ],
        [
            InlineKeyboardButton(text="⬅️ API Dashboard", callback_data="api_key")
        ]
    ])

    await safe_edit_message(callback, text, security_keyboard)
    await callback.answer()

async def cb_test_api(callback: CallbackQuery):
    """Handle API testing"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})
    api_key = user_data.get('api_key')

    if not api_key or api_key == 'Not generated':
        text = """
⚠️ <b>No API Key Found</b>

🔑 <b>API testing के लिए पहले API key create करें</b>
"""

        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Create API Key", callback_data="create_api_key")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="api_key")]
        ])

        await safe_edit_message(callback, text, back_keyboard)
        await callback.answer()
        return

    text = f"""
💻 <b>API Testing Console</b>

🧪 <b>Test Your API Integration</b>

🔑 <b>API Key:</b> {api_key[:16]}...

⚡ <b>Quick Tests:</b>

🔸 <b>Test 1: Authentication</b>
<code>curl -H "Authorization: Bearer {api_key}" \\
https://api.indiasocialpanel.com/v1/profile</code>

🔸 <b>Test 2: Get Services</b>
<code>curl -H "Authorization: Bearer {api_key}" \\
https://api.indiasocialpanel.com/v1/services</code>

🔸 <b>Test 3: Check Balance</b>
<code>curl -H "Authorization: Bearer {api_key}" \\
https://api.indiasocialpanel.com/v1/balance</code>

📊 <b>Expected Response:</b>
<code>{{
  "status": "success",
  "data": {{...}},
  "message": "Request successful"
}}</code>

🛠️ <b>Online API tester coming soon!</b>
💡 <b>For now, use above curl commands in terminal</b>
"""

    test_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Copy Test Commands", callback_data="copy_test_commands"),
            InlineKeyboardButton(text="📚 Documentation", callback_data="api_docs")
        ],
        [
            InlineKeyboardButton(text="⬅️ API Dashboard", callback_data="api_key")
        ]
    ])

    await safe_edit_message(callback, text, test_keyboard)
    await callback.answer()

async def cb_api_examples(callback: CallbackQuery):
    """Handle API code examples"""
    if not callback.message:
        return

    text = """
📋 <b>API Code Examples</b>

💻 <b>Integration Examples in Multiple Languages</b>

🐍 <b>Python Example:</b>
<code>
import requests

api_key = "YOUR_API_KEY"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Get services
response = requests.get(
    "https://api.indiasocialpanel.com/v1/services",
    headers=headers
)

# Create order
order_data = {
    "service": 1,
    "link": "https://instagram.com/user",
    "quantity": 1000
}

response = requests.post(
    "https://api.indiasocialpanel.com/v1/orders",
    headers=headers,
    json=order_data
)
</code>

🟨 <b>JavaScript Example:</b>
<code>
const apiKey = 'YOUR_API_KEY';
const headers = {
    'Authorization': `Bearer ${apiKey}`,
    'Content-Type': 'application/json'
};

// Get services
fetch('https://api.indiasocialpanel.com/v1/services', {
    headers: headers
})
.then(response => response.json())
.then(data => console.log(data));
</code>

💙 <b>PHP Example:</b>
<code>
$api_key = 'YOUR_API_KEY';
$headers = [
    'Authorization: Bearer ' . $api_key,
    'Content-Type: application/json'
];

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, 
    'https://api.indiasocialpanel.com/v1/services');
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$response = curl_exec($ch);
curl_close($ch);
</code>

📱 <b>More examples and SDKs coming soon!</b>
"""

    examples_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📚 Full Documentation", callback_data="api_docs"),
            InlineKeyboardButton(text="💻 Test API", callback_data="test_api")
        ],
        [
            InlineKeyboardButton(text="⬅️ API Dashboard", callback_data="api_key")
        ]
    ])

    await safe_edit_message(callback, text, examples_keyboard)
    await callback.answer()

async def cb_copy_test_commands(callback: CallbackQuery):
    """Handle copying test commands"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})
    api_key = user_data.get('api_key')

    if not api_key or api_key == 'Not generated':
        await callback.answer("❌ Create API key first!", show_alert=True)
        return

    text = f"""
📋 <b>Test Commands (Ready to Copy)</b>

🔍 <b>Get Services List:</b>
<code>curl -H "Authorization: Bearer {api_key}" https://api.indiasocialpanel.com/v1/services</code>

📊 <b>Check Balance:</b>
<code>curl -H "Authorization: Bearer {api_key}" https://api.indiasocialpanel.com/v1/balance</code>

🛒 <b>Create Order:</b>
<code>curl -X POST -H "Authorization: Bearer {api_key}" -H "Content-Type: application/json" -d '{{"service":"1","link":"https://instagram.com/username","quantity":"100"}}' https://api.indiasocialpanel.com/v1/order</code>

📱 <b>Long press on any command to copy</b>
💡 <b>Replace YOUR_URL and quantities as needed</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Full Documentation", callback_data="api_docs")],
        [InlineKeyboardButton(text="⬅️ API Dashboard", callback_data="api_key")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

async def cb_copy_api_key(callback: CallbackQuery):
    """Handle copying API key"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})
    api_key = user_data.get('api_key')

    if api_key and api_key != 'Not generated':
        text = f"""
📋 <b>Your API Key (Ready to Copy)</b>

🔑 <b>Full API Key:</b>
<code>{api_key}</code>

📱 <b>How to Copy:</b>
• <b>Mobile:</b> Long press on key above → Copy
• <b>Desktop:</b> Triple click to select → Ctrl+C

💡 <b>API key को secure place में store करें</b>

⚠️ <b>Security Reminder:</b>
• Keep it confidential
• Use environment variables  
• Never share publicly
• Monitor usage regularly
"""

        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ API Dashboard", callback_data="api_key")]
        ])

        await safe_edit_message(callback, text, back_keyboard)
        await callback.answer()  # No popup alert
    else:
        await callback.answer("❌ No API key found!", show_alert=True)

# ========== EDIT PROFILE ==========
def get_edit_profile_menu() -> InlineKeyboardMarkup:
    """Build edit profile menu with all editing options"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Edit Name", callback_data="edit_name"),
            InlineKeyboardButton(text="📱 Edit Phone", callback_data="edit_phone")
        ],
        [
            InlineKeyboardButton(text="📧 Edit Email", callback_data="edit_email"),
            InlineKeyboardButton(text="🖼️ Update Photo", callback_data="edit_photo")
        ],
        [
            InlineKeyboardButton(text="💼 Edit Bio", callback_data="edit_bio"),
            InlineKeyboardButton(text="🎯 Edit Username", callback_data="edit_username")
        ],
        [
            InlineKeyboardButton(text="🌍 Location", callback_data="edit_location"),
            InlineKeyboardButton(text="🎂 Birthday", callback_data="edit_birthday")
        ],
        [
            InlineKeyboardButton(text="🔄 Sync Telegram Data", callback_data="sync_telegram_data"),
            InlineKeyboardButton(text="👀 Preview Profile", callback_data="preview_profile")
        ],
        [
            InlineKeyboardButton(text="⬅️ My Account", callback_data="my_account")
        ]
    ])

async def cb_edit_profile(callback: CallbackQuery):
    """Handle profile editing dashboard"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})
    telegram_user = callback.from_user

    # Get Telegram user details for display
    telegram_first_name = telegram_user.first_name or "Not Available"
    telegram_last_name = telegram_user.last_name or ""
    telegram_username = telegram_user.username or "Not Available"
    telegram_language = telegram_user.language_code or "en"
    telegram_is_premium = getattr(telegram_user, 'is_premium', False)

    # Calculate profile completion
    profile_fields = ['full_name', 'phone_number', 'email', 'bio', 'location', 'birthday']
    completed_fields = sum(1 for field in profile_fields if user_data.get(field))
    completion_percentage = int((completed_fields / len(profile_fields)) * 100)

    # Progress bar
    progress_filled = "█" * (completion_percentage // 10)
    progress_empty = "░" * (10 - (completion_percentage // 10))
    progress_bar = f"{progress_filled}{progress_empty}"

    text = f"""
✏️ <b>Edit Profile Dashboard</b>

📊 <b>Profile Completion: {completion_percentage}%</b>
{progress_bar} <code>{completion_percentage}%</code>

👤 <b>Current Profile Information:</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━

🆔 <b>User ID:</b> <code>{user_id}</code>
📝 <b>Full Name:</b> {user_data.get('full_name', '❌ Not Set')}
📱 <b>Phone:</b> {user_data.get('phone_number', '❌ Not Set')}
📧 <b>Email:</b> {user_data.get('email', '❌ Not Set')}
💬 <b>Bio:</b> {user_data.get('bio', '❌ Not Set')}
🌍 <b>Location:</b> {user_data.get('location', '❌ Not Set')}
🎂 <b>Birthday:</b> {user_data.get('birthday', '❌ Not Set')}

📱 <b>Telegram Account Details:</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 <b>Telegram Name:</b> {telegram_first_name} {telegram_last_name}
🏷️ <b>Username:</b> @{telegram_username}
🗣️ <b>Language:</b> {telegram_language.upper()}
💎 <b>Premium:</b> {'✅ Yes' if telegram_is_premium else '❌ No'}
📅 <b>Account Created:</b> {format_time(user_data.get('join_date', ''))}
📊 <b>Profile Status:</b> {'🟢 Complete' if completion_percentage == 100 else '🟡 Incomplete'}

🔧 <b>Quick Actions:</b>
• Update any field instantly
• Sync latest Telegram data
• Preview how profile looks
• Upload profile photo

💡 <b>Choose what you want to edit:</b>
"""

    await safe_edit_message(callback, text, get_edit_profile_menu())
    await callback.answer()

# ========== INDIVIDUAL FIELD EDITING HANDLERS ==========
async def cb_edit_name(callback: CallbackQuery):
    """Handle name editing"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    current_name = users_data.get(user_id, {}).get('full_name', 'Not Set')

    # Set user state for name editing
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "editing_name"

    text = f"""
✏️ <b>Edit Full Name</b>

📝 <b>Current Name:</b> {current_name}

💬 <b>Please send your new full name:</b>

⚠️ <b>Examples:</b>
• Rahul Kumar Singh
• Priya Sharma
• Arjun Patel

💡 <b>Tips:</b>
• Use your real name for better service
• Avoid special characters
• Maximum 50 characters allowed

🔙 <b>Send /cancel to go back</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer()

async def cb_edit_phone(callback: CallbackQuery):
    """Handle phone editing"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    current_phone = users_data.get(user_id, {}).get('phone_number', 'Not Set')

    # Set user state for phone editing
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "editing_phone"

    text = f"""
📱 <b>Edit Phone Number</b>

📞 <b>Current Phone:</b> {current_phone}

💬 <b>Please send your new phone number:</b>

⚠️ <b>Formats Accepted:</b>
• +91 9876543210
• 9876543210
• +919876543210

💡 <b>Important:</b>
• Include country code for international numbers
• Only Indian (+91) and international numbers
• Used for account verification and support

🔙 <b>Send /cancel to go back</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer()

async def cb_edit_email(callback: CallbackQuery):
    """Handle email editing"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    current_email = users_data.get(user_id, {}).get('email', 'Not Set')

    # Set user state for email editing
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "editing_email"

    text = f"""
📧 <b>Edit Email Address</b>

📬 <b>Current Email:</b> {current_email}

💬 <b>Please send your new email address:</b>

⚠️ <b>Examples:</b>
• your.name@gmail.com
• user123@yahoo.co.in
• professional@company.com

💡 <b>Important:</b>
• Use a valid email address
• Required for important notifications
• Used for password reset (future)
• Keep it secure and accessible

🔙 <b>Send /cancel to go back</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer()

async def cb_edit_bio(callback: CallbackQuery):
    """Handle bio editing"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    current_bio = users_data.get(user_id, {}).get('bio', 'Not Set')

    # Set user state for bio editing
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "editing_bio"

    text = f"""
💬 <b>Edit Bio/About</b>

📝 <b>Current Bio:</b> {current_bio}

💬 <b>Please send your new bio/about information:</b>

⚠️ <b>Examples:</b>
• Digital Marketing Expert from Mumbai
• Social Media Manager & Content Creator
• Entrepreneur | SMM Enthusiast | Growth Hacker
• Helping brands grow online since 2020

💡 <b>Tips:</b>
• Keep it professional and relevant
• Mention your expertise or interests
• Maximum 200 characters
• Optional but recommended

🔙 <b>Send /cancel to go back</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer()

async def cb_edit_username(callback: CallbackQuery):
    """Handle username editing"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    telegram_username = callback.from_user.username or "Not Available"

    text = f"""
🎯 <b>Edit Username</b>

🏷️ <b>Current Telegram Username:</b> @{telegram_username}

⚠️ <b>Important Information:</b>

🔒 <b>Username Cannot Be Changed Here</b>
• Telegram usernames can only be changed in Telegram app
• This is linked to your Telegram account security
• We display your current Telegram username

📱 <b>To Change Your Telegram Username:</b>
1. Open Telegram app
2. Go to Settings → Username
3. Change your username there
4. Come back and use "Sync Telegram Data"

🔄 <b>Alternative:</b>
• Use "Sync Telegram Data" to update info
• We'll fetch your latest Telegram details

💡 <b>Note:</b> Some users don't have Telegram usernames, and that's okay!
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Sync Telegram Data", callback_data="sync_telegram_data"),
            InlineKeyboardButton(text="❓ Help", callback_data="username_help")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Edit Profile", callback_data="edit_profile")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

async def cb_edit_location(callback: CallbackQuery):
    """Handle location editing"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    current_location = users_data.get(user_id, {}).get('location', 'Not Set')

    # Set user state for location editing
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "editing_location"

    text = f"""
🌍 <b>Edit Location</b>

📍 <b>Current Location:</b> {current_location}

💬 <b>Please send your location:</b>

⚠️ <b>Examples:</b>
• Mumbai, Maharashtra, India
• Delhi, India
• Pune, MH
• Bangalore, Karnataka

💡 <b>Tips:</b>
• Include city and state for clarity
• Optional but helps in regional offers
• Used for location-based services
• Keep it general (city level)

🔙 <b>Send /cancel to go back</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer()

async def cb_edit_birthday(callback: CallbackQuery):
    """Handle birthday editing"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    current_birthday = users_data.get(user_id, {}).get('birthday', 'Not Set')

    # Set user state for birthday editing
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "editing_birthday"

    text = f"""
🎂 <b>Edit Birthday</b>

📅 <b>Current Birthday:</b> {current_birthday}

💬 <b>Please send your birthday:</b>

⚠️ <b>Supported Formats:</b>
• DD/MM/YYYY (25/12/1995)
• DD-MM-YYYY (25-12-1995)
• DD/MM (25/12)
• Month DD (December 25)

💡 <b>Benefits:</b>
• Receive special birthday offers
• Birthday month bonuses
• Personalized wishes
• Optional field for privacy

🔙 <b>Send /cancel to go back</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer()

async def cb_edit_photo(callback: CallbackQuery):
    """Handle profile photo editing"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Set user state for photo editing
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "editing_photo"

    text = f"""
🖼️ <b>Update Profile Photo</b>

📸 <b>Photo Upload Instructions:</b>

💬 <b>Send a photo to update your profile picture:</b>

⚠️ <b>Requirements:</b>
• Send as photo (not document)
• Maximum size: 10MB
• Supported formats: JPG, PNG
• Square photos work best
• Clear, professional image recommended

💡 <b>Tips:</b>
• Use a clear headshot for best results
• Avoid group photos or unclear images
• Professional photos create better impression
• This will be your display picture

🔒 <b>Privacy:</b>
Your photo is stored securely and used only for your profile display.

🔙 <b>Send /cancel to go back</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer()

async def cb_sync_telegram_data(callback: CallbackQuery):
    """Handle syncing Telegram data"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    telegram_user = callback.from_user

    # Update user data with latest Telegram information
    if user_id in users_data:
        users_data[user_id]['username'] = telegram_user.username or ""
        users_data[user_id]['first_name'] = telegram_user.first_name or ""
        users_data[user_id]['last_name'] = telegram_user.last_name or ""
        users_data[user_id]['language_code'] = telegram_user.language_code or "en"
        users_data[user_id]['is_premium'] = getattr(telegram_user, 'is_premium', False)
        users_data[user_id]['last_sync'] = time.time()

    text = f"""
🔄 <b>Telegram Data Synced Successfully!</b>

✅ <b>Updated Information:</b>

👤 <b>Name:</b> {telegram_user.first_name or 'N/A'} {telegram_user.last_name or ''}
🏷️ <b>Username:</b> @{telegram_user.username or 'Not Set'}
🗣️ <b>Language:</b> {(telegram_user.language_code or 'en').upper()}
💎 <b>Premium Status:</b> {'✅ Premium' if getattr(telegram_user, 'is_premium', False) else '❌ Standard'}
🕐 <b>Sync Time:</b> Just now

🎯 <b>What Was Synced:</b>
• Latest Telegram profile name
• Current username (if available)
• Language preference
• Premium status
• Account metadata

💡 <b>Benefits of Syncing:</b>
• Always up-to-date information
• Better personalized experience
• Enhanced security verification
• Improved customer support

✨ <b>Your profile now reflects the latest Telegram data!</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👀 Preview Profile", callback_data="preview_profile"),
            InlineKeyboardButton(text="✏️ Continue Editing", callback_data="edit_profile")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer("✅ Telegram data synced successfully!", show_alert=True)

async def cb_preview_profile(callback: CallbackQuery):
    """Handle profile preview"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})
    telegram_user = callback.from_user

    # Calculate profile score
    profile_fields = ['full_name', 'phone_number', 'email', 'bio', 'location', 'birthday']
    completed_fields = sum(1 for field in profile_fields if user_data.get(field))
    profile_score = int((completed_fields / len(profile_fields)) * 100)

    # Profile strength indicator
    if profile_score >= 90:
        strength = "🌟 Excellent"
        strength_color = "🟢"
    elif profile_score >= 70:
        strength = "🔥 Very Good"
        strength_color = "🟡"
    elif profile_score >= 50:
        strength = "👍 Good"
        strength_color = "🟠"
    else:
        strength = "⚠️ Needs Improvement"
        strength_color = "🔴"

    # Get user timezone and format join date
    user_language = getattr(telegram_user, 'language_code', 'en') or user_data.get('language_code', 'en')
    timezone_info = get_user_timezone_info(user_language)
    join_date_formatted = format_join_date_with_timezone(
        user_data.get('join_date', ''), 
        timezone_info['timezone']
    )

    text = f"""
👀 <b>Profile Preview</b>

{strength_color} <b>Profile Strength: {strength} ({profile_score}%)</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 <b>PUBLIC PROFILE PREVIEW</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━

🆔 <b>User ID:</b> {user_id}
📝 <b>Name:</b> {user_data.get('full_name', '❌ Not Set')}
🏷️ <b>Username:</b> @{telegram_user.username or 'Not Available'}
💬 <b>Bio:</b> {user_data.get('bio', '❌ Not Set')}
🌍 <b>Location:</b> {user_data.get('location', '❌ Not Set')}
🎂 <b>Birthday:</b> {user_data.get('birthday', '❌ Not Set')}

━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>ACCOUNT STATISTICS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>Total Spent:</b> {format_currency(user_data.get('total_spent', 0.0)) if format_currency else f"₹{user_data.get('total_spent', 0.0):.2f}"}
🛒 <b>Orders:</b> {user_data.get('orders_count', 0)}
📅 <b>Joined:</b> {join_date_formatted}
🌍 <b>Timezone:</b> {timezone_info['name']} ({timezone_info['offset']})
⭐ <b>Account Status:</b> ✅ Active

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 <b>PRIVATE INFORMATION</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 <b>Phone:</b> {user_data.get('phone_number', '❌ Not Set')}
📧 <b>Email:</b> {user_data.get('email', '❌ Not Set')}
💎 <b>Telegram Premium:</b> {'✅ Yes' if getattr(telegram_user, 'is_premium', False) else '❌ No'}

💡 <b>This is how your profile appears to others</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Edit Profile", callback_data="edit_profile"),
            InlineKeyboardButton(text="📊 My Account", callback_data="my_account")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

# ========== USER STATISTICS ==========
async def cb_user_stats(callback: CallbackQuery):
    """Handle user statistics display"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})

    # Calculate stats
    total_orders = len([o for o in orders_data.values() if o.get('user_id') == user_id])
    completed_orders = len([o for o in orders_data.values() if o.get('user_id') == user_id and o.get('status') == 'completed'])
    success_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0

    text = f"""
📊 <b>User Statistics</b>

👤 <b>Account Overview:</b>
🆔 <b>User ID:</b> {user_id}
📅 <b>Member Since:</b> {format_time(user_data.get('join_date', '')) if format_time else user_data.get('join_date', 'Unknown')}
🏆 <b>Account Level:</b> Standard

💰 <b>Financial Stats:</b>
💳 <b>Current Balance:</b> {format_currency(user_data.get('balance', 0.0)) if format_currency else f"₹{user_data.get('balance', 0.0):.2f}"}
💸 <b>Total Spent:</b> {format_currency(user_data.get('total_spent', 0.0)) if format_currency else f"₹{user_data.get('total_spent', 0.0):.2f}"}
📈 <b>Average Order:</b> {format_currency(user_data.get('total_spent', 0.0) / max(total_orders, 1)) if format_currency else f"₹{user_data.get('total_spent', 0.0) / max(total_orders, 1):.2f}"}

📦 <b>Order Statistics:</b>
🛒 <b>Total Orders:</b> {total_orders}
✅ <b>Completed:</b> {completed_orders}
📊 <b>Success Rate:</b> {success_rate:.1f}%

🎯 <b>Activity Level:</b> {'Active' if total_orders > 0 else 'New User'}
"""

    await safe_edit_message(callback, text, get_back_to_account_keyboard())
    await callback.answer()

# ========== NEW ACCOUNT FEATURES ==========
async def cb_smart_alerts(callback: CallbackQuery):
    """Handle smart alerts settings"""
    if not callback.message:
        return

    text = """
🔔 <b>Smart Alerts</b>

⚡ <b>Intelligent Notification System</b>

📱 <b>Alert Types:</b>
• Order completion notifications
• Balance low warnings
• Special offer alerts
• Service updates
• System announcements

🎯 <b>Customization Options:</b>
• Choose notification frequency
• Select alert categories
• Set spending thresholds
• Enable/disable sounds

🔧 <b>Coming Soon:</b>
Advanced alert customization features are being developed!
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Alert Settings", callback_data="alert_settings")],
        [InlineKeyboardButton(text="⬅️ My Account", callback_data="my_account")]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

async def cb_language_settings(callback: CallbackQuery):
    """Handle language settings"""
    if not callback.message:
        return

    text = """
🌐 <b>Language Settings / भाषा सेटिंग्स</b>

🗣️ <b>Available Languages:</b>

🇮🇳 <b>हिंदी (Hindi)</b> - Default
🇬🇧 <b>English</b> - Available
🇮🇳 <b>मराठी (Marathi)</b> - Coming Soon
🇮🇳 <b>தமிழ் (Tamil)</b> - Coming Soon
🇮🇳 <b>বাংলা (Bengali)</b> - Coming Soon

💡 <b>Current Language:</b> हिंदी + English (Mixed)

🔧 <b>Note:</b>
Currently bot supports Hindi-English mix for better understanding.
More regional languages coming soon!
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌎 Regions", callback_data="language_regions"), # New button to select region
            InlineKeyboardButton(text="⭐ Popular", callback_data="lang_region_popular") # Popular languages
        ],
        [
            InlineKeyboardButton(text="🇮🇳 Hindi", callback_data="select_lang_hindi"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="select_lang_english")
        ],
        [InlineKeyboardButton(text="⬅️ My Account", callback_data="my_account")]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

async def cb_account_preferences(callback: CallbackQuery):
    """Handle account preferences"""
    if not callback.message:
        return

    text = """
🎯 <b>Account Preferences</b>

⚙️ <b>Customization Options:</b>

🎨 <b>Interface Preferences:</b>
• Theme selection (Light/Dark)
• Menu layout options
• Display currency format
• Time zone settings

📊 <b>Dashboard Settings:</b>
• Default view preferences
• Chart display options
• Quick action buttons
• Statistics visibility

🔔 <b>Notification Preferences:</b>
• Telegram notifications
• Email notifications (future)
• SMS alerts (premium)
• Push notifications

💡 <b>Advanced Settings:</b>
• Auto-renewal preferences
• Security timeout
• API access levels
• Data export options
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎨 Interface", callback_data="interface_prefs"),
            InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard_prefs")
        ],
        [InlineKeyboardButton(text="⬅️ My Account", callback_data="my_account")]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

async def cb_security_settings(callback: CallbackQuery):
    """Handle security settings"""
    if not callback.message:
        return

    text = """
🔐 <b>Security Settings</b>

🛡️ <b>Account Security Features:</b>

🔑 <b>Authentication:</b>
• Two-factor authentication (2FA)
• Login alerts and notifications
• Session management
• Suspicious activity monitoring

🚨 <b>Security Alerts:</b>
• Unknown device login alerts
• API key usage monitoring
• Large transaction notifications
• Account access attempts

💳 <b>Payment Security:</b>
• Transaction verification
• Spending limit controls
• Payment method verification
• Refund request tracking

🔍 <b>Privacy Controls:</b>
• Data visibility settings
• Activity log management
• Information sharing options
• Account deletion requests

⚠️ <b>Security Status:</b> ✅ All systems secure
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔐 Enable 2FA", callback_data="enable_2fa"),
            InlineKeyboardButton(text="📱 Login Alerts", callback_data="login_alerts")
        ],
        [
            InlineKeyboardButton(text="💳 Payment Security", callback_data="payment_security"),
            InlineKeyboardButton(text="🔍 Privacy", callback_data="privacy_settings")
        ],
        [InlineKeyboardButton(text="⬅️ My Account", callback_data="my_account")]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

async def cb_payment_methods(callback: CallbackQuery):
    """Handle payment methods management"""
    if not callback.message:
        return

    text = """
💳 <b>Payment Methods</b>

💰 <b>Available Payment Options:</b>

🇮🇳 <b>Indian Payment Methods:</b>
• 📱 UPI (Google Pay, PhonePe, Paytm)
• 🏦 Net Banking (All major banks)
• 💳 Debit/Credit Cards (Visa, Mastercard, RuPay)
• 💸 Wallets (Paytm, Amazon Pay, JioMoney)

🌍 <b>International Methods:</b>
• 💳 International Cards
• 🌐 PayPal (Coming Soon)
• ₿ Cryptocurrency (Future)

⚡ <b>Quick Pay Features:</b>
• Save payment methods securely
• One-click payments
• Auto-reload balance
• Payment reminders

🔐 <b>Security:</b>
• PCI DSS compliance
• 256-bit SSL encryption
• No card details stored
• Instant transaction alerts

💡 <b>Payment Tips:</b>
• UPI payments are instant and free
• Cards may have small processing fees
• Bulk payments get better rates
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Add Funds", callback_data="add_funds"),
            InlineKeyboardButton(text="💳 Manage Cards", callback_data="manage_cards")
        ],
        [
            InlineKeyboardButton(text="📱 UPI Settings", callback_data="upi_settings"),
            InlineKeyboardButton(text="🔄 Auto-reload", callback_data="auto_reload")
        ],
        [InlineKeyboardButton(text="⬅️ My Account", callback_data="my_account")]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

# ========== LANGUAGE REGION HANDLERS ==========
async def cb_language_regions(callback: CallbackQuery):
    """Handle selection of language regions"""
    if not callback.message:
        return

    text = """
🌍 <b>Language Regions</b>

🗺️ <b>Explore languages by geographical region or popularity</b>

💡 <b>Choose a category to browse languages:</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇮🇳 India", callback_data="lang_region_indian"),
            InlineKeyboardButton(text="⭐ Popular", callback_data="lang_region_popular")
        ],
        [
            InlineKeyboardButton(text="🌍 International", callback_data="lang_region_international"),
            InlineKeyboardButton(text="🇪🇺 European", callback_data="lang_region_european")
        ],
        [
            InlineKeyboardButton(text="🌏 Asian", callback_data="lang_region_asian"),
            InlineKeyboardButton(text="🌐 Middle East & Africa", callback_data="lang_region_middle_east")
        ],
        [
            InlineKeyboardButton(text="🌎 Americas", callback_data="lang_region_americas")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Language Settings", callback_data="language_settings")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

async def cb_lang_region_indian(callback: CallbackQuery):
    """Handle Indian languages selection"""
    if not callback.message:
        return

    text = """
🇮🇳 <b>Indian Languages / भारतीय भाषाएं</b>

🕉️ <b>राष्ट्रीय और क्षेत्रीय भाषाएं</b>

🗣️ <b>22 Official Languages + Regional dialects</b>

💡 <b>Choose your preferred Indian language:</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇮🇳 हिंदी (Hindi)", callback_data="select_lang_hindi"),
            InlineKeyboardButton(text="🇬🇧 English (India)", callback_data="select_lang_english_in")
        ],
        [
            InlineKeyboardButton(text="🇮🇳 বাংলা (Bengali)", callback_data="select_lang_bengali"),
            InlineKeyboardButton(text="🇮🇳 తెలుగు (Telugu)", callback_data="select_lang_telugu")
        ],
        [
            InlineKeyboardButton(text="🇮🇳 મરાઠી (Marathi)", callback_data="select_lang_marathi"),
            InlineKeyboardButton(text="🇮🇳 தமிழ் (Tamil)", callback_data="select_lang_tamil")
        ],
        [
            InlineKeyboardButton(text="🇮🇳 ગુજરાતી (Gujarati)", callback_data="select_lang_gujarati"),
            InlineKeyboardButton(text="🇮🇳 ಕನ್ನಡ (Kannada)", callback_data="select_lang_kannada")
        ],
        [
            InlineKeyboardButton(text="🇮🇳 മലയാളം (Malayalam)", callback_data="select_lang_malayalam"),
            InlineKeyboardButton(text="🇮🇳 ଓଡ଼ିଆ (Odia)", callback_data="select_lang_odia")
        ],
        [
            InlineKeyboardButton(text="🇮🇳 ਪੰਜਾਬੀ (Punjabi)", callback_data="select_lang_punjabi"),
            InlineKeyboardButton(text="🇮🇳 اردو (Urdu)", callback_data="select_lang_urdu")
        ],
        [
            InlineKeyboardButton(text="🇮🇳 অসমীয়া (Assamese)", callback_data="select_lang_assamese"),
            InlineKeyboardButton(text="🇮🇳 संस्कृत (Sanskrit)", callback_data="select_lang_sanskrit")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Language Settings", callback_data="language_settings")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

async def cb_lang_region_international(callback: CallbackQuery):
    """Handle international languages selection"""
    if not callback.message:
        return

    text = """
🌍 <b>International Languages</b>

🗺️ <b>Most Popular Global Languages</b>

💼 <b>Business & Communication languages worldwide</b>

🌐 <b>Choose your preferred international language:</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇸 English (US)", callback_data="select_lang_english_us"),
            InlineKeyboardButton(text="🇨🇳 中文 (Chinese)", callback_data="select_lang_chinese")
        ],
        [
            InlineKeyboardButton(text="🇪🇸 Español (Spanish)", callback_data="select_lang_spanish"),
            InlineKeyboardButton(text="🇫🇷 Français (French)", callback_data="select_lang_french")
        ],
        [
            InlineKeyboardButton(text="🇩🇪 Deutsch (German)", callback_data="select_lang_german"),
            InlineKeyboardButton(text="🇷🇺 Русский (Russian)", callback_data="select_lang_russian")
        ],
        [
            InlineKeyboardButton(text="🇯🇵 日本語 (Japanese)", callback_data="select_lang_japanese"),
            InlineKeyboardButton(text="🇰🇷 한국어 (Korean)", callback_data="select_lang_korean")
        ],
        [
            InlineKeyboardButton(text="🇧🇷 Português (Portuguese)", callback_data="select_lang_portuguese"),
            InlineKeyboardButton(text="🇮🇹 Italiano (Italian)", callback_data="select_lang_italian")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Language Settings", callback_data="language_settings")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

async def cb_lang_region_european(callback: CallbackQuery):
    """Handle European languages selection"""
    if not callback.message:
        return

    text = """
🇪🇺 <b>European Languages</b>

🏰 <b>Languages of Europe</b>

💎 <b>Rich cultural and linguistic diversity</b>

🗣️ <b>Choose your preferred European language:</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇬🇧 English (UK)", callback_data="select_lang_english_uk"),
            InlineKeyboardButton(text="🇩🇪 Deutsch (German)", callback_data="select_lang_german")
        ],
        [
            InlineKeyboardButton(text="🇫🇷 Français (French)", callback_data="select_lang_french"),
            InlineKeyboardButton(text="🇪🇸 Español (Spanish)", callback_data="select_lang_spanish")
        ],
        [
            InlineKeyboardButton(text="🇮🇹 Italiano (Italian)", callback_data="select_lang_italian"),
            InlineKeyboardButton(text="🇳🇱 Nederlands (Dutch)", callback_data="select_lang_dutch")
        ],
        [
            InlineKeyboardButton(text="🇵🇱 Polski (Polish)", callback_data="select_lang_polish"),
            InlineKeyboardButton(text="🇷🇺 Русский (Russian)", callback_data="select_lang_russian")
        ],
        [
            InlineKeyboardButton(text="🇺🇦 Українська (Ukrainian)", callback_data="select_lang_ukrainian"),
            InlineKeyboardButton(text="🇬🇷 Ελληνικά (Greek)", callback_data="select_lang_greek")
        ],
        [
            InlineKeyboardButton(text="🇸🇪 Svenska (Swedish)", callback_data="select_lang_swedish"),
            InlineKeyboardButton(text="🇳🇴 Norsk (Norwegian)", callback_data="select_lang_norwegian")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Language Settings", callback_data="language_settings")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

async def cb_lang_region_asian(callback: CallbackQuery):
    """Handle Asian languages selection"""
    if not callback.message:
        return

    text = """
🇦🇸 <b>Asian Languages</b>

🏯 <b>Languages of Asia-Pacific Region</b>

🌸 <b>Diverse cultures and ancient civilizations</b>

🗣️ <b>Choose your preferred Asian language:</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇨🇳 中文 (Chinese)", callback_data="select_lang_chinese"),
            InlineKeyboardButton(text="🇯🇵 日本語 (Japanese)", callback_data="select_lang_japanese")
        ],
        [
            InlineKeyboardButton(text="🇰🇷 한국어 (Korean)", callback_data="select_lang_korean"),
            InlineKeyboardButton(text="🇹🇭 ไทย (Thai)", callback_data="select_lang_thai")
        ],
        [
            InlineKeyboardButton(text="🇻🇳 Tiếng Việt (Vietnamese)", callback_data="select_lang_vietnamese"),
            InlineKeyboardButton(text="🇮🇩 Bahasa Indonesia", callback_data="select_lang_indonesian")
        ],
        [
            InlineKeyboardButton(text="🇲🇾 Bahasa Malaysia", callback_data="select_lang_malay"),
            InlineKeyboardButton(text="🇵🇭 Filipino", callback_data="select_lang_filipino")
        ],
        [
            InlineKeyboardButton(text="🇱🇰 සිංහල (Sinhala)", callback_data="select_lang_sinhala"),
            InlineKeyboardButton(text="🇲🇲 မြန်မာ (Myanmar)", callback_data="select_lang_myanmar")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Language Settings", callback_data="language_settings")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

async def cb_lang_region_middle_east(callback: CallbackQuery):
    """Handle Middle East & African languages selection"""
    if not callback.message:
        return

    text = """
🇦🇫 <b>Middle East & African Languages</b>

🕌 <b>Languages of Middle East & Africa</b>

🌍 <b>Rich heritage and diverse cultures</b>

🗣️ <b>Choose your preferred language:</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇸🇦 العربية (Arabic)", callback_data="select_lang_arabic"),
            InlineKeyboardButton(text="🇮🇷 فارسی (Persian)", callback_data="select_lang_persian")
        ],
        [
            InlineKeyboardButton(text="🇹🇷 Türkçe (Turkish)", callback_data="select_lang_turkish"),
            InlineKeyboardButton(text="🇮🇱 עברית (Hebrew)", callback_data="select_lang_hebrew")
        ],
        [
            InlineKeyboardButton(text="🇪🇹 አማርኛ (Amharic)", callback_data="select_lang_amharic"),
            InlineKeyboardButton(text="🇿🇦 Afrikaans", callback_data="select_lang_afrikaans")
        ],
        [
            InlineKeyboardButton(text="🇳🇬 Hausa", callback_data="select_lang_hausa"),
            InlineKeyboardButton(text="🇰🇪 Kiswahili", callback_data="select_lang_swahili")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Language Settings", callback_data="language_settings")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

async def cb_lang_region_americas(callback: CallbackQuery):
    """Handle Americas languages selection"""
    if not callback.message:
        return

    text = """
🌎 <b>Americas Languages</b>

🗽 <b>Languages of North & South America</b>

🌎 <b>From Canada to Argentina</b>

🗣️ <b>Choose your preferred language:</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇸 English (US)", callback_data="select_lang_english_us"),
            InlineKeyboardButton(text="🇨🇦 English (Canada)", callback_data="select_lang_english_ca")
        ],
        [
            InlineKeyboardButton(text="🇪🇸 Español (Spanish)", callback_data="select_lang_spanish"),
            InlineKeyboardButton(text="🇧🇷 Português (Portuguese)", callback_data="select_lang_portuguese")
        ],
        [
            InlineKeyboardButton(text="🇨🇦 Français (French-CA)", callback_data="select_lang_french_ca"),
            InlineKeyboardButton(text="🇲🇽 Español (Mexico)", callback_data="select_lang_spanish_mx")
        ],
        [
            InlineKeyboardButton(text="🇦🇷 Español (Argentina)", callback_data="select_lang_spanish_ar"),
            InlineKeyboardButton(text="🇵🇪 Quechua", callback_data="select_lang_quechua")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Language Settings", callback_data="language_settings")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

async def cb_lang_region_popular(callback: CallbackQuery):
    """Handle most popular languages selection"""
    if not callback.message:
        return

    text = """
⭐ <b>Most Popular Languages</b>

📊 <b>Top 10 Most Used Languages</b>

🌟 <b>Based on global user preference</b>

💡 <b>Quick access to popular choices:</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇮🇳 हिंदी (Hindi) ⭐", callback_data="select_lang_hindi"),
            InlineKeyboardButton(text="🇬🇧 English ⭐", callback_data="select_lang_english")
        ],
        [
            InlineKeyboardButton(text="🇨🇳 中文 (Chinese) ⭐", callback_data="select_lang_chinese"),
            InlineKeyboardButton(text="🇪🇸 Español ⭐", callback_data="select_lang_spanish")
        ],
        [
            InlineKeyboardButton(text="🇸🇦 العربية (Arabic) ⭐", callback_data="select_lang_arabic"),
            InlineKeyboardButton(text="🇧🇷 Português ⭐", callback_data="select_lang_portuguese")
        ],
        [
            InlineKeyboardButton(text="🇷🇺 Русский ⭐", callback_data="select_lang_russian"),
            InlineKeyboardButton(text="🇯🇵 日本語 ⭐", callback_data="select_lang_japanese")
        ],
        [
            InlineKeyboardButton(text="🇫🇷 Français ⭐", callback_data="select_lang_french"),
            InlineKeyboardButton(text="🇩🇪 Deutsch ⭐", callback_data="select_lang_german")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Language Settings", callback_data="language_settings")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

async def cb_language_select(callback: CallbackQuery):
    """Handle individual language selection"""
    if not callback.message or not callback.data:
        return

    # Extract language from callback data
    language_code = callback.data.replace("select_lang_", "")

    # Language mapping for display names
    language_names = {
        "hindi": "🇮🇳 हिंदी (Hindi)",
        "english": "🇬🇧 English",
        "english_in": "🇮🇳 English (India)",
        "english_us": "🇺🇸 English (US)",
        "english_uk": "🇬🇧 English (UK)",
        "english_ca": "🇨🇦 English (Canada)",
        "chinese": "🇨🇳 中文 (Chinese)",
        "spanish": "🇪🇸 Español (Spanish)",
        "spanish_mx": "🇲🇽 Español (Mexico)",
        "spanish_ar": "🇦🇷 Español (Argentina)",
        "french": "🇫🇷 Français (French)",
        "french_ca": "🇨🇦 Français (French-CA)",
        "german": "🇩🇪 Deutsch (German)",
        "russian": "🇷🇺 Русский (Russian)",
        "japanese": "🇯🇵 日本語 (Japanese)",
        "korean": "🇰🇷 한국어 (Korean)",
        "portuguese": "🇧🇷 Português (Portuguese)",
        "italian": "🇮🇹 Italiano (Italian)",
        "arabic": "🇸🇦 العربية (Arabic)",
        "bengali": "🇮🇳 বাংলা (Bengali)",
        "telugu": "🇮🇳 తెలుగు (Telugu)",
        "marathi": "🇮🇳 મરાઠી (Marathi)",
        "tamil": "🇮🇳 தமிழ் (Tamil)",
        "gujarati": "🇮🇳 ગુજરાતી (Gujarati)",
        "kannada": "🇮🇳 ಕನ್ನಡ (Kannada)",
        "malayalam": "🇮🇳 മലയാളം (Malayalam)",
        "odia": "🇮🇳 ଓଡ଼ିଆ (Odia)",
        "punjabi": "🇮🇳 ਪੰਜਾਬੀ (Punjabi)",
        "urdu": "🇮🇳اردو (Urdu)",
        "assamese": "🇮🇳 অসমীয়া (Assamese)",
        "sanskrit": "🇮🇳 संस्कृत (Sanskrit)",
        "thai": "🇹🇭 ไทย (Thai)",
        "vietnamese": "🇻🇳 Tiếng Việt (Vietnamese)",
        "indonesian": "🇮🇩 Bahasa Indonesia",
        "malay": "🇲🇾 Bahasa Malaysia",
        "filipino": "🇵🇭 Filipino",
        "sinhala": "🇱🇰 සිංහල (Sinhala)",
        "myanmar": "🇲🇲 မြန်မာ (Myanmar)",
        "persian": "🇮🇷 فارسی (Persian)",
        "turkish": "🇹🇷 Türkçe (Turkish)",
        "hebrew": "🇮🇱 עברית (Hebrew)",
        "amharic": "🇪🇹 አማርኛ (Amharic)",
        "afrikaans": "🇿🇦 Afrikaans",
        "hausa": "🇳🇬 Hausa",
        "swahili": "🇰🇪 Kiswahili",
        "dutch": "🇳🇱 Nederlands (Dutch)",
        "polish": "🇵🇱 Polski (Polish)",
        "ukrainian": "🇺🇦 Українська (Ukrainian)",
        "greek": "🇬🇷 Ελληνικά (Greek)",
        "swedish": "🇸🇪 Svenska (Swedish)",
        "norwegian": "🇳🇴 Norsk (Norwegian)",
        "quechua": "🇵🇪 Quechua"
    }

    selected_language = language_names.get(language_code, "Selected Language")

    text = f"""
✅ <b>Language Selected!</b>

🌐 <b>Selected Language:</b> {selected_language}

🚀 <b>Great Choice!</b>

💡 <b>Language Implementation Status:</b>
• ✅ Interface Ready
• 🔄 Translation In Progress
• 🎯 Coming Very Soon

🔮 <b>What's Next:</b>
• Complete translation system
• Native language support
• Cultural localization
• Region-specific content

📢 <b>Notification:</b>
आपको language ready होने पर notification मिल जाएगी!

🙏 <b>Thank you for choosing India Social Panel!</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔔 Enable Notifications", callback_data="enable_lang_notifications"),
            InlineKeyboardButton(text="🌐 Try Another Language", callback_data="language_settings")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main"),
            InlineKeyboardButton(text="👤 My Account", callback_data="my_account")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer(f"✅ {selected_language} selected! Coming soon...", show_alert=True)

# ========== ACCESS TOKEN & LOGOUT HANDLERS ==========
async def cb_copy_access_token_myaccount(callback: CallbackQuery):
    """Handle access token copy from My Account section"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})
    access_token = user_data.get('access_token', '')

    if access_token:
        text = f"""
🔑 <b>Your Access Token</b>

📋 <b>Access Token (Ready to Copy):</b>
<code>{access_token}</code>

📱 <b>How to Copy:</b>
• <b>Mobile:</b> Long press on token above → Copy
• <b>Desktop:</b> Triple click to select → Ctrl+C

🔐 <b>Security Information:</b>
• यह token आपके account की key है
• इसे safely store करें  
• अगली बार login के लिए इसकी जरूरत होगी
• Token को किसी के साथ share न करें

💡 <b>Usage:</b>
• New device पर login करने के लिए
• Account recovery के लिए
• Secure access के लिए

⚠️ <b>Keep this token private and secure!</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📞 Contact Support", url=f"https://t.me/tech_support_admin"),
                InlineKeyboardButton(text="🔄 Regenerate Token", callback_data="regenerate_access_token")
            ],
            [
                InlineKeyboardButton(text="⬅️ My Account", callback_data="my_account")
            ]
        ])

        await safe_edit_message(callback, text, keyboard)
        await callback.answer()  # No popup alert
    else:
        await callback.answer("❌ Access token not found! Contact support.", show_alert=True)

async def cb_logout_account(callback: CallbackQuery):
    """Handle logout account request with confirmation"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})
    user_display_name = user_data.get('full_name', 'User')

    text = f"""
🚪 <b>Logout Account</b>

⚠️ <b>Account Logout Confirmation</b>

👤 <b>Current Account:</b> {user_display_name}
📱 <b>Phone:</b> {user_data.get('phone_number', 'N/A')}
💰 <b>Balance:</b> {format_currency(user_data.get('balance', 0.0)) if format_currency else f"₹{user_data.get('balance', 0.0):.2f}"}

🔴 <b>Logout करने से क्या होगा:</b>
• Account temporarily deactivated रहेगा
• सभी services access बंद हो जाएंगी  
• Main menu में वापस "Create Account" और "Login" options मिलेंगे
• Data safe रहेगा - कुछ भी delete नहीं होगा
• Same phone/token से दोबारा login कर सकते हैं

💡 <b>Logout के बाद:</b>
• Account create करने का option मिलेगा
• पुराने account में login करने का option भी मिलेगा  
• Access token same रहेगा

❓ <b>क्या आप वाकई logout करना चाहते हैं?</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚪 Yes, Logout", callback_data="confirm_logout"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="my_account")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

async def cb_confirm_logout(callback: CallbackQuery):
    """Confirm and execute logout"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})
    user_display_name = user_data.get('full_name', 'User')

    # Set account as not created (logout)
    users_data[user_id]['account_created'] = False

    # Clear any current user state
    if user_id in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    text = f"""
✅ <b>Successfully Logged Out!</b>

👋 <b>Goodbye {user_display_name}!</b>

🔓 <b>Account logout successful</b>

💡 <b>आप अब दोबारा:</b>
• नया account create कर सकते हैं
• पुराने account में login कर सकते हैं (Phone/Token से)
• सभी services access करने के लिए account required है

🔐 <b>Login Options:</b>
• Phone Number से login करें
• Access Token से login करें
• या बिल्कुल नया account बनाएं

🎯 <b>अपना next action choose करें:</b>
"""

    # Import get_initial_options_menu to show login/create options
    from account_creation import get_initial_options_menu

    await safe_edit_message(callback, text, get_initial_options_menu())
    await callback.answer("✅ Account logout successful!", show_alert=True)

async def cb_regenerate_access_token(callback: CallbackQuery):
    """Handle access token regeneration"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})

    # Generate new access token using the same function from account_creation
    from account_creation import generate_token

    username = user_data.get('full_name', '')
    phone = user_data.get('phone_number', '')
    email = user_data.get('email', '')

    # Determine if it was originally from Telegram name (check if matches current Telegram name)
    telegram_user = callback.from_user
    telegram_name = telegram_user.first_name if telegram_user else ""
    is_telegram_name = (username == telegram_name)

    # Generate new token
    new_access_token = generate_token(username, phone, email, is_telegram_name)

    # Store new token
    old_token = user_data.get('access_token', 'N/A')
    users_data[user_id]['access_token'] = new_access_token

    text = f"""
🔄 <b>Access Token Regenerated!</b>

🔑 <b>New Access Token:</b>
<code>{new_access_token}</code>

✅ <b>Token Update Complete:</b>
• 🗑️ Old token permanently invalidated
• 🔒 New token activated instantly  
• 🛡️ Enhanced security applied
• 📅 Regenerated: Just now

⚠️ <b>Important:</b>
• पुराना token अब काम नहीं करेगा
• नया token safe place में store करें
• Next time इसी token से login करें

💡 <b>Copy new access token और safely store करें</b>

🔒 <b>Security Enhancement Applied Successfully!</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ My Account", callback_data="my_account")
        ]
    ])

    await safe_edit_message(callback, text, keyboard)
    await callback.answer("🔄 New access token generated!", show_alert=True)

# ========== ACCOUNT CREATION FUNCTIONS MOVED TO account_creation.py ==========
# All account creation input handlers moved to account_creation.py
