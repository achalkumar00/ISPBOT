# -*- coding: utf-8 -*-
"""
FSM Handlers - India Social Panel
Dedicated handlers for FSM states in the order flow
"""

import re
from aiogram import F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from states import OrderStates


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
            "⚠️ <b>Invalid Link Format!</b>\n\n"
            "🔗 <b>Link https:// या http:// से शुरू होना चाहिए</b>\n"
            "💡 <b>Example:</b> https://instagram.com/username\n\n"
            "🔄 <b>Correct format में link भेजें</b>")
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
            f"⚠️ <b>Wrong Platform Link!</b>\n\n"
            f"🚫 <b>आपने {platform.title()} के लिए order किया है</b>\n"
            f"🔗 <b>लेकिन link किसी और platform का है</b>\n"
            f"💡 <b>Valid domains for {platform.title()}:</b> {', '.join(valid_domains)}\n\n"
            f"🔄 <b>Correct {platform.title()} link भेजें</b>")
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
                                 "🔢 <b>Quantity 0 से ज्यादा होनी चाहिए</b>\n"
                                 "💡 <b>Example:</b> 1000\n\n"
                                 "🔄 <b>Valid quantity number भेजें</b>")
            return
    except ValueError:
        await message.answer("⚠️ <b>Invalid Number!</b>\n\n"
                             "🔢 <b>केवल numbers allowed हैं</b>\n"
                             "💡 <b>Example:</b> 1000\n\n"
                             "🔄 <b>Number format में quantity भेजें</b>")
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
        "🎟️ <b>यह coupon code valid नहीं है या expired हो गया है</b>\n"
        "💡 <b>कृपया valid coupon code try करें या Skip button दबाएं</b>\n\n"
        "🔄 <b>सही coupon code के लिए support से contact करें</b>")
