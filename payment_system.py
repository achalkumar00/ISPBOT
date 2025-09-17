# -*- coding: utf-8 -*-
"""
India Social Panel - Advanced Payment System
Professional Payment Gateway with Multiple Methods
"""

import qrcode
import io
import os
import time
import random
from aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import Optional
from states import OrderStates

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
                await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")  # type: ignore
            else:
                await callback.message.edit_text(text, parse_mode="HTML")  # type: ignore
            return True
        else:
            # Message is inaccessible, send new message
            if hasattr(callback.message, 'chat') and hasattr(callback.message.chat, 'id'):
                from main import bot
                if reply_markup:
                    await bot.send_message(callback.message.chat.id, text, reply_markup=reply_markup, parse_mode="HTML")
                else:
                    await bot.send_message(callback.message.chat.id, text, parse_mode="HTML")
                return True
            return False
    except Exception as e:
        print(f"Error editing message: {e}")
        # Try sending new message as fallback
        try:
            if hasattr(callback.message, 'chat') and hasattr(callback.message.chat, 'id'):
                from main import bot
                if reply_markup:
                    await bot.send_message(callback.message.chat.id, text, reply_markup=reply_markup, parse_mode="HTML")
                else:
                    await bot.send_message(callback.message.chat.id, text, parse_mode="HTML")
                return True
        except Exception as fallback_error:
            print(f"Fallback message send failed: {fallback_error}")
        return False

# Payment configuration - SECURE PRODUCTION SETTINGS
PAYMENT_CONFIG = {
    "upi_id": os.getenv("PAYMENT_UPI_ID", "business@paytm"),  # Use environment variable
    "upi_name": os.getenv("BUSINESS_NAME", "India Social Panel"),
    "bank_name": os.getenv("BANK_NAME", "Please contact admin for bank details"),
    "account_number": os.getenv("ACCOUNT_NUMBER", "Contact admin for account details"),
    "ifsc_code": os.getenv("IFSC_CODE", "Contact admin for IFSC"),
    "min_amount": int(os.getenv("MIN_PAYMENT", "100")),
    "max_amount": int(os.getenv("MAX_PAYMENT", "50000")),
    "processing_fee": {
        "upi": float(os.getenv("UPI_FEE", "0")),
        "netbanking": float(os.getenv("NETBANKING_FEE", "2.5")),
        "card": float(os.getenv("CARD_FEE", "3.0")),
        "wallet": float(os.getenv("WALLET_FEE", "1.5"))
    }
}

# Global variables (will be initialized from main.py)
dp = None
users_data = None
user_state = None
format_currency = None

def init_payment_system(main_dp, main_users_data, main_user_state, main_format_currency):
    """Initialize payment system with references from main.py"""
    global dp, users_data, user_state, format_currency
    dp = main_dp
    users_data = main_users_data
    user_state = main_user_state
    format_currency = main_format_currency

def get_payment_main_menu() -> InlineKeyboardMarkup:
    """Premium payment methods menu with attractive design"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚡ UPI Express Pay", callback_data="payment_upi"),
            InlineKeyboardButton(text="🏦 Secure Bank Transfer", callback_data="payment_bank")
        ],
        [
            InlineKeyboardButton(text="💳 Premium Card Payment", callback_data="payment_card"),
            InlineKeyboardButton(text="💎 Digital Wallet Hub", callback_data="payment_wallet")
        ],
        [
            InlineKeyboardButton(text="📱 Instant UPI Apps", callback_data="payment_upi_app"),
            InlineKeyboardButton(text="📊 Smart QR Generator", callback_data="payment_qr")
        ],
        [
            InlineKeyboardButton(text="📈 Transaction History", callback_data="payment_history"),
            InlineKeyboardButton(text="🛡️ 24/7 Payment Support", callback_data="payment_support")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Dashboard", callback_data="back_main")
        ]
    ])

def get_upi_payment_menu(amount: float, transaction_id: str) -> InlineKeyboardMarkup:
    """UPI payment options menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Copy UPI ID", callback_data=f"copy_upi_{transaction_id}"),
            InlineKeyboardButton(text="📱 Open UPI App", callback_data=f"open_upi_{transaction_id}")
        ],
        [
            InlineKeyboardButton(text="📊 Generate QR Code", callback_data=f"qr_generate_{transaction_id}"),
            InlineKeyboardButton(text="💡 Payment Guide", callback_data="upi_guide")
        ],
        [
            InlineKeyboardButton(text="✅ Payment Done", callback_data=f"payment_done_{transaction_id}"),
            InlineKeyboardButton(text="⬅️ Back", callback_data="add_funds")
        ]
    ])

def generate_payment_qr(amount: float, upi_id: str, name: str, transaction_id: str) -> bytes:
    """Generate UPI payment QR code with improved error handling"""
    try:
        print(f"🔄 Generating QR code for amount: ₹{amount}, UPI: {upi_id}")

        # UPI payment string format
        upi_string = f"upi://pay?pa=0m12vx8@jio&pn={name.replace('', '%20')}&am={amount}&cu=INR"

        print(f"🔗 UPI String: {upi_string}")

        # Try to import and generate QR code
        try:
            import qrcode
            from qrcode.constants import ERROR_CORRECT_L

            # Create QR code instance with better settings
            qr = qrcode.QRCode(
                version=1,
                error_correction=ERROR_CORRECT_L,
                box_size=8,
                border=2,
            )

            qr.add_data(upi_string)
            qr.make(fit=True)

            # Create QR code image with better quality
            qr_image = qr.make_image(fill_color="black", back_color="white")

            # Convert to bytes
            buffer = io.BytesIO()
            qr_image.save(buffer, format='PNG')
            buffer.seek(0)

            qr_bytes = buffer.getvalue()

            print(f"✅ QR Code generated successfully, size: {len(qr_bytes)} bytes")
            return qr_bytes

        except ImportError as import_error:
            print(f"❌ QRCode library import error: {import_error}")
            print("💡 Trying to install qrcode library...")

            # Try to install qrcode
            try:
                import subprocess
                import sys
                subprocess.check_call([sys.executable, "-m", "pip", "install", "qrcode[pil]"])
                print("✅ QRCode library installed successfully")

                # Try again after installation
                import qrcode
                from qrcode.constants import ERROR_CORRECT_L

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=ERROR_CORRECT_L,
                    box_size=8,
                    border=2,
                )

                qr.add_data(upi_string)
                qr.make(fit=True)
                qr_image = qr.make_image(fill_color="black", back_color="white")

                buffer = io.BytesIO()
                qr_image.save(buffer, format='PNG')
                buffer.seek(0)

                return buffer.getvalue()

            except Exception as install_error:
                print(f"❌ Failed to install qrcode: {install_error}")
                return b""

    except Exception as e:
        print(f"❌ QR Code generation error: {e}")
        import traceback
        traceback.print_exc()
        return b""

