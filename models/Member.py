import logging

logger = logging.getLogger(__name__)

class Member:
    def __init__(self, telegram_name, vehicles):
        self.id = None
        self.author = None
        self.reg_date = None
        self.last_modifier = None
        self.last_modified_date = None
        self.telegram_name = telegram_name
        self.localized_name = {}

