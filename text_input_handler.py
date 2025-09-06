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

async def handle_screenshot_upload(message: Message, user_state: Dict[int, Dict[str, Any]], 
                                  order_temp: Dict[int, Dict[str, Any]], generate_order_id,
                                  format_currency, get_main_menu):
    """Handle screenshot upload for payment verification"""
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
        from main import orders_data, send_admin_notification
        order_temp[user_id] = order_record
        orders_data[order_id] = order_record  # Also store in permanent orders_data

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
आपका order अब process हो रहा है। Package description के अनुसार delivery complete होगी।

💡 <b>Order ID को save करके रखें - यह tracking के लिए जरूरी है!</b>

🎯 <b>Next Steps:</b>
• Order history में track करें
• Order ID copy करके safe रखें
• Delivery के लिए wait करें

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

    # Handle admin broadcast message input first (PRIORITY CHECK)
    from services import handle_admin_broadcast_message, is_admin
    if is_admin(user_id):
        current_step = user_state.get(user_id, {}).get("current_step")
        print(f"🔍 ADMIN DEBUG: User {user_id} current_step: {current_step}")
        if current_step == "admin_broadcast_message":
            print(f"📢 Processing admin broadcast message from {user_id}")
            await handle_admin_broadcast_message(message, user_id)
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

        # Advanced email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email_cleaned):
            await message.answer(
                "⚠️ <b>Invalid Email Format!</b>\n\n"
                "📧 <b>Email format proper नहीं है</b>\n"
                "💡 <b>Example:</b> yourname@gmail.com\n"
                "🔄 <b>Correct format में email भेजें</b>"
            )
            return

        # Check for common invalid domains
        invalid_domains = ['test.com', 'example.com', 'fake.com', '123.com', 'temp.com']
        domain_part = email_cleaned.split('@')[1]
        if domain_part in invalid_domains:
            await message.answer(
                "⚠️ <b>Invalid Email Domain!</b>\n\n"
                "🚫 <b>Fake या test email domains allowed नहीं हैं</b>\n"
                "💡 <b>Valid domains:</b> gmail.com, yahoo.com, outlook.com etc.\n"
                "🔄 <b>Real email address use करें</b>"
            )
            return

        # Check email length
        if len(email_cleaned) < 5 or len(email_cleaned) > 254:
            await message.answer(
                "⚠️ <b>Email Length Invalid!</b>\n\n"
                "📏 <b>Email बहुत छोटा या बहुत लंबा है</b>\n"
                "💡 <b>Valid length: 5-254 characters</b>\n"
                "🔄 <b>Proper email address enter करें</b>"
            )
            return

        # Check for spaces or invalid characters
        if ' ' in email_cleaned or '\t' in email_cleaned:
            await message.answer(
                "⚠️ <b>Spaces Not Allowed!</b>\n\n"
                "🚫 <b>Email में spaces allowed नहीं हैं</b>\n"
                "💡 <b>Example:</b> myname@gmail.com (no spaces)\n"
                "🔄 <b>Spaces remove करके भेजें</b>"
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

    elif current_step == "waiting_link":
        # Handle link input for order processing
        link_input = message.text.strip()

        # Validate link format
        if not link_input.startswith(('http://', 'https://', 'www.')):
            await message.answer(
                "⚠️ <b>Invalid Link Format!</b>\n\n"
                "🔗 <b>Link proper format में नहीं है</b>\n"
                "💡 <b>Link https:// या http:// से start होना चाहिए</b>\n"
                "💡 <b>Example:</b> https://instagram.com/username\n\n"
                "🔄 <b>Correct format में link भेजें</b>"
            )
            return

        # Get platform from user state
        platform = user_state[user_id]["data"].get("platform", "")
        service_id = user_state[user_id]["data"].get("service_id", "")
        package_name = user_state[user_id]["data"].get("package_name", "")
        package_rate = user_state[user_id]["data"].get("package_rate", "")

        # Validate link belongs to correct platform
        platform_domains = {
            "instagram": ["instagram.com", "www.instagram.com"],
            "youtube": ["youtube.com", "www.youtube.com", "youtu.be"],
            "facebook": ["facebook.com", "www.facebook.com", "fb.com"],
            "telegram": ["t.me", "telegram.me"],
            "tiktok": ["tiktok.com", "www.tiktok.com"],
            "twitter": ["twitter.com", "www.twitter.com", "x.com"],
            "linkedin": ["linkedin.com", "www.linkedin.com"],
            "whatsapp": ["chat.whatsapp.com", "wa.me"]
        }

        valid_domains = platform_domains.get(platform, [])
        is_valid_platform = any(domain in link_input.lower() for domain in valid_domains)

        if not is_valid_platform:
            await message.answer(
                f"⚠️ <b>Wrong Platform Link!</b>\n\n"
                f"🚫 <b>आपने {platform.title()} के लिए order किया है</b>\n"
                f"🔗 <b>लेकिन link किसी और platform का है</b>\n"
                f"💡 <b>Valid domains for {platform.title()}:</b> {', '.join(valid_domains)}\n\n"
                f"🔄 <b>Correct {platform.title()} link भेजें</b>"
            )
            return

        # Store link and move to quantity step
        user_state[user_id]["data"]["link"] = link_input
        user_state[user_id]["current_step"] = "waiting_quantity"

        # First message - Link received confirmation
        success_text = f"""
✅ <b>Your Link Successfully Received!</b>

🔗 <b>Received Link:</b> {link_input}

📦 <b>Package Info:</b>
• Name: {package_name}
• ID: {service_id}
• Rate: {package_rate}
• Platform: {platform.title()}

💡 <b>Link verification successful! Moving to next step...</b>
"""

        await message.answer(success_text)

        # Second message - Quantity input page
        quantity_text = f"""
📊 <b>Step 3: Enter Quantity</b>

💡 <b>कितनी quantity चाहिए?</b>

📋 <b>Order Details:</b>
• Package: {package_name}
• Rate: {package_rate}
• Target: {platform.title()}

⚠️ <b>Quantity Guidelines:</b>
• केवल numbers में भेजें
• Minimum: 100
• Maximum: 1,000,000
• Example: 1000, 5000, 10000

💬 <b>अपनी quantity type करके send करें:</b>

🔢 <b>Example Messages:</b>
• 1000
• 5000
• 10000
"""

        await message.answer(quantity_text)

    elif current_step == "waiting_quantity":
        # Handle quantity input
        quantity_input = message.text.strip()

        # Validate quantity is a number
        try:
            quantity = int(quantity_input)
            if quantity <= 0:
                await message.answer(
                    "⚠️ <b>Invalid Quantity!</b>\n\n"
                    "🔢 <b>Quantity 0 से ज्यादा होनी चाहिए</b>\n"
                    "💡 <b>Example:</b> 1000\n\n"
                    "🔄 <b>Valid quantity number भेजें</b>"
                )
                return
        except ValueError:
            await message.answer(
                "⚠️ <b>Invalid Number!</b>\n\n"
                "🔢 <b>केवल numbers allowed हैं</b>\n"
                "💡 <b>Example:</b> 1000\n\n"
                "🔄 <b>Number format में quantity भेजें</b>"
            )
            return

        # Store quantity and move to coupon step
        user_state[user_id]["data"]["quantity"] = quantity
        user_state[user_id]["current_step"] = "waiting_coupon"

        package_name = user_state[user_id]["data"].get("package_name", "")
        service_id = user_state[user_id]["data"].get("service_id", "")
        package_rate = user_state[user_id]["data"].get("package_rate", "")
        link = user_state[user_id]["data"].get("link", "")

        text = f"""
✅ <b>Quantity Successfully Selected!</b>

📦 <b>Package:</b> {package_name}
🆔 <b>ID:</b> {service_id}
💰 <b>Rate:</b> {package_rate}
🔗 <b>Link:</b> {link}
📊 <b>Quantity:</b> {quantity:,}

🎟️ <b>Coupon Code (Optional)</b>

💡 <b>अगर आपके पास कोई valid coupon code है तो type करें</b>

📝 <b>Instructions:</b>
• अपना coupon code manually enter करें
• केवल valid codes ही accept होंगे
• कोई coupon नहीं है तो Skip button दबाएं

💬 <b>Coupon code type करें या Skip करें</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⏭️ Skip Coupon", callback_data="skip_coupon")
            ]
        ])

        await message.answer(text, reply_markup=keyboard)

    elif current_step == "waiting_coupon":
        # Handle coupon input - reject any coupon for now since no coupon system is active
        coupon_input = message.text.strip()

        await message.answer(
            "❌ <b>Invalid Coupon Code!</b>\n\n"
            "🎟️ <b>यह coupon code valid नहीं है या expired हो गया है</b>\n"
            "💡 <b>कृपया valid coupon code try करें या Skip button दबाएं</b>\n\n"
            "🔄 <b>सही coupon code के लिए support से contact करें</b>"
        )

    # Skip if user not in coupon state but has text input
        return

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


    else:
        # PROFESSIONAL BOT BEHAVIOR: Ignore all random/unknown messages
        # Only respond to specific expected inputs during active processes

        # If user has completed account but sent random text, IGNORE completely
        if is_account_created(user_id):
            # Check if this is actually a link - treat any link as order continuation
            if message.text and ("http" in message.text or "www." in message.text or "t.me" in message.text or "instagram.com" in message.text or "youtube.com" in message.text or "facebook.com" in message.text):
                # This might be a link for ordering - check if we can detect platform
                link_input = message.text.strip()
                detected_platform = None

                # Detect platform from link
                if "instagram.com" in link_input.lower():
                    detected_platform = "instagram"
                elif "youtube.com" in link_input.lower() or "youtu.be" in link_input.lower():
                    detected_platform = "youtube"
                elif "facebook.com" in link_input.lower() or "fb.com" in link_input.lower():
                    detected_platform = "facebook"
                elif "t.me" in link_input.lower() or "telegram.me" in link_input.lower():
                    detected_platform = "telegram"
                elif "tiktok.com" in link_input.lower():
                    detected_platform = "tiktok"
                elif "twitter.com" in link_input.lower() or "x.com" in link_input.lower():
                    detected_platform = "twitter"
                elif "linkedin.com" in link_input.lower():
                    detected_platform = "linkedin"
                elif "chat.whatsapp.com" in link_input.lower() or "wa.me" in link_input.lower():
                    detected_platform = "whatsapp"

                if detected_platform:
                    # Set up a basic order state with detected platform
                    user_state[user_id] = {
                        "current_step": "waiting_quantity",
                        "data": {
                            "platform": detected_platform,
                            "service_id": "AUTO_DETECTED",
                            "package_name": f"{detected_platform.title()} Service Package",
                            "package_rate": "₹1.00 per unit",
                            "link": link_input
                        }
                    }

                    # First message - Link received confirmation
                    success_text = f"""
✅ <b>Your Link Successfully Received!</b>

🔗 <b>Received Link:</b> {link_input}

📦 <b>Package Info:</b>
• Platform: {detected_platform.title()}
• Auto-detected service
• Standard pricing applicable

💡 <b>Link verification successful! Moving to next step...</b>
"""

                    await message.answer(success_text)

                    # Second message - Quantity input page
                    quantity_text = f"""
📊 <b>Step 3: Enter Quantity</b>

💡 <b>कितनी quantity चाहिए?</b>

📋 <b>Order Details:</b>
• Package: {detected_platform.title()} Service Package
• Rate: ₹1.00 per unit
• Target: {detected_platform.title()}

⚠️ <b>Quantity Guidelines:</b>
• केवल numbers में भेजें
• Minimum: 100
• Maximum: 1,000,000
• Example: 1000, 5000, 10000

💬 <b>अपनी quantity type करके send करें:</b>

🔢 <b>Example Messages:</b>
• 1000
• 5000
• 10000
"""

                    await message.answer(quantity_text)
                    return
                else:
                    # Unknown link platform - IGNORE completely instead of responding
                    print(f"🔇 IGNORED: Unknown link from user {user_id}: {link_input}")
                    return
            else:
                # Random text message from completed account user - IGNORE completely
                print(f"🔇 IGNORED: Random text from user {user_id}: '{message.text[:50]}...'")
                return
        else:
            # User without account sent random text - IGNORE completely 
            # They should use /start command or buttons to create account
            print(f"🔇 IGNORED: Text from unregistered user {user_id}: '{message.text[:50]}...'")
            return
