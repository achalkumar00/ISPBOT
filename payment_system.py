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
from typing import Optional

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
    """Professional payment methods menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 UPI Payment", callback_data="payment_upi"),
            InlineKeyboardButton(text="🏦 Bank Transfer", callback_data="payment_bank")
        ],
        [
            InlineKeyboardButton(text="💳 Card Payment", callback_data="payment_card"),
            InlineKeyboardButton(text="💸 Digital Wallets", callback_data="payment_wallet")
        ],
        [
            InlineKeyboardButton(text="📱 Open UPI App", callback_data="payment_upi_app"),
            InlineKeyboardButton(text="📊 Generate QR Code", callback_data="payment_qr")
        ],
        [
            InlineKeyboardButton(text="🔄 Payment History", callback_data="payment_history"),
            InlineKeyboardButton(text="📞 Payment Support", callback_data="payment_support")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
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
    """Generate UPI payment QR code"""
    try:
        # UPI payment string format
        upi_string = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR&tn=Payment%20to%20{name.replace(' ', '%20')}&tr={transaction_id}"

        # Generate QR code
        try:
            from qrcode.constants import ERROR_CORRECT_L  # type: ignore
            qr = qrcode.QRCode(  # type: ignore
                version=1,
                error_correction=ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
        except ImportError:
            print("QRCode library not available")
            return b""
        qr.add_data(upi_string)
        qr.make(fit=True)

        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64 for easy handling
        buffer = io.BytesIO()
        qr_image.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer.getvalue()

    except Exception as e:
        print(f"QR Code generation error: {e}")
        return b""  # Return empty bytes instead of None

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
    """Register all payment handlers"""

    # Initialize payment system
    init_payment_system(main_dp, main_users_data, main_user_state, main_format_currency)

    print("🔄 Registering payment handlers...")  # Debug log

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
💰 <b>Custom Amount Entry</b>

💬 <b>कृपया amount enter करें:</b>

⚠️ <b>Minimum:</b> ₹100
⚠️ <b>Maximum:</b> ₹50,000

💡 <b>Example:</b> 2500

🔒 <b>Secure Payment Processing</b>
✅ <b>Multiple payment options available</b>
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
2. Go to "Fund Transfer" या "IMPS/NEFT"
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
2. Select "Send Money" या "Pay"
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

    @main_dp.callback_query(F.data.startswith("payment_done_"))
    async def cb_payment_done(callback: CallbackQuery):
        """Handle payment completion confirmation"""
        if not callback.message or not callback.from_user:
            return

        user_id = callback.from_user.id
        transaction_id = (callback.data or "").replace("payment_done_", "")
        amount = 1000
        if user_state and user_id in user_state:
            state_data = user_state[user_id].get("data", {})
            amount = state_data.get("payment_amount", 1000)

        text = f"""
🎉 <b>Payment Completion Confirmed!</b>

✅ <b>Payment Details Received:</b>
• 💰 <b>Amount:</b> ₹{amount:,}
• 🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>
• ⏰ <b>Time:</b> Just now
• 📱 <b>Method:</b> UPI Payment

📞 <b>Next Steps:</b>
1. Admin को payment screenshot भेजें
2. Transaction verification होगा (5-10 minutes)
3. Balance automatically add हो जाएगा
4. Confirmation notification आएगी

📸 <b>Send screenshot to admin:</b> @tech_support_admin

⏰ <b>Processing Time:</b> 5-10 minutes
🔔 <b>आपको notification मिल जाएगी जब balance add होगा</b>

💡 <b>Thank you for choosing India Social Panel!</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📞 Send Screenshot", url="https://t.me/tech_support_admin")],
            [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")]
        ])

        await safe_edit_message(callback, text, keyboard)
        await callback.answer("✅ Payment confirmed! Send screenshot to admin.", show_alert=True)

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
2. Select "Send Money" या "Pay to Contact"
3. Enter UPI ID: <code>indiasmm@paytm</code>
4. Enter amount
5. Add remark (optional)
6. Enter UPI PIN और pay करें

🔸 <b>Method 2: QR Code Payment</b>
1. Generate QR code from payment menu
2. Open UPI app
3. Select "Scan QR Code"
4. Scan generated code
5. Verify amount और complete payment

🔸 <b>Method 3: UPI App Link</b>
1. Click "Open UPI App" button
2. Copy payment link
3. Paste in browser या UPI app
4. Complete payment

