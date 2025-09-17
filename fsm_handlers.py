# -*- coding: utf-8 -*-
"""
FSM Handlers - India Social Panel
Dedicated handlers for FSM states in the order flow
"""

import re
from aiogram import F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from states import OrderStates, OfferOrderStates


def calculate_offer_amount(rate_string, quantity):
    """Calculate total amount from rate string and quantity"""
    try:
        # Parse rate format: "₹1000 per 1000" or "₹100 per 1K"
        # Remove ₹ symbol and extract numbers with optional K suffix
        import re
        
        # Extract rate and per unit using regex - capture K suffix properly
        # Pattern: ₹(number) per (number)(optional K/k suffix)
        pattern = r'₹([\d,\.]+)\s*per\s*([\d,\.]+)([Kk])?'
        match = re.search(pattern, rate_string)
        
        if match:
            # Remove commas and convert to float
            rate = float(match.group(1).replace(',', ''))
            per_unit = float(match.group(2).replace(',', ''))
            k_suffix = match.group(3)  # K or k or None
            
            # Handle K suffix only if captured (1K = 1000)
            if k_suffix:
                per_unit = per_unit * 1000
            
            # Calculate rate per unit
            rate_per_unit = rate / per_unit
            
            # Calculate total amount
            total_amount = rate_per_unit * quantity
            
            return round(total_amount, 2)
        else:
            # Fallback: try to extract just numbers
            numbers = re.findall(r'[\d,\.]+', rate_string)
            if len(numbers) >= 2:
                rate = float(numbers[0].replace(',', ''))
                per_unit = float(numbers[1].replace(',', ''))
                rate_per_unit = rate / per_unit
                total_amount = rate_per_unit * quantity
                return round(total_amount, 2)
            
        return 0.0
    except Exception as e:
        print(f"Error calculating amount: {e}")
        return 0.0


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
                InlineKeyboardButton(text="✅ Confirm Order", callback_data="offer_process_order_final_btn"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="offer_cancel_order_final_btn")
            ]
        ])
        await message.answer(success_text, reply_markup=confirm_buttons)
    else:
        # Variable quantity - ask for quantity
        success_text += "\n🔢 <b>Step 2: Please specify the quantity you want</b>\n\n"
        success_text += "💡 <b>Example:</b> 1000 (for 1000 followers/likes/views)\n\n"
        success_text += "📤 <b>Type your quantity now</b>"

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
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 🎯 <b>FINAL ORDER CONFIRMATION</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>Excellent! Your order details have been confirmed</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 📋 <b>COMPLETE ORDER BREAKDOWN</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • 📦 <b>Selected Package:</b> {package_name}
┃ • 💰 <b>Premium Rate:</b> {rate}
┃ • 🎯 <b>Target Destination:</b> Your Profile Link
┃ • 📊 <b>Order Quantity:</b> <code>{quantity:,}</code> units
┃ • ⚡ <b>Delivery Type:</b> High Quality & Fast
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ <b>ORDER BENEFITS:</b>
• 🔒 <b>100% Safe & Secure Process</b>
• ⚡ <b>Instant Order Processing</b>
• 💎 <b>Premium Quality Guarantee</b>
• 🎯 <b>Real & Active Engagement</b>
• 📈 <b>Guaranteed Delivery</b>

🎉 <b>Ready to boost your social media presence?</b>

💡 <b>Click "Proceed with Order" to continue with payment</b>
"""

    confirm_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚀 Proceed with Order", callback_data="offer_process_order_final_btn")
        ],
        [
            InlineKeyboardButton(text="✏️ Edit Details", callback_data="offer_cancel_order_final_btn"),
            InlineKeyboardButton(text="❌ Cancel Order", callback_data="offer_cancel_order_final_btn")
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

    if callback_query.data == "offer_process_order_final_btn":
        # Show balance warning and payment options
        print(f"🚀 OFFER FSM: Process order button clicked by user {user.id}")
        
        # Get offer data from FSM state
        data = await state.get_data()
        package_name = data.get("package_name", "Package")
        
        balance_warning_text = f"""
⚠️ <b>Insufficient Balance!</b>

💰 <b>Your Current Balance:</b> ₹0.00
📦 <b>Package:</b> {package_name}

🔔 <b>To place this order, you need to add funds to your account or proceed with direct payment.</b>

