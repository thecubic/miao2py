#!/usr/bin/env python3

import asyncio
import logging

from hbmqtt.client import MQTTClient, ConnectException

from .device import MiaoMiaoDevice

log = logging.getLogger(__name__)


class MiaoMiaoMQPublisher(MiaoMiaoDevice):
    def __init__(self, btaddr, mqurl, mqtopic, *, aioloop=None):
        super().__init__(btaddr)
        self.aioloop = aioloop
        self.mqurl = mqurl
        self.mqtopic = mqtopic
        self.mqclient = MQTTClient()

    def _ensure_aioloop(self):
        """get the event loop here.  we may have been initialized
           in a different thread, hopefully we were called in the
           right one and the default event loop is fine
        """
        if not self.aioloop:
            self.aioloop = asyncio.get_event_loop()

    def handleConnect(self):
        """connect to MQTT when we connect to the actual device"""
        super().handleConnect()
        self._ensure_aioloop()
        self.aioloop.run_until_complete(self.mqclient.connect(self.mqurl))

    def handleDisconnect(self):
        """disconnect from MQTT when we disconnect from the actual device"""
        super().handleDisconnect()
        self._ensure_aioloop()
        self.aioloop.run_until_complete(self.mqclient.disconnect())

    def handlePacket(self, data):
        self._ensure_aioloop()
        self.aioloop.run_until_complete(self.mqclient.publish(self.mqtopic, data))
