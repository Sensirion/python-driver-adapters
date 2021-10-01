# -*- coding: utf-8 -*-
# (c) Copyright 2019 Sensirion AG, Switzerland

from __future__ import absolute_import, division, print_function

import time

import pytest
from sensirion_shdlc_driver import ShdlcSerialPort, ShdlcConnection
from sensirion_shdlc_sensorbridge import SensorBridgePort, \
    SensorBridgeShdlcDevice, SensorBridgeI2cProxy

from sensirion_i2c_adapter.i2c_channel import I2cChannel
from sensirion_i2c_adapter.transfer import Transfer, TxData, RxData, execute_transfer
from sensirion_i2c_driver import I2cConnection, CrcCalculator


class StartO2Measurement(Transfer):
    def pack(self):
        return self.tx_data.pack([])

    tx = TxData(0x3603, ">H", device_busy_delay=0.1)


class StopMeasurements(Transfer):
    def pack(self):
        return self.tx_data.pack([])

    tx = TxData(0x3FF9, '>H', device_busy_delay=0.1)


class ReadResults(Transfer):
    def pack(self):
        return None

    rx = RxData(descriptor='>HHH')


class ReadProductIdentifier(Transfer):
    def pack(self):
        return self.tx_data.pack()

    tx = TxData(0xE102, descriptor='>H')
    rx = RxData(descriptor='>IHHH')


@pytest.mark.needs_hardware
def test_command_invocation():
    with ShdlcSerialPort(port='/dev/ttyUSB0', baudrate=460800) as port:
        bridge = SensorBridgeShdlcDevice(ShdlcConnection(port),
                                         slave_address=0)
        print("SensorBridge SN: {}".format(bridge.get_serial_number()))

        # Configure SensorBridge port 1 for SPS6x
        bridge.set_i2c_frequency(SensorBridgePort.ONE, frequency=100e3)
        bridge.set_supply_voltage(SensorBridgePort.ONE, voltage=5.0)
        bridge.switch_supply_on(SensorBridgePort.ONE)

        i2c_transceiver = SensorBridgeI2cProxy(bridge,
                                               port=SensorBridgePort.ONE)
        channel = I2cChannel(I2cConnection(i2c_transceiver),
                             slave_address=0x29,
                             crc=CrcCalculator(8, 0x31, 0xFF, 0x00))

        res = execute_transfer(channel, ReadProductIdentifier())
        print(res)
        start_measurement = StartO2Measurement()
        read_result = ReadResults()
        stop_measurement = StopMeasurements()
        execute_transfer(channel, start_measurement)
        time.sleep(0.5)
        for i in range(100):
            res = execute_transfer(channel, read_result)
            print(res)

        execute_transfer(channel, stop_measurement)
