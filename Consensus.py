import StatsTracker


def get_max_count(tracker_list):
    max_stat = 0
    for stat in tracker_list:
        if stat.get_count() > max_stat:
            max_stat = stat.get_count()
    return max_stat


def get_consensus(peer_stats):
    found = False
    tracker_list = []
    consensus_stats = []

    for peer in peer_stats:
        if not tracker_list:
            tracker_object = StatsTracker.StatsTracker(peer.get_stats())
            tracker_object.add_peer(peer)
            tracker_list.append(tracker_object)
        else:
            # compare peer to every stat in the list
            # print("\nPEER: \n{}".format(peer))
            for stat in tracker_list:
                # if not found, keep searching
                if not found:
                    if stat.stats_equal(peer):
                        stat.add_peer(peer)
                        found = True
            # if by the time we cycle through all the stats we still haven't found it
            # add the peer to the tracker list
            if not found:
                tracker_object = StatsTracker.StatsTracker(peer.get_stats())
                tracker_object.add_peer(peer)
                tracker_list.append(tracker_object)

        # now reset found to True
        found = False

    max_stat = get_max_count(tracker_list)

    for stat in tracker_list:
        if stat.get_count() == max_stat:
            consensus_stats.append(stat)

    return consensus_stats[0]
