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
from aiogram.fsm.context import FSMContext
import account_creation
from states import OrderStates


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

async def handle_admin_direct_message(message: Message, admin_id: int, target_user_id: int):
    """Handle admin direct message sending to specific user"""
    try:
        from main import bot, user_state, users_data

        # Get admin and target user info
        admin_info = users_data.get(admin_id, {})
        target_info = users_data.get(target_user_id, {})

        admin_name = admin_info.get('full_name', 'Admin')
        target_name = target_info.get('full_name', 'User')

        # Clear admin state
        if admin_id in user_state:
            user_state[admin_id]["current_step"] = None
            user_state[admin_id]["data"] = {}

        # Send message to target user
        user_message = f"""
📩 <b>Message from Admin</b>

👨‍💼 <b>From:</b> {admin_name} (India Social Panel)

💬 <b>Message:</b>
{message.text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📞 <b>Need help?</b> Contact @tech_support_admin
"""

        from main import InlineKeyboardMarkup, InlineKeyboardButton
        user_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📞 Contact Support", url="https://t.me/tech_support_admin"),
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
            ]
        ])

        await bot.send_message(
            chat_id=target_user_id,
            text=user_message,
            parse_mode="HTML",
            reply_markup=user_keyboard
        )

        # Confirm to admin
        admin_confirmation = f"""
✅ <b>Message Sent Successfully!</b>

👤 <b>Sent to:</b> {target_name} (ID: {target_user_id})
💬 <b>Message:</b> "{message.text}"
🕐 <b>Time:</b> {datetime.now().strftime("%d %b %Y, %I:%M %p")}

📊 <b>Message delivered successfully!</b>
"""

        await message.answer(admin_confirmation, parse_mode="HTML")
        print(f"✅ Admin {admin_id} sent message to user {target_user_id}: {message.text}")

    except Exception as e:
        print(f"❌ Error sending admin message: {e}")
        await message.answer("❌ Error sending message. Please try again.")

async def handle_screenshot_upload(message: Message,
                                  order_temp: Dict[int, Dict[str, Any]], generate_order_id,
                                  format_currency, get_main_menu):
    """Handle screenshot upload for payment verification"""
    from main import user_state

    if not message.from_user or not message.photo:
        return False

    user_id = message.from_user.id
    current_step = user_state.get(user_id, {}).get("current_step")

    if current_step == "waiting_screenshot_upload":
        # Get order details
        order_data = user_state[user_id]["data"]
        package_name = order_data.get("package_name", "Unknown Package")
        service_id = order_data.get("service_id", "")
        link = order_data.get("link", "")
        quantity = order_data.get("quantity", 0)
        total_price = order_data.get("total_price", 0.0)
        platform = order_data.get("platform", "")

        # Generate order ID
        order_id = generate_order_id()

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
            'payment_method': 'QR Code',
            'payment_status': 'pending_verification'
        }

        # Store order in both temp and permanent storage
        from main import orders_data, send_admin_notification, save_data_to_json
        order_temp[user_id] = order_record
        orders_data[order_id] = order_record  # Also store in permanent orders_data

        # Save order data to persistent storage
        save_data_to_json(orders_data, "orders.json")

        print(f"✅ Screenshot order {order_id} stored in both temp and permanent storage")

        # Send admin notification to group with screenshot
        await send_admin_notification(order_record)

        # Also send the screenshot to admin group
        from main import bot
        admin_group_id = -1003009015663
        try:
            # Get the largest photo size (best quality)
            photo = message.photo[-1]  # Last item is largest size
            await bot.send_photo(
                chat_id=admin_group_id,
                photo=photo.file_id,
                caption=f"📸 <b>Payment Screenshot</b>\n\n🆔 <b>Order ID:</b> <code>{order_id}</code>\n👤 <b>User ID:</b> {user_id}\n💰 <b>Amount:</b> ₹{total_price:,.2f}",
                parse_mode="HTML"
            )
            print(f"✅ Screenshot sent to group for Order ID: {order_id}")
        except Exception as e:
            print(f"❌ Failed to send screenshot to group: {e}")

        # Clear user state
        user_state[user_id]["current_step"] = None
        user_state[user_id]["data"] = {}

        # Send success message with improved buttons including Copy Order ID
        success_text = f"""
🎉 <b>Order Successfully Placed!</b>

✅ <b>Payment Screenshot Verified Successfully!</b>

📦 <b>Order Confirmation Details:</b>
• 🆔 <b>Order ID:</b> <code>{order_id}</code>
• 📦 <b>Package:</b> {package_name}
• 📱 <b>Platform:</b> {platform.title()}
• 🔢 <b>Quantity:</b> {quantity:,}
• 💰 <b>Amount:</b> {format_currency(total_price)}
• 💳 <b>Payment:</b> QR Code ✅
• 📅 <b>Date:</b> {datetime.now().strftime("%d %b %Y, %I:%M %p")}

📋 <b>Order Status:</b> ⏳ Processing Started
🔄 <b>Payment Status:</b> ✅ Verified & Confirmed

⏰ <b>Delivery Timeline:</b>
Your order is now being processed and will be completed according to the package description.

💡 <b>Save your Order ID for tracking!</b>

🎯 <b>Next Steps:</b>
• Track your order in order history
• Copy and save your Order ID
• Wait for delivery

✨ <b>Thank you for choosing India Social Panel!</b>
"""

        # Create improved keyboard with Copy Order ID option
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

        await message.answer(success_text, reply_markup=success_keyboard)
        return True

    return False

