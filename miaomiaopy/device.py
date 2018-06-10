#!/usr/bin/env python3

from bluepy import btle
import logging

log = logging.getLogger(__name__)

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
    STATE_UNKNOWN = 'unknown'
    # oh hai
    STATE_CONNECTED = 'connected'
    # device communicated that a sensor is present, should it start?
    STATE_NEW_SENSOR = 'new-sensor'
    # device communicated that it believes no sensor is near it
    STATE_NO_SENSOR = 'no-sensor'
    # device in normal state, sending us information over BT
    STATE_READING = 'reading'
    # exchange complete - don't call it, it'll call us
    STATE_NOTIFY_WAIT = 'notify-wait'

    client_chars = btle.UUID("00002902-0000-1000-8000-00805f9b34fb")
    nrf_data = btle.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
    nrf_recv =  btle.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
    nrf_xmit = btle.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
    device_name = "miaomiao"

    new_sensor = 0x32
    no_sensor = 0x34
    start_pkt = 0x28
    end_pkt = 0x29

    @classmethod
    def discover(cls, scanner = None, interval = 10):
        found_devices = []
        if not scanner:
            scanner = btle.Scanner()
        devices = scanner.scan(interval)
        for device in devices:
            name = device.getValueText(9)
            if name == 'miaomiao':
                found_devices.append(cls(device.addr))
        return found_devices

    def __init__(self, btaddr):
        self.btaddr = btaddr
        self.pkt_acc = []
        self.state = self.STATE_UNKNOWN

    def __repr__(self):
        return "<{} @ {}>".format(type(self).__name__, self.btaddr)

    def connect(self):
        log.info("connecting to %s", self.btaddr)
        self.device = btle.Peripheral(self.btaddr, 'random')
        self.state = self.STATE_CONNECTED
        log.debug("connection succeeded, defining structure")
        self.gatt = self.device.getServiceByUUID(self.nrf_data)
        self.xmit = self.gatt.getCharacteristics(self.nrf_xmit)[0]
        self.recv = self.gatt.getCharacteristics(self.nrf_recv)[0]
        self.xmit_desc = self.xmit.getDescriptors(self.client_chars)[0]
        log.debug("connection complete")
        self.handleConnect()

    def handleConnect(self):
        pass

    def disconnect(self):
        self.device.disconnect()
        self.handleDisconnect()

    def handleDisconnect(self):
        pass

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
        log.info("requesting notification from device")
        self.xmit_desc.write(bytes([0x01, 0x00]), False)
        self.device.setDelegate(self)
        self.recv.write(bytes([0xf0]))

    def notify_wait(self, delay=1.0):
        log.info("waiting %0.2f for a notification", delay)
        self.device.waitForNotifications(delay)
        self.state = self.STATE_NOTIFY_WAIT

    def notify_forever(self):
        while True:
            self.notify_wait()

    def handlePacket(self, data):
        """i ain't know your life"""
        raise NotImplementedError("you had one job")

    def handleNewSensor(self):
        """when device asks to start tracking a new sensor
           allow it and signal to proceed by returning True
           callers should not proceeed if this returns False
         """
        self.sensor_allow()
        return True

    def handleNoSensor(self):
        """when device is not attached to a Libre, but responding
           this is called and returns True or False as a signal of
           whether the caller should continue
           (e.g. schedule a notification callback)
        """
        return True

    def handleNotification(self, cHandle, data):
        log.debug("notified")
        # log.info("")
        # print(cHandle, len(data), data)
        if not data:
            log.debug("no-data notification")
            return

        if not self.pkt_acc:
            if data[0] == self.new_sensor:
                log.debug("device offers new_sensor")
                self.state = self.STATE_NEW_SENSOR
                if self.handleNewSensor():
                    self.start_data_notify()
            elif data[0] == self.no_sensor:
                log.warning("device believes no sensor")
                self.state = self.STATE_NO_SENSOR
                if self.handleNoSensor():
                    # meh holla
                    self.start_data_notify()
            elif data[0] == self.start_pkt:
                log.info("data packet start")
                self.state = self.STATE_READING
                self.pkt_acc.append(data)
            else:
                log.info("existing_sensor?")
        else:
            log.debug("data continuation")
            self.pkt_acc.append(data)
            if data[-1] == self.end_pkt:
                log.info("likely end packet")
                packet = b''.join(self.pkt_acc)
                self.handlePacket(packet)
                log.info("round complete")
                self.state = self.STATE_NOTIFY_WAIT
