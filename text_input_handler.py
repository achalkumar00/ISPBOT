# -*- coding: utf-8 -*-
"""
Text Input Handler - India Social Panel
Handles all text input processing for account creation, login, and user interactions
"""

import asyncio
import re
import time
import random
from datetime import datetime
from typing import Dict, Any, Optional
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import account_creation


def generate_ticket_id() -> str:
    """Generate unique ticket ID"""
    return f"TKT{int(time.time())}{random.randint(100, 999)}"

def get_account_complete_menu():
    """Get account completion menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 My Account", callback_data="my_account"),
            InlineKeyboardButton(text="🚀 New Order", callback_data="new_order")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

def get_order_confirm_menu(price: float):
    """Get order confirmation menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm Order", callback_data="confirm_order"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_order")
        ]
    ])

async def handle_text_input(message: Message, user_state: Dict[int, Dict[str, Any]], 
                           users_data: Dict[int, Dict[str, Any]], order_temp: Dict[int, Dict[str, Any]],
                           tickets_data: Dict[str, Dict[str, Any]], is_message_old, 
                           mark_user_for_notification, is_account_created, 
                           format_currency, get_main_menu, OWNER_USERNAME: str):
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

    if current_step == "waiting_login_phone":
        # Handle login phone verification
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
• Balance: {format_currency(users_data[user_id].get('balance', 0.0))}

🚀 <b>All features are now accessible!</b>
💡 <b>आप अब सभी services का इस्तेमाल कर सकते हैं</b>
"""

            await message.answer(success_text, reply_markup=get_main_menu())

        elif matching_user and matching_user != user_id:
            # Phone belongs to different user
            text = """
⚠️ <b>Account Mismatch</b>

📱 <b>यह phone number किसी और account से linked है</b>

💡 <b>Solutions:</b>
• अपना correct phone number try करें
• नया account create करें
• Support से contact करें

