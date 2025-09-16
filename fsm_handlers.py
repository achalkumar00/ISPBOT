# -*- coding: utf-8 -*-
"""
FSM Handlers - India Social Panel
Dedicated handlers for FSM states in the order flow
"""

import re
from aiogram import F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from states import OrderStates, OfferOrderStates


async def handle_link_input(message: Message, state: FSMContext):
    """Handle link input in waiting_link state"""
    print(
        f"🚀 FSM LINK HANDLER: Starting to process link from user {message.from_user.id if message.from_user else 'Unknown'}"
    )

    if not message.text:
        print(f"❌ FSM LINK HANDLER: No text in message")
        return

    link_input = message.text.strip()
    print(f"🔗 FSM LINK HANDLER: Processing link: {link_input}")

    # Basic link validation
    url_pattern = r'^https?://'
    if not re.match(url_pattern, link_input):
        await message.answer(
            "⚠️ <b>Invalid Link Format Detected!</b>\n\n"
            "🔗 <b>Requirements for Valid Links:</b>\n"
            "• Link must be public and accessible\n"
            "• Must be in correct URL format\n"
            "• Should be a working and active link\n\n"
            "💡 <b>Example:</b> https://instagram.com/username\n\n"
            "📤 <b>Please send your link as a message in the correct format:</b>")
        return

    # Get FSM data
    data = await state.get_data()
    platform = data.get("platform", "")
    service_id = data.get("service_id", "")
    package_name = data.get("package_name", "")
    package_rate = data.get("package_rate", "")

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
    is_valid_platform = any(domain in link_input.lower()
                            for domain in valid_domains)

    if not is_valid_platform:
        await message.answer(
            f"⚠️ <b>Platform Mismatch Detected!</b>\n\n"
            f"🚫 <b>You selected a {platform.title()} service package</b>\n"
            f"🔗 <b>But the provided link belongs to a different platform</b>\n"
            f"💡 <b>Valid domains for {platform.title()}:</b> {', '.join(valid_domains)}\n\n"
            f"🔄 <b>Please provide a correct {platform.title()} link to proceed</b>")
        return

    # Store link and move to quantity step
    await state.update_data(link=link_input)
    await state.set_state(OrderStates.waiting_quantity)

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
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>STEP 3: QUANTITY SELECTION</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>How many units would you like to order?</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 📦 <b>ORDER SUMMARY</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • <b>Service:</b> {package_name}
┃ • <b>Pricing:</b> {package_rate}  
┃ • <b>Platform:</b> {platform.title()}
┃ • <b>Target:</b> Your provided link
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ <b>QUANTITY REQUIREMENTS:</b>
┌─────────────────────────────────────┐
│ 🔢 <b>Enter numbers only</b>                │
│ 📉 <b>Minimum:</b> 100 units               │
│ 📈 <b>Maximum:</b> 1,000,000 units         │
│ ✨ <b>Popular choices:</b> 1000, 5000      │
└─────────────────────────────────────┘

💬 <b>Please type your desired quantity and send:</b>

