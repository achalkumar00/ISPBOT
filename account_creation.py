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

# ========== ISP-256 PROTOCOL IMPLEMENTATION ==========
import random
import re

def generate_token(username: str, phone: str, email: str, is_telegram_name: bool = False) -> str:
    """
    Generate ISP-256 encoded token from user data

    Args:
        username: User's name
        phone: Phone number
        email: Email address
        is_telegram_name: True if username is from Telegram, False if manual

    Returns:
        Encoded token string with noise layer
    """

    # 1. Encode Username (A=01, B=02, ..., Z=26)
    def encode_username(name):
        encoded = ""
        for char in name.upper():
            if char.isalpha():
                # A=1, B=2, ..., Z=26, then format as 2-digit
                encoded += f"{ord(char) - ord('A') + 1:02d}"
            else:
                # For non-alphabetic characters, use their ASCII values
                encoded += f"{ord(char):02d}"
        return encoded

    # 2. Encode Phone (0=A, 1=B, 2=C, ..., 9=J)
    def encode_phone(phone_num):
        # Remove any non-digit characters first
        clean_phone = ''.join(char for char in phone_num if char.isdigit())
        encoded = ""
        for digit in clean_phone:
            # 0=A, 1=B, 2=C, 3=D, 4=E, 5=F, 6=G, 7=H, 8=I, 9=J
            encoded += chr(ord('A') + int(digit))
        return encoded

    # 3. Encode Email
    def encode_email(email_addr):
        # Split email into username and domain
        parts = email_addr.split('@')
        if len(parts) != 2:
            return email_addr  # Invalid email format, return as-is

        username_part, domain_part = parts

        # Encode username part like regular username
        encoded_username = encode_username(username_part)

        # Domain encoding
        domain_codes = {
            'gmail.com': 'G1',
            'yahoo.com': 'Y1',
            'hotmail.com': 'H1',
            'outlook.com': 'O1',
            'rediff.com': 'R1',
            'yandex.com': 'Y2',
            'proton.me': 'P1',
            'protonmail.com': 'P2'
        }

        domain_code = domain_codes.get(domain_part.lower(), 'X1')  # X1 for unknown domains

        return f"{encoded_username}@{domain_code}"

    # Encode all components
    encoded_username = encode_username(username)
    encoded_phone = encode_phone(phone)
    encoded_email = encode_email(email)

    # 4. Create flag (Σ for Telegram, empty for manual)
    flag = "Σ" if is_telegram_name else ""

    # 5. Assemble clean token
    clean_token = f"{flag}|{encoded_username}|{encoded_phone}|{encoded_email}"

    # 6. Add noise layer
    def add_noise_layer(token):
        noise_words = ['xcq', 'mbs', 'zqw', 'pnr']
        noise_symbols = ['*', ':', ';', '.', '∅']
        all_noise = noise_words + noise_symbols

        noisy_token = ""
        for i, char in enumerate(token):
            noisy_token += char
            # Add noise after every 3 characters
            if (i + 1) % 3 == 0 and i != len(token) - 1:
                noisy_token += random.choice(all_noise)

        return noisy_token

    # Generate final token with noise
    final_token = add_noise_layer(clean_token)

    return final_token

