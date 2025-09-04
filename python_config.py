
# -*- coding: utf-8 -*-
"""
India Social Panel - Dynamic Package Configuration System
Automatically generates unique descriptions for all package combinations
"""

# ========== DYNAMIC PRICING & CONFIGURATION ==========
def get_package_config(platform: str, service_id: str, quality: str):
    """
    Automatically generate package configuration based on platform, service, quality
    Returns: dict with all package details
    """

    # Base service information
    service_info = get_service_info(platform, service_id)

    # Quality multipliers and features
    quality_config = get_quality_config(quality)

    # Calculate dynamic pricing
    base_rate = service_info['base_rate']
    final_rate = base_rate * quality_config['rate_multiplier']

    # Generate configuration
    config = {
        'rate': final_rate,
        'min_quantity': quality_config['min_quantity'],
        'max_quantity': service_info['max_quantity'],
        'delivery_time': quality_config['delivery_time'],
        'speed': quality_config['speed'],
        'guarantee': quality_config['guarantee'],
        'drop_rate': quality_config['drop_rate'],
        'cancel_allowed': quality_config['cancel_allowed'],
        'refill_period': quality_config['refill_period'],
        'features': service_info['features'] + quality_config['bonus_features'],
        'description': generate_dynamic_description(platform, service_info, quality_config)
    }

    return config

