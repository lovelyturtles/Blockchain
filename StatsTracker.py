class StatsTracker:
    def __init__(self, stats):
        self.stats = stats
        self.majority_peers = []
        self.peer_count = 0

    def add_peer(self, peer):
        self.majority_peers.append(peer)
        self.peer_count += 1

    def stats_equal(self, other):
        height_equals = self.stats["height"] == other.stats["height"]
        hash_equals = self.stats["hash"] == other.stats["hash"]
        return height_equals and hash_equals

    def get_stats(self):
        return self.stats

    def get_count(self):
        return self.peer_count

    def get_majority_peers(self):
        return self.majority_peers

    def __str__(self):

        message = "stats: {}\npeer count: {}\n".format(self.stats, self.peer_count)
        message += "--------------------------------------------------------------\n"
        count = 1
        for item in self.majority_peers:
            message += "Peer {}:\n".format(count) + str(item) + "\n\n"
            count += 1
        message += "--------------------------------------------------------------"
        return message
