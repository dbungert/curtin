import attr

from curtin import config, util

_type_to_cls = {}


@attr.s(auto_attribs=True)
class StorageBaseType:
    id: str
    type: str


def _convert_size(s):
    if isinstance(s, str):
        return int(util.human2bytes(s))
    return s


def asobject(obj):
    cls = _type_to_cls[obj["type"]]
    return config.fromdict(cls, obj)


def size(*, default=attr.NOTHING):
    return attr.ib(converter=_convert_size, default=default)
