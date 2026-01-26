# -*- coding: utf-8 -*-
# (c) Copyright 2026 Sensirion AG, Switzerland
import logging
from typing import Any, Optional, Tuple, Callable, Iterable

from sensirion_driver_adapters.channel import StreamingChannel, TxRxChannel, MeasurementStream
from sensirion_driver_adapters.i2c_adapter.i2c_channel import I2cChannel
from sensirion_driver_adapters.rx_tx_data import RxData

log = logging.getLogger(__name__)


class I2cStreamingChannel(StreamingChannel, TxRxChannel):
    def __init__(self,
                 create_measurement_stream: Callable[[bytes,
                                                      int,
                                                      RxData,
                                                      int,
                                                      int,
                                                      int,
                                                      bool], MeasurementStream],
                 i2c_channel: I2cChannel) -> None:
        self._i2_channel = i2c_channel
        self._create_measurement_stream = create_measurement_stream

    def get_measurement_stream(self, tx_bytes: bytes,
                               payload_offset: int,
                               response: RxData,
                               measurement_interval_us: int,
                               buffered_samples: int = 100,
                               sensor_busy_delay_us: int = 10,
                               repeat_tx_data: bool = False) -> MeasurementStream:
        measurement_stream = self._create_measurement_stream(tx_bytes,
                                                             payload_offset,
                                                             response,
                                                             measurement_interval_us,
                                                             buffered_samples,
                                                             sensor_busy_delay_us,
                                                             repeat_tx_data)
        return measurement_stream

    def write_read(self, tx_bytes: Iterable, payload_offset: int,
                   response: RxData,
                   device_busy_delay: float = 0.0,
                   post_processing_delay: Optional[float] = None,
                   slave_address: Optional[int] = None,
                   ignore_errors: bool = False) -> Optional[Tuple[Any, ...]]:
        return self._i2_channel.write_read(tx_bytes, payload_offset, response, device_busy_delay,
                                           post_processing_delay, slave_address, ignore_errors)

    def strip_protocol(self, data) -> None:
        """"""
        self._i2_channel.strip_protocol(data)

    def timeout(self) -> float:
        return self._i2_channel.timeout
