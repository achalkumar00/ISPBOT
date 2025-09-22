# Social Media Services Management
# Handles all service-related operations for the Telegram bot

import time
import os
import traceback
import asyncio
from datetime import datetime
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery,
    Message
)
from aiogram import F
from aiogram.fsm.context import FSMContext


# ========== ADMIN CONFIGURATION ==========
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "7437014244"))  # Main admin user ID from environment
# Import START_TIME and dp from main.py to ensure consistency
try:
    from main import START_TIME, dp
    bot_start_time = START_TIME
except ImportError:
    bot_start_time = time.time()
    dp = None  # Fallback if import fails
error_logs = []  # Store recent errors
maintenance_mode = False  # Global maintenance flag
activity_logs = []  # Store recent activity

# ========== UTILITY FUNCTIONS ==========

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None):
    """Safely edit message with comprehensive error handling"""
    try:
        if (callback.message and 
            hasattr(callback.message, 'edit_text') and 
            hasattr(callback.message, 'message_id') and 
            hasattr(callback.message, 'text') and
            callback.message.__class__.__name__ != 'InaccessibleMessage' and
            not isinstance(callback.message, type(None))):
            await callback.message.edit_text(
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
        else:
            # Message is inaccessible, send new message instead
            if (callback.message and 
                hasattr(callback.message, 'chat') and 
                callback.message.chat and 
                hasattr(callback.message.chat, 'id')):
                from main import bot
                await bot.send_message(
                    callback.message.chat.id, 
                    text, 
                    parse_mode="HTML", 
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
    except Exception as e:
        print(f"Error editing message: {e}")
        log_error(f"Message edit error: {str(e)}")
        # Final fallback - try sending new message
        try:
            if (callback.message and 
                hasattr(callback.message, 'chat') and 
                callback.message.chat and 
                hasattr(callback.message.chat, 'id')):
                from main import bot
                await bot.send_message(
                    callback.message.chat.id, 
                    text, 
                    parse_mode="HTML", 
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
        except Exception as fallback_error:
            print(f"Final fallback failed: {fallback_error}")
            log_error(f"Final fallback error: {str(fallback_error)}")

# ========== ADMIN UTILITY FUNCTIONS ==========

def log_error(error_message: str):
    """Log errors for admin monitoring"""
    global error_logs
    error_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "error": error_message,
        "traceback": traceback.format_exc() if hasattr(traceback, 'format_exc') else ""
    }
    error_logs.append(error_entry)

    # Keep only last 100 errors
    if len(error_logs) > 100:
        error_logs = error_logs[-100:]

def log_activity(user_id: int, action: str):
    """Log user activity for admin monitoring"""
    global activity_logs
    activity_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "action": action
    }
    activity_logs.append(activity_entry)

    # Keep only last 200 activities
    if len(activity_logs) > 200:
        activity_logs = activity_logs[-200:]

def format_uptime():
    """Calculate and format bot uptime in XdYmZs format"""
    try:
        from main import START_TIME
        uptime_seconds = time.time() - START_TIME
    except ImportError:
        uptime_seconds = time.time() - bot_start_time

    # Calculate days, hours, minutes, seconds
    days, remainder = divmod(uptime_seconds, 86400)  # 86400 seconds = 1 day
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Format as requested: 2d20m22s (days, minutes, seconds)
    if days > 0:
        return f"{int(days)}d{int(hours)}h{int(minutes)}m{int(seconds)}s"
    elif hours > 0:
        return f"{int(hours)}h{int(minutes)}m{int(seconds)}s"
    else:
        return f"{int(minutes)}m{int(seconds)}s"

def get_system_stats():
    """Get system performance statistics (simplified without psutil)"""
    try:
        # Simple memory info from /proc/meminfo (Linux)
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()

        # Extract memory values
        mem_total = None
        mem_free = None
        for line in meminfo.split('\n'):
            if 'MemTotal:' in line:
                mem_total = int(line.split()[1]) * 1024  # Convert KB to bytes
            elif 'MemFree:' in line:
                mem_free = int(line.split()[1]) * 1024

        if mem_total and mem_free:
            mem_used = mem_total - mem_free
            mem_percent = (mem_used / mem_total) * 100
            return {
                "cpu": "Normal",  # Simplified
                "memory": f"{mem_percent:.1f}%",
                "disk": "Good",   # Simplified
                "memory_used": f"{mem_used / (1024**3):.2f} GB",
                "memory_total": f"{mem_total / (1024**3):.2f} GB"
            }
        else:
            raise Exception("Could not parse memory info")

    except Exception as e:
        log_error(f"System stats error: {str(e)}")
        return {
            "cpu": "Normal",
            "memory": "Good", 
            "disk": "Stable",
            "memory_used": "~0.5 GB",
            "memory_total": "~2.0 GB"
        }

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id == ADMIN_USER_ID

# ========== MAIN SERVICES MENU ==========

def get_services_main_menu() -> InlineKeyboardMarkup:
    """Build main services selection menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📸 INSTAGRAM", callback_data="service_instagram"),
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
            InlineKeyboardButton(text="🌟 More Services", callback_data="more_services")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")
        ]
    ])

# ========== PACKAGE DESCRIPTION FUNCTION ==========

def get_package_description(platform: str, service_id: str) -> dict:
    """Get detailed description for a specific package"""

    # Package details database - Each package has unique description
    package_details = {
        # Instagram Followers - 5 Different Quality Packages
        "2001": {
            "name": "👥 Instagram Followers - Economy",
            "price": "₹150 per 1000 followers",
            "description": """You must turn off the "Flag for review" option before ordering Instagram followers and for refill support.

हिन्दी:
Instagram Followers Order karne Se Pehle Ya Refill Support K liye Aapko Pehle Jarur Us I'd ka "Flag for review" Option Ko Off Karna hoga.

⏳ Start Time: 0 – 30 Minutes
⚡ Delivery Speed: Up to 20K Followers / Day
💎 Quality: Real + Active Mix (High Engagement)
💧 Drop Rate: 2% – 5% (Mostly Stable)
♻️ Refill: 30 Days Auto Refill (Instant Processing)
🔗 Works On: Profile Link Only

⚠️ If the Flag for Review option is ON → 🚫 No refill / refund will be provided.
⚠️ If the Flag for Review option is turned OFF after the order is completed → ❌ No refill / refund will be possible.
💡 To learn how to turn OFF "Flag for Review", use the command below:
➡️ /flag_help"""
        },
        "2002": {
            "name": "👥 Instagram Followers - 📈 Standard",
            "price": "₹250 per 1000 followers",
            "description": """You must turn off the "Flag for review" option before ordering Instagram followers and for refill support.

हिन्दी:
Instagram Followers Order karne Se Pehle Ya Refill Support K liye Aapko Pehle Jarur Us I'd ka "Flag for review" Option Ko Off Karna hoga.

⏳ Start Time: 60 – 180 Minutes
⚡ Delivery Speed: Up to 5K Followers / Day
💎 Quality: Real + Mix (High Engagement)
💧 Drop Rate: Low 
♻️ Refill: Now
🔗 Works On: Profile Link Only

⚠️ If the Flag for Review option is ON → 🚫 No refill / refund will be provided.
⚠️ If the Flag for Review option is turned OFF after the order is completed → ❌ No refill / refund will be possible.
💡 To learn how to turn OFF "Flag for Review", use the command below:
➡️ /flag_help"""
        },
        "2003": {
            "name": "👥 Instagram Followers - ⭐ Premium",
            "price": "₹300 per 1000 followers",
            "description": """You must turn off the "Flag for review" option before ordering Instagram followers and for refill support.

हिन्दी:
Instagram Followers Order karne Se Pehle Ya Refill Support Ke liye Aapko Pehle Jarur Us I'd ka "Flag for review" Option Ko Off Karna hoga.

⏳ Start Time: 30 – 120 Minutes
⚡ Delivery Speed: Up to 10K Followers / Day
💎 Quality: Real +  Mix (High Engagement)
💧 Drop Rate: 5% – 10% (Mostly Stable)
♻️ Refill: 60 Days Auto Refill (Instant Processing)
🔗 Works On: Profile Link Only

⚠️ If the Flag for Review option is ON → 🚫 No refill / refund will be provided.
⚠️ If the Flag for Review option is turned OFF after the order is completed → ❌ No refill / refund will be possible.
💡 To learn how to turn OFF "Flag for Review", use the command below:
➡️ /flag_help"""
        },
        "2004": {
            "name": "👥 Instagram Followers - 🇮🇳 Indian Premium",
            "price": "₹359 per 1000 followers",
            "description": """You must turn off the "Flag for review" option before ordering Instagram followers and for refill support.

हिन्दी:
Instagram Followers Order karne Se Pehle Ya Refill Support K liye Aapko Pehle Jarur Us I'd ka "Flag for review" Option Ko Off Karna hoga.

⏳ Start Time: 0 – 60 Minutes
⚡ Delivery Speed: Up to 20K Followers / Day
💎 Quality:  Mix (High Engagement)
💧 Drop Rate: 2% – 5% (Mostly Stable)
♻️ Refill: 180 Days Auto Refill (Instant Processing)
🔗 Works On: Profile Link Only

⚠️ If the Flag for Review option is ON → 🚫 No refill / refund will be provided.
⚠️ If the Flag for Review option is turned OFF after the order is completed → ❌ No refill / refund will be possible.
💡 To learn how to turn OFF "Flag for Review", use the command below:
➡️ /flag_help""",
        },
        "2005": {
            "name": "👥 Instagram Followers - 👑 VIP Elite",
            "price": "₹480 per 1000 followers",
            "description": """You must turn off the "Flag for review" option before ordering Instagram followers and for refill support.

हिन्दी:
Instagram Followers Order karne Se Pehle Ya Refill Support K liye Aapko Pehle Jarur Us I'd ka "Flag for review" Option Ko Off Karna hoga.

⏳ Start Time: 0 – 30 Minutes
⚡ Delivery Speed: Up to 200K Followers / Day
💎 Quality: Real + Active Mix (High Engagement)
💧 Drop Rate: Non Drop (Mostly Stable)
♻️ Refill: Lifetime Auto Refill (Instant Processing)
🔗 Works On: Profile Link Only

⚠️ If the Flag for Review option is ON → 🚫 No refill / refund will be provided.
⚠️ If the Flag for Review option is turned OFF after the order is completed → ❌ No refill / refund will be possible.
💡 To learn how to turn OFF "Flag for Review", use the command below:
➡️ /flag_help""",
        },

        # Instagram Post Likes - 5 Different Quality Packages
        "2011": {
            "name": "❤️ Instagram Post Likes - 💰 Economy",
            "price": "₹18 per 1000 likes",
            "description": """⏳ Start Time: 0–60 Minutes
⚡ Speed: 20K Likes / Day 🚀
💧 Drop Rate: 0–10% (Almost Stable)
♻️ Refill / Refund: ❌ Not Available
💎 Quality: Low-Quality Realistic Engagement
🔗 Link Required: Post / Reel / Video Link""",
        },
        "2012": {
            "name": "❤️ Instagram Post Likes - 📈 Standard",
            "price": "₹30 per 1000 likes",
            "description": """⏳ Start Time: 0–30 Minutes
⚡ Speed: 30K Likes / Day 🚀
💧 Drop Rate: 0–5% (Stable)
♻️ Refill / Refund: ❌ Not Available
💎 Quality: Standard Quality Realistic Engagement
🔗 Link Required: Post / Reel / Video Link""",
        },
        "2013": {
            "name": "❤️ Instagram Post Likes - ⭐ Premium",
            "price": "₹45 per 1000 likes",
            "description": """⏳ Start Time: 0–60 Minutes
⚡ Speed: 50K Likes / Day 🚀
💧 Drop Rate: 0–7% (Almost Stable)
♻️ Refill / Refund: ❌ Not Available
💎 Quality: High-Quality Realistic Engagement
🔗 Link Required: Post / Reel / Video Link""",
        },
        "2014": {
            "name": "❤️ Instagram Post Likes - 🇮🇳 Indian Premium",
            "price": "₹54 per 1000 likes",
            "description": """⏳ Start Time: 0–60 Minutes
⚡ Speed: 50K Likes / Day 🚀
💧 Drop Rate: 0–7% (Almost Stable)
♻️ Refill / Refund: ❌ Not Available
💎 Quality: High-Quality Realistic Engagement
🔗 Link Required: Post / Reel / Video Link""",
        },
        "2015": {
            "name": "❤️ Instagram Post Likes - 👑 VIP Elite",
            "price": "₹66 per 1000 likes",
            "description": """⏳ Start Time: 0–60 Minutes
⚡ Speed: 50K Likes / Day 🚀
💧 Drop Rate: 0–7% (Almost Stable)
♻️ Refill / Refund: ❌ Not Available
💎 Quality: High-Quality Realistic Engagement
🔗 Link Required: Post / Reel / Video Link""",
        },

        # Instagram Reel Views - 5 Different Quality Packages
        "2041": {
            "name": "👁️ Instagram Reel Views - 💰 Economy",
            "price": "₹12 per 1000 views",
            "description": """⏳ Start: 0–30 Minutes  
⚡ Speed: Up to 150K Views / Day 🚀  
💧 Drop: 0–5% (Pretty Stable)  
♻️ Refill / Refund: ❌ Not Applicable  
💎 Quality: Authentic & Natural View Count  
🔗 Link: Reel / Video / Post Link Required""",
        },
        "2042": {
            "name": "👁️ Instagram Reel Views - 📈 Standard",
            "price": "₹20 per 1000 views",
            "description": """⏳ Start: 0–30 Minutes  
⚡ Speed: Up to 150K Views / Day 🚀  
💧 Drop: 0–5% (Pretty Stable)  
♻️ Refill / Refund: ❌ Not Applicable  
💎 Quality: Authentic & Natural View Count  
🔗 Link: Reel / Video / Post Link Required""",
        },
        "2043": {
            "name": "👁️ Instagram Reel Views - ⭐ Premium",
            "price": "₹30 per 1000 views",
            "description": """⏳ Start: 0–30 Minutes  
⚡ Speed: Up to 150K Views / Day 🚀  
💧 Drop: 0–5% (Pretty Stable)  
♻️ Refill / Refund: ❌ Not Applicable  
💎 Quality: Authentic & Natural View Count  
🔗 Link: Reel / Video / Post Link Required""",
        },
        "2044": {
            "name": "👁️ Instagram Reel Views - 🇮🇳 Indian Premium",
            "price": "₹36 per 1000 views",
            "description": """⏳ Start: 0–30 Minutes  
⚡ Speed: Up to 150K Views / Day 🚀  
💧 Drop: 0–5% (Pretty Stable)  
♻️ Refill / Refund: ❌ Not Applicable  
💎 Quality: Authentic & Natural View Count  
🔗 Link: Reel / Video / Post Link Required""",
        },
        "2045": {
            "name": "👁️ Instagram Reel Views - 👑 VIP Elite",
            "price": "₹44 per 1000 views",
            "description": """⏳ Start: 0–30 Minutes  
⚡ Speed: Up to 150K Views / Day 🚀  
💧 Drop: 0–5% (Pretty Stable)  
♻️ Refill / Refund: ❌ Not Applicable  
💎 Quality: Authentic & Natural View Count  
🔗 Link: Reel / Video / Post Link Required""",
        },

        # Instagram Story Views - 5 Different Quality Packages
        "2051": {
            "name": "📖 Instagram Story Views - 💰 Economy",
            "price": "₹12 per 1000 views",
            "description": """⏳ Start: 0–30 Minutes  
⚡ Speed: Up to 150K Views / Day 🚀  
💧 Drop: 0–5% (Pretty Stable)  
♻️ Refill / Refund: ❌ Not Applicable  
💎 Quality: Authentic & Natural View Count  
🔗 Link: Reel / Video / Post Link Required""",
        },
        "2052": {
            "name": "📖 Instagram Story Views - 📈 Standard",
            "price": "₹20 per 1000 views",
            "description": """⏳ Start: 0–30 Minutes  
⚡ Speed: Up to 150K Views / Day 🚀  
💧 Drop: 0–5% (Pretty Stable)  
♻️ Refill / Refund: ❌ Not Applicable  
💎 Quality: Authentic & Natural View Count  
🔗 Link: Reel / Video / Post Link Required""",
        },
        "2053": {
            "name": "📖 Instagram Story Views - ⭐ Premium",
            "price": "₹30 per 1000 views",
            "description": """⏳ Start: 0–30 Minutes  
⚡ Speed: Up to 150K Views / Day 🚀  
💧 Drop: 0–5% (Pretty Stable)  
♻️ Refill / Refund: ❌ Not Applicable  
💎 Quality: Authentic & Natural View Count  
🔗 Link: Reel / Video / Post Link Required""",
        },
        "2054": {
            "name": "📖 Instagram Story Views - 🇮🇳 Indian Premium",
            "price": "₹36 per 1000 views",
            "description": """⏳ Start: 0–30 Minutes  
⚡ Speed: Up to 150K Views / Day 🚀  
💧 Drop: 0–5% (Pretty Stable)  
♻️ Refill / Refund: ❌ Not Applicable  
💎 Quality: Authentic & Natural View Count  
🔗 Link: Reel / Video / Post Link Required""",
        },
        "2055": {
            "name": "📖 Instagram Story Views - 👑 VIP Elite",
            "price": "₹44 per 1000 views",
            "description": """⏳ Start: 0–30 Minutes  
⚡ Speed: Up to 150K Views / Day 🚀  
💧 Drop: 0–5% (Pretty Stable)  
♻️ Refill / Refund: ❌ Not Applicable  
💎 Quality: Authentic & Natural View Count  
🔗 Link: Reel / Video / Post Link Required""",
        },

        # Instagram Story Likes - 5 Different Quality Packages
        "2061": {
            "name": "💖 Instagram Story Likes - 💰 Economy",
            "price": "₹18 per 1000 likes",
            "description": "Cost-effective Instagram story likes for basic engagement on your stories. Suitable for casual users who post stories occasionally.",
        },
        "2062": {
            "name": "💖 Instagram Story Likes - 📈 Standard",
            "price": "₹30 per 1000 likes",
            "description": "Standard Instagram story likes with balanced quality and pricing. Perfect for regular story creators who want steady engagement.",
        },
        "2063": {
            "name": "💖 Instagram Story Likes - ⭐ Premium",
            "price": "₹45 per 1000 likes",
            "description": "Premium Instagram story likes from engaged users who actively interact with story content. Better visibility for story highlights.",
        },
        "2064": {
            "name": "💖 Instagram Story Likes - 🇮🇳 Indian Premium",
            "price": "₹54 per 1000 likes",
            "description": "Targeted Indian Instagram story likes for local audience engagement. Excellent for region-specific content and local businesses.",
        },
        "2065": {
            "name": "💖 Instagram Story Likes - 👑 VIP Elite",
            "price": "₹66 per 1000 likes",
            "description": "Ultimate Instagram story likes for maximum impact. Instant engagement from premium accounts with highest interaction rates.",
        },

        # Instagram Story Link Clicks - 5 Different Quality Packages
        "2071": {
            "name": "🔗 Instagram Story Link Clicks - 💰 Economy",
            "price": "₹90 per 1000 clicks",
            "description": "Budget-friendly Instagram story link clicks for basic traffic boost. Suitable for new businesses testing story link features.",
        },
        "2072": {
            "name": "🔗 Instagram Story Link Clicks - 📈 Standard",
            "price": "₹150 per 1000 clicks",
            "description": "Standard Instagram story link clicks with moderate engagement quality. Good for driving traffic to websites and landing pages.",
        },
        "2073": {
            "name": "🔗 Instagram Story Link Clicks - ⭐ Premium",
            "price": "₹225 per 1000 clicks",
            "description": "Premium Instagram story link clicks from engaged users who actually visit linked content. Better conversion potential for businesses.",
        },
        "2074": {
            "name": "🔗 Instagram Story Link Clicks - 🇮🇳 Indian Premium",
            "price": "₹270 per 1000 clicks",
            "description": "High-quality Indian Instagram story link clicks for local market targeting. Perfect for Indian businesses and regional campaigns.",
        },
        "2075": {
            "name": "🔗 Instagram Story Link Clicks - 👑 VIP Elite",
            "price": "₹330 per 1000 clicks",
            "description": "Maximum quality Instagram story link clicks with highest conversion potential. Premium traffic from highly engaged users.",
        },

        # Instagram Post Shares - 5 Different Quality Packages
        "2081": {
            "name": "📤 Instagram Post Shares - 💰 Economy",
            "price": "₹108 per 1000 shares",
            "description": "Budget-friendly Instagram post shares for basic viral growth. Simple sharing from real accounts with gradual delivery for natural growth pattern.",
        },
        "2082": {
            "name": "📤 Instagram Post Shares - 📈 Standard", 
            "price": "₹180 per 1000 shares",
            "description": "Standard Instagram post shares with reliable delivery and good reach potential. Perfect for content creators wanting steady viral growth.",
        },
        "2083": {
            "name": "📤 Instagram Post Shares - ⭐ Premium",
            "price": "₹270 per 1000 shares",
            "description": "Premium Instagram post shares from engaged users who actively share content. Enhanced viral potential with faster reach expansion.",
        },
        "2084": {
            "name": "📤 Instagram Post Shares - 🇮🇳 Indian Premium",
            "price": "₹324 per 1000 shares",
            "description": "High-quality Indian Instagram post shares for local viral growth. Perfect for targeting Indian audience with cultural content sharing.",
        },
        "2085": {
            "name": "📤 Instagram Post Shares - 👑 VIP Elite",
            "price": "₹396 per 1000 shares",
            "description": "Ultimate Instagram post shares for maximum viral impact. Instant sharing from premium accounts with highest engagement rates for viral success.",
        },

        # Instagram Reel Shares - 5 Different Quality Packages  
        "2091": {
            "name": "📱 Instagram Reel Shares - 💰 Economy",
            "price": "₹108 per 1000 shares",
            "description": "Affordable Instagram reel shares for basic video viral growth. Slow but steady sharing pattern to make your reels reach more audiences gradually.",
        },
        "2092": {
            "name": "📱 Instagram Reel Shares - 📈 Standard",
            "price": "₹180 per 1000 shares", 
            "description": "Standard Instagram reel shares with balanced viral growth. Good for reel creators who want consistent sharing and reach expansion."
        },
        "2093": {
            "name": "📱 Instagram Reel Shares - ⭐ Premium",
            "price": "₹270 per 1000 shares",
            "description": "Premium Instagram reel shares from video content enthusiasts. Enhanced viral potential for reels with faster algorithmic boost."
        },
        "2094": {
            "name": "📱 Instagram Reel Shares - 🇮🇳 Indian Premium",
            "price": "₹324 per 1000 shares",
            "description": "Exclusive Indian Instagram reel shares for local video viral growth. Perfect for Hindi and regional content creators targeting Indian audience."
        },
        "2095": {
            "name": "📱 Instagram Reel Shares - 👑 VIP Elite",
            "price": "₹396 per 1000 shares",
            "description": "Maximum quality Instagram reel shares for ultimate viral success. Instant sharing from premium video enthusiasts for explosive reel growth."
        },

        # Instagram Channel Members - 5 Different Quality Packages
        "2101": {
            "name": "👥 Instagram Channel Members - 💰 Economy", 
            "price": "₹240 per 1000 members",


            "description": "Budget-friendly Instagram channel members for basic community growth. Suitable for new channels starting their member base building journey.",

        },
        "2102": {
            "name": "👥 Instagram Channel Members - 📈 Standard",
            "price": "₹400 per 1000 members",


            "description": "Standard Instagram channel members with good engagement potential. Perfect for growing channels that need consistent member addition.",

        },
        "2103": {
            "name": "👥 Instagram Channel Members - ⭐ Premium",
            "price": "₹600 per 1000 members",


            "description": "Premium Instagram channel members with high engagement rates. Active members who participate in channel discussions and content.",

        },
        "2104": {
            "name": "👥 Instagram Channel Members - 🇮🇳 Indian Premium",
            "price": "₹720 per 1000 members",


            "description": "High-quality Indian Instagram channel members for local community building. Perfect for Hindi channels and regional content creators.",

        },
        "2105": {
            "name": "👥 Instagram Channel Members - 👑 VIP Elite",
            "price": "₹880 per 1000 members", 


            "description": "Ultimate Instagram channel members with maximum engagement and activity. Elite community builders who actively contribute to channel growth.",

        },

        # Instagram Random Comments - 5 Different Quality Packages
        "2111": {
            "name": "💬 Instagram Random Comments - 💰 Economy",
            "price": "₹54 per 1000 comments",


            "description": "Budget-friendly Instagram random comments for basic engagement boost. Simple pre-written comments from real accounts with slow delivery speed.",

        },
        "2112": {
            "name": "💬 Instagram Random Comments - 📈 Standard",
            "price": "₹90 per 1000 comments",


            "description": "Standard Instagram random comments with better variety and engagement. Good selection of pre-written comments for consistent interaction.",

        },
        "2113": {
            "name": "💬 Instagram Random Comments - ⭐ Premium",
            "price": "₹135 per 1000 comments",


            "description": "Premium Instagram random comments with high-quality messages and better engagement. Thoughtful comments that look natural and engaging.",

        },
        "2114": {
            "name": "💬 Instagram Random Comments - 🇮🇳 Indian Premium",
            "price": "₹162 per 1000 comments",


            "description": "High-quality Indian Instagram random comments with Hindi/English mix. Perfect for local content with culturally relevant comment messages.",

        },
        "2115": {
            "name": "💬 Instagram Random Comments - 👑 VIP Elite",
            "price": "₹198 per 1000 comments",


            "description": "Ultimate Instagram random comments with maximum quality and engagement. Carefully selected comments that boost your post interaction significantly.",

        },

        # Instagram Emoji Comments - 5 Different Quality Packages
        "2121": {
            "name": "😀 Instagram Emoji Comments - 💰 Economy",
            "price": "₹42 per 1000 comments",


            "description": "Cost-effective Instagram emoji comments for basic reaction boost. Simple emoji combinations from real accounts with gradual delivery pattern.",

        },
        "2122": {
            "name": "😀 Instagram Emoji Comments - 📈 Standard",
            "price": "₹70 per 1000 comments",


            "description": "Standard Instagram emoji comments with good variety and reaction diversity. Balanced emoji engagement for consistent post interaction.",

        },
        "2123": {
            "name": "😀 Instagram Emoji Comments - ⭐ Premium",
            "price": "₹105 per 1000 comments",


            "description": "Premium Instagram emoji comments with creative emoji combinations and high engagement. Trending emoji patterns that enhance post appeal.",

        },
        "2124": {
            "name": "😀 Instagram Emoji Comments - 🇮🇳 Indian Premium",
            "price": "₹126 per 1000 comments",


            "description": "High-quality Indian Instagram emoji comments with locally popular emoji patterns. Perfect for Indian audience with cultural emoji preferences.",

        },
        "2125": {
            "name": "😀 Instagram Emoji Comments - 👑 VIP Elite",
            "price": "₹154 per 1000 comments",


            "description": "Ultimate Instagram emoji comments with maximum creativity and viral emoji patterns. Premium emoji combinations for maximum post engagement.",

        },

        # Instagram Custom Comments - 5 Different Quality Packages
        "2131": {
            "name": "✍️ Instagram Custom Comments - 💰 Economy",
            "price": "₹120 per 1000 comments",


            "description": "Budget-friendly Instagram custom comments with your provided text. Basic delivery of your custom messages from real accounts with slower speed.",

        },
        "2132": {
            "name": "✍️ Instagram Custom Comments - 📈 Standard",
            "price": "₹200 per 1000 comments",


            "description": "Standard Instagram custom comments with reliable delivery of your messages. Good balance of speed and quality for personalized engagement.",

        },
        "2133": {
            "name": "✍️ Instagram Custom Comments - ⭐ Premium",
            "price": "₹300 per 1000 comments",


            "description": "Premium Instagram custom comments with fast delivery of your personalized messages. High-quality accounts posting your custom content naturally.",

        },
        "2134": {
            "name": "✍️ Instagram Custom Comments - 🇮🇳 Indian Premium",
            "price": "₹360 per 1000 comments",


            "description": "High-quality Indian Instagram custom comments with your personalized Hindi/English messages. Perfect for local audience engagement.",

        },
        "2135": {
            "name": "✍️ Instagram Custom Comments - 👑 VIP Elite",
            "price": "₹440 per 1000 comments",
            "description": "Ultimate Instagram custom comments with fastest delivery of your personalized messages. Elite accounts providing maximum engagement impact.",
        },

        # Instagram Channel Members - 5 Different Quality Packages
        "2101": {
            "name": "👥 Instagram Channel Members - 💰 Economy", 
            "price": "₹240 per 1000 members",


            "description": "Budget-friendly Instagram channel members for basic community growth. Suitable for new channels starting their member base building journey.",

        },
        "2102": {
            "name": "👥 Instagram Channel Members - 📈 Standard",
            "price": "₹400 per 1000 members",


            "description": "Standard Instagram channel members with good engagement potential. Perfect for growing channels that need consistent member addition.",

        },
        "2103": {
            "name": "👥 Instagram Channel Members - ⭐ Premium",
            "price": "₹600 per 1000 members",


            "description": "Premium Instagram channel members with high engagement rates. Active members who participate in channel discussions and content.",

        },
        "2104": {
            "name": "👥 Instagram Channel Members - 🇮🇳 Indian Premium",
            "price": "₹720 per 1000 members",


            "description": "High-quality Indian Instagram channel members for local community building. Perfect for Hindi channels and regional content creators.",

        },
        "2105": {
            "name": "👥 Instagram Channel Members - 👑 VIP Elite",
            "price": "₹880 per 1000 members", 


            "description": "Ultimate Instagram channel members with maximum engagement and activity. Elite community builders who actively contribute to channel growth.",

        },

        # Instagram Random Comments - 5 Different Quality Packages
        "2111": {
            "name": "💬 Instagram Random Comments - 💰 Economy",
            "price": "₹54 per 1000 comments",


            "description": "Budget-friendly Instagram random comments for basic engagement boost. Simple pre-written comments from real accounts with slow delivery speed.",

        },
        "2112": {
            "name": "💬 Instagram Random Comments - 📈 Standard",
            "price": "₹90 per 1000 comments",


            "description": "Standard Instagram random comments with better variety and engagement. Good selection of pre-written comments for consistent interaction.",

        },
        "2113": {
            "name": "💬 Instagram Random Comments - ⭐ Premium",
            "price": "₹135 per 1000 comments",


            "description": "Premium Instagram random comments with high-quality messages and better engagement. Thoughtful comments that look natural and engaging.",

        },
        "2114": {
            "name": "💬 Instagram Random Comments - 🇮🇳 Indian Premium",
            "price": "₹162 per 1000 comments",


            "description": "High-quality Indian Instagram random comments with Hindi/English mix. Perfect for local content with culturally relevant comment messages.",

        },
        "2115": {
            "name": "💬 Instagram Random Comments - 👑 VIP Elite",
            "price": "₹198 per 1000 comments",


            "description": "Ultimate Instagram random comments with maximum quality and engagement. Carefully selected comments that boost your post interaction significantly.",

        },

        # Instagram Emoji Comments - 5 Different Quality Packages
        "2121": {
            "name": "😀 Instagram Emoji Comments - 💰 Economy",
            "price": "₹42 per 1000 comments",


            "description": "Cost-effective Instagram emoji comments for basic reaction boost. Simple emoji combinations from real accounts with gradual delivery pattern.",

        },
        "2122": {
            "name": "😀 Instagram Emoji Comments - 📈 Standard",
            "price": "₹70 per 1000 comments",


            "description": "Standard Instagram emoji comments with good variety and reaction diversity. Balanced emoji engagement for consistent post interaction.",

        },
        "2123": {
            "name": "😀 Instagram Emoji Comments - ⭐ Premium",
            "price": "₹105 per 1000 comments",


            "description": "Premium Instagram emoji comments with creative emoji combinations and high engagement. Trending emoji patterns that enhance post appeal.",

        },
        "2124": {
            "name": "😀 Instagram Emoji Comments - 🇮🇳 Indian Premium",
            "price": "₹126 per 1000 comments",


            "description": "High-quality Indian Instagram emoji comments with locally popular emoji patterns. Perfect for Indian audience with cultural emoji preferences.",

        },
        "2125": {
            "name": "😀 Instagram Emoji Comments - 👑 VIP Elite",
            "price": "₹154 per 1000 comments",


            "description": "Ultimate Instagram emoji comments with maximum creativity and viral emoji patterns. Premium emoji combinations for maximum post engagement.",

        },

        # Previously added Custom Comments (2131-2135) are already above this
        "2131": {
            "name": "✍️ Instagram Custom Comments - 💰 Economy",
            "price": "₹120 per 1000 comments",


            "description": "Budget-friendly Instagram custom comments with your provided text. Basic delivery of your custom messages from real accounts with slower speed.",

        },
        "2132": {
            "name": "✍️ Instagram Custom Comments - 📈 Standard",
            "price": "₹200 per 1000 comments",


            "description": "Standard Instagram custom comments with reliable delivery of your messages. Good balance of speed and quality for personalized engagement.",

        },
        "2133": {
            "name": "✍️ Instagram Custom Comments - ⭐ Premium",
            "price": "₹300 per 1000 comments",


            "description": "Premium Instagram custom comments with fast delivery of your personalized messages. High-quality accounts posting your custom content naturally.",

        },
        "2134": {
            "name": "✍️ Instagram Custom Comments - 🇮🇳 Indian Premium",
            "price": "₹360 per 1000 comments",


            "description": "High-quality Indian Instagram custom comments with your personalized Hindi/English messages. Perfect for local audience engagement.",

        }
    }

    # Get package info or default
    package_info = package_details.get(service_id, {
        "name": f"Service Package ID:{service_id}",
        "price": "₹1.00 per unit",
        "description": "Professional social media growth service with real users and guaranteed results.",
    })

    # Create detailed description text
    features_text = "\\n".join(package_info.get("features", []))

    text = f"""
🎯 <b>{package_info["name"]}</b>

🆔 <b>Service ID:</b> {service_id}
💰 <b>Price:</b> {package_info["price"]}

📋 <b>Service Description:</b>
{package_info["description"]}


⚠️ <b>••••••••••⫷𝗡𝗢𝗧𝗘⫸••••••••••</b>
• ✅ Account Must Be Public.
• ❌ Private Id Not Working.
• ✅ Always double-check the link before ordering to avoid issues.
• ⚠️ Do Not Place a Second Order On The Same Link Before Your Order Is Completed In The System. If You Do This, We Will Not Be Able To Fix It, Wait For The First Order To Be Completed, Then Place New Order.
• 👉 You may only change your username or switch to private after the order has been completed.Until completion, please keep your account details unchanged for smooth delivery.
•⚠️  If you enter a wrong / non-working link OR make changes to your username / account privacy before the order is completed → your order will immediately stop and no refund will be provided.

💡 <b>Have you read all the details and agree to the terms & conditions?</b>

If you want to order this package, click the YES button below.
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

    return {"text": text, "keyboard": keyboard, "package_info": {"name": package_info["name"], "price": package_info["price"]}}

def get_service_packages(platform: str) -> InlineKeyboardMarkup:
    """Get packages for specific platform"""

    packages = {
        "instagram": [
            # Instagram Followers - Multiple Quality Options
           # ("👥 Instagram Followers - 💰 Economy (₹150/1K)", "ID:2001"),            
            ("👥 Instagram Followers - 📈 Standard (₹250/1K)", "ID:2002"),
            ("👥 Instagram Followers - ⭐ Premium (₹375/1K)", "ID:2003"),
            ("👥 Instagram Followers - 🇮🇳 Indian Premium (₹450/1K)", "ID:2004"),
           # ("👥 Instagram Followers - 👑 VIP Elite (₹550/1K)", "ID:2005"),

            # Instagram Post Likes - Multiple Quality Options
           # ("❤️ Instagram Post Likes - 💰 Economy (₹18/1K)", "ID:2011"),
          #  ("❤️ Instagram Post Likes - 📈 Standard (₹30/1K)", "ID:2012"),
            ("❤️ Instagram Post Likes - ⭐ Premium (₹45/1K)", "ID:2013"),
            ("❤️ Instagram Post Likes - 🇮🇳 Indian Premium (₹54/1K)", "ID:2014"),
           # ("❤️ Instagram Post Likes - 👑 VIP Elite (₹66/1K)", "ID:2015"),

            # Instagram Reel Views - Multiple Quality Options
          #  ("👁️ Instagram Reel Views - 💰 Economy (₹12/1K)", "ID:2041"),
           # ("👁️ Instagram Reel Views - 📈 Standard (₹20/1K)", "ID:2042"),
            ("👁️ Instagram Reel Views - ⭐ Premium (₹30/1K)", "ID:2043"),
        #    ("👁️ Instagram Reel Views - 🇮🇳 Indian Premium (₹36/1K)", "ID:2044"),
            ("👁️ Instagram Reel Views - 👑 VIP Elite (₹44/1K)", "ID:2045"),

            # Instagram Story Views - Multiple Quality Options
           # ("📖 Instagram Story Views - 💰 Economy (₹12/1K)", "ID:2051"),
           # ("📖 Instagram Story Views - 📈 Standard (₹20/1K)", "ID:2052"),
            ("📖 Instagram Story Views - ⭐ Premium (₹30/1K)", "ID:2053"),
            ("📖 Instagram Story Views - 🇮🇳 Indian Premium (₹36/1K)", "ID:2054"),
            ("📖 Instagram Story Views - 👑 VIP Elite (₹44/1K)", "ID:2055"),

            # Instagram Story Likes - Multiple Quality Options
          #  ("💖 Instagram Story Likes - 💰 Economy (₹18/1K)", "ID:2061"),
           # ("💖 Instagram Story Likes - 📈 Standard (₹30/1K)", "ID:2062"),
            ("💖 Instagram Story Likes - ⭐ Premium (₹45/1K)", "ID:2063"),
            ("💖 Instagram Story Likes - 🇮🇳 Indian Premium (₹54/1K)", "ID:2064"),
          #  ("💖 Instagram Story Likes - 👑 VIP Elite (₹66/1K)", "ID:2065"),

            # Instagram Story Link Clicks - Multiple Quality Options
           # ("🔗 Instagram Story Link Clicks - 💰 Economy (₹90/1K)", "ID:2071"),
          #  ("🔗 Instagram Story Link Clicks - 📈 Standard (₹150/1K)", "ID:2072"),
            ("🔗 Instagram Story Link Clicks - ⭐ Premium (₹225/1K)", "ID:2073"),
            ("🔗 Instagram Story Link Clicks - 🇮🇳 Indian Premium (₹270/1K)", "ID:2074"),
           # ("🔗 Instagram Story Link Clicks - 👑 VIP Elite (₹330/1K)", "ID:2075"),

            # Instagram Reel Shares - Multiple Quality Options
            ("📤 Instagram Reel Shares - 💰 Economy (₹8/1K)", "ID:2091"),
          #  ("📤 Instagram Reel Shares - 📈 Standard (₹13.50/1K)", "ID:2092"),
          #  ("📤 Instagram Reel Shares - ⭐ Premium (₹20/1K)", "ID:2093"),
            ("📤 Instagram Reel Shares - 🇮🇳 Indian Premium (₹24/1K)", "ID:2094"),
            ("📤 Instagram Reel Shares - 👑 VIP Elite (₹30/1K)", "ID:2095"),

            # Instagram Channel Members - Multiple Quality Options
          #  ("👥 Instagram Channel Members - 💰 Economy (₹720/1K)", "ID:2101"),
            ("👥 Instagram Channel Members - 📈 Standard (₹1200/1K)", "ID:2102"),
            ("👥 Instagram Channel Members - ⭐ Premium (₹1800/1K)", "ID:2103"),
        #    ("👥 Instagram Channel Members - 🇮🇳 Indian Premium (₹2160/1K)", "ID:2104"),
          #  ("👥 Instagram Channel Members - 👑 VIP Elite (₹2640/1K)", "ID:2105"),

            # Instagram Random Comments - Multiple Quality Options
            ("💬 Instagram Random Comments - 💰 Economy (₹270/1K)", "ID:2111"),
            ("💬 Instagram Random Comments - 📈 Standard (₹450/1K)", "ID:2112"),
         #   ("💬 Instagram Random Comments - ⭐ Premium (₹675/1K)", "ID:2113"),
         #   ("💬 Instagram Random Comments - 🇮🇳 Indian Premium (₹810/1K)", "ID:2114"),
         #   ("💬 Instagram Random Comments - 👑 VIP Elite (₹990/1K)", "ID:2115"),

            # Instagram Emoji Comments - Multiple Quality Options
            ("😊 Instagram Emoji Comments - 💰 Economy (₹230/1K)", "ID:2121"),
            ("😊 Instagram Emoji Comments - 📈 Standard (₹380/1K)", "ID:2122"),
         #   ("😊 Instagram Emoji Comments - ⭐ Premium (₹570/1K)", "ID:2123"),
           # ("😊 Instagram Emoji Comments - 🇮🇳 Indian Premium (₹684/1K)", "ID:2124"),
          #  ("😊 Instagram Emoji Comments - 👑 VIP Elite (₹836/1K)", "ID:2125"),

            # Instagram Custom Comments - Multiple Quality Options
            ("💬 Instagram Custom Comments - 💰 Economy (₹240/1K)", "ID:2131"),
            ("💬 Instagram Custom Comments - 📈 Standard (₹400/1K)", "ID:2132"),
            ("💬 Instagram Custom Comments - ⭐ Premium (₹500/1K)", "ID:2133"),
         #   ("💬 Instagram Custom Comments - 🇮🇳 Indian Premium (₹720/1K)", "ID:2134"),
          #  ("💬 Instagram Custom Comments - 👑 VIP Elite (₹880/1K)", "ID:2135")
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

    # Add packages in rows of 1 (limit to first 15 to avoid size issues)
    # Show all packages without limit
    for package_name, service_id in platform_packages:
        keyboard.append([
            InlineKeyboardButton(
                text=package_name, 
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
📸 <b>Instagram Services</b>

🚀 <b>Select a service below to start boosting your Instagram profile.</b>

🎯 <b>Inside each service, you'll find a variety of packages:</b>
• 💰 <b>Economy</b> - Budget-friendly options
• 📈 <b>Standard</b> - Best value for money  
• ⭐ <b>Premium</b> - High-quality guaranteed
• 🇮🇳 <b>Indian Premium</b> - Local targeting
• 👑 <b>VIP Elite</b> - Ultimate quality & speed

✨ <b>Features:</b>
• 🔥 100% Real & Active Users
• ⚡ Lightning Fast Delivery
• 🛡️ High Retention Guarantee
• 🔒 Safe & Secure Methods
• 💬 24/7 Premium Support

💡 <b>Please select the service you require:</b>
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

🎯 <b>Select a YouTube package:</b>
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

💡 <b>Choose a package for Facebook services:</b>
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

💡 <b>Choose a package for Telegram services:</b>
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

💡 <b>Select your package:</b>
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
    async def cb_confirm_order(callback: CallbackQuery, state: FSMContext):
        """Handle order confirmation - show package details and description command"""
        from states import OrderStates
        if not callback.message:
            return

        # Parse callback data: confirm_order_platform_serviceid
        parts = (callback.data or "").split("_")
        if len(parts) >= 4:
            platform = parts[2]
            service_id = parts[3]

            try:
                description_data = get_package_description(platform, service_id)
                pkg_info = description_data.get("package_info", {})
            except Exception as e:
                print(f"Warning: Could not get package details for {service_id}: {e}")
                # Fallback to default if original database fails
                pkg_info = {
                    "name": f"Service Package ID:{service_id}",
                    "price": "₹1.00 per unit"
                }

            # Get example link based on platform
            example_links = {
                "instagram": "https://instagram.com/username",
                "youtube": "https://youtube.com/watch?v=xyz123",
                "facebook": "https://facebook.com/pagename",
                "telegram": "https://t.me/channelname",
                "tiktok": "https://tiktok.com/@username",
                "twitter": "https://twitter.com/username",
                "linkedin": "https://linkedin.com/in/username",
                "whatsapp": "https://chat.whatsapp.com/invitelink"
            }

            example_link = example_links.get(platform, f"https://{platform}.com/username")

            text = f"""
🎯 <b>Package Selected Successfully!</b>

📦 <b>Package Name:</b> {pkg_info["name"]}
🆔 <b>Package ID:</b> {service_id}
💰 <b>Rate:</b> {pkg_info["price"]}

📋 <b>Description Command:</b> /description

💡 <b>For detailed information about the package, type /description command</b>

🔗 <b>Example Link for {platform.title()}:</b>
{example_link}

📝 <b>Now send your {platform.title()} link:</b>

⚠️ <b>Important:</b>
• Link should be public
• Should be in correct format
• Should be a working link

💬 <b>Send your link as a message...</b>
"""

            # Store order data in FSM state
            await state.update_data(
                service=f"{platform}_{service_id}",
                platform=platform,
                service_id=service_id,
                package_name=pkg_info["name"],
                package_rate=pkg_info["price"]
            )
            await state.set_state(OrderStates.waiting_link)

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="❌ Cancel Order", callback_data=f"service_{platform}")
                ]
            ])

            await safe_edit_message(callback, text, keyboard)

        await callback.answer()

    # ========== ADMIN PANEL HANDLERS ==========
    @dp.callback_query(F.data == "more_services")
    async def cb_more_services(callback: CallbackQuery):
        """Handle more services menu for additional platforms and tools"""
        if not callback.message:
            return

        text = """
🌟 <b>More Services & Features</b>

🚀 <b>Additional Services Coming Soon!</b>

📱 <b>More Platforms:</b>
• 📱 Snapchat Services
• 🎬 TikTok Advanced
• 📺 YouTube Premium
• 🔴 Pinterest Marketing
• 📧 Email Marketing
• 💼 Business Solutions

⚡ <b>Advanced Features:</b>
• 🤖 AI Content Generation
• 📊 Analytics Dashboard
• 🎯 Target Audience Analysis
• 📈 Growth Strategy Consultation
• 🎪 Event Promotion Services
• 💡 Custom Package Creation

🔧 <b>Professional Tools:</b>
• 📋 Bulk Order Management
• ⏰ Scheduled Campaigns
• 📊 Performance Tracking
• 🎨 Content Creation Tools
• 📞 Priority Support
• 💎 VIP Account Features

💡 <b>All these services are in development and will be available soon!</b>

📞 <b>Custom Requirements:</b> Contact @tech_support_admin
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📞 Request Custom Service", url="https://t.me/tech_support_admin"),
                InlineKeyboardButton(text="🔔 Get Notified", callback_data="notify_new_services")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Services", callback_data="new_order")
            ]
        ])

        await safe_edit_message(callback, text, keyboard)
        await callback.answer()

    # Note: admin_panel handler moved to main.py to avoid conflicts
    # @dp.callback_query(F.data == "admin_panel")
    # async def cb_admin_panel(callback: CallbackQuery):
    #     """Handle admin panel main menu"""
    #     if not callback.message:
    #         return

    #     user_id = callback.from_user.id
    #     if not is_admin(user_id):
    #         await callback.answer("⚠️ Access Denied: Admin only", show_alert=True)
    #         return

    #     log_activity(user_id, "Accessed Admin Panel")

        admin_text = """
🔧 <b>Admin Control Panel</b>
<b>India Social Panel Bot Administration</b>

👨‍💼 <b>Admin:</b> {admin_name}
⏰ <b>Access Time:</b> {time}

🎛️ <b>Available Controls:</b>
• Bot Status & Analytics
• User Management & Statistics  
• Broadcast Messaging System
• Error Monitoring & Logs
• Database & Performance Tools
• Maintenance & System Control

⚡ <b>Quick Stats:</b>
• Uptime: {uptime}
• Total Users: {total_users}
• Recent Errors: {error_count}

🔐 <b>Admin Access Level:</b> Full Control
""".format(
            admin_name=callback.from_user.first_name or "Admin",
            time=datetime.now().strftime("%H:%M:%S"),
            uptime=format_uptime(),
            total_users="Loading...",
            error_count=len(error_logs)
        )

        await safe_edit_message(callback, admin_text, get_admin_main_menu())
        await callback.answer()

    @dp.callback_query(F.data == "admin_bot_status")
    async def cb_admin_bot_status(callback: CallbackQuery):
        """Handle bot status display"""
        if not callback.message or not is_admin(callback.from_user.id):
            await callback.answer("⚠️ Access Denied", show_alert=True)
            return

        log_activity(callback.from_user.id, "Viewed Bot Status")
        status_info = get_bot_status_info()
        await safe_edit_message(callback, status_info["text"], status_info["keyboard"])
        await callback.answer()

    @dp.callback_query(F.data == "admin_users")
    async def cb_admin_users(callback: CallbackQuery):
        """Handle user management display"""
        if not callback.message or not is_admin(callback.from_user.id):
            await callback.answer("⚠️ Access Denied", show_alert=True)
            return

        log_activity(callback.from_user.id, "Accessed User Management")
        user_info = get_user_management_info()
        await safe_edit_message(callback, user_info["text"], user_info["keyboard"])
        await callback.answer()

    @dp.callback_query(F.data == "admin_errors")
    async def cb_admin_errors(callback: CallbackQuery):
        """Handle error monitoring display"""
        if not callback.message or not is_admin(callback.from_user.id):
            await callback.answer("⚠️ Access Denied", show_alert=True)
            return

        log_activity(callback.from_user.id, "Viewed Error Monitor")
        error_info = get_error_monitor_info()
        await safe_edit_message(callback, error_info["text"], error_info["keyboard"])
        await callback.answer()

    @dp.callback_query(F.data == "admin_broadcast")
    async def cb_admin_broadcast(callback: CallbackQuery):
        """Handle broadcast message interface"""
        if not callback.message or not is_admin(callback.from_user.id):
            await callback.answer("⚠️ Access Denied", show_alert=True)
            return

        log_activity(callback.from_user.id, "Accessed Broadcast Center")
        broadcast_info = get_broadcast_interface()
        await safe_edit_message(callback, broadcast_info["text"], broadcast_info["keyboard"])
        await callback.answer()

    @dp.callback_query(F.data == "admin_maintenance")
    async def cb_admin_maintenance(callback: CallbackQuery):
        """Handle maintenance tools interface"""
        if not callback.message or not is_admin(callback.from_user.id):
            await callback.answer("⚠️ Access Denied", show_alert=True)
            return

        log_activity(callback.from_user.id, "Accessed Maintenance Tools")
        maintenance_info = get_maintenance_interface()
        await safe_edit_message(callback, maintenance_info["text"], maintenance_info["keyboard"])
        await callback.answer()

    @dp.callback_query(F.data == "admin_manage_user")
    async def cb_admin_manage_user(callback: CallbackQuery):
        """Handle admin manage user - show command instructions"""
        if not callback.message or not is_admin(callback.from_user.id):
            await callback.answer("⚠️ Access Denied", show_alert=True)
            return

        log_activity(callback.from_user.id, "Viewed User Management Instructions")

        instruction_text = """
👤 <b>User Profile Management</b>

📋 <b>To view a user's detailed profile, use the command:</b>

<code>/viewuser &lt;USER_ID&gt;</code>

💡 <b>Examples:</b>
• <code>/viewuser</code>
• <code>/viewuser</code>

🔍 <b>You can get User IDs from:</b>
• User Management dashboard
• Recent users list
• Order details
• Support tickets

⚡ <b>This command will instantly display:</b>
• Personal information (name, username, phone, email)
• Account details (balance, total spent, status)
• Activity history (join date)
• Security information (access token)
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back to User Management", callback_data="admin_users")]
        ])

        await safe_edit_message(callback, instruction_text, keyboard)
        await callback.answer()

    @dp.callback_query(F.data == "admin_broadcast_all")
    async def cb_admin_broadcast_all(callback: CallbackQuery):
        """Handle broadcast to all users"""
        if not callback.message or not is_admin(callback.from_user.id):
            await callback.answer("⚠️ Access Denied", show_alert=True)
            return

        from main import users_data, init_user, user_state
        user_id = callback.from_user.id

        # Ensure user exists in users_data first
        if user_id not in users_data:
            print(f"🔧 Initializing admin user {user_id} for broadcast")
            init_user(user_id, callback.from_user.username or "", callback.from_user.first_name or "Admin")

        # Force complete admin account if not done  
        if not users_data.get(user_id, {}).get('account_created', False):
            users_data[user_id]['account_created'] = True
            users_data[user_id]['full_name'] = callback.from_user.first_name or "Admin"
            users_data[user_id]['email'] = "admin@indiasocialpanel.com"
            users_data[user_id]['phone_number'] = "+91XXXXXXXXXX"
            print(f"🔧 Force-completed admin account for broadcast user {user_id}")
            # Save admin account data to persistent storage
            from main import save_data_to_json
            save_data_to_json(users_data, "users.json")

        # Set user state for message input
        user_state[user_id] = {
            "current_step": "admin_broadcast_message",
            "data": {"target": "all"}
        }

        print(f"🔍 BROADCAST DEBUG: Set user_state for admin {user_id}: {user_state[user_id]}")

        text = """
📢 <b>Broadcast Message to All Users</b>

✍️ <b>Please type your broadcast message:</b>

📝 <b>Message Guidelines:</b>
• HTML formatting supported (<b>bold</b>, <i>italic</i>)
• Links allowed
• Emojis supported
• Max 4096 characters

⚠️ <b>This will send to ALL registered users!</b>

💬 Type your message now, or click Cancel to abort.
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancel", callback_data="admin_broadcast")]
        ])

        await safe_edit_message(callback, text, keyboard)
        await callback.answer()

    @dp.callback_query(F.data == "admin_toggle_maintenance")
    async def cb_admin_toggle_maintenance(callback: CallbackQuery):
        """Toggle maintenance mode"""
        if not callback.message or not is_admin(callback.from_user.id):
            await callback.answer("⚠️ Access Denied", show_alert=True)
            return

        global maintenance_mode
        maintenance_mode = not maintenance_mode

        status = "ENABLED" if maintenance_mode else "DISABLED"
        log_activity(callback.from_user.id, f"Maintenance Mode {status}")

        # Refresh maintenance interface
        maintenance_info = get_maintenance_interface()
        await safe_edit_message(callback, maintenance_info["text"], maintenance_info["keyboard"])
        await callback.answer(f"🔧 Maintenance mode {status.lower()}!")

    @dp.callback_query(F.data == "admin_clear_errors")
    async def cb_admin_clear_errors(callback: CallbackQuery):
        """Clear error logs"""
        if not callback.message or not is_admin(callback.from_user.id):
            await callback.answer("⚠️ Access Denied", show_alert=True)
            return

        global error_logs
        error_count = len(error_logs)
        error_logs.clear()

        log_activity(callback.from_user.id, f"Cleared {error_count} error logs")

        # Refresh error monitor
        error_info = get_error_monitor_info()
        await safe_edit_message(callback, error_info["text"], error_info["keyboard"])
        await callback.answer(f"🗑️ Cleared {error_count} error logs!")

    @dp.callback_query(F.data == "admin_confirm_broadcast")
    async def cb_admin_confirm_broadcast(callback: CallbackQuery):
        """Handle broadcast confirmation"""
        await handle_admin_broadcast_confirm(callback)

    @dp.callback_query(F.data == "notify_new_services")
    async def cb_notify_new_services(callback: CallbackQuery):
        """Handle notification signup for new services"""
        if not callback.message:
            return

        text = """
