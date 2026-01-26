# -*- coding: utf-8 -*-
# (c) Copyright 2023 Sensirion AG, Switzerland

import time
from datetime import datetime, timezone
from functools import partial
from typing import Optional, Tuple, Iterator, List

from sensirion_i2c_driver import I2cConnection
from sensirion_i2c_driver.errors import I2cChecksumError
from sensirion_shdlc_driver import ShdlcSerialPort, ShdlcConnection
from sensirion_shdlc_sensorbridge import (SensorBridgePort,
                                          SensorBridgeShdlcDevice,
                                          SensorBridgeI2cProxy)
from sensirion_shdlc_sensorbridge.device import ReadBufferResponse, RepeatedTransceiveHandle

from sensirion_driver_adapters.channel import TxRxChannel, MeasurementStream, Measurement
from sensirion_driver_adapters.channel_provider import I2cChannelProvider
from sensirion_driver_adapters.i2c_adapter.i2c_channel import I2cChannel, RxData
from sensirion_driver_adapters.i2c_adapter.i2c_streaming_channel import I2cStreamingChannel


class SensorBridgeMeasurementStream(MeasurementStream):
    def __init__(self, sensor_bridge: SensorBridgeShdlcDevice,
                 sensor_bridge_port: SensorBridgePort,
                 channel: I2cChannel,
                 tx_bytes: bytes,
                 payload_offset: int,
                 response: RxData,
                 measurement_interval_us: int,
                 buffered_samples: int = 100,
                 sensor_busy_delay_us: int = 10):
        self._tx_bytes = tx_bytes
        self._payload_offset = payload_offset
        self._response_descriptor = response
        self._measurement_interval_us = measurement_interval_us
        self._buffered_samples = buffered_samples
        self._sensor_busy_delay_us = sensor_busy_delay_us
        self._channel = channel
        self._i2c_address = channel._slave_address  # noqa: protected-access
        self._sensor_bridge_port = sensor_bridge_port
        self._sensor_bridge = sensor_bridge
        self._rx_length = response.rx_length * 3 // 2
        self._handle: Optional[RepeatedTransceiveHandle] = None
        self._start_time = datetime.now(tz=timezone.utc).timestamp()
        self._stream_iterator = None

    def open(self) -> MeasurementStream:
        self._handle: RepeatedTransceiveHandle = self._sensor_bridge.start_repeated_i2c_transceive(
            self._sensor_bridge_port,
            self._measurement_interval_us,
            self._i2c_address,
            self._tx_bytes,
            self._rx_length,
            timeout_us=1000,
            read_delay_us=self._sensor_busy_delay_us)
        self._start_time = datetime.now(tz=timezone.utc).timestamp()
        time.sleep(self._buffered_samples * self._measurement_interval_us / 1000000)
        return self

    def close(self) -> None:
        print("closing stream")
        if self._handle is not None:
            self._sensor_bridge.stop_repeated_i2c_transceive(self._handle)
            self._handle = None
            self._stream_iterator = None

    def __enter__(self) -> MeasurementStream:
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.close()
            self._stream_iterator = None
            return False
        except Exception:  # noqa
            return True

    def __iter__(self) -> Iterator[Measurement]:
        self._stream_iterator = self.get_next_measurement()
        return self

    def __next__(self) -> Measurement:
        assert self._stream_iterator is not None, "Illegal state: Stream iterator is None!"
        return next(self._stream_iterator)

    def get_next_measurement(self) -> Iterator[Measurement]:
        def handle_buffer_response(response: ReadBufferResponse) -> List[Optional[bytes]]:
            lost_packets = response.lost_bytes % self._rx_length
            measurement_data = [None for _ in range(lost_packets)]
            measurement_data += [None if d.error else d.data for d in response.values]
            return measurement_data

        interval_s = self._measurement_interval_us / 1_000_000
        while self._handle is not None:
            buffer_response: ReadBufferResponse = self._sensor_bridge.read_buffer(self._handle)
            receive_time = datetime.now(tz=timezone.utc).timestamp()
            measurements = handle_buffer_response(buffer_response)
            computed_interval_s = interval_s
            if len(measurements) > 0:
                computed_interval_s = (receive_time - self._start_time) / len(measurements)
            effective_measurement_interval = min(interval_s,
                                                 computed_interval_s)  # shrink but to not extend the interval
            start_time = self._start_time
            for data in measurements:
                unpacked_data = None
                if data is not None:
                    try:
                        unpacked_data = self._channel.strip_protocol(data)
                    except I2cChecksumError:  # errors are reported the same way as lost packets
                        ...
                yield Measurement(stream_id=self._handle.raw_handle,
                                  timestamp=start_time,
                                  data=None if data is None else self._response_descriptor.unpack(unpacked_data))
                start_time += effective_measurement_interval
            new_start_time = datetime.now(tz=timezone.utc).timestamp()
            start_time = min(start_time, new_start_time)  # measurements must not be in the future
            next_receive_time = receive_time + effective_measurement_interval * self._buffered_samples
            sleep_time = max(0.0, (next_receive_time - new_start_time))
            if sleep_time > 1.0:
                time.sleep(sleep_time)
            self._start_time = start_time