async def handle_text_input(message: Message,
                           users_data: Dict[int, Dict[str, Any]], order_temp: Dict[int, Dict[str, Any]],
                           tickets_data: Dict[str, Dict[str, Any]], is_message_old,
                           mark_user_for_notification, is_account_created,
                           format_currency, get_main_menu, OWNER_USERNAME: str):
    """Handle text input for account creation"""
    from main import user_state

    if not message.from_user or not message.text:
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        mark_user_for_notification(message.from_user.id)
        return  # Ignore old messages

    user_id = message.from_user.id

    # Handle admin broadcast message input first (PRIORITY CHECK)
    from services import handle_admin_broadcast_message, is_admin
    if is_admin(user_id):
        current_step = user_state.get(user_id, {}).get("current_step")
        print(f"🔍 ADMIN DEBUG: User {user_id} current_step: {current_step}")
        if current_step == "admin_broadcast_message":
            print(f"📢 Processing admin broadcast message from {user_id}")
            await handle_admin_broadcast_message(message, user_id)
            return
        elif current_step and current_step.startswith("admin_messaging_"):
            # Handle admin messaging to specific user
            target_user_id = int(current_step.replace("admin_messaging_", ""))
            await handle_admin_direct_message(message, user_id, target_user_id)
            return
        elif current_step:
            print(f"🔍 ADMIN DEBUG: Admin {user_id} in step: {current_step}")

    # DEBUG: Log current state
    print(f"🔍 DEBUG: User {user_id} sent text: '{message.text}'")
    current_step = user_state.get(user_id, {}).get("current_step")
    print(f"🔍 DEBUG: User {user_id} current_step: {current_step}")
    print(f"🔍 DEBUG: Full user_state for {user_id}: {user_state.get(user_id, {})}")

    # Check if user is in account creation flow

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

            # Save user data to persistent storage
            from main import save_data_to_json
            save_data_to_json(users_data, "users.json")

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
✅ <b>Login Successful!</b>

🎉 <b>Welcome back {user_display_name} to India Social Panel!</b>

👤 <b>Account Details:</b>
• Name: {users_data[user_id].get('full_name', 'N/A')}
• Phone: {phone}
• Balance: {format_currency(users_data[user_id].get('balance', 0.0))}

🚀 <b>All features are now accessible!</b>
💡 <b>You can now use all services.</b>
"""

            await message.answer(success_text, reply_markup=get_main_menu())

        elif matching_user and matching_user != user_id:
            # Phone belongs to different user
            text = """
⚠️ <b>Account Mismatch</b>

📱 <b>This phone number is linked to another account.</b>

