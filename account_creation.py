# -*- coding: utf-8 -*-
"""
Account Creation Module - India Social Panel
Separate module for all account creation and login functionality
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
from aiogram import F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)

# Global variables (will be initialized from main.py)
dp: Any = None
users_data: Dict[int, Dict[str, Any]] = {}
user_state: Dict[int, Dict[str, Any]] = {}
safe_edit_message: Any = None
init_user: Any = None
mark_user_for_notification: Any = None
is_message_old: Any = None
bot: Any = None
START_TIME: float = 0

def get_account_creation_menu() -> InlineKeyboardMarkup:
    """Build account creation menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Create Account", callback_data="create_account")]
    ])

# Duplicate functions removed - already defined above

def get_account_complete_menu() -> InlineKeyboardMarkup:
    """Build menu after account creation"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 My Account", callback_data="my_account"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

def get_initial_options_menu() -> InlineKeyboardMarkup:
    """Build initial options menu with create account and login"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Create New Account", callback_data="create_account"),
            InlineKeyboardButton(text="🔐 Login to Account", callback_data="login_account")
        ],
        [
            InlineKeyboardButton(text="❓ Help & Support", callback_data="help_support")
        ]
    ])

def init_account_creation_handlers(main_dp, main_users_data, main_user_state, main_safe_edit_message, 
                                 main_init_user, main_mark_user_for_notification, main_is_message_old, 
                                 main_bot, main_start_time):
    """Initialize account creation handlers with references from main.py"""
    global dp, users_data, user_state, safe_edit_message, init_user, mark_user_for_notification, is_message_old, bot, START_TIME

    dp = main_dp
    users_data = main_users_data
    user_state = main_user_state
    safe_edit_message = main_safe_edit_message
    init_user = main_init_user
    mark_user_for_notification = main_mark_user_for_notification
    is_message_old = main_is_message_old
    bot = main_bot
    START_TIME = main_start_time

    # Register all account creation handlers
    register_account_creation_handlers()

def register_account_creation_handlers():
    """Register all account creation callback handlers"""
    if dp:
        dp.callback_query.register(cb_login_account, F.data == "login_account")
        dp.callback_query.register(cb_create_account, F.data == "create_account")
        dp.callback_query.register(cb_use_telegram_name, F.data == "use_telegram_name")
        dp.callback_query.register(cb_use_custom_name, F.data == "use_custom_name")
        dp.callback_query.register(cb_manual_phone_entry, F.data == "manual_phone_entry")
        dp.callback_query.register(cb_share_telegram_contact, F.data == "share_telegram_contact")

        # Register message handlers for account creation
        dp.message.register(handle_contact_sharing, F.contact)
        dp.message.register(handle_text_input, F.text)

# ========== ACTUAL ACCOUNT CREATION HANDLERS ==========
async def cb_login_account(callback: CallbackQuery):
    """Handle existing user login"""
    if not callback.message or not callback.from_user:
        return

    # Check if callback is old (sent before bot restart)
    if callback.message.date and callback.message.date.timestamp() < START_TIME:
        mark_user_for_notification(callback.from_user.id)
        return  # Ignore old callbacks

    user_id = callback.from_user.id

    # Initialize user state if not exists
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "waiting_login_phone"

    text = """
🔐 <b>Login to Your Account</b>

📱 <b>Account Verification</b>

ЁЯТб <b>рдХреГрдкрдпрд╛ рдЕрдкрдирд╛ registered phone number рднреЗрдЬреЗрдВ:</b>

⚠️ <b>Example:</b> +91 9876543210
ЁЯФТ <b>Security:</b> Phone number verification рдХреЗ рд▓рд┐рдП

ЁЯТб <b>рдЕрдЧрд░ phone number рднреВрд▓ рдЧрдП рд╣реИрдВ рддреЛ support рд╕реЗ contact рдХрд░реЗрдВ</b>
ЁЯУЮ <b>Support:</b> @achal_parvat
"""

    await safe_edit_message(callback, text)
    await callback.answer()