def get_service_info(platform: str, service_id: str):
    """Get base service information"""

    # Service database - easily expandable
    services_db = {
        'instagram': {
            '1001': {  # Instagram Followers
                'name': 'Instagram Followers',
                'base_rate': 0.40,
                'max_quantity': 100000,
                'features': ['Real accounts', 'High retention', 'Safe delivery'],
                'category': 'followers',
                'platform_features': ['Profile growth', 'Credibility boost', 'Organic reach']
            },
            '1002': {  # Instagram Likes
                'name': 'Instagram Likes',
                'base_rate': 0.25,
                'max_quantity': 50000,
                'features': ['Instant delivery', 'Real engagement', 'Safe process'],
                'category': 'engagement',
                'platform_features': ['Post visibility', 'Algorithm boost', 'Social proof']
            },
            '1003': {  # Instagram Views
                'name': 'Instagram Views',
                'base_rate': 0.08,
                'max_quantity': 1000000,
                'features': ['High retention', 'Real views', 'Geographic targeting'],
                'category': 'views',
                'platform_features': ['Video promotion', 'Viral potential', 'Watch time']
            },
            '1004': {  # Instagram Story Views
                'name': 'Instagram Story Views',
                'base_rate': 0.12,
                'max_quantity': 500000,
                'features': ['Real story views', 'Fast delivery', 'Safe process'],
                'category': 'views',
                'platform_features': ['Story visibility', 'Engagement boost', 'Social proof']
            },
            '1005': {  # Instagram Story Likes
                'name': 'Instagram Story Likes',
                'base_rate': 0.35,
                'max_quantity': 25000,
                'features': ['Story engagement', 'Real users', 'High retention'],
                'category': 'engagement',
                'platform_features': ['Story popularity', 'User interaction', 'Visibility boost']
            },
            '1006': {  # Instagram Comments
                'name': 'Instagram Comments',
                'base_rate': 0.80,
                'max_quantity': 10000,
                'features': ['Real comments', 'Custom comments', 'High quality'],
                'category': 'engagement',
                'platform_features': ['Post engagement', 'Community building', 'Algorithm boost']
            },
            '1007': {  # Instagram Shares
                'name': 'Instagram Shares',
                'base_rate': 0.60,
                'max_quantity': 15000,
                'features': ['Real shares', 'Story shares', 'DM shares'],
                'category': 'engagement',
                'platform_features': ['Content spread', 'Viral potential', 'Reach expansion']
            },
            '1008': {  # Instagram Channel Members
                'name': 'Instagram Channel Members',
                'base_rate': 1.20,
                'max_quantity': 50000,
                'features': ['Real subscribers', 'High retention', 'Active users'],
                'category': 'followers',
                'platform_features': ['Channel growth', 'Community building', 'Authority boost']
            },
            '1009': {  # Instagram Saves
                'name': 'Instagram Saves',
                'base_rate': 0.45,
                'max_quantity': 20000,
                'features': ['Real saves', 'High retention', 'Algorithm boost'],
                'category': 'engagement',
                'platform_features': ['Content value', 'Algorithm signal', 'User intent']
            },
            '1010': {  # Instagram Auto Likes
                'name': 'Instagram Auto Likes',
                'base_rate': 0.50,
                'max_quantity': 5000,
                'features': ['Auto delivery', 'Future posts', 'Consistent growth'],
                'category': 'automation',
                'platform_features': ['Automatic growth', 'Time saving', 'Consistent engagement']
            },
            '1011': {  # Instagram Story Poll Votes
                'name': 'Instagram Story Poll Votes',
                'base_rate': 0.30,
                'max_quantity': 10000,
                'features': ['Real votes', 'Custom distribution', 'Fast delivery'],
                'category': 'engagement',
                'platform_features': ['Poll engagement', 'Story interaction', 'User feedback']
            },
            '1012': {  # Instagram Reel Views
                'name': 'Instagram Reel Views',
                'base_rate': 0.06,
                'max_quantity': 2000000,
                'features': ['High retention', 'Real views', 'Geographic targeting'],
                'category': 'views',
                'platform_features': ['Reel visibility', 'Viral potential', 'Algorithm boost']
            }
        },
        'youtube': {
            '3001': {  # YouTube Subscribers
                'name': 'YouTube Subscribers',
                'base_rate': 1.80,
                'max_quantity': 50000,
                'features': ['Real channels', 'High retention', 'Safe delivery'],
                'category': 'subscribers',
                'platform_features': ['Channel growth', 'Monetization help', 'Authority building']
            },
            '3002': {  # YouTube Views
                'name': 'YouTube Views',
                'base_rate': 0.06,
                'max_quantity': 1000000,
                'features': ['Watch time included', 'Real viewers', 'Geo-targeted'],
                'category': 'views',
                'platform_features': ['Video ranking', 'Algorithm boost', 'Viral potential']
            },
            '3003': {  # YouTube Likes
                'name': 'YouTube Likes',
                'base_rate': 0.15,
                'max_quantity': 100000,
                'features': ['Real engagement', 'Fast delivery', 'High retention'],
                'category': 'engagement',
                'platform_features': ['Video popularity', 'Algorithm boost', 'Social proof']
            },
            '3004': {  # YouTube Monetization
                'name': 'YouTube Monetization Help',
                'base_rate': 2.50,
                'max_quantity': 10000,
                'features': ['Watch time boost', 'Subscriber growth', 'Ad-friendly'],
                'category': 'monetization',
                'platform_features': ['Revenue potential', 'Channel growth', 'Partnership ready']
            },
            '3005': {  # YouTube Comments
                'name': 'YouTube Comments',
                'base_rate': 0.65,
                'max_quantity': 5000,
                'features': ['Custom comments', 'Real users', 'Positive feedback'],
                'category': 'engagement',
                'platform_features': ['Community building', 'Engagement boost', 'Discussion starter']
            },
            '3006': {  # YouTube Dislikes
                'name': 'YouTube Dislikes',
                'base_rate': 0.20,
                'max_quantity': 50000,
                'features': ['Real users', 'Balanced feedback', 'Organic look'],
                'category': 'engagement',
                'platform_features': ['Natural appearance', 'Feedback balance', 'Credibility']
            },
            '3007': {  # YouTube Watch Time
                'name': 'YouTube Watch Time',
                'base_rate': 0.08,
                'max_quantity': 500000,
                'features': ['Real watch hours', 'Retention focused', 'Monetization help'],
                'category': 'watch_time',
                'platform_features': ['Monetization ready', 'Algorithm boost', 'Revenue increase']
            },
            '3008': {  # YouTube Channel Memberships
                'name': 'YouTube Channel Memberships',
                'base_rate': 3.20,
                'max_quantity': 25000,
                'features': ['Premium subscribers', 'High engagement', 'Long-term members'],
                'category': 'memberships',
                'platform_features': ['Revenue stream', 'Community building', 'Exclusive access']
            },
            '3009': {  # YouTube Premiere Views
                'name': 'YouTube Premiere Views',
                'base_rate': 0.12,
                'max_quantity': 200000,
                'features': ['Live attendance', 'Real-time engagement', 'Chat interaction'],
                'category': 'live_views',
                'platform_features': ['Premiere success', 'Live interaction', 'Buzz creation']
            },
            '3010': {  # YouTube Shorts Views
                'name': 'YouTube Shorts Views',
                'base_rate': 0.04,
                'max_quantity': 5000000,
                'features': ['Viral potential', 'High retention', 'Algorithm friendly'],
                'category': 'shorts',
                'platform_features': ['Shorts algorithm', 'Viral reach', 'Discovery boost']
            },
            '3011': {  # YouTube Live Stream Views
                'name': 'YouTube Live Stream Views',
                'base_rate': 0.18,
                'max_quantity': 100000,
                'features': ['Real-time viewers', 'Chat engagement', 'Live interaction'],
                'category': 'live_views',
                'platform_features': ['Live engagement', 'Real-time buzz', 'Stream success']
            },
            '3012': {  # YouTube Community Post Likes
                'name': 'YouTube Community Post Likes',
                'base_rate': 0.25,
                'max_quantity': 25000,
                'features': ['Community engagement', 'Real likes', 'Fast delivery'],
                'category': 'community',
                'platform_features': ['Community building', 'Subscriber engagement', 'Post visibility']
            }
        },
        'facebook': {
            '2001': {  # Facebook Page Likes
                'name': 'Facebook Page Likes',
                'base_rate': 0.35,
                'max_quantity': 75000,
                'features': ['Real profiles', 'Active users', 'High retention'],
                'category': 'likes',
                'platform_features': ['Page authority', 'Business credibility', 'Social proof']
            },
            '2002': {  # Facebook Post Likes
                'name': 'Facebook Post Likes',
                'base_rate': 0.28,
                'max_quantity': 50000,
                'features': ['Real likes', 'Fast delivery', 'High engagement'],
                'category': 'engagement',
                'platform_features': ['Post visibility', 'Algorithm boost', 'Social proof']
            },
            '2003': {  # Facebook Group Members
                'name': 'Facebook Group Members',
                'base_rate': 0.45,
                'max_quantity': 100000,
                'features': ['Real members', 'Active participation', 'High retention'],
                'category': 'members',
                'platform_features': ['Group growth', 'Community building', 'Discussion boost']
            },
            '2004': {  # Facebook Live Views
                'name': 'Facebook Live Views',
                'base_rate': 0.15,
                'max_quantity': 200000,
                'features': ['Real-time viewers', 'Live engagement', 'Chat interaction'],
                'category': 'live_views',
                'platform_features': ['Live popularity', 'Real-time buzz', 'Stream success']
            },
            '2005': {  # Facebook Video Views
                'name': 'Facebook Video Views',
                'base_rate': 0.08,
                'max_quantity': 1000000,
                'features': ['High retention', 'Real views', 'Watch time'],
                'category': 'views',
                'platform_features': ['Video promotion', 'Algorithm boost', 'Viral potential']
            },
            '2006': {  # Facebook Monetization
                'name': 'Facebook Monetization',
                'base_rate': 2.80,
                'max_quantity': 15000,
                'features': ['Revenue boost', 'Ad optimization', 'Monetization ready'],
                'category': 'monetization',
                'platform_features': ['Revenue potential', 'Ad performance', 'Creator fund']
            },
            '2007': {  # Facebook Comments
                'name': 'Facebook Comments',
                'base_rate': 0.75,
                'max_quantity': 10000,
                'features': ['Custom comments', 'Real engagement', 'Positive feedback'],
                'category': 'engagement',
                'platform_features': ['Post engagement', 'Community building', 'Discussion starter']
            },
            '2008': {  # Facebook Shares
                'name': 'Facebook Shares',
                'base_rate': 0.85,
                'max_quantity': 25000,
                'features': ['Real shares', 'Viral potential', 'Organic spread'],
                'category': 'engagement',
                'platform_features': ['Content spread', 'Viral boost', 'Reach expansion']
            },
            '2009': {  # Facebook Followers
                'name': 'Facebook Followers',
                'base_rate': 0.42,
                'max_quantity': 75000,
                'features': ['Real profiles', 'High retention', 'Active users'],
                'category': 'followers',
                'platform_features': ['Profile growth', 'Personal brand', 'Social influence']
            },
            '2010': {  # Facebook Page Rating
                'name': 'Facebook Page Rating',
                'base_rate': 1.25,
                'max_quantity': 500,
                'features': ['5-star ratings', 'Real reviews', 'Business credibility'],
                'category': 'ratings',
                'platform_features': ['Business trust', 'Customer confidence', 'Search ranking']
            },
            '2011': {  # Facebook Event Interested
                'name': 'Facebook Event Interested',
                'base_rate': 0.35,
                'max_quantity': 50000,
                'features': ['Real interest', 'Event promotion', 'High attendance'],
                'category': 'events',
                'platform_features': ['Event visibility', 'Attendance boost', 'Social proof']
            },
            '2012': {  # Facebook Reviews
                'name': 'Facebook Reviews',
                'base_rate': 2.50,
                'max_quantity': 1000,
                'features': ['Detailed reviews', 'Star ratings', 'Authentic feedback'],
                'category': 'reviews',
                'platform_features': ['Business reputation', 'Customer trust', 'Local SEO']
            }
        },
        'telegram': {
            '4001': {  # Telegram Channel Members
                'name': 'Telegram Channel Members',
                'base_rate': 0.50,
                'max_quantity': 100000,
                'features': ['Real members', 'High retention', 'Active users'],
                'category': 'members',
                'platform_features': ['Channel growth', 'Authority building', 'Community expansion']
            },
            '4002': {  # Telegram Post Views
                'name': 'Telegram Post Views',
                'base_rate': 0.05,
                'max_quantity': 1000000,
                'features': ['Real views', 'Fast delivery', 'High retention'],
                'category': 'views',
                'platform_features': ['Content visibility', 'Reach expansion', 'Engagement boost']
            },
            '4003': {  # Telegram Group Members
                'name': 'Telegram Group Members',
                'base_rate': 0.45,
                'max_quantity': 75000,
                'features': ['Real members', 'Active participation', 'High retention'],
                'category': 'members',
                'platform_features': ['Group growth', 'Community building', 'Discussion boost']
            },
            '4004': {  # Telegram Channel Boost
                'name': 'Telegram Channel Boost',
                'base_rate': 2.20,
                'max_quantity': 10000,
                'features': ['Premium boost', 'Channel features', 'Enhanced visibility'],
                'category': 'boost',
                'platform_features': ['Premium features', 'Channel ranking', 'Special perks']
            },
            '4005': {  # Telegram Comments
                'name': 'Telegram Comments',
                'base_rate': 0.65,
                'max_quantity': 15000,
                'features': ['Real comments', 'Custom messages', 'High engagement'],
                'category': 'engagement',
                'platform_features': ['Post interaction', 'Community building', 'Discussion starter']
            },
            '4006': {  # Telegram Shares
                'name': 'Telegram Shares',
                'base_rate': 0.55,
                'max_quantity': 25000,
                'features': ['Real shares', 'Forward messages', 'Viral spread'],
                'category': 'engagement',
                'platform_features': ['Content spread', 'Viral potential', 'Reach expansion']
            },
            '4007': {  # Telegram Reactions
                'name': 'Telegram Reactions',
                'base_rate': 0.25,
                'max_quantity': 50000,
                'features': ['Emoji reactions', 'Fast delivery', 'High engagement'],
                'category': 'engagement',
                'platform_features': ['Post popularity', 'User interaction', 'Engagement boost']
            },
            '4008': {  # Telegram Poll Votes
                'name': 'Telegram Poll Votes',
                'base_rate': 0.30,
                'max_quantity': 20000,
                'features': ['Real votes', 'Custom distribution', 'Poll participation'],
                'category': 'engagement',
                'platform_features': ['Poll engagement', 'User participation', 'Feedback collection']
            },
            '4009': {  # Telegram Story Views
                'name': 'Telegram Story Views',
                'base_rate': 0.12,
                'max_quantity': 100000,
                'features': ['Real story views', 'Fast delivery', 'High retention'],
                'category': 'views',
                'platform_features': ['Story visibility', 'User engagement', 'Content reach']
            },
            '4010': {  # Telegram Premium Members
                'name': 'Telegram Premium Members',
                'base_rate': 3.50,
                'max_quantity': 5000,
                'features': ['Premium accounts', 'High value users', 'Enhanced features'],
                'category': 'premium',
                'platform_features': ['Premium engagement', 'Quality members', 'Advanced features']
            }
        },
        'whatsapp': {
            '5001': {  # WhatsApp Group Members
                'name': 'WhatsApp Group Members',
                'base_rate': 0.60,
                'max_quantity': 50000,
                'features': ['Real members', 'Active users', 'Safe delivery'],
                'category': 'members',
                'platform_features': ['Group expansion', 'Community growth', 'Engagement boost']
            },
            '5002': {  # WhatsApp Status Views
                'name': 'WhatsApp Status Views',
                'base_rate': 0.15,
                'max_quantity': 100000,
                'features': ['Real views', 'Fast delivery', 'Safe process'],
                'category': 'views',
                'platform_features': ['Status visibility', 'Story reach', 'Engagement boost']
            },
            '5003': {  # WhatsApp Business Growth
                'name': 'WhatsApp Business Growth',
                'base_rate': 1.80,
                'max_quantity': 25000,
                'features': ['Business contacts', 'Customer growth', 'Lead generation'],
                'category': 'business',
                'platform_features': ['Business expansion', 'Customer base', 'Sales growth']
            }
        },
        'tiktok': {
            '6001': {  # TikTok Followers
                'name': 'TikTok Followers',
                'base_rate': 0.55,
                'max_quantity': 100000,
                'features': ['Real followers', 'High retention', 'Active users'],
                'category': 'followers',
                'platform_features': ['Profile growth', 'Credibility boost', 'Viral potential']
            },
            '6002': {  # TikTok Views
                'name': 'TikTok Views',
                'base_rate': 0.03,
                'max_quantity': 10000000,
                'features': ['High retention', 'Real views', 'Viral potential'],
                'category': 'views',
                'platform_features': ['Algorithm boost', 'Viral reach', 'For You page']
            },
            '6003': {  # TikTok Likes
                'name': 'TikTok Likes',
                'base_rate': 0.20,
                'max_quantity': 500000,
                'features': ['Real engagement', 'Fast delivery', 'High retention'],
                'category': 'engagement',
                'platform_features': ['Video popularity', 'Algorithm boost', 'Social proof']
            },
            '6004': {  # TikTok Comments
                'name': 'TikTok Comments',
                'base_rate': 0.85,
                'max_quantity': 25000,
                'features': ['Custom comments', 'Real users', 'Positive engagement'],
                'category': 'engagement',
                'platform_features': ['Community building', 'Engagement boost', 'Discussion starter']
            },
            '6005': {  # TikTok Shares
                'name': 'TikTok Shares',
                'base_rate': 0.65,
                'max_quantity': 100000,
                'features': ['Real shares', 'Viral spread', 'Organic growth'],
                'category': 'engagement',
                'platform_features': ['Viral potential', 'Content spread', 'Reach expansion']
            },
            '6006': {  # TikTok Live Views
                'name': 'TikTok Live Views',
                'base_rate': 0.25,
                'max_quantity': 50000,
                'features': ['Real-time viewers', 'Live engagement', 'Chat interaction'],
                'category': 'live_views',
                'platform_features': ['Live popularity', 'Real-time buzz', 'Stream success']
            }
        },
        'twitter': {
            '7001': {  # Twitter Followers
                'name': 'Twitter Followers',
                'base_rate': 0.70,
                'max_quantity': 50000,
                'features': ['Real followers', 'High retention', 'Active engagement'],
                'category': 'followers',
                'platform_features': ['Profile authority', 'Tweet reach', 'Influence building']
            },
            '7002': {  # Twitter Likes
                'name': 'Twitter Likes',
                'base_rate': 0.22,
                'max_quantity': 100000,
                'features': ['Real likes', 'Fast delivery', 'High engagement'],
                'category': 'engagement',
                'platform_features': ['Tweet popularity', 'Algorithm boost', 'Social proof']
            },
            '7003': {  # Twitter Retweets
                'name': 'Twitter Retweets',
                'base_rate': 0.45,
                'max_quantity': 50000,
                'features': ['Real retweets', 'Viral potential', 'Organic spread'],
                'category': 'engagement',
                'platform_features': ['Content spread', 'Viral boost', 'Reach expansion']
            },
            '7004': {  # Twitter Views
                'name': 'Twitter Views',
                'base_rate': 0.05,
                'max_quantity': 1000000,
                'features': ['Real views', 'High retention', 'Fast delivery'],
                'category': 'views',
                'platform_features': ['Tweet visibility', 'Reach expansion', 'Engagement boost']
            },
            '7005': {  # Twitter Comments/Replies
                'name': 'Twitter Comments',
                'base_rate': 0.75,
                'max_quantity': 10000,
                'features': ['Custom replies', 'Real users', 'Positive engagement'],
                'category': 'engagement',
                'platform_features': ['Tweet engagement', 'Community building', 'Discussion starter']
            },
            '7006': {  # Twitter Spaces Listeners
                'name': 'Twitter Spaces Listeners',
                'base_rate': 1.20,
                'max_quantity': 25000,
                'features': ['Real listeners', 'Live engagement', 'Audio interaction'],
                'category': 'live_audio',
                'platform_features': ['Space popularity', 'Live engagement', 'Audio reach']
            }
        },
        'linkedin': {
            '8001': {  # LinkedIn Followers
                'name': 'LinkedIn Followers',
                'base_rate': 1.50,
                'max_quantity': 25000,
                'features': ['Professional profiles', 'High retention', 'Active users'],
                'category': 'followers',
                'platform_features': ['Professional growth', 'Network expansion', 'Authority building']
            },
            '8002': {  # LinkedIn Post Likes
                'name': 'LinkedIn Post Likes',
                'base_rate': 0.85,
                'max_quantity': 25000,
                'features': ['Professional engagement', 'Real likes', 'Industry professionals'],
                'category': 'engagement',
                'platform_features': ['Post visibility', 'Professional credibility', 'Network reach']
            },
            '8003': {  # LinkedIn Company Followers
                'name': 'LinkedIn Company Followers',
                'base_rate': 2.20,
                'max_quantity': 15000,
                'features': ['Business profiles', 'Industry professionals', 'High retention'],
                'category': 'business',
                'platform_features': ['Company growth', 'Business authority', 'Industry presence']
            },
            '8004': {  # LinkedIn Post Views
                'name': 'LinkedIn Post Views',
                'base_rate': 0.12,
                'max_quantity': 100000,
                'features': ['Professional views', 'Industry reach', 'High retention'],
                'category': 'views',
                'platform_features': ['Content visibility', 'Professional reach', 'Industry exposure']
            },
            '8005': {  # LinkedIn Comments
                'name': 'LinkedIn Comments',
                'base_rate': 1.85,
                'max_quantity': 5000,
                'features': ['Professional comments', 'Industry insights', 'Meaningful engagement'],
                'category': 'engagement',
                'platform_features': ['Professional discussion', 'Industry networking', 'Thought leadership']
            },
            '8006': {  # LinkedIn Shares
                'name': 'LinkedIn Shares',
                'base_rate': 1.50,
                'max_quantity': 10000,
                'features': ['Professional shares', 'Network spread', 'Industry distribution'],
                'category': 'engagement',
                'platform_features': ['Professional reach', 'Network expansion', 'Industry influence']
            }
        }
    }

    return services_db.get(platform, {}).get(service_id, {
        'name': 'Unknown Service',
        'base_rate': 0.50,
        'max_quantity': 10000,
        'features': ['Standard delivery'],
        'category': 'general',
        'platform_features': ['Growth boost']
    })

