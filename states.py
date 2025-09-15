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