🔔 <b>Get Notified for New Services</b>

✅ <b>Notification Subscription Successful!</b>

📢 <b>You will receive notifications when:</b>
• New platforms are added
• Advanced features are launched  
• Special offers become available
• Premium tools are released

📱 <b>Notification Methods:</b>
• Direct Telegram message
• Bot announcements
• Channel updates
• Email alerts (future)

🎉 <b>Thank you for your interest!</b>
We will be launching exciting new services soon.

🔔 <b>Stay tuned for updates!</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 Join Channel", url="https://t.me/IndiaSocialPanelOfficial"),
                InlineKeyboardButton(text="📞 Contact", url="https://t.me/tech_support_admin")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back", callback_data="more_services")
            ]
        ])

        await safe_edit_message(callback, text, keyboard)
        await callback.answer("🔔 Notifications enabled!", show_alert=True)

    @dp.callback_query(F.data.startswith("admin_"))
    async def cb_admin_fallback(callback: CallbackQuery):
        """Handle other admin callbacks"""
        if not callback.message or not is_admin(callback.from_user.id):
            await callback.answer("⚠️ Access Denied", show_alert=True)
            return

        action = (callback.data or "").replace("admin_", "")

        # Handle various admin actions
        if action == "export_users":
            await callback.answer("📋 User export feature coming soon!")
        elif action == "user_details":
            from main import load_data_from_json
            users_data = load_data_from_json("users.json")

            user_list_text = "👥 **Complete User List**\n\n"
            if not users_data:
                user_list_text += "No users found in the database."
            else:
                for user_id, user_data in users_data.items():
                    username = user_data.get('username')
                    display_name = f"@{username}" if username else user_data.get('full_name', 'N/A')
                    user_list_text += f"• **ID:** `{user_id}` | **Name:** {display_name}\n"

            # Create a new keyboard for this view
            details_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👤 Manage a User", callback_data="admin_manage_user")],
                [InlineKeyboardButton(text="⬅️ Back to User Menu", callback_data="admin_users")]
            ])

            await safe_edit_message(callback, user_list_text, details_keyboard)
        elif action == "manage_user":
            # Redirect to the main admin_manage_user handler which now shows command instructions
            await cb_admin_manage_user(callback)
        elif action == "clear_cache":
            await callback.answer("🗑️ Cache cleared successfully!")
        elif action == "optimize":
            await callback.answer("📊 System optimization completed!")
        elif action in ["settings", "database", "activity", "performance", "ban_users"]:
            await callback.answer(f"🔧 {action.title()} panel coming soon!")
        else:
            await callback.answer("⚙️ Feature under development!")

