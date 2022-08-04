class PeerIterator:
    def __init__(self, peers):
        # reference to the Peers object
        self.peers = peers

        # keep track of the current index
        self.index = 0

    def __next__(self):
        # returns the next value in the Peers object's list
        if self.index < self.peers.get_size():
            result = self.peers.get_element(self.index)
            self.index += 1
            return result
        else:
            raise StopIteration


class Peers:
    def __init__(self):
        self.peer_list = []

    def add_peer(self, new_peer):
        already_added = False
        for peer in self.peer_list:
            if not already_added:
                hosts_match = peer.get_host() == new_peer.get_host()
                ports_match = peer.get_port() == new_peer.get_port()
                names_match = peer.get_name() == new_peer.get_name()
                if hosts_match and ports_match and names_match:
                    already_added = True
        if not already_added:
            self.peer_list.append(new_peer)
        return already_added

    def get_size(self):
        return len(self.peer_list)

    def get_element(self, index):
        return self.peer_list[index]

    def set_stats(self, stats, host, port):
        found = False
        for peer in self.peer_list:
            if not found:
                if peer.get_host() == host and peer.get_port() == port:
                    peer.set_stats(stats)
                    found = True

    def check_in(self, host, port, time):
        found = False
        for peer in self.peer_list:
            if not found:
                if peer.get_host() == host and peer.get_port() == port:
                    peer.check_in(time)
                    found = True

    def remove_peer(self, index):
        peer = self.peer_list.pop(index)
        print("{}:{} removed".format(peer.get_host(), peer.get_port()))
        del peer  # Think on whether to keep this

    def reset_stats(self):
        for peer in self.peer_list:
            peer.set_stats(None)

    def __iter__(self):
        # returns the Iterator object
        return PeerIterator(self)