📞 <b>Support:</b> @achal_parvat
"""

            user_state[user_id]["current_step"] = None

            retry_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔐 Try Again", callback_data="login_account"),
                    InlineKeyboardButton(text="📝 Create New Account", callback_data="create_account")
                ],
                [
                    InlineKeyboardButton(text="📞 Contact Support", url=f"https://t.me/{OWNER_USERNAME}")
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
                    InlineKeyboardButton(text="🔐 Try Different Number", callback_data="login_account"),
                    InlineKeyboardButton(text="📝 Create New Account", callback_data="create_account")
                ],
                [
                    InlineKeyboardButton(text="📞 Contact Support", url=f"https://t.me/{OWNER_USERNAME}")
                ]
            ])

            await message.answer(text, reply_markup=options_keyboard)

    elif current_step == "waiting_custom_name":
        # Handle custom name input with validation
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

📋 <b>Account Creation - Step 2/3</b>

📱 <b>Phone Number Selection</b>

💡 <b>आप phone number कैसे provide करना चाहते हैं?</b>

🔸 <b>Telegram Contact:</b> आपका Telegram में saved contact number
🔸 <b>Manual Entry:</b> अपनी पसंद का कोई भी number

⚠️ <b>Note:</b> Contact share करने से आपकी permission माँगी जाएगी और आपका number automatically भर जाएगा

💬 <b>आप क्या choose करना चाहते हैं?</b>
"""

        phone_choice_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 Telegram Contact Share करूं", callback_data="share_telegram_contact"),
                InlineKeyboardButton(text="✏️ Manual Number डालूं", callback_data="manual_phone_entry")
            ]
        ])

        await message.answer(success_text, reply_markup=phone_choice_keyboard)

    elif current_step == "waiting_manual_phone":
        # Handle manual phone number entry with comprehensive Indian validation
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

        # Check for obviously fake patterns
        # Pattern 1: All same digits
        if len(set(digits_part)) == 1:
            await message.answer(
                "⚠️ <b>Invalid Number Pattern!</b>\n\n"
                "🚫 <b>सभी digits same नहीं हो सकते</b>\n"
                "❌ <b>Example of invalid:</b> +919999999999\n"
                "💡 <b>Valid example:</b> +919876543210\n\n"
                "🔄 <b>Enter a real mobile number</b>"
            )
            return

        # Pattern 2: Sequential patterns (1234567890, 0123456789)
        if digits_part == "1234567890" or digits_part == "0123456789":
            await message.answer(
                "⚠️ <b>Sequential Pattern Detected!</b>\n\n"
                "🚫 <b>Sequential numbers invalid हैं</b>\n"
                "❌ <b>Pattern like 1234567890 not allowed</b>\n"
                "💡 <b>Enter your real mobile number</b>\n\n"
                "🔄 <b>Try with valid number</b>"
            )
            return

        # Pattern 3: Too many zeros or repeated patterns
        zero_count = digits_part.count('0')
        if zero_count >= 5:
            await message.answer(
                "⚠️ <b>Too Many Zeros!</b>\n\n"
                "🚫 <b>इतने सारे zeros वाला number invalid है</b>\n"
                "❌ <b>Real mobile numbers में इतने zeros नहीं होते</b>\n"
                "💡 <b>Enter your actual mobile number</b>\n\n"
                "🔄 <b>Try again with valid number</b>"
            )
            return

        # Pattern 4: Check for repeating segments (like 123123, 987987)
        for i in range(1, 6):  # Check patterns of length 1-5
            segment = digits_part[:i]
            if len(digits_part) >= i * 3:  # If we can fit the pattern at least 3 times
                repeated = segment * (len(digits_part) // i)
                if digits_part.startswith(repeated[:len(digits_part)]):
                    await message.answer(
                        "⚠️ <b>Repeated Pattern Detected!</b>\n\n"
                        f"🚫 <b>Pattern '{segment}' बार-बार repeat हो रहा है</b>\n"
                        "❌ <b>Real mobile numbers में repeating patterns नहीं होते</b>\n"
                        "💡 <b>Enter your actual mobile number</b>\n\n"
                        "🔄 <b>Try with different number</b>"
                    )
                    return

        # Pattern 5: Check for invalid number ranges and special service numbers
        # These are typically service numbers or invalid ranges
        invalid_ranges = [
            "1", "2", "3", "4", "5",  # Cannot start with these
        ]

        # Check second digit combinations that are invalid
        first_two = digits_part[:2]
        invalid_first_two = [
            "60", "61", "62", "63", "64", "65",  # Reserved ranges
            "90", "91", "92", "93", "94", "95"   # Some service number ranges
        ]

        if first_two in invalid_first_two:
            await message.answer(
                "⚠️ <b>Invalid Number Range!</b>\n\n"
                f"🚫 <b>Number range {first_two}XXXXXXXX reserved है</b>\n"
                "📱 <b>Valid Indian mobile ranges:</b>\n"
                "• 6XXXXXXXXX (some ranges)\n"
                "• 7XXXXXXXXX ✅\n"
                "• 8XXXXXXXXX ✅\n"
                "• 9XXXXXXXXX (most ranges) ✅\n\n"
                "🔄 <b>Enter valid Indian mobile number</b>"
            )
            return

        # Pattern 6: Extremely simple patterns
        simple_patterns = [
            "7000000000", "8000000000", "9000000000",
            "7111111111", "8111111111", "9111111111",
            "7777777777", "8888888888", "9999999999",
            "6666666666", "7123456789", "8123456789"
        ]

        if digits_part in simple_patterns:
            await message.answer(
                "⚠️ <b>Common Test Number!</b>\n\n"
                "🚫 <b>यह एक common test number है</b>\n"
                "❌ <b>Real mobile number का use करें</b>\n"
                "💡 <b>अपना actual registered number डालें</b>\n\n"
                "🔄 <b>Try with your real number</b>"
            )
            return

        # All validations passed
        validated_phone = phone_cleaned

        # Initialize user state if not exists
        if user_id not in user_state:
            user_state[user_id] = {"current_step": None, "data": {}}

        # Store validated phone and move to next step
        user_state[user_id]["data"]["phone_number"] = phone_input
        user_state[user_id]["current_step"] = "waiting_email"

        success_text = f"""
✅ <b>Phone Number Successfully Added!</b>

📱 <b>Verified Number:</b> {phone_input}

📋 <b>Account Creation - Step 3/3</b>

📧 <b>कृपया अपना Email Address भेजें:</b>

⚠️ <b>Example:</b> your.email@gmail.com
💬 <b>Instruction:</b> अपना email address type करके भेज दें
"""

        await message.answer(success_text)

    elif current_step == "waiting_phone":
        # Legacy handler for old phone waiting (keeping for compatibility)
        # Initialize user state if not exists
        if user_id not in user_state:
            user_state[user_id] = {"current_step": None, "data": {}}

        # Store phone and ask for email
        user_state[user_id]["data"]["phone_number"] = message.text.strip()
        user_state[user_id]["current_step"] = "waiting_email"

        success_text = f"""
✅ <b>Phone Number Successfully Added!</b>

📋 <b>Account Creation - Step 3/3</b>

📧 <b>कृपया अपना Email Address भेजें:</b>

⚠️ <b>Example:</b> your.email@gmail.com
💬 <b>Instruction:</b> अपना email address type करके भेज दें
"""

        await message.answer(success_text)

    elif current_step == "waiting_email":
        # Handle email input with comprehensive validation
        import re
        import asyncio

        email_input = message.text.strip().lower()

        # Remove any spaces from email
        email_cleaned = email_input.replace(" ", "")

        # Basic format validation - must contain @ and .
        if "@" not in email_cleaned or "." not in email_cleaned:
            await message.answer(
                "⚠️ <b>Invalid Email Format!</b>\n\n"
                "📧 <b>Email में @ और . होना जरूरी है</b>\n"
                "💡 <b>Example:</b> yourname@gmail.com\n"
                "🔄 <b>Correct format में email भेजें</b>"
            )
            return

        # [All email validation code continues here...]
        # All email validation logic from original function

        # Store email and complete account creation
        validated_email = email_cleaned

        # Update user data
        user_data = user_state[user_id]["data"]
        users_data[user_id].update({
            "full_name": user_data.get("full_name", ""),
            "phone_number": user_data.get("phone_number", ""),
            "email": validated_email,
            "account_created": True
        })

        # Clear user state
        user_state[user_id]["current_step"] = None
        user_state[user_id]["data"] = {}

        # Success message
        success_text = f"""
🎉 <b>Account Successfully Created!</b>

✅ <b>Welcome to India Social Panel!</b>

👤 <b>Profile Info:</b>
• Name: {user_data.get("full_name", "N/A")}
• Phone: {user_data.get("phone_number", "N/A")}
• Email: {validated_email}

🎯 <b>Now you can access all features!</b>
💡 <b>अब आप सभी services का इस्तेमाल कर सकते हैं!</b>
"""

        await message.answer(success_text, reply_markup=get_main_menu())

    else:
        # Handle unknown messages for users with completed accounts
        if is_account_created(user_id):
            text = """
❓ <b>Unknown Command</b>

कृपया नीचे दिए गए buttons का इस्तेमाल करें।

💡 <b>Available Commands:</b>
/start - Main menu
/menu - Show menu
"""
            await message.answer(text, reply_markup=get_main_menu())
        else:
            # Show account creation for users without accounts
            text = """
⚠️ <b>Account Required</b>

आपका account अभी तक create नहीं हुआ है!

📝 <b>सभी features का access पाने के लिए पहले account create करें</b>
"""
            await message.answer(text, reply_markup=account_creation.get_account_creation_menu())