def decode_token(encoded_token: str) -> Dict[str, Any]:
    """
    Decode ISP-256 token back to original user data

    Args:
        encoded_token: The encoded token string

    Returns:
        Dictionary containing original user data
    """

    try:
        # 1. Remove noise layer
        def remove_noise_layer(token):
            noise_words = ['xcq', 'mbs', 'zqw', 'pnr']
            noise_symbols = ['*', ':', ';', '.', '∅']

            clean_token = token

            # Remove noise words
            for noise in noise_words:
                clean_token = clean_token.replace(noise, '')

            # Remove noise symbols
            for noise in noise_symbols:
                clean_token = clean_token.replace(noise, '')

            return clean_token

        # 2. Get clean token
        clean_token = remove_noise_layer(encoded_token)

        # 3. Split token by pipes
        parts = clean_token.split('|')
        if len(parts) != 4:
            raise ValueError("Invalid token format")

        flag_part, username_part, phone_part, email_part = parts

        # 4. Decode Username (01=A, 02=B, ..., 26=Z)
        def decode_username(encoded):
            if not encoded:
                return ""

            decoded = ""
            # Process pairs of digits
            for i in range(0, len(encoded), 2):
                if i + 1 < len(encoded):
                    two_digit = encoded[i:i+2]
                    try:
                        num = int(two_digit)
                        if 1 <= num <= 26:
                            # Convert back to letter
                            decoded += chr(ord('A') + num - 1)
                        else:
                            # Handle other ASCII values
                            decoded += chr(num)
                    except ValueError:
                        continue

            return decoded

        # 5. Decode Phone (A=0, B=1, C=2, ..., J=9)
        def decode_phone(encoded):
            decoded = ""
            for char in encoded:
                if 'A' <= char <= 'J':
                    # A=0, B=1, etc.
                    decoded += str(ord(char) - ord('A'))
                else:
                    decoded += char  # Keep non-encoded characters
            return decoded

        # 6. Decode Email
        def decode_email(encoded):
            if '@' not in encoded:
                return encoded

            parts = encoded.split('@')
            if len(parts) != 2:
                return encoded

            username_encoded, domain_code = parts

            # Decode username part
            decoded_username = decode_username(username_encoded)

            # Decode domain
            domain_codes = {
                'G1': 'gmail.com',
                'Y1': 'yahoo.com',
                'H1': 'hotmail.com',
                'O1': 'outlook.com',
                'R1': 'rediff.com',
                'Y2': 'yandex.com',
                'P1': 'proton.me',
                'P2': 'protonmail.com',
                'X1': 'unknown.com'
            }

            domain = domain_codes.get(domain_code, 'unknown.com')

            return f"{decoded_username}@{domain}"

        # Decode all parts
        is_telegram_name = (flag_part == "Σ")
        original_username = decode_username(username_part)
        original_phone = decode_phone(phone_part)
        original_email = decode_email(email_part)

        # Return decoded data
        return {
            'username': original_username,
            'phone': original_phone,
            'email': original_email,
            'is_telegram_name': is_telegram_name,
            'success': True
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Token decoding failed: {str(e)}"
        }

def get_account_creation_menu() -> InlineKeyboardMarkup:
    """Build account creation menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Create Account", callback_data="create_account")]
    ])

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
            InlineKeyboardButton(text="📝 Create New Account", callback_data="create_account")
        ],
        [
            InlineKeyboardButton(text="📱 Login with Phone", callback_data="login_account"),
            InlineKeyboardButton(text="🔐 Login with Token", callback_data="login_with_token")
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

        # Register new handlers for access token functionality
        dp.callback_query.register(cb_copy_access_token, F.data == "copy_my_token")
        dp.callback_query.register(cb_login_with_token, F.data == "login_with_token")

        # Register message handlers for account creation
        dp.message.register(handle_contact_sharing, F.contact)

        print("✅ Account creation handlers registered successfully")

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

📱 <b>कृपया अपना registered phone number भेजें:</b>

⚠️ <b>Example:</b> +91 9876543210
🔒 <b>Security:</b> Phone number verification के लिए

💡 <b>अगर phone number भूल गए हैं तो support से contact करें</b>
📞 <b>Support:</b> @tech_support_admin
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
📝 <b>Account Creation - Step 1/3</b>

👤 <b>Name Selection</b>

💡 <b>आप अपने account के लिए कौन सा name use करना चाहते हैं?</b>

🔸 <b>Your Telegram Name:</b> {telegram_name}
🔸 <b>Custom Name:</b> अपनी पसंद का name

⚠️ <b>Note:</b> Custom name में maximum 6 characters allowed हैं (first name only)

💬 <b>आप क्या choose करना चाहते हैं?</b>
"""

    name_choice_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Telegram Name Use करूं", callback_data="use_telegram_name"),
            InlineKeyboardButton(text="✏️ Custom Name डालूं", callback_data="use_custom_name")
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
✅ <b>Name Successfully Selected!</b>

👤 <b>Selected Name:</b> {telegram_name}

📝 <b>Account Creation - Step 2/3</b>

📱 <b>Phone Number Selection</b>

💡 <b>आप phone number कैसे provide करना चाहते हैं?</b>

🔸 <b>Telegram Contact:</b> आपका Telegram में saved contact number
🔸 <b>Manual Entry:</b> अपनी पसंद का कोई भी number