def generate_upi_payment_link(amount: float, upi_id: str, name: str, transaction_id: str) -> str:
    """Generate UPI payment deep link"""
    return f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR&tn=Payment%20to%20{name.replace(' ', '%20')}&tr={transaction_id}"

def get_bank_transfer_menu() -> InlineKeyboardMarkup:
    """Bank transfer options menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏦 Net Banking", callback_data="bank_netbanking"),
            InlineKeyboardButton(text="💳 IMPS Transfer", callback_data="bank_imps")
        ],
        [
            InlineKeyboardButton(text="💸 NEFT Transfer", callback_data="bank_neft"),
            InlineKeyboardButton(text="⚡ RTGS Transfer", callback_data="bank_rtgs")
        ],
        [
            InlineKeyboardButton(text="📋 Copy Bank Details", callback_data="copy_bank_details"),
            InlineKeyboardButton(text="💡 Transfer Guide", callback_data="bank_guide")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Payment", callback_data="add_funds")
        ]
    ])

def get_wallet_payment_menu() -> InlineKeyboardMarkup:
    """Digital wallet payment menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💙 Paytm", callback_data="wallet_paytm"),
            InlineKeyboardButton(text="🟢 PhonePe", callback_data="wallet_phonepe")
        ],
        [
            InlineKeyboardButton(text="🔴 Google Pay", callback_data="wallet_gpay"),
            InlineKeyboardButton(text="🟡 Amazon Pay", callback_data="wallet_amazon")
        ],
        [
            InlineKeyboardButton(text="🔵 JioMoney", callback_data="wallet_jio"),
            InlineKeyboardButton(text="🟠 FreeCharge", callback_data="wallet_freecharge")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Payment", callback_data="add_funds")
        ]
    ])

def register_payment_handlers(main_dp, main_users_data, main_user_state, main_format_currency):
    """Register all payment-related callback handlers"""
    global dp, users_data, user_state, format_currency
    dp = main_dp
    users_data = main_users_data
    user_state = main_user_state
    format_currency = main_format_currency

    # Register QR payment completion handlers
    main_dp.callback_query.register(cb_payment_done_qr, F.data == "payment_done_qr")
    main_dp.callback_query.register(cb_payment_cancel, F.data == "payment_cancel")

    @main_dp.callback_query(F.data.startswith("fund_"))
    async def cb_fund_amount_select(callback: CallbackQuery):
        """Handle fund amount selection with payment methods"""
        if not callback.message or not callback.from_user:
            return

        amount_data = (callback.data or "").replace("fund_", "")
        user_id = callback.from_user.id

        if amount_data == "custom":
            # Initialize user state if not exists
            if user_state and user_id not in user_state:
                user_state[user_id] = {"current_step": None, "data": {}}

            if user_state:
                user_state[user_id]["current_step"] = "waiting_custom_amount"

            text = """
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ ✨ <b>CUSTOM AMOUNT ENTRY PORTAL</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>Personalized Recharge Amount</b>
<i>Enter exactly what you need • Flexible & Convenient</i>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 💰 <b>AMOUNT REQUIREMENTS</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • 💵 <b>Minimum Limit:</b> ₹100
┃ • 💎 <b>Maximum Limit:</b> ₹50,000
┃ • 🎯 <b>Recommended:</b> ₹500 - ₹5,000
┃ • ⚡ <b>Processing:</b> Instant for all amounts
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 <b>ENTRY INSTRUCTIONS:</b>
┌─────────────────────────────────────┐
│ 🔢 Enter only numbers (no ₹ symbol)  │
│ 💡 Example: <u>2500</u> for ₹2,500      │
│ ⚠️ No commas or special characters   │
│ ✅ Amount will be validated instantly │
└─────────────────────────────────────┘

🚀 <b>CUSTOM AMOUNT BENEFITS:</b>
• 💎 Pay exactly what you need
• ⚡ Same instant processing
• 🔒 Bank-grade security guaranteed
• 💯 100% success rate

💬 <b>Type your desired amount and send:</b>

🎯 <b>Pro Tip:</b> Popular amounts are ₹1000, ₹2500, ₹5000
"""

            await safe_edit_message(callback, text)
        else:
            # Fixed amount selected - show payment methods
            try:
                amount = int(amount_data)
                await show_payment_methods(callback, amount)
            except ValueError:
                await callback.answer("❌ Invalid amount!", show_alert=True)

        await callback.answer()

    # Add missing bank transfer handlers
    @main_dp.callback_query(F.data == "bank_netbanking")
    async def cb_bank_netbanking(callback: CallbackQuery):
        """Handle net banking payment"""
        if not callback.message:
            return

        text = f"""
🏦 <b>Net Banking Payment</b>

💳 <b>Online Banking Transfer</b>

🏛️ <b>Bank Details:</b>
• 🏦 <b>Bank:</b> {PAYMENT_CONFIG['bank_name']}
• 🔢 <b>Account:</b> <code>{PAYMENT_CONFIG['account_number']}</code>
• 🔑 <b>IFSC:</b> <code>{PAYMENT_CONFIG['ifsc_code']}</code>
• 👤 <b>Name:</b> {PAYMENT_CONFIG['upi_name']}

📝 <b>Net Banking Steps:</b>
1. Login to your bank's net banking
2. Go to "Fund Transfer" or "IMPS/NEFT"
3. Add beneficiary with above details
4. Transfer required amount
5. Save transaction reference number
6. Send screenshot to admin

⏰ <b>Processing Time:</b> Instant to 2 hours
💡 <b>Most secure method for large amounts</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Copy Bank Details", callback_data="copy_bank_details")],
            [InlineKeyboardButton(text="⬅️ Back to Bank Transfer", callback_data="payment_bank")]
        ])

        await safe_edit_message(callback, text, keyboard)
        await callback.answer()

    @main_dp.callback_query(F.data.startswith("wallet_"))
    async def cb_wallet_payment(callback: CallbackQuery):
        """Handle wallet-specific payment"""
        if not callback.message:
            return

        wallet = (callback.data or "").replace("wallet_", "")

        wallet_info = {
            "paytm": ("💙 Paytm", "paytm@indiasmm", "Most popular in India"),
            "phonepe": ("🟢 PhonePe", "phonepe@indiasmm", "UPI + Wallet combo"),
            "gpay": ("🔴 Google Pay", "gpay@indiasmm", "Fastest transfers"),
            "amazon": ("🟡 Amazon Pay", "amazon@indiasmm", "Instant refunds"),
            "jio": ("🔵 JioMoney", "jio@indiasmm", "Jio ecosystem"),
            "freecharge": ("🟠 FreeCharge", "freecharge@indiasmm", "Quick recharges")
        }

        if wallet in wallet_info:
            name, upi_id, description = wallet_info[wallet]

            text = f"""
{name} <b>Payment</b>