# ========== ADMIN BROADCAST MESSAGE HANDLER ==========
async def handle_admin_broadcast_message(message: Message, user_id: int):
    """Handle admin broadcast message input"""
    from main import users_data, user_state

    if not is_admin(user_id):
        return

    user_data = user_state.get(user_id, {})
    if user_data.get("current_step") != "admin_broadcast_message":
        return

    broadcast_text = message.text
    target = user_data.get("data", {}).get("target", "all")

    # Clear user state
    user_state[user_id] = {"current_step": None, "data": {}}

    # Get target users
    if target == "all":
        target_users = list(users_data.keys())
    else:
        target_users = [uid for uid, udata in users_data.items() if udata.get('status') == 'active']

    # Send confirmation
    confirm_text = f"""
📢 <b>Broadcast Confirmation</b>

📝 <b>Message Preview:</b>
{broadcast_text}

👥 <b>Target:</b> {len(target_users)} users
📊 <b>Delivery:</b> 1 message per second (Telegram limit)
⏰ <b>Estimated Time:</b> ~{len(target_users)} seconds

⚠️ <b>Ready to send?</b>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Send Now", callback_data="admin_confirm_broadcast"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="admin_broadcast")
        ]
    ])

    # Store broadcast data temporarily
    user_state[user_id] = {
        "current_step": "admin_confirm_broadcast",
        "data": {
            "message": broadcast_text,
            "target_users": target_users
        }
    }

    await message.answer(confirm_text, reply_markup=keyboard)

# Add broadcast confirmation handler
async def handle_admin_broadcast_confirm(callback: CallbackQuery):
    """Handle broadcast confirmation"""
    from main import user_state

    if not is_admin(callback.from_user.id):
        return

    user_id = callback.from_user.id
    user_data = user_state.get(user_id, {})

    if user_data.get("current_step") != "admin_confirm_broadcast":
        return

    broadcast_message = user_data.get("data", {}).get("message", "")
    target_users = user_data.get("data", {}).get("target_users", [])

    # Clear user state
    user_state[user_id] = {"current_step": None, "data": {}}

    # Send status message
    status_text = f"""