⚠️ <b>Note:</b> Contact share करने से आपकी permission मांगी जाएगी और आपका number automatically भर जाएगा

💬 <b>आप क्या choose करना चाहते हैं?</b>
"""

    phone_choice_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 Telegram Contact Share करूं", callback_data="share_telegram_contact"),
            InlineKeyboardButton(text="✏️ Manual Number डालूं", callback_data="manual_phone_entry")
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
✏️ <b>Custom Name Entry</b>

📝 <b>Account Creation - Step 1/3</b>

📝 <b>कृपया अपना नाम भेजें:</b>

⚠️ <b>Rules:</b>
• Maximum 6 characters allowed
• First name only
• No special characters
• English या Hindi में type करें

💬 <b>Example:</b> Rahul, Priya, Arjun

📤 <b>अपना name type करके भेज दें:</b>
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
✏️ <b>Manual Phone Entry</b>

📝 <b>Account Creation - Step 2/3</b>

📱 <b>कृपया अपना Phone Number भेजें:</b>

⚠️ <b>Format Rules:</b>
• Must start with +91 (India)
• Total 13 characters
• Only numbers after +91
• No spaces or special characters

💬 <b>Examples:</b>
• +919876543210 ✅
• +91 9876543210 ❌ (space not allowed)
• 9876543210 ❌ (country code missing)

📤 <b>अपना complete phone number type करके भेज दें:</b>
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
📱 <b>Telegram Contact Permission</b>

📤 <b>Contact Sharing Request</b>

💡 <b>हमें आपके contact को access करने की permission चाहिए</b>

✅ <b>Benefits:</b>
• Automatic phone number fill
• Faster account creation
• No typing errors
• Secure & verified number

🔒 <b>Security:</b>
• आपका phone number safely store होगा
• केवल account creation के लिए use होगा
• Third party के साथ share नहीं होगा
• Complete privacy protection

⚠️ <b>Permission Steps:</b>
1. नीचे "Send Contact" button पर click करें
2. Telegram permission dialog आएगी  
3. "Allow" या "Share Contact" पर click करें
4. आपका number automatically भर जाएगा

💬 <b>Ready to share your contact?</b>
"""

    from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

    # Create contact request keyboard
    contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Send My Contact", request_contact=True)],
            [KeyboardButton(text="❌ Cancel & Enter Manually")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await safe_edit_message(callback, text)

    # Send new message with contact request keyboard
    await callback.message.answer(
        "📱 <b>नीचे वाले button से contact share करें:</b>",
        reply_markup=contact_keyboard
    )

    await callback.answer()

# ========== CONTACT HANDLERS ==========
async def handle_contact_sharing(message):
    """Handle shared contact for phone number"""
    print(f"📞 Contact received from user {message.from_user.id if message.from_user else 'Unknown'}")

    if not message.from_user or not message.contact:
        print("❌ No user or contact found in message")
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        print(f"⏰ Contact message is old, marking user {message.from_user.id} for notification")
        mark_user_for_notification(message.from_user.id)
        return  # Ignore old messages

    user_id = message.from_user.id
    contact = message.contact
    current_step = user_state.get(user_id, {}).get("current_step")

    print(f"🔍 Contact DEBUG: User {user_id} current_step: {current_step}")
    print(f"🔍 Contact DEBUG: Contact user_id: {contact.user_id}")
    print(f"🔍 Contact DEBUG: Contact phone: {contact.phone_number}")

    if current_step == "waiting_contact_permission":
        # User shared their contact
        if contact.user_id == user_id:
            # Contact belongs to the same user
            phone_number = contact.phone_number
            print(f"✅ Contact belongs to user, phone: {phone_number}")

            # Ensure phone starts with + for international format
            if not phone_number.startswith('+'):
                phone_number = f"+{phone_number}"

            # Store phone number and move to next step
            user_state[user_id]["data"]["phone_number"] = phone_number
            user_state[user_id]["current_step"] = "waiting_email"

            print(f"✅ Updated user_state for {user_id}: {user_state[user_id]}")

            # Remove contact keyboard
            from aiogram.types import ReplyKeyboardRemove

            success_text = f"""
✅ <b>Contact Successfully Shared!</b>

📱 <b>Phone Number Received:</b> {phone_number}

👍 <b>Contact sharing successful!</b>

📝 <b>Account Creation - Step 3/3</b>

📧 <b>कृपया अपना Email Address भेजें:</b>

⚠️ <b>Example:</b> your.email@gmail.com
💬 <b>Instruction:</b> अपना email address type करके भेज दें
"""

            await message.answer(success_text, reply_markup=ReplyKeyboardRemove())
            print(f"✅ Email step message sent to user {user_id}")

        else:
            # User shared someone else's contact
            from aiogram.types import ReplyKeyboardRemove

            text = """
⚠️ <b>Wrong Contact Shared</b>

🚫 <b>आपने किसी और का contact share किया है</b>

💡 <b>Solutions:</b>
• अपना own contact share करें
• "Manual Entry" option choose करें
• Account creation restart करें

🔒 <b>Security:</b> केवल अपना own contact share करें
"""

            manual_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Try Again", callback_data="share_telegram_contact"),
                    InlineKeyboardButton(text="✏️ Manual Entry", callback_data="manual_phone_entry")
                ]
            ])

            await message.answer(text, reply_markup=ReplyKeyboardRemove())
            await message.answer("💡 <b>Choose an option:</b>", reply_markup=manual_keyboard)

    else:
        # Contact shared without proper context or step mismatch
        print(f"⚠️ Contact shared but current_step is {current_step}")

        # Force process contact if user is in any account creation flow
        if current_step in ["waiting_contact_permission", "choosing_phone_option", None]:
            print(f"🔄 Force processing contact for user {user_id}")

            # Force set to contact permission step and process
            user_state[user_id]["current_step"] = "waiting_contact_permission" 

            # Process contact
            if contact.user_id == user_id:
                phone_number = contact.phone_number
                if not phone_number.startswith('+'):
                    phone_number = f"+{phone_number}"

                user_state[user_id]["data"]["phone_number"] = phone_number
                user_state[user_id]["current_step"] = "waiting_email"

                from aiogram.types import ReplyKeyboardRemove
                success_text = f"""
✅ <b>Contact Successfully Processed!</b>

📱 <b>Phone Number:</b> {phone_number}

📝 <b>Account Creation - Step 3/3</b>

📧 <b>कृपया अपना Email Address भेजें:</b>

⚠️ <b>Example:</b> your.email@gmail.com
💬 <b>Instruction:</b> अपना email address type करके भेज दें
"""
                await message.answer(success_text, reply_markup=ReplyKeyboardRemove())
                return

        text = """
📱 <b>Contact Received</b>

💡 <b>Contact sharing केवल account creation के दौरान allowed है</b>

🔄 <b>अगर आप account create कर रहे हैं तो /start करके restart करें</b>
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
    text = message.text.strip()

    # Check if user is in account creation flow
    current_step = user_state.get(user_id, {}).get("current_step")

    print(f"🔍 ACCOUNT_CREATION DEBUG: User {user_id} sent text: '{text}'")
    print(f"🔍 ACCOUNT_CREATION DEBUG: User {user_id} current_step: {current_step}")
    print(f"🔍 ACCOUNT_CREATION DEBUG: Full user_state for {user_id}: {user_state.get(user_id, {})}")

    # Handle cancel & enter manually for contact sharing
    if current_step == "waiting_contact_permission" and text == "❌ Cancel & Enter Manually":
        user_state[user_id]["current_step"] = "waiting_manual_phone"

        text = """
