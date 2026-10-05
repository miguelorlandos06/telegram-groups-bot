from aiogram.fsm.state import State, StatesGroup


class AddItemStates(StatesGroup):
    choosing_type = State()
    link = State()
    title = State()
    description = State()
    category = State()
    country = State()
    language = State()
    members = State()
    tags = State()
    adult = State()
    confirm = State()


class SearchStates(StatesGroup):
    waiting_query = State()
