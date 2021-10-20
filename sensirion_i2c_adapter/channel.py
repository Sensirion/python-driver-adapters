# -*- coding: utf-8 -*-
# (c) Copyright 2021 Sensirion AG, Switzerland

import abc


class TxRxChannel(abc.ABC):
    """This is the abstract base class for any channel. A channel is a transportation medium to transfer data from any
    source to any destination"""

    @abc.abstractmethod
    def write_read(self, tx_data, payload_offset, response, device_busy_delay=0.0, slave_address=None,
                   ignore_errors=False):
        """
        transfers the data to and fr
        :param tx_data:
            Raw bytes to be transmitted
        :param payload_offset:
            The data my contain a header that needs to be left untouched, pushing the date through the protocol stack.
            The Payload offset points to the end of the header and the beginning of the data
        :param response:
            The response is an object that is able to unpack a raw response.
            It has to provide a method 'interpret_response.
        :param device_busy_delay:
            Indication how long the receiver of the message will be busy until processing of the data has been
            completed.
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
    def strip_protocol(self, data):
        """"""
        pass

    @property
    @abc.abstractmethod
    def timeout(self):
        pass


class TxRxRequest:
    """This class is an adapter to the class I2cConnection. It keeps compatibility with the SensirionI2cCommand"""

    def __init__(self, channel, tx_data=None, response=None, device_busy_delay=0.0, receive_length=0):
        self._channel = channel
        self._response = response
        self._tx_data = tx_data
        self._device_busy_delay = device_busy_delay
        self._rx_length = receive_length

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
        if self._response is None:
            return self.read_delay
        return 0

    def interpret_response(self, data):
        raw_data = self._channel.strip_protocol(data)
        if self._response is not None:
            return self._response.unpack(raw_data)
        return None
