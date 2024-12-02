import hashlib
from py_bit_torrent.bencode import bdecode
from py_bit_torrent.torrent import MetaInfoStruct


def parse_torrent(path: str) -> MetaInfoStruct:
    with open(path, "rb") as f:
        data = f.read()
    decoded = bdecode(data)

    x = MetaInfoStruct(decoded)
    pieces = decoded.get("info").get("pieces")
    chunks = []
    sha_pieces = []

    for i in range(0, len(pieces), 20):
        chunk = pieces[i : i + 20]
        sha1 = hashlib.sha1()
        sha1.update(chunk)
        sha_pieces.append(sha1.hexdigest())

    decoded["info"]["pieces"] = sha_pieces
    return MetaInfoStruct(decoded)