✏️ <b>Manual Phone Entry</b>

📝 <b>Account Creation - Step 2/3</b>

📱 <b>कृपया अपना Phone Number भेजें:</b>

⚠️ <b>Format Rules:</b>
• Must start with +91 (India)
• Total 13 characters
• Only numbers after +91
• No spaces or special characters

💬 <b>Examples:</b>
• +919876543210 ✅
• +91 9876543210 ❌ (space not allowed)
• 9876543210 ❌ (country code missing)

📤 <b>अपना complete phone number type करके भेज दें:</b>
"""

        await message.answer(text)
        return

    # Only handle account creation related steps, ignore others
    account_creation_steps = ["waiting_login_phone", "waiting_custom_name", "waiting_manual_phone", "waiting_email", "waiting_access_token", "waiting_contact_permission"]

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
    elif current_step == "waiting_access_token":
        await handle_access_token_login(message, user_id)

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
✅ <b>Login Successful!</b>

🎉 <b>Welcome back {user_display_name} to India Social Panel!</b>

👤 <b>Account Details:</b>
• Name: {users_data[user_id].get('full_name', 'N/A')}
• Phone: {phone}
• Balance: ₹{users_data[user_id].get('balance', 0.0):.2f}

🚀 <b>All features are now accessible!</b>
💡 <b>आप अब सभी services का इस्तेमाल कर सकते हैं</b>
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
⚠️ <b>Account Mismatch</b>

📱 <b>यह phone number किसी और account से linked है</b>

💡 <b>Solutions:</b>
• अपना correct phone number try करें
• नया account create करें
• Support से contact करें

📞 <b>Support:</b> @tech_support_admin
"""

        user_state[user_id]["current_step"] = None

        retry_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Try Again", callback_data="login_account"),
                InlineKeyboardButton(text="📝 Create New Account", callback_data="create_account")
            ],
            [
                InlineKeyboardButton(text="📞 Contact Support", url=f"https://t.me/tech_support_admin")
            ]
        ])

        await message.answer(text, reply_markup=retry_keyboard)

    else:
        # Phone not found in system
        text = """
❌ <b>Account Not Found</b>

📱 <b>इस phone number से कोई account registered नहीं है</b>

💡 <b>Options:</b>
• Phone number double-check करें
• नया account create करें
• Support से help लें

🤔 <b>पहले से account नहीं है?</b>
"""

        user_state[user_id]["current_step"] = None

        options_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Try Different Number", callback_data="login_account"),
                InlineKeyboardButton(text="📝 Create New Account", callback_data="create_account")
            ],
            [
                InlineKeyboardButton(text="📞 Contact Support", url=f"https://t.me/tech_support_admin")
            ]
        ])

        await message.answer(text, reply_markup=options_keyboard)

