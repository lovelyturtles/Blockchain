import Block
import hashlib
from operator import attrgetter

DIFFICULTY = 8


class BlockChain:
    def __init__(self):
        self.block_chain = []
        self.target_size = -1
        self.top_height = 0
        self.validated_chain = False

    def set_target_size(self, target_size):
        self.target_size = target_size

    def get_target_size(self):
        return self.target_size

    def reset_chain(self):
        self.block_chain.clear()
        self.target_size = -1
        self.top_height = 0
        self.validated_chain = False

    def load_chain(self, get_block):
        already_added = False
        height = get_block['height']
        # confirm that this block exists first
        if height is not None:
            # also make sure this height isn't already in the chain
            for block in self.block_chain:
                if not already_added:
                    if block.get_height() == height:
                        already_added = True

            # if we don't already have a block with this height, add it:
            if not already_added:
                mined_by = get_block['minedBy']
                nonce = get_block['nonce']
                messages = get_block['messages']
                hash_value = get_block['hash']

                # create a new block with all these values
                new_block = Block.Block(height, mined_by, nonce, messages, hash_value)

                # insert the block into the blockchain
                self.block_chain.append(new_block)

                # increase the height counter (for the top block)
                self.top_height += 1

    def chain_complete(self):
        return len(self.block_chain) == self.target_size

    def sort_chain(self):
        self.block_chain.sort(key=attrgetter('height'))

    def validate_chain(self):
        # make sure the list isn't empty
        if self.block_chain:
            # print("In validate_chain")
            # print(len(self.block_chain))
            # print("self.top_height: {}".format(self.top_height))
            for block in self.block_chain:
                hash_base = hashlib.sha256()

                height = block.get_height()
                # print("height: {}".format(height))
                if height > 0:
                    # get the most recent hash
                    last_hash = self.block_chain[height - 1].get_hash()
                    # add it to this hash
                    hash_base.update(last_hash.encode())

                # add the miner
                hash_base.update(self.block_chain[height].get_miner().encode())

                # add the messages in order
                for m in self.block_chain[height].get_messages():
                    hash_base.update(m.encode())

                # add the nonce
                hash_base.update(self.block_chain[height].get_nonce().encode())

                # get the pretty hexadecimal
                hash_value = hash_base.hexdigest()

                # check if it's difficult enough
                if hash_value[-1 * DIFFICULTY:] != '0' * DIFFICULTY:
                    print("Block wasn't difficult enough: {}".format(hash_value))

                # check if it matches what we have
                if hash_value != self.block_chain[height].get_hash():
                    print("hash values don't match, this is not a valid block")

        self.validated_chain = True

    def add_block(self, new_block):
        already_added = False
        height = new_block['height']
        # make sure this block exists
        if height is not None:

            # make sure this height isn't already in the chain
            for block in self.block_chain:
                if not already_added:
                    if block.get_height() == height:
                        already_added = True

            if not already_added:

                # validate the block
                hash_base = hashlib.sha256()

                # get the most recent hash
                last_hash = self.block_chain[self.top_height-1].get_hash()

                # add it to this hash
                hash_base.update(last_hash.encode())

                # add the miner
                hash_base.update(new_block['minedBy'].encode())

                # add the messages in order
                for m in new_block['messages']:
                    hash_base.update(m.encode())

                # add the nonce
                hash_base.update(new_block['nonce'].encode())

                # get the pretty hexadecimal
                hash_value = hash_base.hexdigest()

                # check if it's difficult enough
                if hash_value[-1 * DIFFICULTY:] != '0' * DIFFICULTY:
                    print("Block wasn't difficult enough: {}".format(hash_value))

                # check if it matches what we have
                if hash_value != self.block_chain[height].get_hash():
                    print("hash values don't match, this is not a valid block")

                # even if it's invalid, we add it to the blockchain anyway
                self.block_chain.append(new_block)

                # increase the height counter (for the top block)
                self.top_height += 1

    def get_stats_reply(self):
        stats_reply = None
        top_block = self.block_chain[self.top_height - 1]
        if top_block is not None:
            stats_reply = {
                "type": "STATS_REPLY",
                "height": top_block.get_height(),
                "hash": top_block.get_hash()
            }
        return stats_reply

    def stats_equal(self, their_stats):
        our_stats = self.get_stats_reply()
        height_equals = our_stats['height'] == their_stats['height']
        hash_equals = our_stats['hash'] == their_stats['hash']
        return height_equals and hash_equals

    def get_block_reply(self, get_block):

        height = get_block['height']
        reply = {
            "type": "GET_BLOCK_REPLY",
            "height": None,
            "minedBy": None,
            "nonce": None,
            "messages": None,
            "hash": None
        }

        if height is not None and 0 <= height < len(self.block_chain):
            this_block = self.block_chain[height]
            reply['height'] = this_block.get_height()
            reply['minedBy'] = this_block.get_miner()
            reply['nonce'] = this_block.get_nonce()
            reply['messages'] = this_block.get_messages()
            reply['hash'] = this_block.get_hash()

        return reply

    def block_added(self, height):
        block_exists = False

        # make sure this height is even in range
        # when using this, all the blocks probably haven't
        # been added yet, so we can't put an upper limit on height
        if height is not None and height >= 0:
            # go through each block and check if any of the heights
            # matches the one we passed in as parameter
            for block in self.block_chain:
                if not block_exists:
                    if block.get_height() == height:
                        block_exists = True

        return block_exists

    def __str__(self):

        index = self.top_height
        stop = index - 10

        message = "Last 10 block of the Blockchain:\n"
        message += "--------------------------------------------------------------\n"
        while index > stop:
            message += str(self.block_chain[index])
            index -= 1
        message += "--------------------------------------------------------------"
        return message
