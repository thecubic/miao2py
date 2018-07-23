#!/usr/bin/env python3

import click
import logging

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)

from miaomiaopy.device import MiaoMiaoDevice

class MiaoMiaoDecoder(MiaoMiaoDevice):
    def handlePacket(self, data):
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
            print(f"{btaddr}: device reports no sensor attached")
        elif miaomiao.state == miaomiao.STATE_NEW_SENSOR:
            print(f"{btaddr}: device reports new sensor attached (not allowed)")
        elif miaomiao.state == miaomiao.STATE_SENSOR_READ:
            print(f"{btaddr}: sensor was read")
        else:
            print(f"{btaddr}: It's Complicated")

if __name__ == '__main__':
    decode()