⚡ <b>सभी methods instant हैं और 100% secure हैं!</b>
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
कोई payment history नहीं मिली

💡 <b>Payment history में दिखेगा:</b>
• Transaction date & time
• Payment method used
• Amount और fees
• Transaction status
• Reference numbers

🔔 <b>जैसे ही आप payment करेंगे, यहाँ history दिख जाएगी!</b>
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

🎯 <b>हमारी team आपकी जल्दी help करेगी!</b>
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
    async def cb_payment_upi(callback: CallbackQuery):
        """Handle UPI payment selection"""
        if not callback.message or not callback.from_user:
            return

        user_id = callback.from_user.id
        amount = 1000
        if user_state and user_id in user_state:
            state_data = user_state[user_id].get("data", {})
            amount = state_data.get("payment_amount", 1000)

        transaction_id = f"UPI{int(time.time())}{random.randint(100, 999)}"

        # Store transaction details
        if user_state and user_id not in user_state:
            user_state[user_id] = {"current_step": None, "data": {}}
        if user_state:
            user_state[user_id]["data"]["transaction_id"] = transaction_id
            user_state[user_id]["data"]["payment_method"] = "upi"

        text = f"""
📱 <b>UPI Payment</b>

💰 <b>Amount:</b> ₹{amount:,}
🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>

📱 <b>UPI Details:</b>
🔸 <b>UPI ID:</b> <code>{PAYMENT_CONFIG['upi_id']}</code>
🔸 <b>Name:</b> {PAYMENT_CONFIG['upi_name']}

⚡ <b>Payment Options:</b>
• Copy UPI ID और manually transfer करें
• QR Code scan करके pay करें
• UPI app directly open करें (with amount)

💡 <b>सबसे fast और secure method है!</b>

🔒 <b>100% Safe & Secure</b>
⚡ <b>Instant Credit Guarantee</b>
"""

        await safe_edit_message(callback, text, get_upi_payment_menu(amount, transaction_id))
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
2. Select "Send Money" या "Pay to Contact"
3. UPI ID paste करें: <code>{PAYMENT_CONFIG['upi_id']}</code>
4. Amount enter करें: ₹{amount:,}
5. Payment complete करें

💡 <b>या फिर QR code generate करके scan करें!</b>
"""

        try:
            await safe_edit_message(callback, text, get_upi_payment_menu(amount, transaction_id))
        except Exception:
            # If edit fails, send new message
            await callback.message.answer(text, reply_markup=get_upi_payment_menu(amount, transaction_id))

        await callback.answer("✅ UPI ID copied: 0m12vx8@jio", show_alert=True)

    # QR generation handler
    @main_dp.callback_query(F.data.startswith("qr_generate_"))
    async def cb_qr_generate(callback: CallbackQuery):
        """Generate and send QR code"""
        if not callback.message or not callback.from_user:
            return

        user_id = callback.from_user.id
        transaction_id = (callback.data or "").replace("qr_generate_", "")
        amount = 1000
        if user_state and user_id in user_state:
            state_data = user_state[user_id].get("data", {})
            amount = state_data.get("payment_amount", 1000)

        await callback.answer("🔄 QR Code generate कर रहे हैं...")

        # Generate QR code
        qr_data = generate_payment_qr(
            amount,
            PAYMENT_CONFIG['upi_id'],
            PAYMENT_CONFIG['upi_name'],
            transaction_id
        )

        if qr_data:
            text = f"""
📊 <b>Payment QR Code Generated!</b>

💰 <b>Amount:</b> ₹{amount:,}
📱 <b>UPI ID:</b> <code>{PAYMENT_CONFIG['upi_id']}</code>
🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>

📱 <b>Scan Instructions:</b>
1. Open any UPI app (GPay, PhonePe, Paytm, JioMoney)
2. Select "Scan QR Code"
3. Scan the QR code image
4. Verify amount और details
5. Enter UPI PIN और pay करें

⚡ <b>Amount automatically ₹{amount:,} filled होगी!</b>
🔒 <b>100% Safe & Secure Payment</b>
"""

            # Send QR code as photo
            try:
                from aiogram.types import BufferedInputFile

                # Create input file from bytes
                qr_file = BufferedInputFile(qr_data, filename="payment_qr.png")

                await callback.message.answer_photo(
                    photo=qr_file,
                    caption=text,
                    reply_markup=get_upi_payment_menu(amount, transaction_id)
                )

                # Try to delete original message
                try:
                    if hasattr(callback.message, 'delete'):
                        await callback.message.delete()  # type: ignore
                except Exception:
                    pass

            except Exception as e:
                print(f"QR Photo send error: {e}")
                # Fallback - send QR code info with manual payment option
                fallback_text = f"""
