import asyncio
import json
import os
import sys
import time
import threading
from logging import DEBUG

from py_bit_torrent.protocol.kademlia import Server
from py_bit_torrent.protocol.shared_file_handler import torrent_shared_file_handler

# tracker module for making tracker request and recieving peer data
from py_bit_torrent.protocol.swarm import swarm
from py_bit_torrent.protocol.torrent import torrent
from py_bit_torrent.protocol.torrent_file_handler import torrent_file_reader
from py_bit_torrent.protocol.torrent_logger import BITTORRENT_LOG_FILE, torrent_logger

# torrent file hander module for reading .torrent files

# torrent module holds all the information about the torrent file

# swarm module controls the operations over the multiple peers

# share file handler module provides file I/O interface

# torrent logger module for execution logging

TORRENT_FILE_PATH = "torrent_file_path"
DOWNLOAD_DIR_PATH = "download_directory_path"
SEEDING_DIR_PATH = "seeding_directory_path"
MAX_PEERS = "max_peers"
RATE_LIMIT = "rate_limit"

"""
    Torrent client would help interacting with the tracker server and
    download the files from other peers which are participating in sharing
"""


class bittorrent_client:
    """
    initialize the BTP client with torrent file and user arguments
    reads the torrent file and creates torrent class object
    """

    def __init__(self, user_arguments):
        # extract the torrent file path
        self.dht_server = Server()
        self.is_server_listening = False
        torrent_file_path = user_arguments[TORRENT_FILE_PATH]

        # bittorrent client logger
        self.bittorrent_logger = torrent_logger(
            "bittorrent", BITTORRENT_LOG_FILE, DEBUG
        )
        self.bittorrent_logger.set_console_logging()

        self.bittorrent_logger.log("Reading " + torrent_file_path + " file ...")

        # read metadata from the torrent torrent file
        self.torrent_info = torrent_file_reader(torrent_file_path)

        # decide whether the user want to download or seed the torrent
        self.client_request = {
            "seeding": None,
            "downloading": None,
            "uploading rate": sys.maxsize,
            "downloading rate": sys.maxsize,
            "max peers": 4,
        }

        # user wants to download the torrent file
        if user_arguments[DOWNLOAD_DIR_PATH]:
            self.client_request["downloading"] = user_arguments[DOWNLOAD_DIR_PATH]
            if user_arguments[RATE_LIMIT]:
                self.client_request["downloading rate"] = int(
                    user_arguments[RATE_LIMIT]
                )
        # user wants to seed the torrent file
        elif user_arguments[SEEDING_DIR_PATH]:
            self.client_request["seeding"] = user_arguments[SEEDING_DIR_PATH]
            if user_arguments[RATE_LIMIT]:
                self.client_request["uploading rate"] = int(user_arguments[RATE_LIMIT])

        # max peer connections
        if user_arguments[MAX_PEERS]:
            self.client_request["max peers"] = int(user_arguments[MAX_PEERS])

        # make torrent class instance from torrent data extracted from torrent file
        self.torrent = torrent(self.torrent_info.get_data(), self.client_request)

        self.bittorrent_logger.log(str(self.torrent))

    """
        functions helps in contacting the trackers requesting for 
        swarm information in which multiple peers are sharing file
    """

    async def set_dht_peer(self, info_hash, peer_data):
        """Store peer info in DHT network"""
        try:
            # Convert peer data to string for storage
            peer_info = json.dumps(
                {
                    "ip": peer_data["ip"],
                    "port": peer_data["port"],
                    "timestamp": peer_data["timestamp"],
                }
            )

            # Store in DHT using info_hash as key
            await self.dht_server.set(info_hash, peer_info)
            self.bittorrent_logger.log(
                f"Successfully announced peer to DHT for {info_hash.hex()}"
            )

        except Exception as e:
            self.bittorrent_logger.log(f"Failed to store peer in DHT: {str(e)}")

    async def get_dht_peers(self, info_hash):
        """Retrieve peers from DHT network"""
        try:
            # Query DHT for peers with this info_hash
            peers_data = await self.dht_server.get(info_hash)
            if peers_data:
                # Parse stored peer data
                if isinstance(peers_data, list):
                    return [json.loads(p) for p in peers_data if p]
                elif isinstance(peers_data, str):
                    return [json.loads(peers_data)]
            return []
        except Exception as e:
            self.bittorrent_logger.log(f"Failed to get peers from DHT: {str(e)}")
            return []

    async def contact_dht(self):
        """Contact DHT network to find peers or announce presence"""
        self.bittorrent_logger.log("Bootstrapping DHT node...")

        try:
            # Start listening on a random port
            if not self.is_server_listening:
                await self.dht_server.listen(self.torrent.client_port)
                self.is_server_listening = True

            # Bootstrap with known DHT node
            bootstrap_nodes = [
                (os.getenv("BOOTSTRAP_NODE_IP"), int(os.getenv("BOOTSTRAP_NODE_PORT")))
            ]
            self.bittorrent_logger.log("Connecting to bootstrap nodes...")

            contacted_bootstrap_nodes = await self.dht_server.bootstrap(bootstrap_nodes)

            if len(contacted_bootstrap_nodes) == 0:
                return False

            info_hash = self.torrent.torrent_metadata.info_hash

            # If seeding, announce ourselves to the DHT
            if self.client_request["seeding"] is not None:
                peer_data = {
                    "ip": self.torrent.client_IP,  # Will be replaced with actual IP
                    "port": self.torrent.client_port,  # Use standard BT port or make configurable
                    "timestamp": int(time.time()),
                }
                await self.set_dht_peer(info_hash, peer_data)
                self.dht_peers_data = {"peers": [], "interval": 1800}

            # If downloading, look for peers
            elif self.client_request["downloading"] is not None:
                peers = await self.get_dht_peers(info_hash)
                self.dht_peers_data = {"peers": peers, "interval": 1800}
                self.bittorrent_logger.log(f"Found {len(peers)} peers via DHT")
            return True

        except Exception as e:
            self.bittorrent_logger.log(f"DHT Error: {str(e)}")
            self.dht_peers_data = {"peers": [], "interval": 1800}

    """
        function initilizes swarm from the active tracker connection 
        response peer data participating in file sharing
    """

    def initialize_swarm(self):
        self.bittorrent_logger.log("Initializing the swarm of peers via DHT ...")
        peers_data = (
            self.dht_peers_data
            if hasattr(self, "dht_peers_data")
            else {"peers": [], "interval": 1800}
        )
        if self.client_request["downloading"] is not None:
            self.swarm = swarm(peers_data, self.torrent)
        if self.client_request["seeding"] is not None:
            peers_data["peers"] = []
            self.swarm = swarm(peers_data, self.torrent)

    """
        function helps in uploading the torrent file that client has 
        downloaded completely, basically the client becomes the seeder
    """

    def seed(self):
        self.bittorrent_logger.log("Client started seeding ... ")

        # download file initialization
        upload_file_path = self.client_request["seeding"]

        # create file handler for downloading data from peers
        file_handler = torrent_shared_file_handler(upload_file_path, self.torrent)

        # add the file handler
        self.swarm.add_shared_file_handler(file_handler)

        # start seeding the file
        self.swarm.seed_file()

    """
        function helps in downloading the torrent file form swarm 
        in which peers are sharing file data
    """

    def download(self):
        # download file initialization
        download_file_path = (
            self.client_request["downloading"] + self.torrent.torrent_metadata.file_name
        )

        self.bittorrent_logger.log(
            "Initializing the file handler for peers in swarm ... "
        )

        # create file handler for downloading data from peers
        file_handler = torrent_shared_file_handler(download_file_path, self.torrent)

        # initialize file handler for downloading
        file_handler.initialize_for_download()

        # distribute file handler among all peers for reading/writing
        self.swarm.add_shared_file_handler(file_handler)

        self.bittorrent_logger.log(
            "Client started downloading (check torrent statistics) ... "
        )

        # lastly download the whole file
        self.swarm.download_file()

    """
        the event loop that either downloads / uploads a file
    """

    def event_loop(self):
        if self.client_request["downloading"] is not None:
            # Start new thread for monitoring new seeder nodes periodically
            monitor_thread = threading.Thread(
                target=self.monitor_dht_seeders, daemon=True
            )
            monitor_thread.start()
            self.download()
        if self.client_request["seeding"] is not None:
            self.seed()

    # Add a new method to monitor for new seeders via DHT
    def monitor_dht_seeders(self):
        while not self.swarm.download_complete():
            try:
                # Call the asynchronous get_dht_peers from a synchronous context
                new_peers = asyncio.run(
                    self.get_dht_peers(self.torrent.torrent_metadata.info_hash)
                )
                for peer_info in new_peers:
                    # Check if the peer is already in the swarm by matching ip and port
                    exists = any(
                        p.IP == peer_info["ip"] and p.port == int(peer_info["port"])
                        for p in self.swarm.peers_list
                    )
                    if not exists:
                        from py_bit_torrent.protocol.peer import Peer  # local import

                        new_peer = Peer(
                            peer_info["ip"], int(peer_info["port"]), self.torrent
                        )
                        self.swarm.peers_list.append(new_peer)
                        self.bittorrent_logger.log(
                            f"Added new seeder {peer_info['ip']}:{peer_info['port']}"
                        )
                time.sleep(10)  # poll every 10 seconds
            except Exception as e:
                self.bittorrent_logger.log("Error monitoring DHT seeders: " + str(e))
                time.sleep(10)
