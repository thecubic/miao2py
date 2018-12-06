#!/usr/bin/env python3

import click
import logging

from miao2py.mqpub import MiaoMiaoMQPublisher
from bluepy.btle import BTLEException

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


@click.command()
@click.argument("btaddr")
@click.argument("mqurl")
@click.argument("mqtopic")
@click.option("--btfatal/--no-btfatal", default=False, help="make bluetooth problems fatal")
def publish(btaddr, mqurl, mqtopic, btfatal):
    while True:
        with MiaoMiaoMQPublisher(btaddr, mqurl, mqtopic, btle_excmask=btfatal) as miaomiao:
            miaomiao.connect()
            miaomiao.start_notify()
            miaomiao.notify_forever()
        log.debug("new iteration")

if __name__ == "__main__":
    publish()