async def cb_create_account(callback: CallbackQuery):
    """Start account creation process"""
    if not callback.message or not callback.from_user:
        return

    # Check if callback is old (sent before bot restart)
    if callback.message.date and callback.message.date.timestamp() < START_TIME:
        mark_user_for_notification(callback.from_user.id)
        return  # Ignore old callbacks

    user_id = callback.from_user.id
    telegram_name = callback.from_user.first_name or "User"

    # Initialize user state if not exists
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "choosing_name_option"

    text = f"""
ЁЯУЛ <b>Account Creation - Step 1/3</b>

ЁЯСд <b>Name Selection</b>

ЁЯТб <b>рдЖрдк рдЕрдкрдиреЗ account рдХреЗ рд▓рд┐рдП рдХреМрди рд╕рд╛ name use рдХрд░рдирд╛ рдЪрд╛рд╣рддреЗ рд╣реИрдВ?</b>

ЁЯФ╕ <b>Your Telegram Name:</b> {telegram_name}
ЁЯФ╕ <b>Custom Name:</b> рдЕрдкрдиреА рдкрд╕рдВрдж рдХрд╛ name

тЪая╕П <b>Note:</b> Custom name рдореЗрдВ maximum 6 characters allowed рд╣реИрдВ (first name only)

ЁЯТм <b>рдЖрдк рдХреНрдпрд╛ choose рдХрд░рдирд╛ рдЪрд╛рд╣рддреЗ рд╣реИрдВ?</b>
"""

    name_choice_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="тЬЕ Telegram Name Use рдХрд░реВрдВ", callback_data="use_telegram_name"),
            InlineKeyboardButton(text="тЬПя╕П Custom Name рдбрд╛рд▓реВрдВ", callback_data="use_custom_name")
        ]
    ])

    await safe_edit_message(callback, text, name_choice_keyboard)
    await callback.answer()

async def cb_use_telegram_name(callback: CallbackQuery):
    """Use Telegram name for account creation"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    telegram_name = callback.from_user.first_name or "User"

    # Store telegram name and move to next step
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["data"]["full_name"] = telegram_name
    user_state[user_id]["current_step"] = "choosing_phone_option"

    text = f"""
тЬЕ <b>Name Successfully Selected!</b>

ЁЯСд <b>Selected Name:</b> {telegram_name}

ЁЯУЛ <b>Account Creation - Step 2/3</b>

ЁЯУ▒ <b>Phone Number Selection</b>

ЁЯТб <b>рдЖрдк phone number рдХреИрд╕реЗ provide рдХрд░рдирд╛ рдЪрд╛рд╣рддреЗ рд╣реИрдВ?</b>

ЁЯФ╕ <b>Telegram Contact:</b> рдЖрдкрдХрд╛ Telegram рдореЗрдВ saved contact number
ЁЯФ╕ <b>Manual Entry:</b> рдЕрдкрдиреА рдкрд╕рдВрдж рдХрд╛ рдХреЛрдИ рднреА number

тЪая╕П <b>Note:</b> Contact share рдХрд░рдиреЗ рд╕реЗ рдЖрдкрдХреА permission рдорд╛рдБрдЧреА рдЬрд╛рдПрдЧреА рдФрд░ рдЖрдкрдХрд╛ number automatically рднрд░ рдЬрд╛рдПрдЧрд╛

