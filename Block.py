class Block:
    def __init__(self, height, mined_by, nonce, messages, hash_value):
        self.height = height
        self.mined_by = mined_by
        self.nonce = nonce
        self.messages = messages
        self.hash_value = hash_value

    def get_height(self):
        return self.height

    def get_miner(self):
        return self.mined_by

    def get_nonce(self):
        return self.nonce

    def get_messages(self):
        return self.messages

    def get_hash(self):
        return self.hash_value

    def __str__(self):
        message = 'height: {}\nmined_by: {}\nnonce: {}\nmessages: {}\nhash_value: {}'.format(
            self.height, self.mined_by, self.nonce, self.messages, self.hash_value)
        return message
