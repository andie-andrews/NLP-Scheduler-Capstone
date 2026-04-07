class ConversationMemory:
    def __init__(self):
        self.last_intent = None
        self.last_options = None  # for disambiguation
        self.last_entity_type = None  # "employee" or "shift"

    def save_intent(self, intent):
        self.last_intent = intent

    def save_disambiguation(self, entity_type, options):
        self.last_entity_type = entity_type
        self.last_options = options

    def clear_disambiguation(self):
        self.last_entity_type = None
        self.last_options = None