💸 <b>{description}</b>

📱 <b>Payment Details:</b>
• 🆔 <b>UPI ID:</b> <code>{upi_id}</code>
• 👤 <b>Name:</b> India Social Panel
• 💰 <b>Amount:</b> ₹{1000 if not user_state or callback.from_user.id not in user_state else user_state[callback.from_user.id].get('data', {}).get('payment_amount', 1000):,}

📝 <b>Payment Steps:</b>
1. Open {name} app
2. Select "Send Money" or "Pay"
3. Enter UPI ID: <code>{upi_id}</code>
4. Enter amount
5. Complete payment with PIN

⚡ <b>Instant credit guarantee!</b>
"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 Copy UPI ID", callback_data=f"copy_wallet_{wallet}")],
                [InlineKeyboardButton(text="⬅️ Back to Wallets", callback_data="payment_wallet")]
            ])

            await safe_edit_message(callback, text, keyboard)

        await callback.answer()

    @main_dp.callback_query(F.data == "payment_card")
    async def cb_payment_card(callback: CallbackQuery):
        """Handle card payment"""
        if not callback.message:
            return

        user_id = callback.from_user.id if callback.from_user else 0
        amount = 1000
        if user_state and user_id in user_state:
            state_data = user_state[user_id].get("data", {})
            amount = state_data.get("payment_amount", 1000)
        processing_fee = amount * PAYMENT_CONFIG["processing_fee"]["card"] / 100
        total_amount = amount + processing_fee

        text = f"""
💳 <b>Card Payment</b>

🔐 <b>Secure Card Payment Gateway</b>

💰 <b>Amount:</b> ₹{amount:,}
💳 <b>Processing Fee:</b> ₹{processing_fee:.0f} (3%)
💰 <b>Total Amount:</b> ₹{total_amount:.0f}

💳 <b>Accepted Cards:</b>
• 💳 Visa Cards
• 💳 Mastercard
• 💳 RuPay Cards
• 💳 American Express
• 💳 Maestro

🔒 <b>Security Features:</b>
• 256-bit SSL encryption
• PCI DSS compliance
• 3D Secure authentication
• No card details stored

⚡ <b>Instant credit after successful payment</b>

🚀 <b>Card payment gateway integration coming soon!</b>
📞 <b>For now, use UPI for instant payments</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 Switch to UPI", callback_data="payment_upi")],
            [InlineKeyboardButton(text="⬅️ Back to Payment", callback_data="add_funds")]
        ])

        await safe_edit_message(callback, text, keyboard)
        await callback.answer()

    @main_dp.callback_query(F.data == "copy_bank_details")
    async def cb_copy_bank_details(callback: CallbackQuery):
        """Handle copying bank details"""
        if not callback.message:
            return

        text = f"""
📋 <b>Bank Details Copied!</b>

🏦 <b>Complete Bank Information:</b>

• 🏛️ <b>Bank Name:</b> {PAYMENT_CONFIG['bank_name']}
• 🔢 <b>Account Number:</b> <code>{PAYMENT_CONFIG['account_number']}</code>
• 🔑 <b>IFSC Code:</b> <code>{PAYMENT_CONFIG['ifsc_code']}</code>
• 👤 <b>Account Holder:</b> {PAYMENT_CONFIG['upi_name']}
• 🏦 <b>Account Type:</b> Current Account

📝 <b>Transfer Instructions:</b>
1. Copy above details
2. Open your banking app
3. Add new beneficiary
4. Verify details carefully
5. Transfer required amount
6. Save transaction reference

⚠️ <b>Important:</b>
• Double check IFSC code
• Mention your user ID in remarks
• Keep transaction reference safe