class SensorBridgeI2cChannelProvider(I2cChannelProvider):
    """Create a channel that is using a I2cConnection to communicate with a sensor over the SensorBridgeShdlcDevice."""

    def __init__(self, sensor_bridge_port: SensorBridgePort,
                 serial_port: str,
                 serial_baud_rate: int,
                 *args, **kwargs):
        """
        Initialize additional members for sensor bridge channel.

        :param sensor_bridge_port:
            The port of the sensor bridge where the sensor is attached
        :param serial_port:
            The serial port or serial device that is used by a programming device that uses the serial interface
        :param serial_baud_rate:
            The baud rate that can be applied on the serial line used by a programming device that uses the serial
            interface.
        """
        super().__init__(*args, **kwargs)
        self._sensor_bridge_port: SensorBridgePort = sensor_bridge_port
        self.serial_port = serial_port
        self.serial_baud_rate = serial_baud_rate
        self._shdlc_port: Optional[ShdlcSerialPort] = None
        self._sensor_bridge: Optional[SensorBridgeShdlcDevice] = None
        self._i2c_transceiver: Optional[SensorBridgeI2cProxy] = None
        self._streams: List[SensorBridgeMeasurementStream] = []

    def release_channel_resources(self):
        """
        Free up all resources that where acquired when initializing the channel:
            - switch off power
            - release serial connection
        """
        if self._sensor_bridge is None:
            return
        for stream in self._streams:
            stream.close()
        self._streams.clear()
        assert self._sensor_bridge_port is not None, "Illegal state: SensorBridgePort is None!"
        assert self._shdlc_port is not None, "Illegal state: Shdlc port is None!"
        self._sensor_bridge.switch_supply_off(self._sensor_bridge_port)
        self._shdlc_port.close()
        self._shdlc_port = None

    def prepare_channel(self):
        """Initialize a concrete channel object that can be used to create a new sensor instance."""
        self._shdlc_port = ShdlcSerialPort(port=self.serial_port, baudrate=self.serial_baud_rate)
        self._sensor_bridge = SensorBridgeShdlcDevice(connection=ShdlcConnection(self._shdlc_port),
                                                      slave_address=0)
        self._sensor_bridge.set_i2c_frequency(self._sensor_bridge_port, frequency=self.i2c_frequency)
        self._sensor_bridge.set_supply_voltage(self._sensor_bridge_port, voltage=self.supply_voltage)
        self._sensor_bridge.switch_supply_on(self._sensor_bridge_port)
        self._i2c_transceiver = SensorBridgeI2cProxy(self._sensor_bridge, port=self._sensor_bridge_port)
        time.sleep(0.1)

    def get_channel(self, slave_address: int,
                    crc_parameters: Tuple[int, int, int, int]) -> TxRxChannel:
        """
        Create and return an initialized channel based on an I2cConnection.

        The channel provider can return several channels with different channel parameters. This is needed in case
        more than one sensor is attached on the same bus.

        :param slave_address:
            The i2c address where the sensor is attached
        :param crc_parameters:
            The crc calculator that can compute the crc checksum of the byte stream
        """

        i2c_channel = I2cChannel(I2cConnection(self._i2c_transceiver),
                                 slave_address=slave_address,
                                 crc=self.try_create_crc_calculator(crc_parameters))
        channel = I2cStreamingChannel(
            partial(self._create_measurement_stream, i2c_channel),
            i2c_channel=i2c_channel)
        return channel

    def _create_measurement_stream(self, i2c_channel: I2cChannel,
                                   tx_bytes: bytes,
                                   payload_offset: int,
                                   response: RxData,
                                   measurement_interval_us: int,
                                   buffered_samples: int = 100,
                                   sensor_busy_delay_us: int = 10,
                                   _: bool = False
                                   ) -> MeasurementStream:
        stream = SensorBridgeMeasurementStream(self._sensor_bridge,
                                               self._sensor_bridge_port,
                                               i2c_channel,
                                               tx_bytes,
                                               payload_offset,
                                               response,
                                               measurement_interval_us,
                                               buffered_samples,
                                               sensor_busy_delay_us)
        self._streams.append(stream)
        return stream