ЁЯТм <b>рдЖрдк рдХреНрдпрд╛ choose рдХрд░рдирд╛ рдЪрд╛рд╣рддреЗ рд╣реИрдВ?</b>
"""

    phone_choice_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="ЁЯУ▒ Telegram Contact Share рдХрд░реВрдВ", callback_data="share_telegram_contact"),
            InlineKeyboardButton(text="тЬПя╕П Manual Number рдбрд╛рд▓реВрдВ", callback_data="manual_phone_entry")
        ]
    ])

    await safe_edit_message(callback, text, phone_choice_keyboard)
    await callback.answer()

async def cb_use_custom_name(callback: CallbackQuery):
    """Use custom name for account creation"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Initialize user state if not exists
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "waiting_custom_name"

    text = """
тЬПя╕П <b>Custom Name Entry</b>

ЁЯУЛ <b>Account Creation - Step 1/3</b>

ЁЯУЭ <b>рдХреГрдкрдпрд╛ рдЕрдкрдирд╛ рдирд╛рдо рднреЗрдЬреЗрдВ:</b>

тЪая╕П <b>Rules:</b>
тАв Maximum 6 characters allowed
тАв First name only
тАв No special characters
тАв English рдпрд╛ Hindi рдореЗрдВ type рдХрд░реЗрдВ

ЁЯТм <b>Example:</b> Rahul, Priya, Arjun

ЁЯФЩ <b>рдЕрдкрдирд╛ name type рдХрд░рдХреЗ рднреЗрдЬ рджреЗрдВ:</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer()

async def cb_manual_phone_entry(callback: CallbackQuery):
    """Handle manual phone number entry"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Initialize user state if not exists
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "waiting_manual_phone"

    text = """
тЬПя╕П <b>Manual Phone Entry</b>

ЁЯУЛ <b>Account Creation - Step 2/3</b>

ЁЯУ▒ <b>рдХреГрдкрдпрд╛ рдЕрдкрдирд╛ Phone Number рднреЗрдЬреЗрдВ:</b>

тЪая╕П <b>Format Rules:</b>
тАв Must start with +91 (India)
тАв Total 13 characters
тАв Only numbers after +91
тАв No spaces or special characters

ЁЯТм <b>Examples:</b>
тАв +919876543210 тЬЕ
тАв +91 9876543210 тЭМ (space not allowed)
тАв 9876543210 тЭМ (country code missing)

ЁЯФЩ <b>рдЕрдкрдирд╛ complete phone number type рдХрд░рдХреЗ рднреЗрдЬ рджреЗрдВ:</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer()

async def cb_share_telegram_contact(callback: CallbackQuery):
    """Request Telegram contact sharing for phone number"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Initialize user state if not exists
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "waiting_contact_permission"

    text = """
ЁЯУ▒ <b>Telegram Contact Permission</b>

ЁЯФР <b>Contact Sharing Request</b>

ЁЯТб <b>рд╣рдореЗрдВ рдЖрдкрдХреЗ contact рдХреЛ access рдХрд░рдиреЗ рдХреА permission рдЪрд╛рд╣рд┐рдП</b>

тЬЕ <b>Benefits:</b>
тАв Automatic phone number fill
тАв Faster account creation
тАв No typing errors
тАв Secure & verified number

ЁЯФТ <b>Security:</b>
тАв рдЖрдкрдХрд╛ phone number safely store рд╣реЛрдЧрд╛
тАв рдХреЗрд╡рд▓ account creation рдХреЗ рд▓рд┐рдП use рд╣реЛрдЧрд╛
тАв Third party рдХреЗ рд╕рд╛рде share рдирд╣реАрдВ рд╣реЛрдЧрд╛
тАв Complete privacy protection

тЪая╕П <b>Permission Steps:</b>
1. рдиреАрдЪреЗ "Send Contact" button рдкрд░ click рдХрд░реЗрдВ
2. Telegram permission dialog рдЖрдПрдЧреА  
3. "Allow" рдпрд╛ "Share Contact" рдкрд░ click рдХрд░реЗрдВ
4. рдЖрдкрдХрд╛ number automatically рднрд░ рдЬрд╛рдПрдЧрд╛

ЁЯТм <b>Ready to share your contact?</b>
"""

    from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

    # Create contact request keyboard
    contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ЁЯУ▒ Send My Contact", request_contact=True)],
            [KeyboardButton(text="тЭМ Cancel & Enter Manually")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await safe_edit_message(callback, text)

    # Send new message with contact request keyboard
    await callback.message.answer(
        "ЁЯУ▒ <b>Neeche wale button se contact share рдХрд░реЗрдВ:</b>",
        reply_markup=contact_keyboard
    )

    await callback.answer()

# ========== CONTACT HANDLERS ==========
async def handle_contact_sharing(message):
    """Handle shared contact for phone number"""
    if not message.from_user or not message.contact:
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        mark_user_for_notification(message.from_user.id)
        return  # Ignore old messages

    user_id = message.from_user.id
    contact = message.contact
    current_step = user_state.get(user_id, {}).get("current_step")

    if current_step == "waiting_contact_permission":
        # User shared their contact
        if contact.user_id == user_id:
            # Contact belongs to the same user
            phone_number = contact.phone_number

            # Ensure phone starts with + for international format
            if not phone_number.startswith('+'):
                phone_number = f"+{phone_number}"

            # Store phone number and move to next step
            user_state[user_id]["data"]["phone_number"] = phone_number
            user_state[user_id]["current_step"] = "waiting_email"

            # Remove contact keyboard
            from aiogram.types import ReplyKeyboardRemove

            success_text = f"""
тЬЕ <b>Contact Successfully Shared!</b>

ЁЯУ▒ <b>Phone Number Received:</b> {phone_number}

ЁЯОЙ <b>Contact sharing successful!</b>

ЁЯУЛ <b>Account Creation - Step 3/3</b>

ЁЯУз <b>рдХреГрдкрдпрд╛ рдЕрдкрдирд╛ Email Address рднреЗрдЬреЗрдВ:</b>

тЪая╕П <b>Example:</b> your.email@gmail.com
ЁЯТм <b>Instruction:</b> рдЕрдкрдирд╛ email address type рдХрд░рдХреЗ рднреЗрдЬ рджреЗрдВ
"""

            await message.answer(success_text, reply_markup=ReplyKeyboardRemove())

        else:
            # User shared someone else's contact
            from aiogram.types import ReplyKeyboardRemove

            text = """
тЪая╕П <b>Wrong Contact Shared</b>

ЁЯЪл <b>рдЖрдкрдиреЗ рдХрд┐рд╕реА рдФрд░ рдХрд╛ contact share рдХрд┐рдпрд╛ рд╣реИ</b>

ЁЯТб <b>Solutions:</b>
тАв рдЕрдкрдирд╛ own contact share рдХрд░реЗрдВ
тАв "Manual Entry" option choose рдХрд░реЗрдВ
тАв Account creation restart рдХрд░реЗрдВ

ЁЯФТ <b>Security:</b> рдХреЗрд╡рд▓ рдЕрдкрдирд╛ own contact share рдХрд░реЗрдВ
"""

            manual_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="ЁЯФД Try Again", callback_data="share_telegram_contact"),
                    InlineKeyboardButton(text="тЬПя╕П Manual Entry", callback_data="manual_phone_entry")
                ]
            ])

            await message.answer(text, reply_markup=ReplyKeyboardRemove())
            await message.answer("ЁЯТб <b>Choose an option:</b>", reply_markup=manual_keyboard)

    else:
        # Contact shared without proper context
        text = """
ЁЯУ▒ <b>Contact Received</b>

ЁЯТб <b>Contact sharing рдХреЗрд╡рд▓ account creation рдХреЗ рджреМрд░рд╛рди allowed рд╣реИ</b>

ЁЯФД <b>рдЕрдЧрд░ рдЖрдк account create рдХрд░ рд░рд╣реЗ рд╣реИрдВ рддреЛ /start рдХрд░рдХреЗ restart рдХрд░реЗрдВ</b>
"""

        from aiogram.types import ReplyKeyboardRemove
        await message.answer(text, reply_markup=ReplyKeyboardRemove())

