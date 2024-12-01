from io import BytesIO, SEEK_CUR
from string import digits


END_CHAR = b"e"


def get_int(data: BytesIO, end=END_CHAR) -> int:
    """
    Read until reach the int end char
    """
    value = ""
    byte = data.read(1)  # we need the first number of length

    while byte != end:
        if byte == end:
            break

        value += byte.decode()
        byte = data.read(1)

    return int(value)


def get_string(data: BytesIO) -> bytes:
    """
    Read the length of the string,
    And then read this amount of bytes
    """
    data.seek(-1, SEEK_CUR)
    length = get_int(data, b":")
    value = data.read(length)
    try:
        value = value.decode()
    except UnicodeDecodeError:
        pass

    return value


def get_dict(data) -> dict:
    """
    Read the first key, and then
    iterate over the all the dictionary.
    """
    key: bytes = bdecode(data)
    dictionary = {}
    while key:
        if type(key) == dict:
            for k, v in key.items():
                if k not in dictionary:
                    dictionary[k] = v
        else:
            value = bdecode(data)
            dictionary[key] = value

        key = bdecode(data)

    return dictionary


def get_list(data):
    """
    Read the first value, then
    iterate over all the list values
    """
    values = []
    value = bdecode(data)
    while value:
        values.append(value)
        value = bdecode(data)

    return values


TYPES = {b"i": get_int, b"d": get_dict, b"l": get_list}
TYPES.update({digit.encode(): get_string for digit in digits})


def bdecode(data: bytes) -> bytes | int | dict | list:
    # For the user call
    if isinstance(data, bytes):
        data = BytesIO(data)

    first_char = data.read(1)
    if first_char == END_CHAR:
        return None

    try:
        decoder = TYPES[first_char]
    except:
        raise ValueError("Invalid data type")

    value = decoder(data)
    return value


# Encoders
def with_end(func):
    def inner(*args, **kwargs):
        func(*args, **kwargs)
        stream = args[1]
        stream.write(END_CHAR)

    return inner


def encode_buffer(data: bytes | str, stream):
    if type(data) is str:
        data = data.encode()

    stream.write(str(len(data)).encode())  # Write buffer length
    stream.write(":".encode())  # String seperator
    stream.write(data)  # Write buffer itself


@with_end
def encode_int(data: int, stream: BytesIO):
    stream.write(f"i{str(data)}".encode())


@with_end
def encode_list(data: list, stream: BytesIO):
    stream.write(b"l")
    for item in data:
        bencode(item, stream)


@with_end
def encode_dict(data: dict, stream: BytesIO):
    stream.write(b"d")
    for key, value in data.items():
        bencode(key, stream)
        bencode(value, stream)


ENCODE_TYPES = {
    str: encode_buffer,
    bytes: encode_buffer,
    int: encode_int,
    list: encode_list,
    dict: encode_dict,
}


def bencode(data, stream=None):
    if not stream:
        stream = BytesIO()

    ENCODE_TYPES[type(data)](data, stream)

    return stream.getvalue()


def test_bencode_decode_torrent():
    path = "/home/rafa01/Documents/codes/git-repos/bit-torrent/sample.torrent"
    with open(path, "rb") as f:
        data = f.read()
    decoded = bdecode(data)

    print(decoded)


# test_bencode_decode_torrent()
print(bdecode(b'd8:announce41:http://bttracker.debian.org:6969/announce7:comment35:"Debian CD from cdimage.debian.org"13:creation datei1573903810e9:httpseedsl145:https://cdimage.debian.org/cdimage/release/10.2.0//srv/cdbuilder.debian.org/dst/deb-cd/weekly-builds/amd64/iso-cd/debian-10.2.0-amd64-netinst.iso145:https://cdimage.debian.org/cdimage/archive/10.2.0//srv/cdbuilder.debian.org/dst/deb-cd/weekly-builds/amd64/iso-cd/debian-10.2.0-amd64-netinst.isoe4:infod6:lengthi351272960e4:name31:debian-10.2.0-amd64-netinst.iso12:piece lengthi262144e6:pieces26800:�����PS�^��ee'))
