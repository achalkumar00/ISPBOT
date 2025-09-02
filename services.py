# Social Media Services Management
# Handles all service-related operations for the Telegram bot

import json
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery
)
from aiogram import F

# ========== UTILITY FUNCTIONS ==========

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None):
    """Safely edit message with error handling"""
    try:
        if callback.message:
            await callback.message.edit_text(
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
    except Exception as e:
        print(f"Error editing message: {e}")

# ========== MAIN SERVICES MENU ==========

def get_services_main_menu() -> InlineKeyboardMarkup:
    """Build main services selection menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📷 Instagram", callback_data="service_instagram"),
            InlineKeyboardButton(text="📘 Facebook", callback_data="service_facebook")
        ],
        [
            InlineKeyboardButton(text="🎥 YouTube", callback_data="service_youtube"),
            InlineKeyboardButton(text="📞 Telegram", callback_data="service_telegram")
        ],
        [
            InlineKeyboardButton(text="🎵 TikTok", callback_data="service_tiktok"),
            InlineKeyboardButton(text="🐦 Twitter", callback_data="service_twitter")
        ],
        [
            InlineKeyboardButton(text="💼 LinkedIn", callback_data="service_linkedin"),
            InlineKeyboardButton(text="💬 WhatsApp", callback_data="service_whatsapp")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")
        ]
    ])

# ========== PACKAGE DESCRIPTION FUNCTION ==========

def get_package_description(platform: str, service_id: str) -> dict:
    """Get detailed description for a specific package"""

    # Package details database
    package_details = {
        # Instagram Packages
        "5629": {
            "name": "📷 Instagram Followers - Real & Active",
            "price": "₹0.45 per follower",
            "delivery_time": "0-2 hours start, complete in 24-72 hours",
            "quality": "Real Active Indian Users",
            "description": "High-quality Instagram followers from real, active Indian accounts. These followers have profile pictures, posts, and regular activity. Perfect for building authentic engagement and credibility for your Instagram profile.",
            "features": ["✅ 100% Real Active Users", "✅ Profile Pictures & Posts", "✅ Gradual Delivery", "✅ No Password Required", "✅ 90% Retention Rate", "✅ 24/7 Support"]
        },
        "5630": {
            "name": "📷 Instagram Followers - Premium Quality",
            "price": "₹0.65 per follower", 
            "delivery_time": "Instant start, 12-48 hours completion",
            "quality": "Premium Global Users",
            "description": "Premium Instagram followers from high-quality global accounts with excellent engagement rates. These are carefully selected accounts that actively like and comment on posts, providing genuine growth for your profile.",
            "features": ["✅ Premium Global Accounts", "✅ High Engagement Rate", "✅ Instant Start", "✅ Natural Growth Pattern", "✅ 95% Retention Rate", "✅ Refill Guarantee"]
        },
        "5631": {
            "name": "📷 Instagram Followers - High Retention",
            "price": "₹0.55 per follower",
            "delivery_time": "1-3 hours start, 48-96 hours completion", 
            "quality": "High Retention Real Users",
            "description": "Special high-retention Instagram followers designed for long-term growth. These followers are sourced from stable accounts with low drop rates, ensuring your follower count remains consistent over time.",
            "features": ["✅ 98% Retention Rate", "✅ Stable Accounts", "✅ Long-term Growth", "✅ Natural Delivery", "✅ Minimal Drops", "✅ 30-day Refill"]
        }
    }

    # Get package info or default
    package_info = package_details.get(service_id, {
        "name": f"Service Package ID:{service_id}",
        "price": "₹1.00 per unit",
        "delivery_time": "0-24 hours",
        "quality": "High Quality",
        "description": "Professional social media growth service with real users and guaranteed results.",
        "features": ["✅ Real Users", "✅ Fast Delivery", "✅ High Quality", "✅ Safe Methods", "✅ 24/7 Support"]
    })

    # Create detailed description text
    features_text = "\\n".join(package_info["features"])

    text = f"""
🎯 <b>{package_info["name"]}</b>

🆔 <b>Service ID:</b> {service_id}
💰 <b>Price:</b> {package_info["price"]}
⏰ <b>Delivery:</b> {package_info["delivery_time"]}
🏆 <b>Quality:</b> {package_info["quality"]}

📋 <b>Service Description:</b>
{package_info["description"]}

✨ <b>Key Features:</b>
{features_text}

⚠️ <b>Important Terms & Conditions:</b>
• Your profile/link must be public and accessible
• We guarantee the promised delivery time and quality
• Refill provided within 30 days if any drops occur
• No password or sensitive information required
• Safe and secure delivery methods only
• 24/7 customer support available

💡 <b>आपने सभी details पढ़ लीं हैं और terms & conditions से agree हैं?</b>

यदि आप इस package को order करना चाहते हैं तो नीचे YES button पर click करें।
"""

    # Create keyboard with YES and Back buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ YES - Order This Package", callback_data=f"confirm_order_{platform}_{service_id}")
        ],
        [
            InlineKeyboardButton(text="🔄 Choose Another Package", callback_data=f"service_{platform}"),
            InlineKeyboardButton(text="⬅️ Back to Services", callback_data="new_order")
        ]
    ])

    return {"text": text, "keyboard": keyboard}

def get_service_packages(platform: str) -> InlineKeyboardMarkup:
    """Get packages for specific platform"""

    packages = {
        "instagram": [
            # Basic Instagram Services
            ("👥 Instagram Followers - Real & Active", "ID:5629"),
            ("👥 Instagram Followers - Premium Quality", "ID:5630"),
            ("👥 Instagram Followers - High Retention", "ID:5631"),
            ("👥 Instagram Followers - Instant Start", "ID:5632"),
            ("👥 Instagram Followers - Targeted India", "ID:5633"),
            ("👥 Instagram Followers - Global Mix", "ID:5634"),

            # Instagram Likes
            ("❤️ Instagram Post Likes - Real Users", "ID:5635"),
            ("❤️ Instagram Post Likes - Instant", "ID:5636"),
            ("❤️ Instagram Post Likes - High Quality", "ID:5637"),
            ("❤️ Instagram Reel Likes - Viral Boost", "ID:5638"),
            ("❤️ Instagram Photo Likes - Premium", "ID:5639"),
            ("❤️ Instagram Video Likes - Fast", "ID:5640"),

            # Instagram Views
            ("👁️ Instagram Post Views - Real", "ID:5641"),
            ("👁️ Instagram Reel Views - Viral", "ID:5642"),
            ("👁️ Instagram Video Views - High Retention", "ID:5643"),
            ("👁️ Instagram Profile Views - Organic", "ID:5644"),
            ("👁️ Instagram IGTV Views - Premium", "ID:5645"),

            # Instagram Story Services
            ("📖 Instagram Story Views - Real Users", "ID:5646"),
            ("📖 Instagram Story Views - Instant", "ID:5647"),
            ("📖 Instagram Story Views - High Quality", "ID:5648"),
            ("💖 Instagram Story Likes - Premium", "ID:5649"),
            ("💖 Instagram Story Likes - Fast Delivery", "ID:5650"),
            ("⏰ Instagram Story Poll Votes - Real", "ID:5651"),

            # Instagram Engagement
            ("💬 Instagram Comments - Real Users", "ID:5652"),
            ("💬 Instagram Comments - Custom Text", "ID:5653"),
            ("💬 Instagram Comments - Positive Only", "ID:5654"),
            ("💬 Instagram Comments - Random Mix", "ID:5655"),

            # Instagram Advanced
            ("📤 Instagram Shares - Real Accounts", "ID:5656"),
            ("📤 Instagram Shares - Viral Boost", "ID:5657"),
            ("💾 Instagram Saves - Bookmark Boost", "ID:5658"),
            ("💾 Instagram Saves - High Quality", "ID:5659"),
            ("🔄 Instagram Auto Likes - 30 Days", "ID:5660"),
            ("🔄 Instagram Auto Views - Monthly", "ID:5661"),

            # Instagram Channel/Business
            ("👥 Instagram Channel Members", "ID:5662"),
            ("📊 Instagram Reach Boost", "ID:5663"),
            ("🎯 Instagram Impressions", "ID:5664"),
            ("⭐ Instagram Profile Visits", "ID:5665")
        ],

        "facebook": [
            # Facebook Page Services
            ("📄 Facebook Page Likes - Real Users", "ID:6001"),
            ("📄 Facebook Page Likes - Premium Quality", "ID:6002"),
            ("📄 Facebook Page Likes - Instant Start", "ID:6003"),
            ("📄 Facebook Page Likes - Indian Users", "ID:6004"),
            ("📄 Facebook Page Likes - Global Mix", "ID:6005"),

            # Facebook Post Engagement
            ("❤️ Facebook Post Likes - Real Accounts", "ID:6006"),
            ("❤️ Facebook Post Likes - Fast Delivery", "ID:6007"),
            ("❤️ Facebook Post Likes - High Quality", "ID:6008"),
            ("❤️ Facebook Photo Likes - Premium", "ID:6009"),
            ("❤️ Facebook Video Likes - Viral", "ID:6010"),

            # Facebook Groups
            ("👥 Facebook Group Members - Real", "ID:6011"),
            ("👥 Facebook Group Members - Active Users", "ID:6012"),
            ("👥 Facebook Group Members - Targeted", "ID:6013"),
            ("👥 Facebook Group Members - Indian", "ID:6014"),

            # Facebook Live & Video
            ("🔴 Facebook Live Views - Real Time", "ID:6015"),
            ("🔴 Facebook Live Views - High Retention", "ID:6016"),
            ("👁️ Facebook Video Views - Organic", "ID:6017"),
            ("👁️ Facebook Video Views - Fast Boost", "ID:6018"),
            ("👁️ Facebook Video Views - Premium", "ID:6019"),

            # Facebook Monetization
            ("💰 Facebook Page Monetization Setup", "ID:6020"),
            ("💰 Facebook Creator Fund Eligible", "ID:6021"),
            ("💰 Facebook Watch Time Boost", "ID:6022"),

            # Facebook Engagement
            ("💬 Facebook Comments - Real Users", "ID:6023"),
            ("💬 Facebook Comments - Positive", "ID:6024"),
            ("💬 Facebook Comments - Custom Text", "ID:6025"),
            ("📤 Facebook Shares - Real Accounts", "ID:6026"),
            ("📤 Facebook Shares - Viral Boost", "ID:6027"),

            # Facebook Followers
            ("👥 Facebook Followers - Profile", "ID:6028"),
            ("👥 Facebook Followers - Real Active", "ID:6029"),
            ("👥 Facebook Followers - Premium", "ID:6030"),

            # Facebook Business
            ("📊 Facebook Page Rating Boost", "ID:6031"),
            ("🎯 Facebook Event Interested", "ID:6032"),
            ("⭐ Facebook Reviews - Positive", "ID:6033"),
            ("📈 Facebook Page Reach", "ID:6034"),
            ("🎪 Facebook Event Attendees", "ID:6035")
        ],

        "youtube": [
            # YouTube Subscribers
            ("👥 YouTube Subscribers - Real Active", "ID:7001"),
            ("👥 YouTube Subscribers - Premium Quality", "ID:7002"),
            ("👥 YouTube Subscribers - Instant Start", "ID:7003"),
            ("👥 YouTube Subscribers - High Retention", "ID:7004"),
            ("👥 YouTube Subscribers - Indian Audience", "ID:7005"),
            ("👥 YouTube Subscribers - Global Mix", "ID:7006"),

            # YouTube Views
            ("👁️ YouTube Video Views - Real", "ID:7007"),
            ("👁️ YouTube Video Views - High Retention", "ID:7008"),
            ("👁️ YouTube Video Views - Fast Delivery", "ID:7009"),
            ("👁️ YouTube Video Views - Premium", "ID:7010"),
            ("👁️ YouTube Views - Monetizable", "ID:7011"),

            # YouTube Likes
            ("❤️ YouTube Video Likes - Real Users", "ID:7012"),
            ("❤️ YouTube Video Likes - Instant", "ID:7013"),
            ("❤️ YouTube Video Likes - High Quality", "ID:7014"),
            ("❤️ YouTube Shorts Likes - Viral", "ID:7015"),

            # YouTube Monetization
            ("💰 YouTube Monetization - 4000 Hours", "ID:7016"),
            ("💰 YouTube Monetization - 1000 Subs", "ID:7017"),
            ("💰 YouTube Watch Time - Premium", "ID:7018"),
            ("💰 YouTube AdSense Approval", "ID:7019"),

            # YouTube Engagement
            ("💬 YouTube Comments - Real Users", "ID:7020"),
            ("💬 YouTube Comments - Positive", "ID:7021"),
            ("💬 YouTube Comments - Custom Text", "ID:7022"),
            ("👎 YouTube Dislikes - Competitor", "ID:7023"),

            # YouTube Advanced
            ("📊 YouTube Watch Time - 4000 Hours", "ID:7024"),
            ("📊 YouTube Watch Time - Premium", "ID:7025"),
            ("🔔 YouTube Channel Memberships", "ID:7026"),
            ("📺 YouTube Premiere Views", "ID:7027"),

            # YouTube Shorts
            ("🎯 YouTube Shorts Views - Viral", "ID:7028"),
            ("🎯 YouTube Shorts Views - Fast", "ID:7029"),
            ("🎯 YouTube Shorts Likes - Premium", "ID:7030"),
            ("🎯 YouTube Shorts Comments", "ID:7031"),

            # YouTube Live
            ("⏰ YouTube Live Stream Views - Real Time", "ID:7032"),
            ("⏰ YouTube Live Stream Viewers", "ID:7033"),
            ("⏰ YouTube Live Chat Messages", "ID:7034"),

            # YouTube Community
            ("📱 YouTube Community Post Likes", "ID:7035"),
            ("📱 YouTube Community Comments", "ID:7036"),
            ("📱 YouTube Community Shares", "ID:7037")
        ],

        "telegram": [
            # Telegram Channel Services
            ("👥 Telegram Channel Members - Real", "ID:8001"),
            ("👥 Telegram Channel Members - Premium", "ID:8002"),
            ("👥 Telegram Channel Members - Indian", "ID:8003"),
            ("👥 Telegram Channel Members - Global", "ID:8004"),
            ("👥 Telegram Channel Subscribers", "ID:8005"),

            # Telegram Views
            ("👁️ Telegram Post Views - Real", "ID:8006"),
            ("👁️ Telegram Post Views - Fast", "ID:8007"),
            ("👁️ Telegram Channel Views", "ID:8008"),
            ("👁️ Telegram Story Views", "ID:8009"),

            # Telegram Groups
            ("👥 Telegram Group Members - Active", "ID:8010"),
            ("👥 Telegram Group Members - Real", "ID:8011"),
            ("👥 Telegram Group Members - Targeted", "ID:8012"),

            # Telegram Engagement
            ("📊 Telegram Channel Boost", "ID:8013"),
            ("💬 Telegram Comments - Real", "ID:8014"),
            ("📤 Telegram Shares - Viral", "ID:8015"),
            ("⭐ Telegram Reactions - Mix", "ID:8016"),
            ("⭐ Telegram Reactions - Heart", "ID:8017"),
            ("⭐ Telegram Reactions - Fire", "ID:8018"),

            # Telegram Advanced
            ("🔔 Telegram Poll Votes", "ID:8019"),
            ("🎯 Telegram Premium Members", "ID:8020"),
            ("📈 Telegram Channel Growth", "ID:8021"),
            ("📱 Telegram Auto Views", "ID:8022")
        ],

        "whatsapp": [
            # WhatsApp Groups
            ("👥 WhatsApp Group Members - Real Active", "ID:13001"),
            ("👥 WhatsApp Group Members - Premium", "ID:13002"),
            ("👥 WhatsApp Group Members - Indian", "ID:13003"),
            ("👥 WhatsApp Group Members - Global", "ID:13004"),

            # WhatsApp Channel
            ("📊 WhatsApp Channel Subscribers", "ID:13005"),
            ("📊 WhatsApp Channel Followers", "ID:13006"),
            ("👁️ WhatsApp Channel Views", "ID:13007"),

            # WhatsApp Status
            ("👁️ WhatsApp Status Views - Real", "ID:13008"),
            ("👁️ WhatsApp Status Views - Fast", "ID:13009"),
            ("⭐ WhatsApp Status Reactions", "ID:13010"),
            ("💬 WhatsApp Status Replies", "ID:13011"),

            # WhatsApp Business
            ("📱 WhatsApp Business Reviews", "ID:13012"),
            ("💬 WhatsApp Group Activity Boost", "ID:13013"),
            ("🔔 WhatsApp Broadcast List Growth", "ID:13014"),
            ("📈 WhatsApp Business Growth", "ID:13015")
        ],

        "tiktok": [
            # TikTok Followers
            ("👥 TikTok Followers - Real Active", "ID:10001"),
            ("👥 TikTok Followers - Premium Quality", "ID:10002"),
            ("👥 TikTok Followers - Indian Users", "ID:10003"),
            ("👥 TikTok Followers - Global Mix", "ID:10004"),
            ("👥 TikTok Followers - Targeted", "ID:10005"),

            # TikTok Likes
            ("❤️ TikTok Video Likes - Real Users", "ID:10006"),
            ("❤️ TikTok Likes - Fast Delivery", "ID:10007"),
            ("❤️ TikTok Likes - Viral Boost", "ID:10008"),
            ("❤️ TikTok Auto Likes - Monthly", "ID:10009"),

            # TikTok Views
            ("👁️ TikTok Video Views - Real Users", "ID:10010"),
            ("👁️ TikTok Views - Fast Delivery", "ID:10011"),
            ("👁️ TikTok Views - Premium Quality", "ID:10012"),
            ("👁️ TikTok Profile Views", "ID:10013"),

            # TikTok Engagement
            ("💬 TikTok Comments - Real Users", "ID:10014"),
            ("💬 TikTok Comments - Positive Only", "ID:10015"),
            ("📤 TikTok Shares - Viral Boost", "ID:10016"),
            ("💾 TikTok Saves - Bookmark", "ID:10017"),

            # TikTok Advanced
            ("🔴 TikTok Live Views - Real Time", "ID:10018"),
            ("🎵 TikTok Sound Usage - Viral", "ID:10019"),
            ("⏰ TikTok Story Views", "ID:10020"),
            ("🎯 TikTok Duet Views", "ID:10021"),
            ("✨ TikTok For You Page", "ID:10022"),
            ("🚀 TikTok Viral Package", "ID:10023")
        ],

        "twitter": [
            # Twitter Followers
            ("👥 Twitter Followers - Real Active", "ID:12001"),
            ("👥 Twitter Followers - Premium Quality", "ID:12002"),
            ("👥 Twitter Followers - Targeted India", "ID:12003"),
            ("👥 Twitter Followers - Global Mix", "ID:12004"),
            ("👥 Twitter Followers - Instant Start", "ID:12005"),

            # Twitter Engagement
            ("❤️ Twitter Tweet Likes - Real Users", "ID:12006"),
            ("❤️ Twitter Likes - Fast Delivery", "ID:12007"),
            ("❤️ Twitter Post Likes - Premium", "ID:12008"),
            ("🔄 Twitter Retweets - Real Accounts", "ID:12009"),
            ("🔄 Twitter Retweets - Viral Boost", "ID:12010"),

            # Twitter Comments & Replies
            ("💬 Twitter Comments - Real Users", "ID:12011"),
            ("💬 Twitter Replies - Custom Text", "ID:12012"),
            ("💬 Twitter Comments - Positive", "ID:12013"),

            # Twitter Views & Impressions
            ("👁️ Twitter Tweet Impressions", "ID:12014"),
            ("👁️ Twitter Profile Views", "ID:12015"),
            ("🎯 Twitter Video Views", "ID:12016"),
            ("📱 Twitter Thread Views", "ID:12017"),

            # Twitter Advanced
            ("📊 Twitter Space Listeners", "ID:12018"),
            ("🔔 Twitter Tweet Bookmarks", "ID:12019"),
            ("⭐ Twitter Poll Votes", "ID:12020"),
            ("📈 Twitter Reach Boost", "ID:12021"),
            ("🎪 Twitter Trending Boost", "ID:12022")
        ],

        "linkedin": [
            # LinkedIn Followers & Connections
            ("👥 LinkedIn Followers - Real Active", "ID:14001"),
            ("👥 LinkedIn Followers - Premium", "ID:14002"),
            ("👥 LinkedIn Followers - Targeted Industry", "ID:14003"),
            ("📈 LinkedIn Connection Requests", "ID:14004"),
            ("📈 LinkedIn Network Growth", "ID:14005"),

            # LinkedIn Post Engagement
            ("❤️ LinkedIn Post Likes - Real Users", "ID:14006"),
            ("❤️ LinkedIn Post Likes - Professional", "ID:14007"),
            ("💬 LinkedIn Comments - Real Professionals", "ID:14008"),
            ("💬 LinkedIn Comments - Industry Related", "ID:14009"),
            ("📤 LinkedIn Shares - Professional Network", "ID:14010"),

            # LinkedIn Profile Services
            ("👁️ LinkedIn Profile Views - Real", "ID:14011"),
            ("👁️ LinkedIn Profile Views - Premium", "ID:14012"),
            ("💼 LinkedIn Skill Endorsements", "ID:14013"),
            ("⭐ LinkedIn Recommendations", "ID:14014"),

            # LinkedIn Company & Business
            ("📊 LinkedIn Company Page Follows", "ID:14015"),
            ("📊 LinkedIn Company Page Likes", "ID:14016"),
            ("🎯 LinkedIn Article Views", "ID:14017"),
            ("🎯 LinkedIn Article Engagement", "ID:14018"),
            ("📈 LinkedIn Business Growth", "ID:14019"),
            ("📱 LinkedIn Lead Generation", "ID:14020")
        ]
    }

    keyboard = []
    platform_packages = packages.get(platform, [])

    # Add packages in rows of 1
    for package_name, service_id in platform_packages:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{package_name}\\n{service_id}", 
                callback_data=f"package_{platform}_{service_id.replace('ID:', '')}"
            )
        ])

    # Add back button
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Back to Services", callback_data="new_order")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ========== SERVICE HANDLERS ==========

def register_service_handlers(dp, require_account):
    """Register all service-related handlers"""

    print("🔄 Registering service handlers...")

    # ========== PLATFORM SELECTION HANDLERS ==========
    @dp.callback_query(F.data.startswith("service_"))
    async def cb_service_select(callback: CallbackQuery):
        """Handle service platform selection"""
        if not callback.message:
            return

        platform = (callback.data or "").replace("service_", "")

        if platform == "instagram":
            text = """
📷 <b>Instagram Services</b>

🌟 <b>Premium Instagram Growth Services</b>

✅ <b>High Quality Features:</b>
• Real & Active Users Only
• Instant Start (0-30 minutes)
• High Retention Rate (90%+)
• Safe & Secure Methods
• 24/7 Customer Support

💰 <b>Competitive Pricing:</b>
• Followers: ₹0.50 per follower
• Likes: ₹0.30 per like
• Views: ₹0.10 per view
• Comments: ₹0.80 per comment

💡 <b>अपनी जरूरत का package चुनें:</b>
"""
            await safe_edit_message(callback, text, get_service_packages("instagram"))

        elif platform == "youtube":
            text = """
🎥 <b>YouTube Services</b>

🚀 <b>Professional YouTube Growth Services</b>

✅ <b>Premium Features:</b>
• Real Subscribers & Views
• Instant Delivery
• High Retention Guarantee
• AdSense Safe Methods
• Monetization Friendly

💰 <b>Best Pricing:</b>
• Subscribers: ₹2.00 per subscriber
• Views: ₹0.05 per view
• Likes: ₹0.40 per like
• Comments: ₹1.00 per comment

🎯 <b>YouTube का package select करें:</b>
"""
            await safe_edit_message(callback, text, get_service_packages("youtube"))

        elif platform == "facebook":
            text = """
📘 <b>Facebook Services</b>

🔵 <b>Professional Facebook Growth</b>

📋 <b>Available Services:</b>
• Page Likes & Followers
• Post Likes & Shares
• Group Members
• Video Views
• Live Stream Views

💡 <b>Facebook services के लिए package choose करें:</b>
"""
            await safe_edit_message(callback, text, get_service_packages("facebook"))

        elif platform == "telegram":
            text = """
📞 <b>Telegram Services</b>

💬 <b>Professional Telegram Growth</b>

📋 <b>Available Services:</b>
• Channel Members
• Group Members
• Post Views
• Channel Boost
• Poll Votes

💡 <b>Telegram services के लिए package choose करें:</b>
"""
            await safe_edit_message(callback, text, get_service_packages("telegram"))

        else:
            text = f"""
🚀 <b>{platform.title()} Services</b>

🔧 <b>Services Available!</b>

💡 <b>{platform.title()} services packages:</b>

⚡ <b>Features:</b>
• High-quality {platform} services
• Competitive pricing
• Instant delivery
• 24/7 support

💡 <b>अपना package select करें:</b>
"""
            await safe_edit_message(callback, text, get_service_packages(platform))

        await callback.answer()

    @dp.callback_query(F.data.startswith("package_"))
    async def cb_package_select(callback: CallbackQuery):
        """Handle package selection with detailed description"""
        if not callback.message:
            return

        # Parse callback data: package_platform_serviceid
        parts = (callback.data or "").split("_")
        if len(parts) >= 3:
            platform = parts[1]
            service_id = parts[2]

            # Get detailed package description
            description = get_package_description(platform, service_id)

            await safe_edit_message(callback, description["text"], description["keyboard"])

        await callback.answer()

    @dp.callback_query(F.data.startswith("confirm_order_"))
    async def cb_confirm_order(callback: CallbackQuery):
        """Handle order confirmation and ask for link"""
        if not callback.message:
            return

        # Parse callback data: confirm_order_platform_serviceid
        parts = (callback.data or "").split("_")
        if len(parts) >= 4:
            platform = parts[2]
            service_id = parts[3]

            text = f"""
✅ <b>Order Confirmation</b>

🎯 <b>Platform:</b> {platform.title()}
🆔 <b>Service ID:</b> {service_id}

📝 <b>Next Step: Enter Your Link</b>

💡 <b>कृपया अपना {platform} link send करें:</b>

📋 <b>Link Requirements:</b>
• Must be public and accessible
• Correct format for {platform}
• No private or locked accounts

⚠️ <b>Example Formats:</b>
• Instagram: https://instagram.com/username
• YouTube: https://youtube.com/watch?v=xyz या https://youtube.com/channel/xyz
• Facebook: https://facebook.com/pagename
• TikTok: https://tiktok.com/@username
• Twitter: https://twitter.com/username

💬 <b>Simply send your link as a message...</b>
"""

            # Store order data in user state
            from main import user_state
            user_id = callback.from_user.id if callback.from_user else 0
            if user_id not in user_state:
                user_state[user_id] = {"current_step": None, "data": {}}

            user_state[user_id]["current_step"] = "waiting_link"
            user_state[user_id]["data"]["service"] = f"{platform}_{service_id}"
            user_state[user_id]["data"]["platform"] = platform
            user_state[user_id]["data"]["service_id"] = service_id

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="❌ Cancel Order", callback_data=f"service_{platform}")
                ]
            ])

            await safe_edit_message(callback, text, keyboard)

        await callback.answer()

# Export functions for main.py
__all__ = ['register_service_handlers', 'get_services_main_menu']
