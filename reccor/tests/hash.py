import io
import pytest

from reccor.modules.hash import Module


def test_read():

    module = Module()
    record = module.read(name="1", data=io.BytesIO(bytes("123", 'ascii')))

    assert record.attributes is not None
    assert "hash" in record.attributes
    assert isinstance(record.attributes["hash"], bytes) and len(record.attributes["hash"]) != 0


@pytest.mark.parametrize("hash_function", ["sha256", "sha384", "md5", "sha1"])
def test_compare(hash_function):
    module = Module(config={"hash": hash_function})
    data = [
        module.read(name="1", data=io.BytesIO(bytes("123", 'ascii'))),
        module.read(name="2", data=io.BytesIO(bytes("def", 'ascii'))),
        module.read(name="3", data=io.BytesIO(bytes(".,-", 'ascii'))),
    ]

    for i in range(3):
        for j in range(3):
            if i == j:
                assert module.compare(data[i], data[j])
            else:
                assert not module.compare(data[i], data[j])


@pytest.mark.parametrize("hash_function", ["sha256", "sha384", "md5", "sha1"])
def test_process(hash_function):
    module = Module(config={"hash": hash_function})
    data = [
        module.read(name="1", data=io.BytesIO(bytes("123", 'ascii'))),
        module.read(name="2", data=io.BytesIO(bytes("123", 'ascii'))),
    ]
    assert module.process(r1=data[0], r2=data[1]).name == "1"