# ========== INPUT HANDLERS ==========
async def handle_text_input(message):
    """Handle text input for account creation"""
    if not message.from_user or not message.text:
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        mark_user_for_notification(message.from_user.id)
        return  # Ignore old messages

    user_id = message.from_user.id

    # Check if user is in account creation flow
    current_step = user_state.get(user_id, {}).get("current_step")

    # Only handle account creation related steps, ignore others
    account_creation_steps = ["waiting_login_phone", "waiting_custom_name", "waiting_manual_phone", "waiting_email"]

    if current_step not in account_creation_steps:
        return  # Let other handlers deal with non-account creation text

    if current_step == "waiting_login_phone":
        await handle_login_phone_verification(message, user_id)
    elif current_step == "waiting_custom_name":
        await handle_custom_name_input(message, user_id)
    elif current_step == "waiting_manual_phone":
        await handle_manual_phone_input(message, user_id)
    elif current_step == "waiting_email":
        await handle_email_input(message, user_id)

# Helper functions for text input handling
async def handle_login_phone_verification(message, user_id):
    """Handle login phone verification"""
    phone = message.text.strip()

    # Find user with matching phone number
    matching_user = None
    for uid, data in users_data.items():
        if data.get('phone_number') == phone:
            matching_user = uid
            break

    if matching_user and matching_user == user_id:
        # Phone matches, complete login
        users_data[user_id]['account_created'] = True
        user_state[user_id]["current_step"] = None
        user_state[user_id]["data"] = {}

        # Get user display name for login success
        user_display_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name or 'Friend'

        success_text = f"""
тЬЕ <b>Login Successful!</b>

ЁЯОЙ <b>Welcome back {user_display_name} to India Social Panel!</b>

ЁЯСд <b>Account Details:</b>
тАв Name: {users_data[user_id].get('full_name', 'N/A')}
тАв Phone: {phone}
тАв Balance: тВ╣{users_data[user_id].get('balance', 0.0):.2f}

ЁЯЪА <b>All features are now accessible!</b>
ЁЯТб <b>рдЖрдк рдЕрдм рд╕рднреА services рдХрд╛ рдЗрд╕реНрддреЗрдорд╛рд▓ рдХрд░ рд╕рдХрддреЗ рд╣реИрдВ</b>
"""

        # Import get_main_menu dynamically to avoid circular imports
        try:
            from main import get_main_menu
            await message.answer(success_text, reply_markup=get_main_menu())
        except ImportError:
            await message.answer(success_text)

    elif matching_user and matching_user != user_id:
        # Phone belongs to different user
        text = """
тЪая╕П <b>Account Mismatch</b>

ЁЯУ▒ <b>рдпрд╣ phone number рдХрд┐рд╕реА рдФрд░ account рд╕реЗ linked рд╣реИ</b>

ЁЯТб <b>Solutions:</b>
тАв рдЕрдкрдирд╛ correct phone number try рдХрд░реЗрдВ
тАв рдирдпрд╛ account create рдХрд░реЗрдВ
тАв Support рд╕реЗ contact рдХрд░реЗрдВ

ЁЯУЮ <b>Support:</b> @achal_parvat
"""

        user_state[user_id]["current_step"] = None

        retry_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="ЁЯФР Try Again", callback_data="login_account"),
                InlineKeyboardButton(text="ЁЯУЭ Create New Account", callback_data="create_account")
            ],
            [
                InlineKeyboardButton(text="ЁЯУЮ Contact Support", url=f"https://t.me/achal_parvat")
            ]
        ])

        await message.answer(text, reply_markup=retry_keyboard)

    else:
        # Phone not found in system
        text = """
тЭМ <b>Account Not Found</b>

ЁЯУ▒ <b>рдЗрд╕ phone number рд╕реЗ рдХреЛрдИ account registered рдирд╣реАрдВ рд╣реИ</b>

ЁЯТб <b>Options:</b>
тАв Phone number double-check рдХрд░реЗрдВ
тАв рдирдпрд╛ account create рдХрд░реЗрдВ
тАв Support рд╕реЗ help рд▓реЗрдВ

ЁЯдФ <b>рдкрд╣рд▓реЗ рд╕реЗ account рдирд╣реАрдВ рд╣реИ?</b>
"""

        user_state[user_id]["current_step"] = None

        options_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="ЁЯФР Try Different Number", callback_data="login_account"),
                InlineKeyboardButton(text="ЁЯУЭ Create New Account", callback_data="create_account")
            ],
            [
                InlineKeyboardButton(text="ЁЯУЮ Contact Support", url=f"https://t.me/achal_parvat")
            ]
        ])

        await message.answer(text, reply_markup=options_keyboard)

