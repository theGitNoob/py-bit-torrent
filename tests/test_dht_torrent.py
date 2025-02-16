import pytest
import asyncio
from unittest.mock import MagicMock, patch

from py_bit_torrent.protocol.client import bittorrent_client
from py_bit_torrent.protocol.kademlia.network import Server


@pytest.fixture
def mock_torrent_file():
    return {
        "torrent_file_path": "test.torrent",
        "download_directory_path": "/tmp/downloads",
        "seeding_directory_path": None,
        "max_peers": "10",
        "rate_limit": "1000",
    }


@pytest.mark.asyncio
async def test_dht_bootstrap():
    """Test DHT bootstrap process"""
    server = Server()
    await server.listen(8468)

    bootstrap_nodes = [("router.bittorrent.com", 6881)]
    result = await server.bootstrap(bootstrap_nodes)

    assert result is not None
    server.stop()


@pytest.mark.asyncio
async def test_dht_store_and_retrieve():
    """Test storing and retrieving values from DHT"""
    server1 = Server()
    server2 = Server()

    await server1.listen(8469)
    await server2.listen(8470)

    await server2.bootstrap([("127.0.0.1", 8469)])

    # Store test data
    test_key = b"test_key"
    test_value = b"test_value"
    await server1.set(test_key, test_value)

    # Retrieve test data
    result = await server2.get(test_key)
    assert result == test_value

    server1.stop()
    server2.stop()


@pytest.mark.asyncio
@patch("py_bit_torrent.protocol.client.Server")
async def test_client_dht_integration(mock_server, mock_torrent_file):
    """Test DHT integration with BitTorrent client"""

    # Mock DHT server responses
    mock_server_instance = MagicMock()
    mock_server_instance.listen = asyncio.Future()
    mock_server_instance.listen.set_result(None)
    mock_server_instance.bootstrap = asyncio.Future()
    mock_server_instance.bootstrap.set_result(None)
    mock_server_instance.get = asyncio.Future()
    mock_server_instance.get.set_result([("127.0.0.1", 6881)])

    mock_server.return_value = mock_server_instance

    # Create client instance
    client = bittorrent_client(mock_torrent_file)

    # Test DHT contact
    client.contact_dht()

    assert hasattr(client, "dht_peers_data")
    assert isinstance(client.dht_peers_data["peers"], list)
    assert client.dht_peers_data["interval"] == 1800


@pytest.mark.asyncio
async def test_dht_error_handling():
    """Test DHT error handling"""
    server = Server()

    # Test invalid bootstrap
    with pytest.raises(Exception):
        await server.bootstrap([("invalid.node", 6881)])

    # Test invalid key retrieval
    result = await server.get(b"nonexistent_key")
    assert result is None

    server.stop()