💡 <b>Choose your preferred option:</b>
"""
        
        balance_buttons = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Add Fund", callback_data="offer_add_fund_btn")
            ],
            [
                InlineKeyboardButton(text="💳 Direct Payment", callback_data="offer_direct_payment_btn")
            ],
            [
                InlineKeyboardButton(text="❌ Cancel", callback_data="offer_cancel_order_final_btn")
            ]
        ])
        
        await callback_query.answer("⚠️ Balance check completed")
        
        if callback_query.message:
            await callback_query.message.edit_text(balance_warning_text, reply_markup=balance_buttons)
        
        print(f"💰 OFFER FSM: Balance warning shown to user {user.id}")
        return

    elif callback_query.data == "offer_cancel_order_final_btn":
        # Cancel the order and clear state
        await state.clear()

        cancel_text = """
❌ <b>Order Cancelled</b>

Your order has been cancelled successfully.

🔄 <b>You can start a new order anytime by clicking on an offer</b>

💡 <b>No charges have been applied to your account</b>
"""

        await callback_query.answer("❌ Order cancelled")

        if callback_query.message:
            await callback_query.message.edit_text(cancel_text)

        print(f"❌ OFFER FSM: Order cancelled by user {user.id}")
        
    else:
        await callback_query.answer("❌ Unknown action!")
        print(f"⚠️ OFFER FSM: Unknown callback data: {callback_query.data}")


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


async def handle_offer_direct_payment(callback_query, state: FSMContext):
    """Handle direct payment option for offer orders"""
    if not callback_query.data:
        await callback_query.answer("❌ Invalid action!")
        return
    
    user = callback_query.from_user
    if not user:
        await callback_query.answer("❌ User not found!")
        return
    
    print(f"💳 OFFER FSM: Direct payment selected by user {user.id}")
    
    # Get all offer data from FSM state
    data = await state.get_data()
    offer_id = data.get("offer_id", "")
    package_name = data.get("package_name", "")
    rate = data.get("rate", "")
    link = data.get("link", "")
    quantity = data.get("quantity", 0)
    has_fixed_quantity = data.get("has_fixed_quantity", False)
    fixed_quantity = data.get("fixed_quantity")
    
    # Use fixed quantity if enabled, otherwise use user input
    final_quantity = fixed_quantity if has_fixed_quantity and fixed_quantity else quantity
    
    if not final_quantity:
        await callback_query.answer("⚠️ Order data incomplete!", show_alert=True)
        return
    
    # Calculate total amount using our calculation function
    total_amount = calculate_offer_amount(rate, final_quantity)
    
    direct_payment_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 💳 <b>DIRECT PAYMENT MODE</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>Instant Payment without Adding Fund to Account</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 📋 <b>ORDER DETAILS</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • 📦 <b>Package:</b> {package_name}
┃ • 💰 <b>Rate:</b> {rate}
┃ • 🔗 <b>Target Link:</b> {link}
┃ • 📈 <b>Quantity:</b> {final_quantity:,} units
┃ • 💳 <b>Total Amount:</b> ₹{total_amount:,.2f}
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎆 <b>PAYMENT METHOD SELECTION</b>

✨ <b>Choose your preferred payment method to proceed:</b>

💡 <b>Recommended:</b> QR Code for fastest processing
"""
    
    payment_method_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 Generate QR Code", callback_data="offer_generate_qr_btn")
        ],
        [
            InlineKeyboardButton(text="← Back to Options", callback_data="offer_process_order_final_btn"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="offer_cancel_order_final_btn")
        ]
    ])
    
    await callback_query.answer("💳 Loading direct payment...")
    
    if callback_query.message:
        await callback_query.message.edit_text(direct_payment_text, reply_markup=payment_method_buttons)
    
    print(f"💳 OFFER FSM: Direct payment details shown to user {user.id}, amount: ₹{total_amount}")


async def handle_offer_add_fund(callback_query, state: FSMContext):
    """Handle add fund option for offer orders"""
    if not callback_query.data:
        await callback_query.answer("❌ Invalid action!")
        return
    
    user = callback_query.from_user
    if not user:
        await callback_query.answer("❌ User not found!")
        return
    
    print(f"💰 OFFER FSM: Add fund selected by user {user.id}")
    
    add_fund_text = """
💰 <b>Add Fund to Account</b>

🚀 <b>Recharge your account and then place order</b>

💳 <b>Benefits of Adding Fund:</b>
• ⚙️ Instant order processing
• 📈 Better control over balance
• 🔄 Reusable for future orders
• 🔒 Secure payment history

💡 <b>Use the main Add Fund section from menu to recharge your account</b>

🔄 <b>After adding fund, return here to place your order</b>
"""
    
    add_fund_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="← Back to Options", callback_data="offer_process_order_final_btn"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="offer_cancel_order_final_btn")
        ]
    ])
    
    await callback_query.answer("💰 Add fund option selected")
    
    if callback_query.message:
        await callback_query.message.edit_text(add_fund_text, reply_markup=add_fund_buttons)
    
    print(f"💰 OFFER FSM: Add fund info shown to user {user.id}")