async def handle_custom_name_input(message, user_id):
    """Handle custom name input with validation"""
    custom_name = message.text.strip()

    # Validate name length (max 6 characters)
    if len(custom_name) > 6:
        await message.answer(
            "тЪая╕П <b>Name too long!</b>\n\n"
            "ЁЯУП <b>Maximum 6 characters allowed</b>\n"
            "ЁЯТб <b>Please enter a shorter name</b>\n\n"
            "ЁЯФД <b>Try again with max 6 characters</b>"
        )
        return

    if len(custom_name) < 2:
        await message.answer(
            "тЪая╕П <b>Name too short!</b>\n\n"
            "ЁЯУП <b>Minimum 2 characters required</b>\n"
            "ЁЯТб <b>Please enter a valid name</b>\n\n"
            "ЁЯФД <b>Try again with at least 2 characters</b>"
        )
        return

    # Initialize user state if not exists
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    # Store custom name and move to next step
    user_state[user_id]["data"]["full_name"] = custom_name
    user_state[user_id]["current_step"] = "choosing_phone_option"

    success_text = f"""
тЬЕ <b>Custom Name Successfully Added!</b>

ЁЯСд <b>Your Name:</b> {custom_name}

ЁЯУЛ <b>Account Creation - Step 2/3</b>

ЁЯУ▒ <b>Phone Number Selection</b>

ЁЯТб <b>рдЖрдк phone number рдХреИрд╕реЗ provide рдХрд░рдирд╛ рдЪрд╛рд╣рддреЗ рд╣реИрдВ?</b>

ЁЯФ╕ <b>Telegram Contact:</b> рдЖрдкрдХрд╛ Telegram рдореЗрдВ saved contact number
ЁЯФ╕ <b>Manual Entry:</b> рдЕрдкрдиреА рдкрд╕рдВрдж рдХрд╛ рдХреЛрдИ рднреА number

тЪая╕П <b>Note:</b> Contact share рдХрд░рдиреЗ рд╕реЗ рдЖрдкрдХреА permission рдорд╛рдБрдЧреА рдЬрд╛рдПрдЧреА рдФрд░ рдЖрдкрдХрд╛ number automatically рднрд░ рдЬрд╛рдПрдЧрд╛

ЁЯТм <b>рдЖрдк рдХреНрдпрд╛ choose рдХрд░рдирд╛ рдЪрд╛рд╣рддреЗ рд╣реИрдВ?</b>
"""

    phone_choice_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="ЁЯУ▒ Telegram Contact Share рдХрд░реВрдВ", callback_data="share_telegram_contact"),
            InlineKeyboardButton(text="тЬПя╕П Manual Number рдбрд╛рд▓реВрдВ", callback_data="manual_phone_entry")
        ]
    ])

    await message.answer(success_text, reply_markup=phone_choice_keyboard)