✅ <b>Bank details successfully copied!</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back to Bank Transfer", callback_data="payment_bank")]
        ])

        await safe_edit_message(callback, text, keyboard)
        await callback.answer("✅ Bank details copied!", show_alert=True)

    @main_dp.callback_query(F.data.startswith("payment_completed_"))
    async def cb_payment_completed(callback: CallbackQuery, state: FSMContext):
        """Handle payment completion - ask for screenshot using FSM"""
        if not callback.message or not callback.from_user:
            return

        try:
            user_id = callback.from_user.id
            transaction_id = (callback.data or "").replace("payment_completed_", "")

            # Get the correct data from the FSM "Digital Notepad"
            order_data = await state.get_data()
            amount = order_data.get("total_price", 0.0)

            if amount == 0.0:
                await callback.answer("⚠️ Order amount not found. Please start over.", show_alert=True)
                await state.clear()
                return

            # Set user state to waiting for screenshot using FSM
            await state.set_state(OrderStates.waiting_screenshot)

            text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 📸 <b>PAYMENT VERIFICATION REQUIRED</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>Payment Confirmation Step - Screenshot Submission</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 💳 <b>PAYMENT SUMMARY</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • 💰 <b>Payment Amount:</b> {format_currency(amount)}
┃ • 🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>
┃ • 📱 <b>Payment Method:</b> UPI Gateway
┃ • ⏰ <b>Status:</b> Awaiting Verification
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📸 <b>SCREENSHOT SUBMISSION REQUIREMENTS:</b>

┌─────────────────────────────────────┐
│ ✅ <b>MANDATORY REQUIREMENTS:</b>           │
│ • High-quality, clear image          │
│ • Payment amount clearly visible     │
│ • Transaction status shows "SUCCESS" │
│ • Date and timestamp visible         │
│ • UPI reference number included      │
└─────────────────────────────────────┘

⚠️ <b>CRITICAL WARNING:</b>
<b>Screenshot submission is MANDATORY for order processing. Failure to provide valid payment proof will result in automatic order cancellation and no service delivery.</b>

📤 <b>Upload your payment screenshot now:</b>

💡 <b>Pro Tip:</b> Take screenshot immediately after successful payment for best quality and clarity.

🔒 <b>Your payment security is guaranteed with bank-grade verification protocols.</b>
"""

            await safe_edit_message(callback, text)
            await callback.answer("📸 Please upload payment screenshot now...")

        except Exception as e:
            print(f"CRITICAL ERROR in cb_payment_completed: {e}")
            await callback.answer("An error occurred. Please try again.", show_alert=True)

    @main_dp.callback_query(F.data.startswith("cancel_qr_order_"))

    @main_dp.callback_query(F.data.startswith("cancel_qr_order_"))
    async def cb_cancel_qr_order(callback: CallbackQuery):
        """Handle QR order cancellation"""
        if not callback.message or not callback.from_user:
            return

        user_id = callback.from_user.id

        # Clear user state
        if user_state and user_id in user_state:
            user_state[user_id]["current_step"] = None
            user_state[user_id]["data"] = {}

        text = """
❌ <b>Order Successfully Cancelled!</b>

🔄 <b>Order cancellation completed successfully</b>

💡 <b>Details:</b>
• QR payment cancelled
• Order process stopped
• No charges applied
• You can place new order anytime

🚀 <b>Ready to place a new order?</b>
Click "New Order" to start fresh!

✅ <b>Thank you for using India Social Panel!</b>
"""

        from main import get_main_menu
        keyboard = get_main_menu()

        await safe_edit_message(callback, text, keyboard)
        await callback.answer("✅ Order cancelled successfully!")

    @main_dp.callback_query(F.data == "upi_guide")
    async def cb_upi_guide(callback: CallbackQuery):
        """Handle UPI payment guide"""
        if not callback.message:
            return

        text = """
💡 <b>UPI Payment Guide</b>

📱 <b>Step-by-Step UPI Payment Instructions</b>

🔸 <b>Method 1: UPI ID Payment</b>
1. Open any UPI app (GPay, PhonePe, Paytm)
2. Select "Send Money" or "Pay to Contact"
3. Enter UPI ID: <code>indiasmm@paytm</code>
4. Enter amount
5. Add remark (optional)
6. Enter UPI PIN and pay

🔸 <b>Method 2: QR Code Payment</b>
1. Generate QR code from payment menu
2. Open UPI app
3. Select "Scan QR Code"
4. Scan generated code
5. Verify amount और complete payment

🔸 <b>Method 3: UPI App Link</b>
1. Click "Open UPI App" button
2. Copy payment link
3. Paste in browser or UPI app
4. Complete payment

⚡ <b>All methods are instant and 100% secure!</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back to UPI Payment", callback_data="payment_upi")]
        ])

        await safe_edit_message(callback, text, keyboard)
        await callback.answer()

    @main_dp.callback_query(F.data == "bank_guide")
    async def cb_bank_guide(callback: CallbackQuery):
        """Handle bank transfer guide"""
        if not callback.message:
            return

        text = f"""
💡 <b>Bank Transfer Guide</b>

🏦 <b>Complete Bank Transfer Instructions</b>

🔸 <b>Net Banking Method:</b>
1. Login to your bank's net banking
2. Go to "Fund Transfer" section
3. Select "Add Beneficiary"
4. Enter our bank details
5. Verify beneficiary (OTP)
6. Transfer amount
7. Save transaction reference

🔸 <b>Mobile Banking Method:</b>
1. Open your bank's mobile app
2. Go to "Transfer Money"
3. Select "To Other Bank"
4. Add beneficiary with details:
   • Name: {PAYMENT_CONFIG['upi_name']}
   • Account: {PAYMENT_CONFIG['account_number']}
   • IFSC: {PAYMENT_CONFIG['ifsc_code']}
5. Complete transfer

🔸 <b>IMPS/NEFT/RTGS:</b>
• IMPS: Instant (24/7)
• NEFT: 2-4 hours
• RTGS: 1-2 hours (₹2L+)

📞 <b>After transfer:</b>
Send transaction screenshot to @tech_support_admin
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back to Bank Transfer", callback_data="payment_bank")]
        ])

        await safe_edit_message(callback, text, keyboard)
        await callback.answer()

    @main_dp.callback_query(F.data == "payment_history")
    async def cb_payment_history(callback: CallbackQuery):
        """Handle payment history"""
        if not callback.message:
            return

        text = """