async def handle_custom_name_input(message, user_id):
    """Handle custom name input with validation"""
    custom_name = message.text.strip()

    # Validate name length (max 6 characters)
    if len(custom_name) > 6:
        await message.answer(
            "⚠️ <b>Name too long!</b>\n\n"
            "📏 <b>Maximum 6 characters allowed</b>\n"
            "💡 <b>Please enter a shorter name</b>\n\n"
            "🔄 <b>Try again with max 6 characters</b>"
        )
        return

    if len(custom_name) < 2:
        await message.answer(
            "⚠️ <b>Name too short!</b>\n\n"
            "📏 <b>Minimum 2 characters required</b>\n"
            "💡 <b>Please enter a valid name</b>\n\n"
            "🔄 <b>Try again with at least 2 characters</b>"
        )
        return

    # Initialize user state if not exists
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    # Store custom name and move to next step
    user_state[user_id]["data"]["full_name"] = custom_name
    user_state[user_id]["current_step"] = "choosing_phone_option"

    success_text = f"""
✅ <b>Custom Name Successfully Added!</b>

👤 <b>Your Name:</b> {custom_name}

📝 <b>Account Creation - Step 2/3</b>

📱 <b>Phone Number Selection</b>

💡 <b>आप phone number कैसे provide करना चाहते हैं?</b>

🔸 <b>Telegram Contact:</b> आपका Telegram में saved contact number
🔸 <b>Manual Entry:</b> अपनी पसंद का कोई भी number

⚠️ <b>Note:</b> Contact share करने से आपकी permission मांगी जाएगी और आपका number automatically भर जाएगा

💬 <b>आप क्या choose करना चाहते हैं?</b>
"""

    phone_choice_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 Telegram Contact Share करूं", callback_data="share_telegram_contact"),
            InlineKeyboardButton(text="✏️ Manual Number डालूं", callback_data="manual_phone_entry")
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
            "⚠️ <b>Letters Not Allowed!</b>\n\n"
            "🔤 <b>Phone number में letters नहीं हो सकते</b>\n"
            "🔢 <b>केवल numbers और +91 allowed है</b>\n"
            "💡 <b>Example:</b> +919876543210\n\n"
            "🔄 <b>Try again with only numbers</b>"
        )
        return

    # Validate country code presence
    if not phone_cleaned.startswith('+91'):
        await message.answer(
            "⚠️ <b>Country Code Missing!</b>\n\n"
            "🇮🇳 <b>Indian numbers must start with +91</b>\n"
            "❌ <b>Numbers without +91 are not accepted</b>\n"
            "💡 <b>Example:</b> +919876543210\n\n"
            "🔄 <b>Add +91 before your number</b>"
        )
        return

    # Check exact length (should be 13: +91 + 10 digits)
    if len(phone_cleaned) != 13:
        await message.answer(
            "⚠️ <b>Invalid Length!</b>\n\n"
            f"📏 <b>Entered length: {len(phone_cleaned)} characters</b>\n"
            "📏 <b>Required: Exactly 13 characters</b>\n"
            "💡 <b>Format:</b> +91 followed by 10 digits\n"
            "💡 <b>Example:</b> +919876543210\n\n"
            "🔄 <b>Check your number length</b>"
        )
        return

    # Extract the 10-digit number part
    digits_part = phone_cleaned[3:]  # Remove +91

    # Check if only digits after +91
    if not digits_part.isdigit():
        await message.answer(
            "⚠️ <b>Invalid Characters!</b>\n\n"
            "🔢 <b>Only numbers allowed after +91</b>\n"
            "❌ <b>No spaces, letters, or special characters</b>\n"
            "💡 <b>Example:</b> +919876543210\n\n"
            "🔄 <b>Use only digits after +91</b>"
        )
        return

    # Check for invalid starting digits (Indian mobile rules)
    first_digit = digits_part[0]
    invalid_starting_digits = ['0', '1', '2', '3', '4', '5']

    if first_digit in invalid_starting_digits:
        await message.answer(
            "⚠️ <b>Invalid Starting Digit!</b>\n\n"
            f"📱 <b>Indian mobile numbers cannot start with {first_digit}</b>\n"
            "✅ <b>Valid starting digits:</b> 6, 7, 8, 9\n"
            "💡 <b>Example:</b> +919876543210, +917894561230\n\n"
            "🔄 <b>Use a valid Indian mobile number</b>"
        )
        return

    # Store phone number and move to next step
    user_state[user_id]["data"]["phone_number"] = phone_cleaned
    user_state[user_id]["current_step"] = "waiting_email"

    success_text = f"""
✅ <b>Phone Number Successfully Added!</b>

📱 <b>Your Phone:</b> {phone_cleaned}

📝 <b>Account Creation - Step 3/3</b>

📧 <b>कृपया अपना Email Address भेजें:</b>

⚠️ <b>Example:</b> your.email@gmail.com
💬 <b>Instruction:</b> अपना email address type करके भेज दें
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
            "⚠️ <b>Invalid Email Format!</b>\n\n"
            "📧 <b>Please enter a valid email address</b>\n"
            "💡 <b>Example:</b> your.email@gmail.com\n\n"
            "🔄 <b>Try again with correct format</b>"
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

    # Generate ISP-256 Access Token
    username = user_data.get('full_name', '')
    phone = user_data.get('phone_number', '')

    # Check if this was a Telegram name (stored in user state or detect from source)
    # We'll check if the name matches the original Telegram name for this determination
    telegram_user = message.from_user
    telegram_name = telegram_user.first_name if telegram_user else ""
    is_telegram_name = (username == telegram_name)

    # Generate the access token using ISP-256 protocol
    access_token = generate_token(username, phone, email, is_telegram_name)

    # Store the access token for future reference
    users_data[user_id]['access_token'] = access_token

    success_text = f"""