async def handle_manual_phone_input(message, user_id):
    """Handle manual phone number entry with comprehensive Indian validation"""
    phone_input = message.text.strip()

    # Remove any spaces, dashes, brackets or other common separators
    phone_cleaned = phone_input.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace(".", "")

    # Check if input contains any letters
    if any(char.isalpha() for char in phone_cleaned):
        await message.answer(
            "тЪая╕П <b>Letters Not Allowed!</b>\n\n"
            "ЁЯФд <b>Phone number рдореЗрдВ letters рдирд╣реАрдВ рд╣реЛ рд╕рдХрддреЗ</b>\n"
            "ЁЯФв <b>рдХреЗрд╡рд▓ numbers рдФрд░ +91 allowed рд╣реИ</b>\n"
            "ЁЯТб <b>Example:</b> +919876543210\n\n"
            "ЁЯФД <b>Try again with only numbers</b>"
        )
        return

    # Validate country code presence
    if not phone_cleaned.startswith('+91'):
        await message.answer(
            "тЪая╕П <b>Country Code Missing!</b>\n\n"
            "ЁЯЗоЁЯЗ│ <b>Indian numbers must start with +91</b>\n"
            "тЭМ <b>Numbers without +91 are not accepted</b>\n"
            "ЁЯТб <b>Example:</b> +919876543210\n\n"
            "ЁЯФД <b>Add +91 before your number</b>"
        )
        return

    # Check exact length (should be 13: +91 + 10 digits)
    if len(phone_cleaned) != 13:
        await message.answer(
            "тЪая╕П <b>Invalid Length!</b>\n\n"
            f"ЁЯУП <b>Entered length: {len(phone_cleaned)} characters</b>\n"
            "ЁЯУП <b>Required: Exactly 13 characters</b>\n"
            "ЁЯТб <b>Format:</b> +91 followed by 10 digits\n"
            "ЁЯТб <b>Example:</b> +919876543210\n\n"
            "ЁЯФД <b>Check your number length</b>"
        )
        return

    # Extract the 10-digit number part
    digits_part = phone_cleaned[3:]  # Remove +91

    # Check if only digits after +91
    if not digits_part.isdigit():
        await message.answer(
            "тЪая╕П <b>Invalid Characters!</b>\n\n"
            "ЁЯФв <b>Only numbers allowed after +91</b>\n"
            "тЭМ <b>No spaces, letters, or special characters</b>\n"
            "ЁЯТб <b>Example:</b> +919876543210\n\n"
            "ЁЯФД <b>Use only digits after +91</b>"
        )
        return

    # Check for invalid starting digits (Indian mobile rules)
    first_digit = digits_part[0]
    invalid_starting_digits = ['0', '1', '2', '3', '4', '5']

    if first_digit in invalid_starting_digits:
        await message.answer(
            "тЪая╕П <b>Invalid Starting Digit!</b>\n\n"
            f"ЁЯУ▒ <b>Indian mobile numbers cannot start with {first_digit}</b>\n"
            "тЬЕ <b>Valid starting digits:</b> 6, 7, 8, 9\n"
            "ЁЯТб <b>Example:</b> +919876543210, +917894561230\n\n"
            "ЁЯФД <b>Use a valid Indian mobile number</b>"
        )
        return

    # Store phone number and move to next step
    user_state[user_id]["data"]["phone_number"] = phone_cleaned
    user_state[user_id]["current_step"] = "waiting_email"

    success_text = f"""
тЬЕ <b>Phone Number Successfully Added!</b>

ЁЯУ▒ <b>Your Phone:</b> {phone_cleaned}

ЁЯУЛ <b>Account Creation - Step 3/3</b>

ЁЯУз <b>рдХреГрдкрдпрд╛ рдЕрдкрдирд╛ Email Address рднреЗрдЬреЗрдВ:</b>

тЪая╕П <b>Example:</b> your.email@gmail.com
ЁЯТм <b>Instruction:</b> рдЕрдкрдирд╛ email address type рдХрд░рдХреЗ рднреЗрдЬ рджреЗрдВ
"""

    await message.answer(success_text)

