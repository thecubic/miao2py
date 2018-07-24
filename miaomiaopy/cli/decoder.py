#!/usr/bin/env python3

import click
import logging
import code

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)

from miaomiaopy.device import MiaoMiaoDevice
from miaomiaopy.packet import MiaoMiaoPacket


class MiaoMiaoDecoder(MiaoMiaoDevice):
    def handlePacket(self, data):
        self.packet = MiaoMiaoPacket.from_bytes(data)
        super().handlePacket(data)


@click.command()
@click.argument("btaddr")
def decode(btaddr):
    with MiaoMiaoDecoder(btaddr) as miaomiao:
        miaomiao.start_notify()
        miaomiao.notify_wait()

        while miaomiao.state == miaomiao.STATE_READING:
            miaomiao.notify_wait()

        log.debug("device ended in state: %s", miaomiao.state)
        if miaomiao.state == miaomiao.STATE_NO_SENSOR:
            print("{}: device reports no sensor attached".format(btaddr))
        elif miaomiao.state == miaomiao.STATE_NEW_SENSOR:
            print("{}: device reports new sensor attached (not allowed)".format(btaddr))
        elif miaomiao.state == miaomiao.STATE_SENSOR_READ:
            print("{}: sensor was read".format(btaddr))
        else:
            print("{}: It's Complicated".format(btaddr))
        code.interact(local=dict(globals(), **locals()))


if __name__ == "__main__":
    decode()
