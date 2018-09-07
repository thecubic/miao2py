#!/usr/bin/env python3

import click
import code
import logging
import time

logging.basicConfig(level=logging.NOTSET)

log = logging.getLogger(__name__)

from miaomiaopy.device import MiaoMiaoDevice
from miaomiaopy.packet import MiaoMiaoPacket


class MiaoMiaoDecoder(MiaoMiaoDevice):
    def handlePacket(self, data):
        self.packet = MiaoMiaoPacket.from_bytes(data)
        super().handlePacket(data)


@click.command()
@click.option("--continuous/--once", default=True, help="continually read the device")
@click.option("--interval", type=float, default=60.0, help="interval to pause between successful attempts (when continuous)")
@click.option("--debug/--no-debug", default=False, help="debugging loglevel")
@click.option("--btfatal/--no-btfatal", default=False, help="make bluetooth problems fatal")
@click.argument("btaddr")
def decode(continuous, interval, debug, btfatal, btaddr):
    if debug:
        logging.root.setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)
    else:
        logging.root.setLevel(logging.INFO)
        log.setLevel(logging.INFO)
    while True:
        with MiaoMiaoDecoder(btaddr, btle_excmask=btfatal) as miaomiao:
            miaomiao.connect()
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
            print(miaomiao.packet)
        if not continuous:
            break
        time.sleep(interval)

if __name__ == "__main__":
    decode()