🎉 <b>Account Created Successfully!</b>

✅ <b>Welcome to India Social Panel!</b>

👤 <b>Your Account Details:</b>
• Name: {user_data.get('full_name', 'N/A')}
• Phone: {user_data.get('phone_number', 'N/A')}
• Email: {email}
• Balance: ₹0.00

🔐 <b>Your Secure Access Token:</b>
<code>{access_token}</code>

⚠️ <b>Important:</b>
• यह token आपके account की key है
• इसे safely store करें
• अगली बार login के लिए इसकी जरूरत होगी
• Token को किसी के साथ share न करें

🚀 <b>All features are now accessible!</b>
💡 <b>आप अब सभी services का इस्तेमाल कर सकते हैं</b>

🎯 <b>Next Steps:</b>
• Add funds to your account
• Browse our premium services  
• Place your first order
"""

    # Create keyboard with Copy Access Token button and main menu options  
    # Simple callback data to avoid Telegram limits
    account_success_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Copy Access Token", callback_data="copy_my_token")
        ],
        [
            InlineKeyboardButton(text="👤 My Account", callback_data="my_account"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

    await message.answer(success_text, reply_markup=account_success_keyboard)

# ========== ACCESS TOKEN HANDLERS ==========
async def cb_copy_access_token(callback: CallbackQuery):
    """Handle copy access token button click"""
    if not callback.message or not callback.from_user:
        return

    # Check if callback is old (sent before bot restart)
    if callback.message.date and callback.message.date.timestamp() < START_TIME:
        mark_user_for_notification(callback.from_user.id)
        return  # Ignore old callbacks

    # Get user's access token directly
    user_id = callback.from_user.id  
    token = users_data.get(user_id, {}).get('access_token', '')

    if token:
        copy_text = f"""