def get_quality_config(quality: str):
    """Get quality-specific configuration"""

    quality_configs = {
        'premium': {
            'rate_multiplier': 3.0,
            'min_quantity': 100,
            'delivery_time': '0-15 minutes',
            'speed': '50K per day',
            'guarantee': '365 days',
            'drop_rate': 'Maximum 2%',
            'cancel_allowed': True,
            'refill_period': '365 days',
            'quality_name': 'Premium Quality',
            'quality_emoji': '💎',
            'bonus_features': [
                'Priority processing',
                'Dedicated support',
                'VIP delivery',
                'Maximum retention',
                'Premium accounts only'
            ]
        },
        'high': {
            'rate_multiplier': 2.2,
            'min_quantity': 100,
            'delivery_time': '0-30 minutes',
            'speed': '30K per day',
            'guarantee': '180 days',
            'drop_rate': 'Maximum 5%',
            'cancel_allowed': True,
            'refill_period': '180 days',
            'quality_name': 'High Quality',
            'quality_emoji': '🔥',
            'bonus_features': [
                'Fast processing',
                'Priority support',
                'High retention',
                'Active accounts'
            ]
        },
        'medium': {
            'rate_multiplier': 1.5,
            'min_quantity': 50,
            'delivery_time': '0-2 hours',
            'speed': '20K per day',
            'guarantee': '90 days',
            'drop_rate': 'Maximum 10%',
            'cancel_allowed': True,
            'refill_period': '90 days',
            'quality_name': 'Medium Quality',
            'quality_emoji': '⚡',
            'bonus_features': [
                'Standard processing',
                'Good retention',
                'Mixed accounts'
            ]
        },
        'standard': {
            'rate_multiplier': 1.0,
            'min_quantity': 50,
            'delivery_time': '1-6 hours',
            'speed': '10K per day',
            'guarantee': '30 days',
            'drop_rate': 'Maximum 15%',
            'cancel_allowed': False,
            'refill_period': '30 days',
            'quality_name': 'Standard Quality',
            'quality_emoji': '✅',
            'bonus_features': [
                'Basic processing',
                'Standard accounts'
            ]
        },
        'basic': {
            'rate_multiplier': 0.7,
            'min_quantity': 25,
            'delivery_time': '2-24 hours',
            'speed': '5K per day',
            'guarantee': '15 days',
            'drop_rate': 'Maximum 25%',
            'cancel_allowed': False,
            'refill_period': '15 days',
            'quality_name': 'Basic Quality',
            'quality_emoji': '💰',
            'bonus_features': [
                'Budget-friendly',
                'Basic accounts'
            ]
        }
    }

    return quality_configs.get(quality, quality_configs['standard'])

