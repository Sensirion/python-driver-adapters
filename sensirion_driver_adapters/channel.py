# -*- coding: utf-8 -*-
# (c) Copyright 2021 Sensirion AG, Switzerland

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, Iterable, Optional, Tuple, Iterator, Protocol

from sensirion_driver_adapters.rx_tx_data import RxData


@dataclass
class MeasurementPacket:
    timestamp: float
    data: Optional[bytes]


@dataclass
class Measurement:
    stream_id: int  # the id of the stream that produced this measurement
    timestamp: float  # the timestamp of the measurement
    data: Tuple[Any, ...]  # the measurement data


class MeasurementStream(Protocol):

    def open(self) -> Iterator[Measurement]:
        """ Open the stream"""

    def close(self):
        """ Close the stream"""

    def get_stream_id(self) -> int:
        """Return the id of the stream"""

    def __enter__(self) -> MeasurementStream:
        """Enter the streaming context"""

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit the streaming context"""

    def __iter__(self) -> Iterator[Measurement]:
        """Open the stream and return an iterator over the measurements"""

    def __next__(self) -> Measurement:
        """Get the next measurement from the stream"""


class StreamingChannel(Protocol):
    def get_measurement_stream(self, tx_bytes: bytes,
                               payload_offset: int,
                               response: RxData,
                               measurement_interval_us: int,
                               buffered_samples: int = 100,
                               sensor_busy_delay_us: int = 10,
                               repeat_tx_data: bool = False) -> MeasurementStream:
        """Start a measurement stream.

        :param tx_bytes: The command and its parameters to trigger the measurement on the sensor.
        :param payload_offset: The bytes up to the payload_offset represent the command id
        :param response: The response is an object that is able to unpack a raw response.
        :param measurement_interval_us: The interval between two measurements in microseconds.
        :param buffered_samples: The number of samples that shall be buffered.
        :param sensor_busy_delay_us: The number of microseconds between write data tx and read result.
        :param repeat_tx_data: If True, the tx_bytes will be repeated for each measurement until the stream is closed.
            Otherwise, the tx_bytes will be transmitted only once to trigger the measurement.
        :param slave_address: Overwrite the i2c-address of the channel
        """


class TxRxChannel(abc.ABC):
    """
    Defines an abstract base class for bidirectional communication with a sensor device.

    This class provides an interface for transmitting and receiving data with a sensor.
    It also allows streaming measurements, stripping protocol-level data, and enforcing a
    timeout property for communication.

    """

    @abc.abstractmethod
    def write_read(self, tx_bytes: Iterable, payload_offset: int,
                   response: RxData,
                   device_busy_delay: float = 0.0,
                   post_processing_delay: Optional[float] = None,
                   slave_address: Optional[int] = None,
                   ignore_errors: bool = False) -> Optional[Tuple[Any, ...]]:
        """
        Transfers the data to and from a sensor.

        :param tx_bytes:
            Raw bytes to be transmitted
        :param payload_offset:
            The data may contain a header that needs to be left untouched, pushing the date through the protocol stack.
            The Payload offset points to the end of the header and the beginning of the data
        :param response:
            The response is an object that is able to unpack a raw response.
            It has to provide a method 'interpret_response'.
        :param device_busy_delay:
            Indication how long the receiver of the message will be busy until processing of the data has been
            completed.
            Time unit: seconds
        :param post_processing_delay:
            This is the time one has to wait for until the next communication with the device can take place.
            Time unit: seconds
        :param slave_address:
            Used for i2c addressing. Denotes the i2c address of the receiving slave
        :param ignore_errors:
            Some transfers may generate an exception even when they execute properly. In these situations the exception
            is swallowed and an empty result is returned
        :return:
            Return a tuple of the interpreted data or None if there is no response at all
        """
        pass

    @abc.abstractmethod
    def strip_protocol(self, data) -> None:
        """"""
        pass

    @property
    @abc.abstractmethod
    def timeout(self) -> float:
        pass


class AbstractMultiChannel(TxRxChannel):
    """
    This is the base class for any multichannel implementation. A multichannel is used to mimic simultaneous
    communication with several sensors and is used by the MultiDeviceDecorator.
    """

    @property
    @abc.abstractmethod
    def channel_count(self) -> int:
        """return: number of contained channels"""
        raise NotImplementedError()

    def get_channel(self, i: int) -> TxRxChannel:
        """
        Return a specific channel.

        The returned channel my work properly only during the transaction (within the
        with .. block). The exact behaviour is up to the the AbstractMultiChannel implementation.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def __enter__(self) -> "AbstractMultiChannel":
        """
        A MultiChannel is a context manager. The begin and end of the communication over the contained channels is
        marked by the __enter__ and __exit__ method.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Marks the end of the communication over contained channels."""
        raise NotImplementedError()


class TxRxRequest:
    """This class is an adapter to the class I2cConnection. It keeps compatibility with the SensirionI2cCommand"""

    def __init__(self, channel,
                 tx_bytes=None,
                 response=None,
                 device_busy_delay=0.0,
                 post_processing_time=0.0,
                 receive_length=0) -> None:
        self._channel = channel
        self._response = response
        self._tx_data = tx_bytes
        self._device_busy_delay = device_busy_delay
        self._rx_length = receive_length
        self._post_processing_time = post_processing_time

    @property
    def read_delay(self):
        return self._device_busy_delay

    @property
    def tx_data(self):
        return self._tx_data

    @property
    def rx_length(self):
        return self._rx_length

    @property
    def timeout(self):
        return self._channel.timeout

    @property
    def post_processing_time(self):
        """This is the time that has to be waited before the next communication with the sensor can take place.
        """
        if self._post_processing_time is not None:
            return self._post_processing_time
        if self._response is None:
            return self.read_delay
        return 0.0

    def interpret_response(self, data):
        raw_data = self._channel.strip_protocol(data)
        if self._response is not None:
            return self._response.unpack(raw_data)
        return None