📋 <b>Access Token Copied!</b>

🔐 <b>Your Access Token:</b>
<code>{token}</code>

✅ <b>Token ready to copy!</b>
💡 <b>Long press on the code above and select "Copy" to copy your token</b>

⚠️ <b>Security Tips:</b>
• Save this token in a secure place
• Don't share with anyone
• Use this for future logins
• Keep it confidential

🔄 <b>Next time just use "Login with Token" option and paste this code</b>
"""

        # Create back to main menu keyboard
        copy_success_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 My Account", callback_data="my_account"),
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
            ]
        ])

        await safe_edit_message(callback, copy_text, copy_success_keyboard)
        await callback.answer("✅ Token ready to copy! Long press on the code above.")
    else:
        await callback.answer("❌ Error: Token not found!", show_alert=True)

async def cb_login_with_token(callback: CallbackQuery):
    """Handle login with access token"""
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

    user_state[user_id]["current_step"] = "waiting_access_token"

    text = """
🔐 <b>Login with Access Token</b>

🎯 <b>Token-Based Login</b>

🔑 <b>कृपया अपना Access Token भेजें:</b>

💡 <b>Instructions:</b>
• Copy your saved Access Token
• Paste it here as a message  
• Token will be verified automatically
• Account will login instantly

🔒 <b>Security:</b>
• Token-based login is 100% secure
• No password needed
• Direct access to your account
• Encrypted ISP-256 protocol

⚠️ <b>Note:</b> Token वही है जो आपको account creation के time मिला था

📤 <b>अपना Access Token paste करके भेज दें:</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer()

