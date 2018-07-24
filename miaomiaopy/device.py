#!/usr/bin/env python3

from bluepy import btle
import logging

log = logging.getLogger(__name__)


class MiaoMiaoScanner(btle.DefaultDelegate):
    def __init__(self, sensitivity=False):
        super().__init__()
        self.miaomiaos = {}
        self.sensitivity = sensitivity

    def handleDiscovery(self, scanentry, is_new, is_new_data):
        if self.sensitivity and scanentry.rssi < self.sensitivity:
            return
        if not self.is_miaomiao(scanentry):
            return
        if scanentry.addr in self.miaomiaos:
            # not new
            ...
        else:
            ...
            self.miaomiaos[scanentry.addr] = scanentry
        print("{} {} dBm".format(scanentry.addr, scanentry.rssi))

    @staticmethod
    def is_miaomiao(scanentry):
        return scanentry.getValueText(9) == "miaomiao"


class MiaoMiaoDevice(btle.DefaultDelegate):
    """Interacts with a miaomiao reader over Bluetooth, yielding
       raw packets usually containing a Libre payload

       usage:

       class MMPacketPrinter(MiaoMiaoDevice):
           def handlePacket(self, data):
               print(data)

       miaomiao = MMPacketPrinter(bt_address)
       try:
           miaomiao.connect()
           miaomiao.start_notify()
           miaomiao.notify_forever()
        except btle.BTLEException:
           print('such is the nature of things')
    """

    # ain't even tried to talk to it yet
    STATE_DISCONNECTED = "disconnected"
    # oh hai
    STATE_CONNECTED = "connected"
    # device communicated that a sensor is present, should it start?
    STATE_NEW_SENSOR = "new-sensor"
    # device communicated that it believes no sensor is near it
    STATE_NO_SENSOR = "no-sensor"
    # device in normal state, sending us information over BT
    STATE_READING = "reading"
    # notification requested
    STATE_NOTIFY_REQ = "notify-requested"
    # waiting on notification callback
    STATE_NOTIFY_WAIT = "notify-wait"
    # reading completed
    STATE_SENSOR_READ = "sensor-read"

    notification_delay = 2.0

    client_chars = btle.UUID("00002902-0000-1000-8000-00805f9b34fb")
    nrf_data = btle.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
    nrf_recv = btle.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
    nrf_xmit = btle.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
    device_name = "miaomiao"

    new_sensor = 0x32
    no_sensor = 0x34
    start_pkt = 0x28
    end_pkt = 0x29

    @classmethod
    def discover(cls, scanner=None, interval=10):
        found_devices = []
        if not scanner:
            scanner = btle.Scanner()
        devices = scanner.scan(interval)
        for device in devices:
            name = device.getValueText(9)
            if name == cls.device_name:
                found_devices.append(cls(device.addr))
        return found_devices

    def __init__(self, btaddr):
        super().__init__()
        self.btaddr = btaddr
        self.pkt_acc = []
        self.state = self.STATE_DISCONNECTED

    def __repr__(self):
        return "<{} @ {}>".format(type(self).__name__, self.btaddr)

    def connect(self):
        log.debug("connecting to %s", self.btaddr)
        self.device = btle.Peripheral(self.btaddr, "random")
        self.gatt = self.device.getServiceByUUID(self.nrf_data)
        self.xmit = self.gatt.getCharacteristics(self.nrf_xmit)[0]
        self.recv = self.gatt.getCharacteristics(self.nrf_recv)[0]
        self.xmit_desc = self.xmit.getDescriptors(self.client_chars)[0]
        self.handleConnect()

    def handleConnect(self):
        log.debug("connected")
        self._state_transition(self.STATE_CONNECTED)

    def disconnect(self):
        self.device.disconnect()
        self.handleDisconnect()

    def handleDisconnect(self):
        log.debug("disconnected")
        self._state_transition(self.STATE_DISCONNECTED)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()

    def sensor_allow(self):
        log.debug("-> allow sensor")
        self.recv.write(bytes([0xd3, 0x01]))

    def start_data_notify(self):
        log.debug("-> begin reading")
        self.recv.write(bytes([0xf0]))

    def start_notify(self):
        log.debug("requesting notification from device")
        self.xmit_desc.write(bytes([0x01, 0x00]), False)
        self.device.setDelegate(self)
        self.recv.write(bytes([0xf0]))
        self._state_transition(self.STATE_NOTIFY_REQ)

    def notify_wait(self, delay=None):
        delay = delay or self.notification_delay
        log.debug("waiting %0.2f for a notification", delay)
        self._state_transition(self.STATE_NOTIFY_WAIT)
        self.device.waitForNotifications(delay)

    def notify_forever(self):
        while True:
            self.notify_wait()
            log.debug("moving to next round")

    def handlePacket(self, data):
        """Override this for application data handling"""
        self._state_transition(self.STATE_SENSOR_READ)

    def handleNewSensor(self, allow=False):
        log.debug("device offers new_sensor")
        if allow:
            log.debug("allowing new sensor")
            self.sensor_allow()
        self._state_transition(self.STATE_NEW_SENSOR)

    def handleNoSensor(self):
        """when device is not attached to a Libre, but responding
           this is called and returns True or False as a signal of
           whether the caller should continue
           (e.g. schedule a notification callback)
        """
        log.debug("device believes no sensor")
        self._state_transition(self.STATE_NO_SENSOR)

    def _state_transition(self, newstate):
        log.debug("%s -> %s", self.state, newstate)
        self.state = newstate

    def handleNotification(self, cHandle, data):
        self._state_transition(self.STATE_READING)
        if not data:
            log.debug("no-data notification")
            return

        if not self.pkt_acc:
            if data[0] == self.new_sensor:
                self.handleNewSensor(allow=True)
            elif data[0] == self.no_sensor:
                self.handleNoSensor()
            elif data[0] == self.start_pkt:
                log.debug("data packet start")
                self._state_transition(self.STATE_READING)
                self.pkt_acc.append(data)
            else:
                log.debug("existing_sensor?")
        else:
            log.debug("data continuation")
            self.pkt_acc.append(data)
            if data[-1] == self.end_pkt:
                log.debug("end packet")
                packet = b"".join(self.pkt_acc)
                self.handlePacket(packet)
        log.debug("leaving handleNotification in state %s", self.state)