🎯 <b>Pro Tip:</b> Higher quantities often provide better value for money!
"""

    await message.answer(quantity_text)


async def handle_quantity_input(message: Message, state: FSMContext):
    """Handle quantity input in waiting_quantity state"""
    if not message.text:
        return

    quantity_input = message.text.strip()

    # Validate quantity is a number
    try:
        quantity = int(quantity_input)
        if quantity <= 0:
            await message.answer("⚠️ <b>Invalid Quantity!</b>\n\n"
                                 "🔢 <b>Quantity must be greater than 0</b>\n"
                                 "💡 <b>Example:</b> 1000\n\n"
                                 "🔄 <b>Please send a valid quantity number</b>")
            return
    except ValueError:
        await message.answer("⚠️ <b>Invalid Number!</b>\n\n"
                             "🔢 <b>Only numbers are allowed</b>\n"
                             "💡 <b>Example:</b> 1000\n\n"
                             "🔄 <b>Please send quantity in number format</b>")
        return

    # Store quantity and move to coupon step
    await state.update_data(quantity=quantity)
    await state.set_state(OrderStates.waiting_coupon)

    # Get FSM data for display
    data = await state.get_data()
    package_name = data.get("package_name", "")
    service_id = data.get("service_id", "")
    package_rate = data.get("package_rate", "")
    link = data.get("link", "")

    text = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ <b>QUANTITY CONFIRMED SUCCESSFULLY!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 📋 <b>ORDER CONFIRMATION</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • 📦 <b>Package:</b> {package_name}
┃ • 🆔 <b>Service ID:</b> {service_id}
┃ • 💰 <b>Rate:</b> {package_rate}
┃ • 🔗 <b>Target:</b> {link}
┃ • 📊 <b>Quantity:</b> {quantity:,} units
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎟️ <b>DISCOUNT COUPON CODE</b> <i>(Optional)</i>

💡 <b>Have a promo code? Enter it below to save money!</b>

┌─────────────────────────────────────┐
│ 📝 <b>COUPON INSTRUCTIONS:</b>             │
│ • Enter your coupon code manually      │
│ • Only valid codes will be accepted    │
│ • Click Skip if you don't have one     │
│ • Codes are case-sensitive            │
└─────────────────────────────────────┘

💬 <b>Type your coupon code or click Skip to continue:</b>

🎯 <b>Save More:</b> Follow our channel for exclusive discount codes!
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⏭️ Skip Coupon",
                             callback_data="skip_coupon")
    ]])

    await message.answer(text, reply_markup=keyboard)


async def handle_coupon_input(message: Message, state: FSMContext):
    """Handle coupon input in waiting_coupon state"""
    if not message.text:
        return

    coupon_input = message.text.strip()

    # Handle coupon input - reject any coupon for now since no coupon system is active
    await message.answer(
        "❌ <b>Invalid Coupon Code!</b>\n\n"
        "🎟️ <b>This coupon code is not valid or has expired</b>\n"
        "💡 <b>Please try a valid coupon code or press the Skip button</b>\n\n"
        "🔄 <b>Contact support for valid coupon codes</b>")


# ========== NEW OFFER ORDER FLOW HANDLERS ==========

async def handle_offer_link_input(message: Message, state: FSMContext):
    """Handle link input for OfferOrderStates.getting_link state"""
    print(
        f"🚀 OFFER FSM: Processing link input from user {message.from_user.id if message.from_user else 'Unknown'}"
    )

    if not message.text:
        print(f"❌ OFFER FSM: No text in message")
        return

    link_input = message.text.strip()
    print(f"🔗 OFFER FSM: Processing link: {link_input}")

    # Basic link validation
    url_pattern = r'^https?://'
    if not re.match(url_pattern, link_input):
        await message.answer(
            "⚠️ <b>Invalid Link Format!</b>\n\n"
            "🔗 <b>Link must start with https:// or http://</b>\n"
            "💡 <b>Example:</b> https://instagram.com/yourprofile\n\n"
            "🔄 <b>Please send a valid link</b>")
        return

    # Store link and get offer data from FSM state
    await state.update_data(link=link_input)
    data = await state.get_data()

    package_name = data.get("package_name", "")
    rate = data.get("rate", "")
    has_fixed_quantity = data.get("has_fixed_quantity", False)
    fixed_quantity = data.get("fixed_quantity")

    # Link received confirmation
    success_text = f"""
✅ <b>Link Successfully Received!</b>

🔗 <b>Your Link:</b> {link_input}

📦 <b>Package:</b> {package_name}
💰 <b>Rate:</b> {rate}
"""

    if has_fixed_quantity and fixed_quantity:
        # Fixed quantity - move directly to confirmation
        success_text += f"🔢 <b>Quantity:</b> {fixed_quantity}\n\n"
        success_text += "✅ <b>Ready to confirm your order?</b>"

        await state.set_state(OfferOrderStates.confirming_order)

        confirm_buttons = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirm Order", callback_data="confirm_offer_order"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_offer_order")
            ]
        ])
        await message.answer(success_text, reply_markup=confirm_buttons)
    else:
        # Variable quantity - ask for quantity
        success_text += "\n🔢 <b>Step 2: Please specify the quantity you want</b>\n\n"
        success_text += "💡 <b>Example:</b> 1000 (for 1000 followers/likes/views)\n\n"
        success_text += "📤 <b>Enter quantity number:</b>"

        await state.set_state(OfferOrderStates.getting_quantity)
        await message.answer(success_text)

    print(f"🔗 OFFER FSM: Link processed for user {message.from_user.id if message.from_user else 'Unknown'}")


async def handle_offer_quantity_input(message: Message, state: FSMContext):
    """Handle quantity input for OfferOrderStates.getting_quantity state"""
    if not message.text:
        return

    quantity_input = message.text.strip()

    # Validate quantity is a number
    try:
        quantity = int(quantity_input)
        if quantity <= 0:
            await message.answer(
                "⚠️ <b>Invalid Quantity!</b>\n\n"
                "🔢 <b>Quantity must be greater than 0</b>\n"
                "💡 <b>Example:</b> 1000\n\n"
                "🔄 <b>Please send a valid quantity number</b>")
            return
    except ValueError:
        await message.answer(
            "⚠️ <b>Invalid Number!</b>\n\n"
            "🔢 <b>Only numbers are allowed</b>\n"
            "💡 <b>Example:</b> 1000\n\n"
            "🔄 <b>Please send quantity in number format</b>")
        return

    # Store quantity and get order data for confirmation
    await state.update_data(quantity=quantity)
    data = await state.get_data()

    package_name = data.get("package_name", "")
    rate = data.get("rate", "")
    link = data.get("link", "")

    # Move to confirmation step
    await state.set_state(OfferOrderStates.confirming_order)

    confirmation_text = f"""
