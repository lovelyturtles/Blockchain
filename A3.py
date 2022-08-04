import json
import socket
import uuid
import sys
import time
import threading
import copy

import Peer
import Peers
import BlockChain
import Consensus

# declare the blockchains as global variables
my_chain = BlockChain.BlockChain()
build_chain = BlockChain.BlockChain()

# General connection information
BYTE_SIZE = 1024
FORMAT = "utf-8"

# My connection information
HOST = socket.gethostbyname(socket.gethostname())
PORT = 8265
MY_ADDRESS = (HOST, PORT)
MY_ID = str(uuid.uuid4())
MY_NAME = "susiesusie"

# Rob's connection information
SERVER_HOST = "silicon.cs.umanitoba.ca"
SERVER_PORT = 8999
SERVER_ADDRESS = (SERVER_HOST, SERVER_PORT)

# how many times to try the UDP connection again before giving up
TRY_AGAIN = 3

# Holds all the flood ID's we've already forwarded
flood_ids = []
# Holds all the peers we're currently connected to
current_peers = Peers.Peers()

# Keeping track of time
START_TIME = time.time()
HALF_A_MINUTE = 30.0
ONE_MINUTE = 60.0
THREE_MINUTES = 3 * 60.0

# Tracking if we're already doing a consensus
doing_consensus = False

# Formatting the messages we're going to send
FLOOD_MESSAGE = {
    "type": "FLOOD",
    "host": HOST,
    "port": PORT,
    "id": MY_ID,
    "name": MY_NAME
}

STATS_MESSAGE = {
    "type": "STATS"
}


def get_block(height):
    msg = {
        "type": "GET_BLOCK",
        "height": height
    }
    return msg


# Handlers -------------------------------------------------------------------------
def handle_block_reply(block_reply):
    build_chain.load_chain(block_reply)


def handle_get_block(my_socket, get_message, client_host, client_port):
    block_reply = json.dumps(build_chain.get_block_reply(get_message).encode())
    my_socket.sendto(block_reply, client_host, client_port)


def handle_stats_reply(stats_reply, client_host, client_port):
    current_peers.set_stats(stats_reply, client_host, client_port)


def handle_stats(my_socket, client_host, client_port):
    stats_reply = build_chain.get_stats_reply()
    if stats_reply is not None:
        my_socket.sendto(json.dumps(stats_reply).encode(), client_host, client_port)


def handle_flood(my_socket, flood_msg):
    originator_host = flood_msg['host']
    originator_port = flood_msg['port']
    flood_reply = {
        "type": "FLOOD_REPLY",
        "host": HOST,
        "port": PORT,
        "name": MY_NAME
    }

    # reply with our information to the originator of the flood message
    my_socket.sendto(flood_reply, originator_host, originator_port)

    # forward this flood to our peers if we haven't already done so
    if flood_msg['id'] not in flood_ids:
        flood_ids.append(flood_msg['id'])
        for peer in current_peers:
            my_socket.sendto(json.dumps(flood_msg).encode(), peer.get_address())

    # update our "last heard from" (should I do this in flood_reply?)


def handle_flood_reply(flood_reply, current_time):
    new_peer = Peer.Peer(flood_reply['host'], flood_reply['port'], current_time, flood_reply['name'])
    already_added = current_peers.add_peer(new_peer)
    if already_added:
        del new_peer


def build_my_chain(my_socket, majority):
    get_majority_blocks(my_socket, majority)
    print("chain_complete: {}".format(build_chain.chain_complete()))
    if build_chain.chain_complete():
        build_chain.sort_chain()
        build_chain.validate_chain()
        global my_chain
        my_chain = copy.deepcopy(build_chain)
        build_chain.reset_chain()


def handle_consensus(my_socket):
    global doing_consensus
    if not doing_consensus:
        doing_consensus = True
        do_consensus(my_socket)
        majority = Consensus.get_consensus(current_peers)
        # if our stats don't match the majority, we have to rebuild
        if not build_chain.stats_equal(majority.get_stats()):
            build_my_chain(my_socket, majority)
        doing_consensus = False


def handle_announce(new_block):
    if my_chain.get_target_size() >= 0:
        my_chain.add_block(new_block)


# Helper Functions -----------------------------------------------------------------
def process_response(my_socket, response, client_address, client_port):
    response = json.loads(response.decode())
    response_type = response['type']

    if response_type == 'GET_BLOCK_REPLY':
        handle_block_reply(response)

    elif response_type == 'GET_BLOCK':
        handle_get_block(my_socket, response, client_address, client_port)

    elif response_type == 'STATS_REPLY':
        handle_stats_reply(response, client_address, client_port)

    elif response_type == 'STATS':
        handle_stats(my_socket, client_address, client_port)

    elif response_type == 'FLOOD':
        handle_flood(my_socket, response)

    elif response_type == 'FLOOD_REPLY':
        handle_flood_reply(response, time.time())

    elif response_type == 'CONSENSUS':
        handle_consensus(my_socket)

    elif response_type == 'ANNOUNCE':
        handle_announce(response)