async def handle_access_token_login(message, user_id):
    """Handle access token login verification"""
    access_token = message.text.strip()

    try:
        # Decode the access token using ISP-256 protocol
        decoded_data = decode_token(access_token)

        if not decoded_data.get('success'):
            # Token decoding failed
            error_text = """
❌ <b>Invalid Access Token</b>

🔐 <b>Token decoding failed</b>

⚠️ <b>Possible Issues:</b>
• Token format is incorrect
• Token is corrupted or incomplete
• Copy-paste error occurred
• Token is not from this system

💡 <b>Solutions:</b>
• Double-check your token
• Copy the complete token (no missing parts)
• Try creating a new account if token is lost
• Contact support for help

📞 <b>Support:</b> @tech_support_admin
"""

            user_state[user_id]["current_step"] = None

            retry_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Try Again", callback_data="login_with_token"),
                    InlineKeyboardButton(text="📱 Login with Phone", callback_data="login_account")
                ],
                [
                    InlineKeyboardButton(text="📝 Create New Account", callback_data="create_account")
                ],
                [
                    InlineKeyboardButton(text="📞 Contact Support", url=f"https://t.me/tech_support_admin")
                ]
            ])

            await message.answer(error_text, reply_markup=retry_keyboard)
            return

        # Token decoded successfully, extract user data
        decoded_username = decoded_data.get('username', '')
        decoded_phone = decoded_data.get('phone', '') 
        decoded_email = decoded_data.get('email', '')
        is_telegram_name = decoded_data.get('is_telegram_name', False)

        # Find matching user in database by phone and email combination
        matching_user_id = None
        for uid, data in users_data.items():
            if (data.get('phone_number') == decoded_phone and 
                data.get('email') == decoded_email and 
                data.get('full_name') == decoded_username):
                matching_user_id = uid
                break

        if matching_user_id:
            # Existing account found - login the user
            if matching_user_id != user_id:
                # Account belongs to different Telegram user - create new entry
                users_data[user_id] = users_data[matching_user_id].copy()
                users_data[user_id]['created_at'] = init_user(user_id)

            # Mark account as created and clear state (but protect admin broadcast state)
            users_data[user_id]['account_created'] = True
            
            # Only clear state if it's not an admin broadcast operation
            current_step = user_state[user_id].get("current_step")
            if current_step != "admin_broadcast_message":
                user_state[user_id]["current_step"] = None  
                user_state[user_id]["data"] = {}
            else:
                print(f"🔒 PROTECTED: Admin broadcast state preserved for user {user_id}")

            # Get user display name for login success
            user_display_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name or 'Friend'

            success_text = f"""
✅ <b>Token Login Successful!</b>

🎉 <b>Welcome back {user_display_name} to India Social Panel!</b>

🔐 <b>Access Token Verified Successfully!</b>

👤 <b>Your Account Details:</b>
• Name: {decoded_username}
• Phone: {decoded_phone}
• Email: {decoded_email}
• Balance: ₹{users_data[user_id].get('balance', 0.0):.2f}

🚀 <b>All features are now accessible!</b>
💡 <b>आप अब सभी services का इस्तेमाल कर सकते हैं</b>

🎯 <b>Ready to go:</b>
• Browse premium services
• Add funds to account  
• Place orders instantly
"""

            # Import get_main_menu dynamically to avoid circular imports
            try:
                from main import get_main_menu
                await message.answer(success_text, reply_markup=get_main_menu())
            except ImportError:
                # Fallback keyboard
                fallback_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="👤 My Account", callback_data="my_account"),
                        InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
                    ]
                ])
                await message.answer(success_text, reply_markup=fallback_keyboard)

        else:
            # No existing account found, create new account with decoded data
            users_data[user_id] = {
                'full_name': decoded_username,
                'phone_number': decoded_phone,
                'email': decoded_email,
                'balance': 0.0,
                'account_created': True,
                'access_token': access_token,  # Store the original token
                'created_at': init_user(user_id)
            }

            # Clear user state (but protect admin broadcast state)
            current_step = user_state[user_id].get("current_step")
            if current_step != "admin_broadcast_message":
                user_state[user_id]["current_step"] = None
                user_state[user_id]["data"] = {}
            else:
                print(f"🔒 PROTECTED: Admin broadcast state preserved for user {user_id}")

            # Get user display name
            user_display_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name or 'Friend'

            success_text = f"""
🎉 <b>Account Restored Successfully!</b>

✅ <b>Welcome back {user_display_name} to India Social Panel!</b>

🔐 <b>Your account has been restored from Access Token!</b>

👤 <b>Account Details:</b>
• Name: {decoded_username}
• Phone: {decoded_phone} 
• Email: {decoded_email}
• Balance: ₹0.00

🚀 <b>All features are now accessible!</b>
💡 <b>आप अब सभी services का इस्तेमाल कर सकते हैं</b>

🎯 <b>Next Steps:</b>
• Add funds to your account
• Browse our premium services
• Place your first order
"""

            # Import get_main_menu dynamically to avoid circular imports
            try:
                from main import get_main_menu  
                await message.answer(success_text, reply_markup=get_main_menu())
            except ImportError:
                # Fallback keyboard
                fallback_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="👤 My Account", callback_data="my_account"),
                        InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
                    ]
                ])
                await message.answer(success_text, reply_markup=fallback_keyboard)

    except Exception as e:
        # Unexpected error during token processing
        error_text = """
❌ <b>Login Error</b>

🔐 <b>Token processing failed</b>

⚠️ <b>An unexpected error occurred while processing your token</b>

💡 <b>Please try again or contact support</b>

📞 <b>Support:</b> @tech_support_admin
"""

        user_state[user_id]["current_step"] = None

        error_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Try Again", callback_data="login_with_token"),
                InlineKeyboardButton(text="📞 Contact Support", url=f"https://t.me/tech_support_admin")
            ]
        ])

        await message.answer(error_text, reply_markup=error_keyboard)
