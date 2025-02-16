import argparse
import asyncio
import logging

from client import *

"""
    Client bittorrent protocol implementation in python
"""

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def run_bootstrap_node(host="0.0.0.0", port=8468):
    """Run a bootstrap node for the DHT network"""
    asyncio.get_event_loop().set_debug(True)
    logger = logging.getLogger(__name__)

    server = Server()
    await server.listen(port, host)
    try:
        stop_event = asyncio.Event()
        await stop_event.wait()
    except KeyboardInterrupt:
        logger.info("Stopping bootstrap node...")
    finally:
        server.stop()


async def main(user_arguments=None):
    if user_arguments is None:
        print("Starting as bootstrap node...")
        host = os.getenv("BOOTSTRAP_NODE_IP", "0.0.0.0")
        port = int(os.getenv("BOOTSTRAP_NODE_PORT", "8468"))

        try:
            await run_bootstrap_node(host, port)
        except KeyboardInterrupt:
            print("\nBootstrap node stopped")
        return

    # create torrent client object
    client = bittorrent_client(user_arguments)

    # contact the DHT
    flag = False
    while not flag:
        flag = await client.contact_dht()
    # initialize the swarm of peers
    client.initialize_swarm()
    # download the file from the swarm
    client.event_loop()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        try:
            asyncio.run(main())  # Run as bootstrap node
        except KeyboardInterrupt:
            sys.exit(0)

    bittorrent_description = "Bittorrent Client implementation in python"
    parser = argparse.ArgumentParser(description=bittorrent_description)
    parser.add_argument(TORRENT_FILE_PATH, help="unix file path of torrent file")
    parser.add_argument(
        "-d", "--" + DOWNLOAD_DIR_PATH, help="unix directory path of downloading file"
    )
    parser.add_argument(
        "-s", "--" + SEEDING_DIR_PATH, help="unix directory path for the seeding file"
    )
    parser.add_argument(
        "-m",
        "--" + MAX_PEERS,
        help="maximum peers participating in upload/download of file",
    )
    parser.add_argument(
        "-l", "--" + RATE_LIMIT, help="upload / download limits in Kbps"
    )

    # get the user input option after parsing the command line argument
    options = vars(parser.parse_args(sys.argv[1:]))

    if options[DOWNLOAD_DIR_PATH] is None and options[SEEDING_DIR_PATH] is None:
        print(
            "Bittorrent works with either download or upload arguments, try using --help"
        )
        sys.exit()

    if options[MAX_PEERS] and int(options[MAX_PEERS]) > 50:
        print("Bittorrent client doesn't support more than 50 peer connection !")
        sys.exit()

    if options[RATE_LIMIT] and int(options[RATE_LIMIT]) <= 0:
        print(
            "Bittorrent client upload / download rate must always greater than 0 Kbps"
        )
        sys.exit()

    # call the main function
    asyncio.run(main(options))