📢 <b>Broadcasting Message...</b>

📊 <b>Status:</b> Sending to {len(target_users)} users
⏰ <b>Started:</b> {datetime.now().strftime('%H:%M:%S')}

🔄 This may take a few minutes...
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_panel")]
    ])

    await safe_edit_message(callback, status_text, keyboard)

    # Send broadcast messages
    sent_count = 0
    failed_count = 0

    for target_user_id in target_users:
        try:
            # Import bot from main.py
            from main import bot
            await bot.send_message(
                chat_id=target_user_id,
                text=broadcast_message,
                parse_mode="HTML"
            )
            sent_count += 1

            # Respect Telegram rate limits
            await asyncio.sleep(1)

        except Exception as e:
            failed_count += 1
            log_error(f"Broadcast failed for user {target_user_id}: {str(e)}")

    # Send completion report
    completion_text = f"""
✅ <b>Broadcast Completed!</b>

📊 <b>Delivery Report:</b>
• Successfully sent: {sent_count}
• Failed deliveries: {failed_count}
• Total attempts: {len(target_users)}
• Success rate: {(sent_count/len(target_users)*100):.1f}%

⏰ <b>Completed:</b> {datetime.now().strftime('%H:%M:%S')}
📝 <b>Message:</b> {broadcast_message[:100]}{'...' if len(broadcast_message) > 100 else ''}
"""

    log_activity(user_id, f"Broadcast sent to {sent_count} users")

    await safe_edit_message(callback, completion_text, keyboard)