def generate_dynamic_description(platform: str, service_info: dict, quality_config: dict):
    """
    Automatically generate unique description for each combination
    This creates different descriptions automatically!
    """

    service_name = service_info['name']
    quality_name = quality_config['quality_name']
    quality_emoji = quality_config['quality_emoji']
    # default_quality = 'standard'  # Removed broken line

    # Platform-specific intro
    platform_intros = {
        'instagram': f"📷 <b>Instagram {service_name}</b> - Boost your Instagram presence!",
        'youtube': f"🎥 <b>YouTube {service_name}</b> - Grow your YouTube channel fast!",
        'facebook': f"📘 <b>Facebook {service_name}</b> - Increase your Facebook engagement!",
        'telegram': f"📞 <b>Telegram {service_name}</b> - Expand your Telegram reach!",
        'tiktok': f"🎵 <b>TikTok {service_name}</b> - Go viral on TikTok!",
        'twitter': f"🐦 <b>Twitter {service_name}</b> - Boost your Twitter influence!",
        'linkedin': f"💼 <b>LinkedIn {service_name}</b> - Professional growth guaranteed!"
    }

    intro = platform_intros.get(platform, f"🌟 <b>{service_name}</b> - Premium social media growth!")

    # Dynamic description based on quality and service type
    description = f"""
{intro}

{quality_emoji} <b>{quality_name} Selected</b>

⚡ <b>Service Details:</b>
💰 Rate: ₹{quality_config['rate_multiplier'] * service_info['base_rate']:.2f} per unit
📊 Min: {quality_config['min_quantity']} | Max: {service_info['max_quantity']:,}
⏰ Delivery: {quality_config['delivery_time']}
🚀 Speed: {quality_config['speed']}
🛡️ Guarantee: {quality_config['guarantee']}
💧 Drop rate: {quality_config['drop_rate']}

🎯 <b>Key Features:</b>"""

    # Add service features
    for feature in service_info['features'][:3]:  # Top 3 features
        description += f"\n✅ {feature}"

    # Add quality-specific features
    for feature in quality_config['bonus_features'][:2]:  # Top 2 bonus features
        description += f"\n🌟 {feature}"

    # Add platform-specific benefits
    description += f"\n\n💡 <b>Platform Benefits:</b>"
    for benefit in service_info.get('platform_features', [])[:2]:
        description += f"\n🎯 {benefit}"

    # Add quality-specific guarantee info
    if quality_config['cancel_allowed']:
        description += f"\n\n🔒 <b>Guarantee:</b>\n✅ {quality_config['refill_period']} refill guarantee\n✅ Cancellation allowed before start"
    else:
        description += f"\n\n🔒 <b>Guarantee:</b>\n✅ {quality_config['refill_period']} refill guarantee\n⚠️ No cancellation after order placed"

    # Add call to action based on quality
    if quality_config['quality_name'] == 'Premium Quality':
        description += f"\n\n🚀 <b>Premium Experience:</b> Best quality + Maximum results!"
    elif quality_config['quality_name'] == 'Basic Quality':
        description += f"\n\n💰 <b>Budget Option:</b> Great value for money!"
    elif quality_config['quality_name'] == 'High Quality':
        description += f"\n\n🔥 <b>High Performance:</b> Excellent results guaranteed!"
    elif quality_config['quality_name'] == 'Medium Quality':
        description += f"\n\n⚡ <b>Balanced Choice:</b> Good quality at fair price!"
    else:
        description += f"\n\n✅ <b>Standard Service:</b> Reliable and affordable!"

    return description

