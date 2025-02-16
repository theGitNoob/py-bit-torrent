import asyncio
import pytest

from py_bit_torrent.protocol.kademlia.network import Server
from py_bit_torrent.protocol.kademlia.utils import digest
import bencodepy


@pytest.mark.asyncio
async def test_file_sharing():
    # Create 3 server instances with different ports
    server1 = Server()
    server2 = Server()
    server3 = Server()

    # Start listening on different ports
    await server1.listen(8467)
    await server2.listen(8468)
    await server3.listen(8469)

    # Bootstrap server2 and server3 with server1's address
    await server2.bootstrap([("127.0.0.1", 8467)])
    await server3.bootstrap([("127.0.0.1", 8467)])

    # Wait for routing tables to be populated
    await asyncio.sleep(1)

    # Create a sample file content
    file_content = {
        "filename": "test.txt",
        "size": 1024,
        "pieces": ["piece1hash", "piece2hash"],
        "piece_length": 512,
    }

    # Server1 sets the file metadata in bencode format
    # This is a placeholder for the actual bencode encoding
    # In a real scenario, you would use a bencode library to encode the data
    file_content_bencoded = bencodepy.encode(file_content)
    file_key = "test_file_key"
    await server1.set(file_key, file_content_bencoded)

    # Wait for value propagation
    await asyncio.sleep(1)

    # Server2 tries to get the file metadata
    result2 = await server2.get(file_key)
    assert result2 == file_content_bencoded

    # Server3 tries to get the file metadata
    result3 = await server3.get(file_key)
    assert result3 == file_content_bencoded

    # Test with binary key (digest)
    binary_key = "test_binary_key"
    binary_value = b"Hello, Binary World!"

    # Set using binary key
    await server2.set(binary_key, binary_value)
    await asyncio.sleep(1)

    # Get using binary key from different servers
    result1 = await server1.get(binary_key)
    result3 = await server3.get(binary_key)

    assert result1 == binary_value
    assert result3 == binary_value

    # Clean up
    server1.stop()
    server2.stop()
    server3.stop()
    await asyncio.sleep(0.1)  # Allow servers to properly shut down
