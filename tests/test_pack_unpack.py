# -*- coding: utf-8 -*-
# (c) Copyright 2022 Sensirion AG, Switzerland

import struct
from typing import Iterable

import pytest

from sensirion_driver_adapters.rx_tx_data import RxData, TxData


@pytest.mark.parametrize("tx, data", [
    (TxData(0xABCD, ">HH"), (1234,)),
    (TxData(0xABCD, ">HH8B"), (1234, [0] * 8)),
    (TxData(0xABCD, ">HH8s"), (1234, "hello")),
    (TxData(0xABCD, ">HH252B"), (1234, [0] * 8)),
    (TxData(0xABCD, ">HH128s"), (1234, "hello world")),
    (TxData(0xABCD, ">HH16I"), (1234, [0] * 8)),
    (TxData(0xABCD, ">HH16f"), (1234, [float(22.7)] * 8)),
    (TxData(0xABCD, ">HH128H"), (1234, [0xFFFF] * 64))

]
                         )
def test_pack(tx: TxData, data):
    def compare_values(v1, v2):
        if isinstance(v1, str):
            return v1 == v2.decode()
        return v1 == v2

    packed = tx.pack(data)
    ref = [tx._cmd_id]
    for d in data:
        if isinstance(d, str):
            ref.append(d)
        elif isinstance(d, Iterable):
            ref.extend(d)
        else:
            ref.append(d)
    descriptor, _ = tx._prepare_pack(data)
    unpacked = list(struct.unpack(descriptor, packed))
    equal = filter(lambda x: compare_values(x[0], x[1]), zip(ref, unpacked))
    assert all(equal)


@pytest.mark.parametrize("rx, data", [(RxData(">HH"), (0xABCD, 1234,))])
def test_unpack(rx: RxData, data):
    packed = struct.pack(rx._descriptor, *data)
    unpacked = rx.unpack(packed)
    not_equal = filter(lambda x: x[0] != x[1], zip(data, unpacked))
    assert not any(not_equal)


@pytest.mark.parametrize("rx, data", [(RxData(">HH"), (0xABCD, 1234)),
                                      (RxData(">HH8B"), (0xABCD, 1234, (1, 2, 3, 4, 5, 6, 7, 8))),
                                      (RxData(">I16s"), (0xABCD, 'hello world'))])
def test_dynamic_unpack(rx: RxData, data):
    to_pack = []
    for d in data:
        if isinstance(d, str):
            to_pack.append(d.encode())
        elif isinstance(d, Iterable):
            to_pack.extend(d)
        else:
            to_pack.append(d)
    packed = struct.pack(rx._descriptor, *to_pack)
    unpacked = rx.unpack_dynamic_sized(packed)
    all_received = []
    for received_data in unpacked:
        if isinstance(received_data, bytes):
            all_received.append(received_data.decode())
        else:
            all_received.append(received_data)
    not_equal = filter(lambda x: x[0] != x[1], zip(data, all_received))

    assert not any(not_equal)