# ========== EASY UPDATE FUNCTIONS ==========
def update_service_rate(platform: str, service_id: str, new_rate: float):
    """Easily update service rate - for future use"""
    # This will be connected to database later
    print(f"Updated {platform} service {service_id} rate to ₹{new_rate}")

def add_new_service(platform: str, service_id: str, service_data: dict):
    """Easily add new service - for future use"""
    # This will be connected to database later
    print(f"Added new service: {platform} - {service_id}")

def get_platform_services(platform: str):
    """Get all services for a platform"""
    # Return list of all service IDs for the platform
    services_db = {
        'instagram': ['1001', '1002', '1003', '1004', '1005', '1006', '1007', '1008', '1009', '1010', '1011', '1012'],
        'youtube': ['3001', '3002', '3003', '3004', '3005', '3006', '3007', '3008', '3009', '3010', '3011', '3012'],
        'facebook': ['2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012'],
        'telegram': ['4001', '4002', '4003', '4004', '4005', '4006', '4007', '4008', '4009', '4010'],
        'whatsapp': ['5001', '5002', '5003', '5004', '5005', '5006', '5007', '5008'],
        'tiktok': ['6001', '6002', '6003', '6004', '6005', '6006', '6007', '6008', '6009', '6010'],
        'twitter': ['7001', '7002', '7003', '7004', '7005', '7006', '7007', '7008', '7009', '7010'],
        'linkedin': ['8001', '8002', '8003', '8004', '8005', '8006', '8007', '8008', '8009', '8010']
    }
    return services_db.get(platform, [])

    # Base rates per platform (per unit in rupees)
    base_rates = {
        "instagram": 0.50,
        "facebook": 0.60,
        "youtube": 1.20,
        "telegram": 0.40,
        "whatsapp": 0.80,
        "tiktok": 0.45,
        "twitter": 0.55,
        "linkedin": 1.50
    }

    # Service type rates (multiplier on base rate)
    service_multipliers = {
        "1001": 1.0,  # followers
        "1002": 0.6,  # likes
        "1003": 0.3,  # views
        "1004": 0.4,  # story views
        "1005": 0.7,  # story likes
        "1006": 2.0,  # comments
        "1007": 1.2,  # shares
        "1008": 1.5,  # channel members
        "1009": 0.8,  # saves
        "1010": 1.8,  # auto likes
        "1011": 1.1,  # poll votes
        "1012": 0.35, # reel views

        "2001": 1.2,  # fb page likes
        "2002": 0.7,  # fb post likes
        "2003": 1.0,  # fb group members
        "2004": 0.9,  # fb live views
        "2005": 0.4,  # fb video views
        "2006": 3.0,  # fb monetization
        "2007": 2.2,  # fb comments
        "2008": 1.3,  # fb shares
        "2009": 1.1,  # fb followers
        "2010": 4.0,  # fb rating
        "2011": 1.4,  # fb event interested
        "2012": 3.5,  # fb reviews

        "3001": 2.0,  # yt subscribers
        "3002": 0.15, # yt views
        "3003": 0.8,  # yt likes
        "3004": 5.0,  # yt monetization
        "3005": 2.5,  # yt comments
        "3006": 0.9,  # yt dislikes
        "3007": 0.8,  # yt watch time
        "3008": 3.0,  # yt memberships
        "3009": 0.6,  # yt premiere views
        "3010": 0.2,  # yt shorts views
        "3011": 1.5,  # yt live views
        "3012": 1.0,  # yt community likes

        "4001": 0.8,  # tg channel members
        "4002": 0.2,  # tg post views
        "4003": 0.9,  # tg group members
        "4004": 2.0,  # tg boost
        "4005": 1.5,  # tg comments
        "4006": 1.0,  # tg shares
        "4007": 0.7,  # tg reactions
        "4008": 1.2,  # tg poll votes
        "4009": 0.5,  # tg story views
        "4010": 3.0,  # tg premium members

        "5001": 1.5,  # wa group members
        "5002": 1.2,  # wa channel subs
        "5003": 0.6,  # wa status views
        "5004": 2.5,  # wa business reviews
        "5005": 1.8,  # wa group activity
        "5006": 1.0,  # wa broadcast
        "5007": 0.8,  # wa status reactions
        "5008": 2.0,  # wa business growth

        "6001": 1.0,  # tt followers
        "6002": 0.5,  # tt likes
        "6003": 0.25, # tt views
        "6004": 1.8,  # tt comments
        "6005": 1.2,  # tt shares
        "6006": 0.9,  # tt saves
        "6007": 1.5,  # tt live views
        "6008": 2.0,  # tt sound usage
        "6009": 0.4,  # tt story views
        "6010": 0.7,  # tt duet views

        "7001": 1.2,  # tw followers
        "7002": 0.6,  # tw likes
        "7003": 1.0,  # tw retweets
        "7004": 2.0,  # tw comments
        "7005": 0.3,  # tw impressions
        "7006": 1.8,  # tw space listeners
        "7007": 0.4,  # tw thread views
        "7008": 0.8,  # tw bookmarks
        "7009": 1.1,  # tw poll votes
        "7010": 0.5,  # tw video views

        "8001": 2.0,  # li followers
        "8002": 1.2,  # li post likes
        "8003": 3.0,  # li comments
        "8004": 1.8,  # li shares
        "8005": 0.8,  # li profile views
        "8006": 2.5,  # li company follows
        "8007": 1.0,  # li article views
        "8008": 4.0,  # li endorsements
        "8009": 5.0,  # li recommendations
        "8010": 3.5   # li connections
    }

    # Calculate final rate
    base_rate = base_rates.get(platform, 0.50)
    service_mult = service_multipliers.get(service_id, 1.0)
    quality_mult = quality_multipliers.get(quality, quality_multipliers["standard"])["rate_mult"]

    final_rate = base_rate * service_mult * quality_mult

    # Generate quantities based on service type
    if service_id in ["1001", "2001", "3001", "4001", "7001", "8001"]:  # Followers/Subscribers
        min_qty = 100
        max_qty = 100000
    elif service_id in ["1003", "2005", "3002", "4002", "6003", "7005"]:  # Views
        min_qty = 1000
        max_qty = 1000000
    elif service_id in ["1002", "2002", "3003", "6002", "7002"]:  # Likes
        min_qty = 50
        max_qty = 50000
    else:  # Other services
        min_qty = 10
        max_qty = 25000

    # Platform name mapping
    platform_names = {
        "instagram": "📷 Instagram",
        "facebook": "📘 Facebook",
        "youtube": "🎥 YouTube",
        "telegram": "📞 Telegram",
        "whatsapp": "💬 WhatsApp",
        "tiktok": "🎵 TikTok",
        "twitter": "🐦 Twitter",
        "linkedin": "💼 LinkedIn"
    }

    # Service name mapping
    service_names = {
        "1001": "👥 Followers", "1002": "❤️ Likes", "1003": "👁️ Views",
        "2001": "📄 Page Likes", "2002": "❤️ Post Likes", "2003": "👥 Group Members",
        "3001": "👥 Subscribers", "3002": "👁️ Views", "3003": "❤️ Likes",
        "4001": "👥 Channel Members", "4002": "👁️ Post Views", "4003": "👥 Group Members",
        "5001": "👥 Group Members", "5002": "📊 Channel Subscribers", "5003": "👁️ Status Views",
        "6001": "👥 Followers", "6002": "❤️ Likes", "6003": "👁️ Views",
        "7001": "👥 Followers", "7002": "❤️ Likes", "7003": "🔄 Retweets",
        "8001": "👥 Followers", "8002": "❤️ Post Likes", "8003": "💬 Comments"
    }

    # Quality descriptions
    quality_descriptions = {
        "premium": "💎 Premium Quality - सबसे बेहतरीन results",
        "high": "🔥 High Quality - बहुत अच्छे results", 
        "medium": "⚡ Medium Quality - अच्छे results",
        "standard": "✅ Standard Quality - सामान्य results",
        "basic": "💰 Basic Quality - बुनियादी results"
    }

    platform_name = platform_names.get(platform, platform.title())
    service_name = service_names.get(service_id, f"Service {service_id}")
    quality_desc = quality_descriptions.get(quality, quality.title())
    quality_info = quality_multipliers.get(quality, quality_multipliers["standard"])

    # Generate description
    description = f"""
{platform_name} <b>{service_name}</b>

{quality_desc}

📊 <b>Package Details:</b>
• 🎯 <b>Quality:</b> {quality_info['retention']} retention rate
• ⚡ <b>Delivery:</b> {quality_info['speed']}
• 🔒 <b>Safety:</b> 100% Safe & Secure
• 💎 <b>Type:</b> Real & Active Users

✨ <b>Special Features:</b>
• No password required
• Instant start guarantee
• 24/7 customer support
• Money back guarantee
• High retention rate

💰 <b>Pricing Information:</b>
• Rate per unit: ₹{final_rate:.3f}
• Minimum order: {min_qty:,} units
• Maximum order: {max_qty:,} units

🎯 <b>Perfect for:</b>
• Organic growth boost
• Brand credibility
• Social proof enhancement
• Marketing campaigns
"""

    return {
        "platform": platform,
        "service_id": service_id,
        "quality": quality,
        "rate": final_rate,
        "min_quantity": min_qty,
        "max_quantity": max_qty,
        "retention": quality_info['retention'],
        "delivery_time": quality_info['speed'],
        "description": description,
        "platform_name": platform_name,
        "service_name": service_name
    }