📊 <b>QR Code Payment Info</b>

💰 <b>Amount:</b> ₹{amount:,}
📱 <b>UPI ID:</b> <code>{PAYMENT_CONFIG['upi_id']}</code>
🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>

📱 <b>Manual Payment Steps:</b>
1. Open any UPI app (GPay, PhonePe, Paytm, JioMoney)
2. Select "Send Money" या "Pay to Contact"
3. Enter UPI ID: <code>{PAYMENT_CONFIG['upi_id']}</code>
4. Enter amount: ₹{amount:,}
5. Add remark: {transaction_id}
6. Complete payment

⚠️ <b>QR image display में technical issue है</b>
💡 <b>Manual payment method use करें</b>
"""

                try:
                    await callback.message.edit_text(fallback_text, reply_markup=get_upi_payment_menu(amount, transaction_id))
                except Exception:
                    await callback.message.answer(fallback_text, reply_markup=get_upi_payment_menu(amount, transaction_id))
        else:
            await callback.answer("❌ QR Code generation failed! Manual payment use करें.", show_alert=True)

            # Show manual payment option
            manual_text = f"""
💰 <b>Manual UPI Payment</b>

📱 <b>UPI ID:</b> <code>{PAYMENT_CONFIG['upi_id']}</code>
💰 <b>Amount:</b> ₹{amount:,}
🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>

📝 <b>Payment Steps:</b>
1. Open UPI app
2. Send money to: <code>{PAYMENT_CONFIG['upi_id']}</code>
3. Enter amount: ₹{amount:,}
4. Complete payment

⚡ <b>QR generation में issue है, manual payment करें</b>
"""

            try:
                await callback.message.edit_text(manual_text, reply_markup=get_upi_payment_menu(amount, transaction_id))
            except Exception:
                await callback.message.answer(manual_text, reply_markup=get_upi_payment_menu(amount, transaction_id))

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
• Manual transfer करें

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

        await callback.answer("💡 UPI ID copied! ₹{amount:,} transfer करें")

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

💡 <b>सबसे suitable method choose करें:</b>
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

💡 <b>अपना preferred wallet चुनें:</b>
"""

        await safe_edit_message(callback, text, get_wallet_payment_menu())
        await callback.answer()

async def show_payment_methods(callback: CallbackQuery, amount: int):
    """Show payment methods selection for specific amount"""
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
    # netbanking_total = amount + netbanking_fee  # Not used in current display
    card_fee = amount * PAYMENT_CONFIG["processing_fee"]["card"] / 100
    card_total = amount + card_fee

    text = f"""
💳 <b>Payment Method Selection</b>

💰 <b>Amount to Add:</b> ₹{amount:,}

💡 <b>Choose your preferred payment method:</b>

📱 <b>UPI Payment</b> (Recommended)
• ✅ No processing fee
• ⚡ Instant credit
• 🔒 100% secure
• 💰 <b>Total:</b> ₹{upi_total:,}

🏦 <b>Bank Transfer</b>
• ✅ No processing fee
• ⏰ 2-4 hours processing
• 🔒 Highly secure
• 💰 <b>Total:</b> ₹{amount:,}

💳 <b>Card Payment</b>
• ⚡ Instant credit
• 💳 All cards accepted
• 🔄 Processing fee: ₹{card_fee:.0f}
• 💰 <b>Total:</b> ₹{card_total:.0f}

💸 <b>Digital Wallets</b>
• ⚡ Quick transfer
• 🎁 Cashback offers
• 💰 <b>Total:</b> ₹{amount:,}

🔥 <b>Special Features:</b>
• Generate QR codes for easy payment
• Direct UPI app opening
• Step-by-step payment guide
• 24/7 payment support

💡 <b>UPI recommended for fastest & cheapest payments!</b>
"""

    await safe_edit_message(callback, text, get_payment_main_menu())

# Export function for main.py
def setup_payment_system(dp, users_data, user_state, format_currency):
    """Setup payment system - called from main.py"""
    register_payment_handlers(dp, users_data, user_state, format_currency)
