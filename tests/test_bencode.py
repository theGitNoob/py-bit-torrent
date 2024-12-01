from bit_torrent.bencode import bencode, bdecode


def test_bencode_int():
    assert bencode(42) == b"i42e"
    assert bencode(-42) == b"i-42e"
    assert bencode(0) == b"i0e"


def test_bencode_bytes():
    assert bencode(b"spam") == b"4:spam"
    assert bencode(b"") == b"0:"


def test_bencode_str():
    assert bencode("spam") == b"4:spam"
    assert bencode("") == b"0:"


def test_bencode_list():
    assert bencode([1, 2, 3]) == b"li1ei2ei3ee"
    assert bencode(["spam", "eggs"]) == b"l4:spam4:eggse"
    assert bencode([]) == b"le"


def test_bencode_dict():
    assert bencode({"spam": "eggs"}) == b"d4:spam4:eggse"
    assert bencode({"a": 1, "b": 2}) == b"d1:ai1e1:bi2ee"
    assert bencode({}) == b"de"


def test_bdecode_int():
    assert bdecode(b"i42e") == 42
    assert bdecode(b"i-42e") == -42
    assert bdecode(b"i0e") == 0


def test_bdecode_bytes():
    assert bdecode(b"4:spam") == "spam"
    assert bdecode(b"0:") == ""


def test_bdecode_str():
    assert bdecode(b"4:spam") == "spam"
    assert bdecode(b"0:") == ""


def test_bdecode_list():
    assert bdecode(b"li1ei2ei3ee") == [1, 2, 3]
    assert bdecode(b"l4:spam4:eggse") == ["spam", "eggs"]
    assert bdecode(b"le") == []


def test_bdecode_dict():
    assert bdecode(b"d1:ai1e1:bi2ee") == {"a": 1, "b": 2}
    assert bdecode(b"de") == {}


def test_bencode_bdecode():
    assert bdecode(bencode(42)) == 42
    assert bdecode(bencode("spam")) == "spam"
    assert bdecode(bencode([1, 2, 3])) == [1, 2, 3]
    assert bdecode(bencode({"spam": "eggs"})) == {"spam": "eggs"}
