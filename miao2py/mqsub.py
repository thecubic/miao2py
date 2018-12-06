#!/usr/bin/env python3

import asyncio
import logging

from hbmqtt.client import MQTTClient, ConnectException

log = logging.getLogger(__name__)


class MiaoMiaoMQSubscriber:
    def __init__(self, mqurl, mqtopic, *, aioloop=None):
        super().__init__(btaddr)
        self.aioloop = aioloop
        self.mqurl = mqurl
        self.mqtopic = mqtopic
        self.mqclient = MQTTClient()

    async def subscriber(self):
        await self.mqclient.connect(self.mqurl)
        await self.mqclient.subscribe([self.mqtopic])
        async for message in self.mqclient.deliver_message():
            yield message

    async def disconnect(self):
        await self.mqclient.disconnect()

    def handleMessage(self, message):
        print("message:", message)
