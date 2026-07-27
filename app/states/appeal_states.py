"""FSM states for the appeal submission flow."""

from aiogram.fsm.state import State, StatesGroup


class AppealForm(StatesGroup):
    full_name = State()          # 1. Ism Familya
    mahalla = State()            # 2. Mahalla
    street_and_house = State()   # 3. Ko'cha va uy raqami
    phone_number = State()       # 4. Tel raqami
    message_text = State()       # 5. Muammo yoki taklifi
    media = State()              # 6. Rasm/video/ovoz (ixtiyoriy)
    confirm = State()            # Yakuniy tasdiqlash


class AIChat(StatesGroup):
    active = State()             # "AI maslahatchi" rejimida suhbat
