#!/usr/bin/env python3

import click

from miao2py.device import MiaoMiaoScanner
from bluepy import btle


@click.command()
@click.option(
    "--iface", type=int, default=0, help="BT interface index to use (e.g. hci0 -> 0)"
)
@click.option("--interval", type=int, default=1, help="BT scanning interval")
@click.option("--continuous", is_flag=True, help="Scan continuously")
def scan(iface, interval, continuous):
    delegate = MiaoMiaoScanner()
    scanner = btle.Scanner(iface).withDelegate(delegate)
    while True:
        device = scanner.scan(interval)
        if not continuous:
            break


if __name__ == "__main__":
    scan()