def get_majority_blocks(my_socket, consensus_info):
    height = consensus_info.get_stats()['height']
    # height will be our target size for the blockchain
    build_chain.set_target_size(height)
    majority_peers = consensus_info.get_majority_peers()
    block_number = 0
    peer_number = 0
    while block_number < height:
        host = majority_peers[peer_number].get_host()
        port = majority_peers[peer_number].get_port()
        my_socket.sendto(get_block(block_number), host, port)
        tries = TRY_AGAIN
        # check if the block was added, if not send the message again
        while tries and not build_chain.block_added(block_number):
            my_socket.sendto(get_block(block_number), host, port)
            tries -= 1
        # receiver deals with my_socket.recv
        block_number += 1
        peer_number = (peer_number + 1) % len(majority_peers)


def do_consensus(my_socket):
    # reset the stats because we'll be using Nones to check if we have to
    # resend the UDP message
    current_peers.reset_stats()
    for peer in current_peers:
        tries = TRY_AGAIN
        my_socket.sendto(STATS_MESSAGE, peer.get_address())
        # if we didn't get a response, try another "tries" number of times
        while tries and peer.get_stats() is None:
            my_socket.sendto(STATS_MESSAGE, peer.get_address())
            tries -= 1


# Threads --------------------------------------------------------------------------

# this thread processes all the messages that come in
def receiver_thread(my_socket):
    while True:
        response, (client_address, client_port) = my_socket.recvfrom(BYTE_SIZE)
        process_response(my_socket, response, client_address, client_port)


# this thread sends a flood every 30 seconds
def keep_alive_ping_thread(my_socket):
    while True:
        time.sleep(HALF_A_MINUTE - ((time.time() - START_TIME) % HALF_A_MINUTE))
        my_socket.sendto(FLOOD_MESSAGE, SERVER_ADDRESS)


# this thread drops any peers we haven't heard from in a minute
def drop_peers_thread():
    while True:
        # sleep for 60 seconds
        time.sleep(ONE_MINUTE - ((time.time() - START_TIME) % ONE_MINUTE))
        current_time = time.time()
        remove_indices = []
        for index, peer in enumerate(current_peers):
            # check if we last heard from them over a minute ago
            if current_time - peer.last_heard_from() > ONE_MINUTE:
                # index of the current_peers collection we want to remove
                remove_indices.append(index)
        for index in remove_indices:
            current_peers.remove_peer(index)


# this thread does a consensus every 3 minutes
def consensus_loop_thread(my_socket):
    while True:
        time.sleep(THREE_MINUTES - ((time.time() - START_TIME) % THREE_MINUTES))
        handle_consensus(my_socket)


# Functions ------------------------------------------------------------------------
def join_network(my_socket):
    my_socket.sendto(FLOOD_MESSAGE, SERVER_ADDRESS)
    receiver = threading.Thread(target=receiver_thread, args=(my_socket,))
    receiver.daemon = True
    receiver.start()

    global doing_consensus
    doing_consensus = True
    do_consensus(my_socket)
    majority = Consensus.get_consensus(current_peers)
    build_my_chain(my_socket, majority)
    doing_consensus = False
# ----------------------------------------------------------------------------------


def main():
    # Initialize UDP socket
    try:
        print("Creating UDP socket")
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # bind to 0 will give us a random port. Bind to mine will give us?
        my_socket.bind((HOST, PORT))
        my_socket.settimeout(5)

        response = ''

        print("Test send to peer {}:{}".format(SERVER_HOST, SERVER_PORT))
        try:
            join_network(my_socket)
            ping = threading.Thread(target=keep_alive_ping_thread, args=(my_socket,))
            drop = threading.Thread(target=drop_peers_thread)
            consensus = threading.Thread(target=consensus_loop_thread, args=(my_socket,))

            # daemon means they'll die when the main does
            ping.daemon = True
            drop.daemon = True
            consensus.daemon = True

            ping.start()
            drop.start()
            consensus.start()

        except socket.timeout:
            print("Time out! Peer not responding?")
            sys.exit(1)
        except json.JSONDecodeError:
            print("Got a reply, but it wasn't json")
            print(response)
        except Exception as e:
            print("Not sure what the error is")
            print(e)
            sys.exit(1)

    except Exception as e:
        print("Could not connect. Quitting")
        print(e)
        sys.exit(1)


main()