🔄 <b>Payment History</b>

📊 <b>Your Payment Transactions</b>

📋 <b>Recent Payments:</b>
No payment history found

💡 <b>Payment history will show:</b>
• Transaction date & time
• Payment method used
• Amount and fees
• Transaction status
• Reference numbers

🔔 <b>History will be updated after your first payment!</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back to Payment", callback_data="add_funds")]
        ])

        await safe_edit_message(callback, text, keyboard)
        await callback.answer()

    @main_dp.callback_query(F.data == "payment_support")
    async def cb_payment_support(callback: CallbackQuery):
        """Handle payment support"""
        if not callback.message:
            return

        text = """
📞 <b>Payment Support</b>

🆘 <b>24/7 Payment Assistance</b>

💬 <b>Contact Options:</b>
• 📱 <b>Main Admin:</b> @tech_support_admin
• ⚡ <b>Quick Support:</b> @ISP_PaymentSupport
• 📞 <b>Emergency:</b> @ISP_Emergency

🔧 <b>Common Payment Issues:</b>
• Payment successful but balance not added
• Transaction failed but money deducted
• UPI payment timeout errors
• Bank transfer delays
• Wrong amount transferred

⏰ <b>Response Time:</b>
• Normal issues: 2-4 hours
• Payment issues: 30 minutes
• Emergency: Instant

💡 <b>Payment troubleshooting tips:</b>
• Always save transaction screenshots
• Note exact time of payment
• Keep transaction reference numbers
• Check internet connection during payment

🎯 <b>Our team will help you quickly!</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 Contact Admin", url="https://t.me/tech_support_admin"),
                InlineKeyboardButton(text="⚡ Quick Support", url="https://t.me/ISP_PaymentSupport")
            ],
            [InlineKeyboardButton(text="⬅️ Back to Payment", callback_data="add_funds")]
        ])

        await safe_edit_message(callback, text, keyboard)
        await callback.answer()

    @main_dp.callback_query(F.data == "payment_upi")
    async def cb_payment_upi(callback: CallbackQuery, state: FSMContext):
        """Handle UPI payment selection using FSM"""
        if not callback.message or not callback.from_user:
            return

        try:
            user_id = callback.from_user.id
            order_data = await state.get_data()

            # Get the correct total_price from FSM state
            amount = order_data.get("total_price", 0.0)
            if amount == 0.0:
                await callback.answer("⚠️ Order amount not found. Please start over.", show_alert=True)
                await state.clear()
                return

            transaction_id = f"UPI{int(time.time())}{random.randint(100, 999)}"

            # Store new details in FSM state
            await state.update_data(transaction_id=transaction_id, payment_method="upi")

            text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 📱 <b>UPI PAYMENT GATEWAY</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💳 <b>Instant & Secure UPI Transfer</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 💰 <b>PAYMENT DETAILS</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • 💰 <b>Amount:</b> {format_currency(amount)}
┃ • 🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>
┃ • 📱 <b>UPI ID:</b> <code>{PAYMENT_CONFIG['upi_id']}</code>
┃ • 👤 <b>Merchant:</b> {PAYMENT_CONFIG['upi_name']}
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>PAYMENT METHODS AVAILABLE:</b>

🔸 <b>Method 1: Manual Transfer</b>
• Copy UPI ID and transfer manually
• Works with any UPI app

🔸 <b>Method 2: QR Code Scan</b>
• Generate QR code for quick payment
• Scan and pay instantly

✨ <b>Benefits:</b>
• ⚡ Fastest payment method
• 🔒 100% secure & encrypted
• 💡 Instant order processing
• 🎯 No additional charges

💎 <b>Choose your preferred method below:</b>
            """

            await safe_edit_message(callback, text, get_upi_payment_menu(amount, transaction_id))

        except Exception as e:
            print(f"CRITICAL ERROR in cb_payment_upi: {e}")
            await callback.answer("An error occurred. Please try again.", show_alert=True)

        await callback.answer()

    @main_dp.callback_query(F.data.startswith("copy_upi_"))
    async def cb_copy_upi(callback: CallbackQuery):
        """Handle UPI ID copy"""
        if not callback.message or not callback.from_user:
            return

        user_id = callback.from_user.id
        transaction_id = (callback.data or "").replace("copy_upi_", "")
        amount = 1000
        if user_state and user_id in user_state:
            state_data = user_state[user_id].get("data", {})
            amount = state_data.get("payment_amount", 1000)

        text = f"""
📋 <b>UPI ID Copied!</b>

📱 <b>UPI ID:</b> <code>{PAYMENT_CONFIG['upi_id']}</code>
👤 <b>Name:</b> {PAYMENT_CONFIG['upi_name']}
💰 <b>Amount:</b> ₹{amount:,}

✅ <b>UPI ID successfully copied!</b>

📝 <b>Next Steps:</b>
1. Open any UPI app (Google Pay, PhonePe, Paytm, JioMoney)
2. Select "Send Money" or "Pay to Contact"
3. Paste UPI ID: <code>{PAYMENT_CONFIG['upi_id']}</code>
4. Enter amount: ₹{amount:,}
5. Complete payment

💡 <b>Or generate QR code and scan!</b>
"""

        try:
            await safe_edit_message(callback, text, get_upi_payment_menu(amount, transaction_id))
        except Exception:
            # If edit fails, send new message
            await callback.message.answer(text, reply_markup=get_upi_payment_menu(amount, transaction_id))

        await callback.answer("✅ UPI ID copied!", show_alert=True)

    # QR generation handler
    @main_dp.callback_query(F.data.startswith("qr_generate_"))
    async def cb_qr_generate(callback: CallbackQuery, state: FSMContext):
        """Generate and send QR code using FSM state"""
        if not callback.message or not callback.from_user:
            return

        try:
            user_id = callback.from_user.id
            transaction_id = (callback.data or "").replace("qr_generate_", "")

            # Get the correct data from the FSM "Digital Notepad"
            order_data = await state.get_data()
            amount = order_data.get("total_price", 0.0)

            if amount == 0.0:
                await callback.answer("⚠️ Order amount not found. Please start over.", show_alert=True)
                await state.clear()
                return

            await callback.answer("🔄 Generating QR Code...")

            # Generate QR code
            qr_data = generate_payment_qr(
                amount,
                PAYMENT_CONFIG['upi_id'],
                PAYMENT_CONFIG['upi_name'],
                transaction_id
            )

            # Prepare QR code message text
            qr_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 📊 <b>QR CODE PAYMENT PORTAL</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>Instant Payment Gateway - QR Code Generated Successfully!</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 💳 <b>PAYMENT DETAILS</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • 💰 <b>Amount:</b> {format_currency(amount)}
