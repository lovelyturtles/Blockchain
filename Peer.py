class Peer:
    def __init__(self, host, port, time, name):
        self.host = host
        self.port = port
        self.stats = None
        self.name = name
        self.last_heard = time

    def get_host(self):
        return self.host

    def get_port(self):
        return self.port

    def get_address(self):
        return tuple((self.host, self.port))

    def get_name(self):
        return self.name

    def get_stats(self):
        return self.stats

    def set_stats(self, stats):
        self.stats = stats

    def stats_equal(self, other):
        height_equals = self.stats["height"] == other.stats["height"]
        hash_equals = self.stats["hash"] == other.stats["hash"]
        return height_equals and hash_equals

    def check_in(self, time):
        self.last_heard = time

    def last_heard_from(self):
        return self.last_heard

    def __str__(self):
        return "host: {}\nport: {}\nSTAT_REPLY: {}".format(self.host, self.port, self.stats)