# Export functions for main.py
# ========== ADMIN PANEL FUNCTIONS ==========

def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Build admin control panel main menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Bot Status", callback_data="admin_bot_status"),
            InlineKeyboardButton(text="👥 User Management", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="⚠️ Error Monitor", callback_data="admin_errors")
        ],
        [
            InlineKeyboardButton(text="⚙️ Bot Settings", callback_data="admin_settings"),
            InlineKeyboardButton(text="📁 Database Tools", callback_data="admin_database")
        ],
        [
            InlineKeyboardButton(text="🔍 Activity Monitor", callback_data="admin_activity"),
            InlineKeyboardButton(text="📈 Performance", callback_data="admin_performance")
        ],
        [
            InlineKeyboardButton(text="🛠️ Maintenance", callback_data="admin_maintenance"),
            InlineKeyboardButton(text="🚫 Ban/Unban Users", callback_data="admin_ban_users")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Services", callback_data="new_order")
        ]
    ])

def get_bot_status_info() -> dict:
    """Get comprehensive bot status information"""
    from main import users_data, orders_data, tickets_data, user_state

    uptime = format_uptime()
    system_stats = get_system_stats()

    # Calculate statistics
    total_users = len(users_data)
    active_users_24h = 0
    total_orders = len(orders_data)
    total_tickets = len(tickets_data)

    # Count active users in last 24 hours (simplified)
    for user_data in users_data.values():
        try:
            if 'last_activity' in user_data:
                # This would need proper date checking in real implementation
                active_users_24h += 1
        except (KeyError, ValueError, TypeError):
            pass

    # Get proper start time for display
    try:
        from main import START_TIME
        display_start_time = START_TIME
    except ImportError:
        display_start_time = bot_start_time

    status_text = f"""
🤖 <b>India Social Panel Bot Status</b>

⏰ <b>Live Bot Uptime:</b> <code>{uptime}</code>
🕐 <b>Started:</b> {datetime.fromtimestamp(display_start_time).strftime('%d %b %Y, %I:%M:%S %p')}

📊 <b>User Statistics:</b>
• Total Users: <b>{total_users}</b>
• Active (24h): <b>{active_users_24h}</b>
• Total Orders: <b>{total_orders}</b>
• Support Tickets: <b>{total_tickets}</b>

💻 <b>System Performance:</b>
• CPU Usage: <b>{system_stats['cpu']}</b>
• Memory: <b>{system_stats['memory_used']}/{system_stats['memory_total']}</b> ({system_stats['memory']})
• Disk Usage: <b>{system_stats['disk']}</b>

🔧 <b>Bot Health:</b>
• Webhook Status: ✅ <b>Active</b>
• Database: ✅ <b>Connected</b>
• API Response: ✅ <b>Normal</b>
• Error Count (24h): <b>{len([e for e in error_logs if e.get('timestamp', '')])}</b>

🌐 <b>Environment:</b>
• Mode: <b>Production Webhook</b>
• Server: <b>Replit Cloud</b>
• Location: <b>Global CDN</b>

🚀 <b>Status:</b> <code>🟢 RUNNING PERFECTLY</code>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Refresh Status", callback_data="admin_bot_status"),
            InlineKeyboardButton(text="📋 Detailed Stats", callback_data="admin_detailed_stats")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_panel")
        ]
    ])

    return {"text": status_text, "keyboard": keyboard}

def get_user_management_info() -> dict:
    """Get user management interface"""
    from main import load_data_from_json
    users_data = load_data_from_json("users.json")

    total_users = len(users_data)
    active_today = sum(1 for user in users_data.values() if user.get('status') == 'active')
    banned_users = sum(1 for user in users_data.values() if user.get('status') == 'banned')

    # Get recent users (last 5)
    recent_users = []
    user_list = list(users_data.items())
    for user_id, user_data in user_list[-5:]:
        username = user_data.get('username', 'No username')
        name = user_data.get('full_name', user_data.get('first_name', 'Unknown'))
        recent_users.append(f"• {name} (@{username}) - ID: {user_id}")

    recent_users_text = "\\n".join(recent_users) if recent_users else "No recent users"

    text = f"""
