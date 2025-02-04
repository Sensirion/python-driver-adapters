# -*- coding: utf-8 -*-
# (c) Copyright 2021 Sensirion AG, Switzerland
import time

import pytest
from sensirion_i2c_driver.crc_calculator import CrcCalculator

from sensirion_driver_adapters.channel import AbstractMultiChannel
from sensirion_driver_adapters.multi_device_support import multi_driver
from sensirion_driver_adapters.multi_sensor_bridge import Config, UsedPorts, I2cMultiSensorBridgeConnection
from sensirion_driver_adapters.transfer import Transfer, execute_transfer
from sensirion_driver_adapters.rx_tx_data import RxData, TxData


class ExecuteSelfTest(Transfer):
    CMD_ID = 0x280e

    def pack(self):
        return self.tx_data.pack([])

    tx = TxData(CMD_ID, '>H', device_busy_delay=0.32, slave_address=None, ignore_ack=False)
    rx = RxData('>H')


class MiniSgp:
    def __init__(self, channel) -> None:
        self._channel = channel

    def execute_self_test(self):
        transfer = ExecuteSelfTest()
        return execute_transfer(self._channel, transfer)[0]

    @property
    def channel(self):
        return self._channel


@multi_driver(MiniSgp, execute_concurrent=True)
class MultiMiniSgp:
    ...


@pytest.mark.needs_hardware
def test_multi_sensor_bridge_one_device():
    with I2cMultiSensorBridgeConnection(config_list=(Config(serial_port='COM4', ports=UsedPorts.ALL),),
                                        baud_rate=460800,
                                        voltage=3.3,
                                        i2c_frequency=100000) as multi_device:
        try:
            channel = multi_device.get_multi_channel(0x29, CrcCalculator(8, 0x31, 0xFF, 0))
            assert isinstance(channel, AbstractMultiChannel)
            assert channel.channel_count == 2
        finally:
            multi_device.switch_supply_off()


@pytest.mark.needs_hardware
def test_multi_sensor_bridge_two_devices():
    with I2cMultiSensorBridgeConnection(config_list=(Config(serial_port='COM4', ports=UsedPorts.ALL),
                                                     Config(serial_port='COM14', ports=UsedPorts.ALL)),
                                        baud_rate=460800,
                                        voltage=3.3,
                                        i2c_frequency=100000) as multi_device:
        try:
            channel = multi_device.get_multi_channel(0x29, CrcCalculator(8, 0x31, 0xFF, 0))
            assert isinstance(channel, AbstractMultiChannel)
            channel.channel_count == 4
        finally:
            multi_device.switch_supply_off()


@pytest.mark.needs_hardware
def test_multi_sensor_bridge_2_devices_2_channel():
    with I2cMultiSensorBridgeConnection(config_list=(Config(serial_port='COM4', ports=UsedPorts.PORT_1),
                                                     Config(serial_port='COM14', ports=UsedPorts.PORT_1)),
                                        baud_rate=460800,
                                        voltage=3.3,
                                        i2c_frequency=100000) as multi_device:
        try:
            channel = multi_device.get_multi_channel(0x59, CrcCalculator(8, 0x31, 0xFF, 0))
            time.sleep(0.5)
            assert isinstance(channel, AbstractMultiChannel)
            channel.channel_count == 2
            multi_sensor = MultiMiniSgp(channel)
            results = multi_sensor.execute_self_test()
            assert len(results) == 2
        finally:
            multi_device.switch_supply_off()


@pytest.mark.needs_hardware
def test_multi_sensor_bridge_2_devices_4_channel():
    with I2cMultiSensorBridgeConnection(config_list=(Config(serial_port='COM4', ports=UsedPorts.ALL),
                                                     Config(serial_port='COM14', ports=UsedPorts.ALL)),
                                        baud_rate=460800,
                                        voltage=3.3,
                                        i2c_frequency=100000) as multi_device:
        try:
            channel = multi_device.get_multi_channel(0x59, CrcCalculator(8, 0x31, 0xFF, 0))
            time.sleep(0.5)
            assert isinstance(channel, AbstractMultiChannel)
            channel.channel_count == 4
            multi_sensor = MultiMiniSgp(channel)
            results = multi_sensor.execute_self_test()
            assert len(results) == 4
        finally:
            multi_device.switch_supply_off()
