#!/usr/bin/env python3

import click
import logging

from miaomiaopy.mqpub import MiaoMiaoMQPublisher
from bluepy.btle import BTLEException

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


@click.command()
@click.argument("btaddr")
@click.argument("mqurl")
@click.argument("mqtopic")
@click.option("--retry", is_flag=True, help="Retry on failures")
def publish(btaddr, mqurl, mqtopic, retry):
    while True:
        try:
            with MiaoMiaoMQPublisher(btaddr, mqurl, mqtopic) as miaomiao:
                miaomiao.start_notify()
                miaomiao.notify_forever()
            log.debug("new iteration")
        except BTLEException as e:
            if not retry:
                raise click.ClickException("connection failure") from e
            else:
                log.exception("connection failure (retrying)")

if __name__ == '__main__':
    publish()