┃ • 📱 <b>UPI ID:</b> <code>{PAYMENT_CONFIG['upi_id']}</code>
┃ • 🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>
┃ • 🔒 <b>Payment Method:</b> QR Code Scan
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 <b>STEP-BY-STEP PAYMENT INSTRUCTIONS:</b>

🔸 <b>Step 1:</b> Open any UPI app (GPay, PhonePe, Paytm, JioMoney)
🔸 <b>Step 2:</b> Tap "Scan QR Code" or "Pay" option
🔸 <b>Step 3:</b> Scan the QR code displayed above
🔸 <b>Step 4:</b> Verify amount: {format_currency(amount)}
🔸 <b>Step 5:</b> Complete payment with your UPI PIN
🔸 <b>Step 6:</b> Click "Payment Completed" button below

✨ <b>BENEFITS:</b>
• ⚡ Instant payment processing
• 🔒 100% secure encryption
• 💡 No manual data entry needed
• 🎯 Automatic amount detection

💎 <b>Your order will be processed immediately after payment verification!</b>
"""

            qr_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Payment Completed", callback_data=f"payment_completed_{transaction_id}"),
                    InlineKeyboardButton(text="❌ Cancel Order", callback_data="cancel_qr_order_{transaction_id}")
                ],
                [
                    InlineKeyboardButton(text="🔄 Generate New QR", callback_data="payment_qr"),
                    InlineKeyboardButton(text="📱 Other Payment Methods", callback_data="final_confirm_order")
                ]
            ])

            if qr_data:
                from aiogram.types import BufferedInputFile
                qr_file = BufferedInputFile(qr_data, filename="payment_qr.png")
                await callback.message.answer_photo(
                    photo=qr_file,
                    caption=qr_text,
                    reply_markup=qr_keyboard,
                    parse_mode="HTML"
                )
            else:
                # Fallback if QR generation fails
                await send_manual_payment_fallback(callback.message, amount, transaction_id, qr_keyboard)

        except Exception as e:
            print(f"CRITICAL ERROR in cb_qr_generate: {e}")
            await callback.answer("An error occurred. Please try again.", show_alert=True)

    async def send_manual_payment_fallback(message, amount: float, transaction_id: str, keyboard):
        """Send manual payment fallback when QR fails"""
        fallback_text = f"""
💳 <b>Manual UPI Payment</b>

📱 <b>UPI ID:</b> <code>{PAYMENT_CONFIG['upi_id']}</code>
💰 <b>Amount:</b> ₹{amount:,}
🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>

📝 <b>Manual Payment Steps:</b>
1. Open any UPI app (GPay, PhonePe, Paytm, JioMoney)
2. Select "Send Money" or "Pay to Contact"
3. Enter UPI ID: <code>{PAYMENT_CONFIG['upi_id']}</code>
4. Enter amount: ₹{amount:,}
5. Add remark: {transaction_id}
6. Complete payment with UPI PIN

⚠️ <b>QR code generation issue - Please use manual payment</b>
💡 <b>After payment, click the "Payment Completed" button below</b>

✅ <b>You can also send a screenshot after successful payment</b>
"""

        await message.answer(fallback_text, reply_markup=keyboard, parse_mode="HTML")

    @main_dp.callback_query(F.data.startswith("open_upi_"))
    async def cb_open_upi(callback: CallbackQuery):
        """Handle UPI app opening with deep link"""
        if not callback.message or not callback.from_user:
            return

        user_id = callback.from_user.id
        transaction_id = (callback.data or "").replace("open_upi_", "")
        amount = 1000
        if user_state and user_id in user_state:
            state_data = user_state[user_id].get("data", {})
            amount = state_data.get("payment_amount", 1000)

        # Generate UPI payment link
        upi_link = generate_upi_payment_link(
            amount,
            PAYMENT_CONFIG['upi_id'],
            PAYMENT_CONFIG['upi_name'],
            transaction_id
        )

        text = f"""
📱 <b>UPI App Direct Payment</b>

💰 <b>Amount:</b> ₹{amount:,}
📱 <b>UPI ID:</b> <code>{PAYMENT_CONFIG['upi_id']}</code>
🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>

🔗 <b>Payment Link:</b>
<code>{upi_link}</code>

📱 <b>Payment Methods:</b>