✅ <b>Quantity Confirmed!</b>

🛒 <b>ORDER SUMMARY</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 <b>Package:</b> {package_name}
💰 <b>Rate:</b> {rate}
🔗 <b>Target:</b> {link}
🔢 <b>Quantity:</b> {quantity:,} units

✅ <b>Ready to confirm your order?</b>
"""

    confirm_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm Order", callback_data="confirm_offer_order"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_offer_order")
        ]
    ])

    await message.answer(confirmation_text, reply_markup=confirm_buttons)
    print(f"🔢 OFFER FSM: Quantity {quantity} confirmed for user {message.from_user.id if message.from_user else 'Unknown'}")


async def handle_offer_confirmation(callback_query, state: FSMContext):
    """Handle offer order confirmation callback"""
    if not callback_query.data:
        await callback_query.answer("❌ Invalid action!")
        return

    user = callback_query.from_user
    if not user:
        await callback_query.answer("❌ User not found!")
        return

    if callback_query.data == "confirm_offer_order":
        # Get all order data from FSM state
        data = await state.get_data()

        offer_id = data.get("offer_id", "")
        package_name = data.get("package_name", "")
        rate = data.get("rate", "")
        link = data.get("link", "")
        quantity = data.get("quantity", data.get("fixed_quantity", ""))

        # Move to payment/screenshot waiting state
        await state.set_state(OfferOrderStates.waiting_screenshot)

        payment_text = f"""
🎉 <b>Order Confirmed Successfully!</b>

🧾 <b>ORDER DETAILS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 <b>Package:</b> {package_name}
💰 <b>Rate:</b> {rate}
🔗 <b>Target:</b> {link}
🔢 <b>Quantity:</b> {quantity}

💳 <b>PAYMENT REQUIRED</b>

Please make the payment and send a screenshot as proof.

📱 <b>Payment Methods:</b>
• UPI/PhonePe/Paytm
• Bank Transfer
• Other digital methods

📸 <b>Send payment screenshot to proceed</b>
"""

        await callback_query.answer("✅ Order confirmed!")

        if callback_query.message:
            await callback_query.message.edit_text(payment_text)

        print(f"✅ OFFER FSM: Order confirmed for user {user.id}, waiting for payment screenshot")

    elif callback_query.data == "cancel_offer_order":
        # Cancel the order and clear state
        await state.clear()

        cancel_text = """
❌ <b>Order Cancelled</b>

Your order has been cancelled successfully.

🔄 <b>You can start a new order anytime by clicking on an offer</b>
"""

        await callback_query.answer("❌ Order cancelled")

        if callback_query.message:
            await callback_query.message.edit_text(cancel_text)

        print(f"❌ OFFER FSM: Order cancelled by user {user.id}")


async def handle_offer_screenshot(message: Message, state: FSMContext):
    """Handle screenshot submission for OfferOrderStates.waiting_screenshot state"""
    user = message.from_user
    if not user:
        return

    # Check if message contains a photo
    if not message.photo:
        await message.answer(
            "⚠️ <b>Screenshot Required!</b>\n\n"
            "📸 <b>Please send a screenshot of your payment</b>\n"
            "💡 <b>Make sure the image is clear and shows payment details</b>\n\n"
            "🔄 <b>Send payment screenshot to proceed</b>")
        return

    # Get order data from FSM state
    data = await state.get_data()
    offer_id = data.get("offer_id", "")
    package_name = data.get("package_name", "")

    # Clear the FSM state as the order process is complete
    await state.clear()

    success_text = f"""
🎉 <b>Payment Screenshot Received!</b>

✅ <b>Order Processing Started</b>

📦 <b>Package:</b> {package_name}
🆔 <b>Offer ID:</b> {offer_id}

⏰ <b>Processing Time:</b> 24-48 hours
📱 <b>You will receive updates on your order status</b>

💬 <b>For support:</b> Contact @tech_support_admin

🙏 <b>Thank you for your order!</b>
"""

    await message.answer(success_text)
    print(f"📸 OFFER FSM: Payment screenshot received from user {user.id} for offer {offer_id}")
    print(f"✅ OFFER FSM: Order process completed for user {user.id}")
