# -*- coding: utf-8 -*-
"""
States Definition - India Social Panel
Defines FSM states for the order flow process
"""

from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    """States for the order process flow"""
    waiting_link = State()
    waiting_quantity = State()
    waiting_coupon = State()
    confirming_final_order = State()
    selecting_payment = State()
    waiting_screenshot = State()


class CreateOfferStates(StatesGroup):
    """States for creating new offers (admin only)"""
    getting_message = State()
    getting_package_name = State()
    getting_rate = State()
    asking_fixed_quantity = State()
    getting_fixed_quantity = State()


class AdminSendOfferStates(StatesGroup):
    """States for sending offers to users (admin only)"""
    getting_offer_id = State()
    choosing_target = State()
    getting_specific_user_id = State()


class OfferOrderStates(StatesGroup):
    """States for the simplified offer order process flow"""
    getting_link = State()
    getting_quantity = State()
    confirming_order = State()
    waiting_screenshot = State()


class AdminCreateUserStates(StatesGroup):
    """States for admin creating user accounts via tokens"""
    waiting_for_token = State()


class AdminDirectMessageStates(StatesGroup):
    """States for admin sending direct messages to users"""
    waiting_for_message = State()


class FeedbackStates(StatesGroup):
    """States for feedback collection after order completion"""
    waiting_feedback = State()