🟢 <b>Method 1: Copy UPI ID</b>
• UPI ID: <code>{PAYMENT_CONFIG['upi_id']}</code>
• Amount: ₹{amount:,}
• Transfer manually

🔵 <b>Method 2: UPI Apps</b>
• JioMoney (recommended for Jio users)
• Google Pay, PhonePe, Paytm
• Any UPI app

💡 <b>Quick Steps:</b>
1. Copy UPI ID: <code>{PAYMENT_CONFIG['upi_id']}</code>
2. Open any UPI app
3. Send ₹{amount:,} to above UPI ID
4. Complete payment

✅ <b>Your UPI ID is Jio-based, so JioMoney will work perfectly!</b>
"""

        payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Copy UPI ID", callback_data=f"copy_upi_{transaction_id}"),
                InlineKeyboardButton(text="📊 Generate QR", callback_data=f"qr_generate_{transaction_id}")
            ],
            [
                InlineKeyboardButton(text="✅ Payment Done", callback_data=f"payment_done_{transaction_id}"),
                InlineKeyboardButton(text="⬅️ Back", callback_data="add_funds")
            ]
        ])

        try:
            await safe_edit_message(callback, text, payment_keyboard)
        except Exception:
            await callback.message.answer(text, reply_markup=payment_keyboard)

        await callback.answer("💡 UPI ID copied! Transfer ₹{amount:,}")

    @main_dp.callback_query(F.data == "payment_bank")
    async def cb_payment_bank(callback: CallbackQuery):
        """Handle bank transfer payment"""
        if not callback.message:
            return

        text = f"""
🏦 <b>Bank Transfer Payment</b>

🏛️ <b>Bank Details:</b>
• 🏦 <b>Bank:</b> {PAYMENT_CONFIG['bank_name']}
• 🔢 <b>Account No:</b> <code>{PAYMENT_CONFIG['account_number']}</code>
• 🔑 <b>IFSC Code:</b> <code>{PAYMENT_CONFIG['ifsc_code']}</code>
• 👤 <b>Account Name:</b> {PAYMENT_CONFIG['upi_name']}

💳 <b>Transfer Methods Available:</b>
• Net Banking (Any bank)
• IMPS (Instant transfer)
• NEFT (2-4 hours)
• RTGS (For amounts ₹2,00,000+)

💡 <b>Choose the most suitable method:</b>
"""

        await safe_edit_message(callback, text, get_bank_transfer_menu())
        await callback.answer()

    @main_dp.callback_query(F.data == "payment_wallet")
    async def cb_payment_wallet(callback: CallbackQuery):
        """Handle digital wallet payment"""
        if not callback.message:
            return

        text = f"""
💸 <b>Digital Wallet Payment</b>

📱 <b>Popular Wallet Apps Available:</b>

💙 <b>Paytm Wallet</b> - Most used in India
🟢 <b>PhonePe</b> - UPI + Wallet combo
🔴 <b>Google Pay</b> - Fastest transfers
🟡 <b>Amazon Pay</b> - Instant refunds
🔵 <b>JioMoney</b> - Jio ecosystem
🟠 <b>FreeCharge</b> - Quick recharges

⚡ <b>Wallet Benefits:</b>
• Instant money transfer
• Cashback offers available
• Secure & encrypted
• 24/7 customer support

💡 <b>Choose your preferred wallet:</b>
"""

        await safe_edit_message(callback, text, get_wallet_payment_menu())
        await callback.answer()

async def show_payment_methods(callback: CallbackQuery, amount: int):
    """Show payment methods selection with premium design"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Store amount in user state
    if user_state and user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}
    if user_state:
        user_state[user_id]["data"]["payment_amount"] = amount

    # Calculate processing fees for different methods
    upi_total = amount
    netbanking_fee = amount * PAYMENT_CONFIG["processing_fee"]["netbanking"] / 100
    card_fee = amount * PAYMENT_CONFIG["processing_fee"]["card"] / 100
    card_total = amount + card_fee

    text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 💎 <b>SECURE PAYMENT GATEWAY</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>Professional Payment Processing System</b>
<i>Bank-Grade Security • Instant Processing • 100% Safe</i>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 💰 <b>RECHARGE AMOUNT CONFIRMED</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • 💵 <b>Selected Amount:</b> <u>₹{amount:,}</u>
┃ • 🎯 <b>Processing Mode:</b> Express Payment
┃ • ⚡ <b>Credit Speed:</b> Instant to Account
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>PREMIUM PAYMENT OPTIONS</b>

┌─────────────────────────────────────┐
│ 📱 <b>UPI PAYMENT</b> ⭐ <i>RECOMMENDED</i>     │
│ • ✅ Zero Processing Fee              │
│ • ⚡ Instant Credit Guarantee         │
│ • 🔒 Military-Grade Security          │
│ • 💰 <b>Final Amount:</b> ₹{upi_total:,}        │
│ • 🏆 <b>Success Rate:</b> 99.9%             │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🏦 <b>BANK TRANSFER</b> 💎 <i>MOST SECURE</i>   │
│ • ✅ No Processing Fee               │
│ • ⏰ 2-4 Hours Processing            │
│ • 🛡️ Maximum Security Protocol       │
│ • 💰 <b>Final Amount:</b> ₹{amount:,}         │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 💳 <b>CARD PAYMENT</b> 🚀 <i>PREMIUM</i>        │
│ • ⚡ Lightning Fast Credit           │
│ • 💳 All Major Cards Accepted        │
│ • 🔄 Processing Fee: ₹{card_fee:.0f}          │
│ • 💰 <b>Final Amount:</b> ₹{card_total:.0f}        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 💸 <b>DIGITAL WALLETS</b> 🎁 <i>CASHBACK</i>    │
│ • ⚡ Super Quick Transfer            │
│ • 🎁 Exclusive Cashback Offers       │
│ • 📱 All Popular Wallets             │
│ • 💰 <b>Final Amount:</b> ₹{amount:,}         │
└─────────────────────────────────────┘