async def handle_email_input(message, user_id):
    """Handle email input for account creation completion"""
    email = message.text.strip()

    # Basic email validation
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_pattern, email):
        await message.answer(
            "тЪая╕П <b>Invalid Email Format!</b>\n\n"
            "ЁЯУз <b>Please enter a valid email address</b>\n"
            "ЁЯТб <b>Example:</b> your.email@gmail.com\n\n"
            "ЁЯФД <b>Try again with correct format</b>"
        )
        return

    # Store email and complete account creation
    user_state[user_id]["data"]["email"] = email

    # Save all data to users_data
    user_data = user_state[user_id]["data"]
    users_data[user_id] = {
        'full_name': user_data.get('full_name', ''),
        'phone_number': user_data.get('phone_number', ''),
        'email': email,
        'balance': 0.0,
        'account_created': True,
        'created_at': init_user(user_id)
    }

    # Clear user state
    user_state[user_id]["current_step"] = None
    user_state[user_id]["data"] = {}

    success_text = f"""
ЁЯОЙ <b>Account Created Successfully!</b>

тЬЕ <b>Welcome to India Social Panel!</b>

ЁЯСд <b>Your Account Details:</b>
тАв Name: {user_data.get('full_name', 'N/A')}
тАв Phone: {user_data.get('phone_number', 'N/A')}
тАв Email: {email}
тАв Balance: тВ╣0.00

ЁЯЪА <b>All features are now accessible!</b>
ЁЯТб <b>рдЖрдк рдЕрдм рд╕рднреА services рдХрд╛ рдЗрд╕реНрддреЗрдорд╛рд▓ рдХрд░ рд╕рдХрддреЗ рд╣реИрдВ</b>

ЁЯОп <b>Next Steps:</b>
тАв Add funds to your account
тАв Browse our premium services
тАв Place your first order
"""

    # Import get_main_menu dynamically to avoid circular imports
    try:
        from main import get_main_menu
        await message.answer(success_text, reply_markup=get_main_menu())
    except ImportError:
        await message.answer(success_text)