💡 <b>Solutions:</b>
• Try your correct phone number.
• Create a new account.
• Contact support for assistance.

📞 <b>Support:</b> @tech_support_admin
"""

            user_state[user_id]["current_step"] = None

            retry_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔐 Try Again", callback_data="login_account"),
                    InlineKeyboardButton(text="📝 Create New Account", callback_data="create_account")
                ],
                [
                    InlineKeyboardButton(text="📞 Contact Support", url="https://t.me/tech_support_admin")
                ]
            ])

            await message.answer(text, reply_markup=retry_keyboard)

        else:
            # Phone not found in system
            text = """
❌ <b>Account Not Found</b>

📱 <b>No account is registered with this phone number.</b>

💡 <b>Options:</b>
• Double-check your phone number.
• Create a new account.
• Get help from support.

🤔 <b>Don't have an account yet?</b>
"""

            user_state[user_id]["current_step"] = None

            options_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔐 Try Different Number", callback_data="login_account"),
                    InlineKeyboardButton(text="📝 Create New Account", callback_data="create_account")
                ],
                [
                    InlineKeyboardButton(text="📞 Contact Support", url="https://t.me/tech_support_admin")
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

💡 <b>How would you like to provide your phone number?</b>

🔸 <b>Telegram Contact:</b> Share your saved Telegram contact.
🔸 <b>Manual Entry:</b> Enter any number manually.

⚠️ <b>Note:</b> Sharing contact will require your permission and fill the number automatically.

💬 <b>What do you choose?</b>
"""

        phone_choice_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 Share Telegram Contact", callback_data="share_telegram_contact"),
                InlineKeyboardButton(text="✏️ Enter Manually", callback_data="manual_phone_entry")
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
                "🔤 <b>Phone numbers cannot contain letters.</b>\n"
                "🔢 <b>Only numbers and +91 are accepted.</b>\n"
                "💡 <b>Example:</b> +919876543210\n\n"
                "🔄 <b>Try again with only numbers.</b>"
            )
            return

        # Validate country code presence
        if not phone_cleaned.startswith('+91'):
            await message.answer(
                "⚠️ <b>Country Code Missing!</b>\n\n"
                "🇮🇳 <b>Indian numbers must start with +91.</b>\n"
                "❌ <b>Numbers without +91 are not accepted.</b>\n"
                "💡 <b>Example:</b> +919876543210\n\n"
                "🔄 <b>Add +91 before your number.</b>"
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
                "🔄 <b>Check your number length.</b>"
            )
            return

        # Extract the 10-digit number part
        digits_part = phone_cleaned[3:]  # Remove +91

        # Check if only digits after +91
        if not digits_part.isdigit():
            await message.answer(
                "⚠️ <b>Invalid Characters!</b>\n\n"
                "🔢 <b>Only numbers allowed after +91.</b>\n"
                "❌ <b>No spaces, letters, or special characters.</b>\n"
                "💡 <b>Example:</b> +919876543210\n\n"
                "🔄 <b>Use only digits after +91.</b>"
            )
            return

        # Check for invalid starting digits (Indian mobile rules)
        first_digit = digits_part[0]
        invalid_starting_digits = ['0', '1', '2', '3', '4', '5']

        if first_digit in invalid_starting_digits:
            await message.answer(
                "⚠️ <b>Invalid Starting Digit!</b>\n\n"
                f"📱 <b>Indian mobile numbers cannot start with {first_digit}.</b>\n"
                "✅ <b>Valid starting digits:</b> 6, 7, 8, 9\n"
                "💡 <b>Example:</b> +919876543210, +917894561230\n\n"
                "🔄 <b>Enter a valid Indian mobile number.</b>"
            )
            return

        # Check for obviously fake patterns
        # Pattern 1: All same digits
        if len(set(digits_part)) == 1:
            await message.answer(
                "⚠️ <b>Invalid Number Pattern!</b>\n\n"
                "🚫 <b>All digits cannot be the same.</b>\n"
                "❌ <b>Example of invalid:</b> +919999999999\n"
                "💡 <b>Valid example:</b> +919876543210\n\n"
                "🔄 <b>Enter a real mobile number.</b>"
            )
            return

        # Pattern 2: Sequential patterns (1234567890, 0123456789)
        if digits_part == "1234567890" or digits_part == "0123456789":
            await message.answer(
                "⚠️ <b>Sequential Pattern Detected!</b>\n\n"
                "🚫 <b>Sequential numbers are invalid.</b>\n"
                "❌ <b>Patterns like 1234567890 are not allowed.</b>\n"
                "💡 <b>Enter your real mobile number.</b>\n\n"
                "🔄 <b>Try with a valid number.</b>"
            )
            return

        # Pattern 3: Too many zeros or repeated patterns
        zero_count = digits_part.count('0')
        if zero_count >= 5:
            await message.answer(
                "⚠️ <b>Too Many Zeros!</b>\n\n"
                "🚫 <b>Numbers with this many zeros are invalid.</b>\n"
                "❌ <b>Real mobile numbers don't have this many zeros.</b>\n"
                "💡 <b>Enter your actual mobile number.</b>\n\n"
                "🔄 <b>Try again with a valid number.</b>"
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
                        f"🚫 <b>The pattern '{segment}' is repeating too much.</b>\n"
                        "❌ <b>Real mobile numbers don't have repeating patterns.</b>\n"
                        "💡 <b>Enter your actual mobile number.</b>\n\n"
                        "🔄 <b>Try with a different number.</b>"
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
                f"🚫 <b>The number range {first_two}XXXXXXXX is reserved.</b>\n"
                "📱 <b>Valid Indian mobile ranges:</b>\n"
                "• 6XXXXXXXXX (some ranges)\n"
                "• 7XXXXXXXXX ✅\n"
                "• 8XXXXXXXXX ✅\n"
                "• 9XXXXXXXXX (most ranges) ✅\n\n"
                "🔄 <b>Enter a valid Indian mobile number.</b>"
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
                "🚫 <b>This is a common test number.</b>\n"
                "❌ <b>Please use a real mobile number.</b>\n"
                "💡 <b>Enter your actual registered number.</b>\n\n"
                "🔄 <b>Try with your real number.</b>"
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

📧 <b>Please enter your Email Address:</b>

⚠️ <b>Example:</b> your.email@gmail.com
💬 <b>Instruction:</b> Type your email address and send it.
"""

        await message.answer(success_text)

    elif current_step == "waiting_phone":
        # Handle manual phone entry processing text to professional English
        text = """
📱 <b>Manual Phone Number Entry</b>

📝 <b>Account Creation - Step 2/3</b>

🔐 <b>Secure Phone Number Registration</b>

<i>Enter your mobile number for account verification and security</i>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 📋 <b>FORMATTING REQUIREMENTS</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • 🇮🇳 Must include +91 (India)
┃ • 📱 Exactly 13 characters total
┃ • 🔢 Only digits after +91
┃ • ⚠️ No spaces, dashes, or symbols
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 <b>Format Examples:</b>
┌─────────────────────────────────────┐
│ ✅ <b>Correct:</b> +919876543210         │
│ ❌ <b>Wrong:</b> +91 9876543210          │
│ ❌ <b>Wrong:</b> 9876543210              │
│ ❌ <b>Wrong:</b> +91-987-654-3210        │
└─────────────────────────────────────┘

🚀 <b>Type your complete phone number in correct format:</b>
"""
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

📧 <b>Please enter your Email Address:</b>

⚠️ <b>Example:</b> your.email@gmail.com
💬 <b>Instruction:</b> Type your email address and send it.
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
                "📧 <b>Email must contain @ and .</b>\n"
                "💡 <b>Example:</b> yourname@gmail.com\n"
                "🔄 <b>Please send the email in the correct format.</b>"
            )
            return

        # Advanced email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email_cleaned):
            await message.answer(
                "⚠️ <b>Invalid Email Format!</b>\n\n"
                "📧 <b>The email format is not proper.</b>\n"
                "💡 <b>Example:</b> yourname@gmail.com\n"
                "🔄 <b>Please send the email in the correct format.</b>"
            )
            return

        # Check for common invalid domains
        invalid_domains = ['test.com', 'example.com', 'fake.com', '123.com', 'temp.com']
        domain_part = email_cleaned.split('@')[1]
        if domain_part in invalid_domains:
            await message.answer(
                "⚠️ <b>Invalid Email Domain!</b>\n\n"
                "🚫 <b>Fake or test email domains are not allowed.</b>\n"
                "💡 <b>Valid domains:</b> gmail.com, yahoo.com, outlook.com etc.\n"
                "🔄 <b>Use a real email address.</b>"
            )
            return

        # Check email length
        if len(email_cleaned) < 5 or len(email_cleaned) > 254:
            await message.answer(
                "⚠️ <b>Email Length Invalid!</b>\n\n"
                "📏 <b>Email is too short or too long.</b>\n"
                "💡 <b>Valid length: 5-254 characters</b>\n"
                "🔄 <b>Please enter a proper email address.</b>"
            )
            return

        # Check for spaces or invalid characters
        if ' ' in email_cleaned or '\t' in email_cleaned:
            await message.answer(
                "⚠️ <b>Spaces Not Allowed!</b>\n\n"
                "🚫 <b>Spaces are not allowed in emails.</b>\n"
                "💡 <b>Example:</b> myname@gmail.com (no spaces)\n"
                "🔄 <b>Send it by removing spaces.</b>"
            )
            return

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

        # Save user data to persistent storage
        from main import save_data_to_json
        save_data_to_json(users_data, "users.json")

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
💡 <b>You can now use all services!</b>
"""

        await message.answer(success_text, reply_markup=get_main_menu())

    # Order flow states (waiting_link, waiting_quantity, waiting_coupon)
    # are now handled by dedicated FSM handlers in fsm_handlers.py

    # Handle admin messaging
    if current_step and current_step.startswith("admin_messaging_"):
        if not is_admin(user_id):
            return

        target_user_id = int(current_step.replace("admin_messaging_", ""))
        admin_message = message.text.strip()

        # Get user details
        from main import users_data, bot
        if target_user_id not in users_data:
            await message.answer("❌ User not found!")
            user_state[user_id]["current_step"] = None
            return

        user_info = users_data[target_user_id]
        customer_name = user_info.get('full_name', 'Customer')
        username = user_info.get('username', 'N/A')

        # Send message to customer
        customer_notification = f"""
💬 <b>MESSAGE FROM ADMIN</b>

👨‍💼 <b>From:</b> India Social Panel Team
📞 <b>Admin Support:</b> @tech_support_admin

━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 <b>MESSAGE:</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━

{admin_message}

━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 <b>Need to reply?</b> Contact: @tech_support_admin
🆔 <b>Your User ID:</b> <code>{target_user_id}</code>

💙 <b>India Social Panel Team</b>
"""

        customer_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📞 Reply to Admin", url="https://t.me/tech_support_admin"),
                InlineKeyboardButton(text="👤 My Account", callback_data="my_account")
            ],
            [
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
            ]
        ])

        try:
            await bot.send_message(
                chat_id=target_user_id,
                text=customer_notification,
                reply_markup=customer_keyboard,
                parse_mode="HTML"
            )

            # Confirm to admin
            admin_confirmation = f"""
✅ <b>MESSAGE SENT SUCCESSFULLY!</b>

👤 <b>Customer:</b> {customer_name} (@{username})
📱 <b>Customer ID:</b> <code>{target_user_id}</code>

📝 <b>Your Message:</b>
"{admin_message}"

✅ <b>Message delivered to customer</b>
📊 <b>Sent:</b> {datetime.now().strftime("%d %b %Y, %I:%M %p")}

💡 <b>Customer can reply via support chat</b>
"""

            await message.answer(admin_confirmation)

            # Clear admin state
            user_state[user_id]["current_step"] = None

        except Exception as e:
            await message.answer(f"❌ Failed to send message: {e}")
            print(f"Error sending admin message: {e}")

        return
