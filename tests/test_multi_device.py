# -*- coding: utf-8 -*-
# (c) Copyright 2021 Sensirion AG, Switzerland

import i2c_device_mocks as mocks
from sensirion_driver_adapters.multi_device_support import multi_driver


@multi_driver(mocks.DummyDriver)
class MultiDummyDriver:
    ...


@multi_driver(mocks.DummyDriver, execute_concurrent=True)
class ParallelDummyDriver:
    ...


@multi_driver(mocks.DummyDriver, execute_concurrent=True)
class ParallelDummyDriverWithInit:
    """This is possible but it is not encouraged. Note that the **_ argument is required"""

    def __init__(self, test_str, **_) -> None:
        self._test_str = test_str

    def do_something(self):
        print(self._test_str)
        self.invoke_command(50, 10)
        print("done")


def test_multi_sensor():
    driver = MultiDummyDriver(mocks.create_multi_channel(nr_of_channels=4,
                                                         i2c_address=0x59,
                                                         cmd_width=2,
                                                         crc=(8, 0x31, 0xFF, 0)))
    driver.invoke_command(50, 10)


def test_parallel_multi_sensor():
    driver = ParallelDummyDriver(mocks.create_multi_channel(nr_of_channels=4,
                                                            i2c_address=0x59,
                                                            cmd_width=2,
                                                            crc=(8, 0x31, 0xFF, 0)))
    driver.invoke_command(50, 10)


def test_parallel_multi_sensor_with_init():
    driver = ParallelDummyDriverWithInit(channel=mocks.create_multi_channel(nr_of_channels=4,
                                                                            i2c_address=0x59,
                                                                            cmd_width=2,
                                                                            crc=(8, 0x31, 0xFF, 0)),
                                         test_str="hello")
    driver.invoke_command(50, 10)
    driver.do_something()