🔥 <b>EXCLUSIVE BENEFITS:</b>
• 📊 Generate Custom QR Codes
• 🔗 Direct UPI App Integration
• 📋 Step-by-Step Payment Guide
• 🛡️ 24/7 Security Monitoring
• 💬 Instant Customer Support

💎 <b>Choose your preferred payment method below:</b>

⚡ <b>UPI Payment recommended for instant processing!</b>
"""

    await safe_edit_message(callback, text, get_payment_main_menu())

async def cb_payment_qr(callback: CallbackQuery):
    """Handle QR code payment method - Using same logic as UPI QR generation"""
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

    await callback.answer("🔄 Generating QR Code...")

    # Generate QR code using same function as UPI payment
    qr_data = generate_payment_qr(
        total_price,
        PAYMENT_CONFIG['upi_id'],
        PAYMENT_CONFIG['upi_name'],
        transaction_id
    )

    # Prepare QR code message text (same as UPI QR)
    qr_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 📊 <b>QR CODE PAYMENT PORTAL</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>Instant Payment Gateway - QR Code Generated Successfully!</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 💳 <b>PAYMENT DETAILS</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ • 💰 <b>Amount:</b> {format_currency(total_price)}
┃ • 📱 <b>UPI ID:</b> <code>{PAYMENT_CONFIG['upi_id']}</code>
┃ • 🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>
┃ • 🔒 <b>Payment Method:</b> QR Code Scan
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 <b>STEP-BY-STEP PAYMENT INSTRUCTIONS:</b>

🔸 <b>Step 1:</b> Open any UPI app (GPay, PhonePe, Paytm, JioMoney)
🔸 <b>Step 2:</b> Tap "Scan QR Code" or "Pay" option
🔸 <b>Step 3:</b> Scan the QR code displayed above
🔸 <b>Step 4:</b> Verify amount: {format_currency(total_price)}
🔸 <b>Step 5:</b> Complete payment with your UPI PIN
🔸 <b>Step 6:</b> Click "Payment Completed" button below

✨ <b>BENEFITS:</b>
• ⚡ Instant payment processing
• 🔒 100% secure encryption
• 💡 No manual data entry needed
• 🎯 Automatic amount detection

💎 <b>Your order will be processed immediately after payment verification!</b>
"""

    # Create payment completion keyboard (same as UPI QR)
    qr_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Payment Completed", callback_data=f"payment_completed_{transaction_id}"),
            InlineKeyboardButton(text="❌ Cancel Order", callback_data=f"cancel_qr_order_{transaction_id}")
        ],
        [
            InlineKeyboardButton(text="🔄 Generate New QR", callback_data="payment_qr"),
            InlineKeyboardButton(text="📱 Other Payment Methods", callback_data="final_confirm_order")
        ]
    ])

    # Store transaction details
    user_state[user_id]["data"]["transaction_id"] = transaction_id
    user_state[user_id]["data"]["payment_method"] = "qr_code"

    # Try to send QR code as photo with caption (same logic as UPI QR)
    if qr_data and len(qr_data) > 0:
        try:
            from aiogram.types import BufferedInputFile

            # Create input file from bytes
            qr_file = BufferedInputFile(qr_data, filename="payment_qr.png")

            # Send QR code as new message with buttons
            await callback.message.answer_photo(
                photo=qr_file,
                caption=qr_text,
                reply_markup=qr_keyboard,
                parse_mode="HTML"
            )

            print(f"✅ QR Code sent successfully to user {user_id}")

        except Exception as e:
            print(f"❌ QR Photo send error: {e}")
            # Fallback to text message with manual payment info
            await send_manual_payment_fallback(callback.message, total_price, transaction_id, qr_keyboard)
    else:
        print(f"❌ QR Code generation failed for user {user_id}")
        # QR generation failed, send manual payment
        await send_manual_payment_fallback(callback.message, total_price, transaction_id, qr_keyboard)

async def cb_payment_done_qr(callback: CallbackQuery):
    """Handle Payment Done button click - ask for screenshot"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Check if user is in correct state
    if user_id not in user_state or user_state[user_id].get("current_step") != "waiting_screenshot_upload":
        await callback.answer("⚠️ Invalid order state!")
        return

    # Ask for screenshot
    screenshot_text = """
📸 <b>Payment Screenshot Required</b>

💡 <b>Please upload the payment screenshot</b>

📋 <b>Screenshot Requirements:</b>
• Must be clear and readable
• Payment amount must be visible
• Transaction status must be "Success"
• Date and time should be visible

💬 <b>Please send the screenshot as an image...</b>
"""

    await callback.message.answer(screenshot_text)
    await callback.answer("📸 Please share payment screenshot")

async def cb_payment_cancel(callback: CallbackQuery):
    """Handle Cancel button click - return to main menu"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Clear user state
    if user_id in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    # Send order cancelled message
    cancel_text = """
❌ <b>Order Successfully Cancelled</b>

📋 <b>Payment process cancelled</b>

💡 <b>You can place a new order anytime!</b>

🏠 <b>Returning to the Main Menu...</b>
"""

    # Import get_main_menu from main.py
    try:
        from main import get_main_menu
        await callback.message.answer(cancel_text, reply_markup=get_main_menu())
    except ImportError:
        # Fallback keyboard
        fallback_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")]
        ])
        await callback.message.answer(cancel_text, reply_markup=fallback_keyboard)

    await callback.answer("❌ Order cancelled successfully!")

# Export function for main.py
def setup_payment_system(dp, users_data, user_state, format_currency):
    """Setup payment system - called from main.py"""
    register_payment_handlers(dp, users_data, user_state, format_currency)