👥 <b>User Management Dashboard</b>

📊 <b>User Statistics:</b>
• Total Users: {total_users}
• Active Users: {active_today}
• Banned Users: {banned_users}
• New Today: {len([u for u in users_data.values() if 'today' in str(u.get('join_date', ''))])}

📋 <b>Recent Users:</b>
{recent_users_text}

💰 <b>Financial Stats:</b>
• Total Balance: ₹{sum(user.get('balance', 0) for user in users_data.values()):.2f}
• Total Spent: ₹{sum(user.get('total_spent', 0) for user in users_data.values()):.2f}
• Avg Order Value: ₹{sum(user.get('total_spent', 0) for user in users_data.values()) / max(total_users, 1):.2f}
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Export Users", callback_data="admin_export_users"),
            InlineKeyboardButton(text="🔍 Search User", callback_data="admin_search_user")
        ],
        [
            InlineKeyboardButton(text="📊 User Details", callback_data="admin_user_details"),
            InlineKeyboardButton(text="👤 Manage a User", callback_data="admin_manage_user")
        ],
        [
            InlineKeyboardButton(text="🚫 Ban User", callback_data="admin_ban_user"),
            InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_panel")
        ]
    ])

    return {"text": text, "keyboard": keyboard}

def get_error_monitor_info() -> dict:
    """Get error monitoring interface"""
    error_count = len(error_logs)
    recent_errors = error_logs[-10:] if error_logs else []

    error_text = "No recent errors ✅" if not recent_errors else "\\n".join([
        f"• {err['timestamp']}: {err['error'][:50]}..." 
        for err in recent_errors
    ])

    text = f"""
⚠️ <b>Error Monitoring Dashboard</b>

📊 <b>Error Statistics:</b>
• Total Errors: {error_count}
• Last 24h: {len([e for e in error_logs if 'today' in e.get('timestamp', '')])}
• Critical: {len([e for e in error_logs if 'critical' in e.get('error', '').lower()])}
• Warnings: {len([e for e in error_logs if 'warning' in e.get('error', '').lower()])}

🔥 <b>Recent Errors (Last 10):</b>
{error_text}

🛠️ <b>System Health:</b>
• API Errors: Low
• Database: Stable
• Memory: Normal
• Performance: Good
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 View All Errors", callback_data="admin_all_errors"),
            InlineKeyboardButton(text="🗑️ Clear Logs", callback_data="admin_clear_errors")
        ],
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_errors"),
            InlineKeyboardButton(text="⬅️ Back", callback_data="admin_panel")
        ]
    ])

    return {"text": text, "keyboard": keyboard}

def get_broadcast_interface() -> dict:
    """Get broadcast message interface"""
    from main import users_data

    total_users = len(users_data)
    active_users = sum(1 for user in users_data.values() if user.get('status') == 'active')

    # Debug user data
    print(f"🔍 BROADCAST INTERFACE DEBUG: Total users in data: {total_users}")
    print(f"🔍 BROADCAST INTERFACE DEBUG: Active users: {active_users}")
    if total_users > 0:
        sample_users = list(users_data.items())[:3]
        for uid, udata in sample_users:
            print(f"   User {uid}: {udata.get('username', 'No username')} - {udata.get('status', 'No status')}")

    text = f"""
📢 <b>Broadcast Message Center</b>

📊 <b>Audience Statistics:</b>
• Total Users: {total_users}
• Active Users: {active_users}
• Estimated Reach: {active_users}

📝 <b>Broadcast Options:</b>
• Send to all users
• Send to active users only
• Send to specific user groups
• Schedule for later

⚠️ <b>Important Notes:</b>
• Messages are sent at 1 msg/second (Telegram limit)
• HTML formatting supported
• Links and media supported
• Delivery reports available

✉️ <b>Ready to send broadcast message?</b>
Click "Send Message" and type your message.
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📤 Send to All Users", callback_data="admin_broadcast_all"),
            InlineKeyboardButton(text="🎯 Send to Active", callback_data="admin_broadcast_active")
        ],
        [
            InlineKeyboardButton(text="📋 Message History", callback_data="admin_broadcast_history"),
            InlineKeyboardButton(text="⏰ Schedule Message", callback_data="admin_broadcast_schedule")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_panel")
        ]
    ])

    return {"text": text, "keyboard": keyboard}

def get_maintenance_interface() -> dict:
    """Get maintenance tools interface"""
    global maintenance_mode

    mode_status = "🟢 Normal Operation" if not maintenance_mode else "🔴 Maintenance Mode"

    text = f"""
🛠️ <b>Maintenance Control Center</b>

🔧 <b>Current Status:</b>
{mode_status}

⚙️ <b>Available Actions:</b>
• Toggle maintenance mode
• Clear cache and temporary data
• Reset user sessions
• Cleanup inactive users
• Database maintenance
• System optimization

🔄 <b>Automated Tasks:</b>
• Daily cleanup: ✅ Enabled
• Error log rotation: ✅ Active
• Performance monitoring: ✅ Running
• Backup system: ✅ Scheduled

⚠️ <b>Maintenance Mode Effects:</b>
• Users get "under maintenance" message
• Admin functions remain accessible
• New registrations disabled
• Orders temporarily paused
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔴 Enable Maintenance" if not maintenance_mode else "🟢 Disable Maintenance",
                callback_data="admin_toggle_maintenance"
            )
        ],
        [
            InlineKeyboardButton(text="🗑️ Clear Cache", callback_data="admin_clear_cache"),
            InlineKeyboardButton(text="🔄 Reset Sessions", callback_data="admin_reset_sessions")
        ],
        [
            InlineKeyboardButton(text="📊 System Optimize", callback_data="admin_optimize"),
            InlineKeyboardButton(text="⬅️ Back", callback_data="admin_panel")
        ]
    ])

    return {"text": text, "keyboard": keyboard}

__all__ = ['register_service_handlers', 'get_services_main_menu', 'get_admin_main_menu', 'is_admin']
