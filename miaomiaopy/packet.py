#!/usr/bin/env python3

import struct
import logging
import datetime
from binascii import hexlify

log = logging.getLogger(__name__)


class crc16:
    table = [
        0,
        4489,
        8978,
        12955,
        17956,
        22445,
        25910,
        29887,
        35912,
        40385,
        44890,
        48851,
        51820,
        56293,
        59774,
        63735,
        4225,
        264,
        13203,
        8730,
        22181,
        18220,
        30135,
        25662,
        40137,
        36160,
        49115,
        44626,
        56045,
        52068,
        63999,
        59510,
        8450,
        12427,
        528,
        5017,
        26406,
        30383,
        17460,
        21949,
        44362,
        48323,
        36440,
        40913,
        60270,
        64231,
        51324,
        55797,
        12675,
        8202,
        4753,
        792,
        30631,
        26158,
        21685,
        17724,
        48587,
        44098,
        40665,
        36688,
        64495,
        60006,
        55549,
        51572,
        16900,
        21389,
        24854,
        28831,
        1056,
        5545,
        10034,
        14011,
        52812,
        57285,
        60766,
        64727,
        34920,
        39393,
        43898,
        47859,
        21125,
        17164,
        29079,
        24606,
        5281,
        1320,
        14259,
        9786,
        57037,
        53060,
        64991,
        60502,
        39145,
        35168,
        48123,
        43634,
        25350,
        29327,
        16404,
        20893,
        9506,
        13483,
        1584,
        6073,
        61262,
        65223,
        52316,
        56789,
        43370,
        47331,
        35448,
        39921,
        29575,
        25102,
        20629,
        16668,
        13731,
        9258,
        5809,
        1848,
        65487,
        60998,
        56541,
        52564,
        47595,
        43106,
        39673,
        35696,
        33800,
        38273,
        42778,
        46739,
        49708,
        54181,
        57662,
        61623,
        2112,
        6601,
        11090,
        15067,
        20068,
        24557,
        28022,
        31999,
        38025,
        34048,
        47003,
        42514,
        53933,
        49956,
        61887,
        57398,
        6337,
        2376,
        15315,
        10842,
        24293,
        20332,
        32247,
        27774,
        42250,
        46211,
        34328,
        38801,
        58158,
        62119,
        49212,
        53685,
        10562,
        14539,
        2640,
        7129,
        28518,
        32495,
        19572,
        24061,
        46475,
        41986,
        38553,
        34576,
        62383,
        57894,
        53437,
        49460,
        14787,
        10314,
        6865,
        2904,
        32743,
        28270,
        23797,
        19836,
        50700,
        55173,
        58654,
        62615,
        32808,
        37281,
        41786,
        45747,
        19012,
        23501,
        26966,
        30943,
        3168,
        7657,
        12146,
        16123,
        54925,
        50948,
        62879,
        58390,
        37033,
        33056,
        46011,
        41522,
        23237,
        19276,
        31191,
        26718,
        7393,
        3432,
        16371,
        11898,
        59150,
        63111,
        50204,
        54677,
        41258,
        45219,
        33336,
        37809,
        27462,
        31439,
        18516,
        23005,
        11618,
        15595,
        3696,
        8185,
        63375,
        58886,
        54429,
        50452,
        45483,
        40994,
        37561,
        33584,
        31687,
        27214,
        22741,
        18780,
        15843,
        11370,
        7921,
        3960,
    ]

    @classmethod
    def of(cls, block):
        """calculate crc of a block using the maths"""
        crc = 0xFFFF
        for char in block:
            crc = (crc >> 8) ^ cls.table[(crc ^ char) & 0xFF]
        # flippin bitz
        return crc ^ 0xFFFF

    @classmethod
    def at(cls, block):
        """crc+data block; compute real, return both"""
        ecrc = struct.unpack(">H", block[0:2])[0]
        crc = cls.of(block[2:])
        return ecrc, crc

    @classmethod
    def check(cls, block):
        """crc+data block;  embedded CRC matches block calculated"""
        ecrc, crc = cls.at(block)
        return crc == ecrc


class LibrePacket:
    @classmethod
    def from_bytes(cls, data, timestamp=None):
        packet = cls()
        packet.data = data

        # L0-1: CRC of 2-23 [TODO: does not work]
        ecrc1, crc1 = crc16.at(packet.data[0:24])
        log.info("crc1: %x %x %s", ecrc1, crc1, ecrc1 == crc1)

        # Second arena: Sensor data
        # L24-25: CRC of 26-319  [TODO: does not work]
        ecrc2, crc2 = crc16.at(packet.data[24:320])
        log.info("crc2: %x %x %s", ecrc2, crc2, ecrc2 == crc2)

        packet.index_trend = packet.data[26]
        packet.index_history = packet.data[27]

        # L320-321: CRC16 of 322-343  [TODO: does not work]
        ecrc3, crc3 = crc16.at(packet.data[320:344])
        log.info("crc3: %x %x %s", ecrc3, crc3, ecrc3 == crc3)

        packet.minutes = struct.unpack(">h", data[335:337])[0]
        packet.sensor_start = datetime.datetime.now() - datetime.timedelta(
            minutes=packet.minutes
        )

        packet.history = []

        nhistory = 32
        packet.history = []
        for imem in range(nhistory):
            ird = (packet.index_history - imem - 1) % nhistory
            bias = 142
            low, high = bias + ird * 6, bias + (ird + 1) * 6

            entrydata = data[low:high]
            entrybe = struct.unpack(">HHH", entrydata)
            entryle = struct.unpack("<HHH", entrydata)
            entry = [dtry / 8.5 for dtry in entrybe + entryle]
            packet.history.append(entry)
            if imem == 0:
                print("H%d@%d %s" % (imem, ird, entry))

        packet.trends = []
        ntrends = 16
        for imem in range(ntrends):
            ird = (packet.index_trend - imem - 1) % ntrends
            bias = 46
            low, high = bias + ird * 6, bias + (ird + 1) * 6
            entrydata = data[low:high]
            entrybe = struct.unpack(">HHH", entrydata)
            entryle = struct.unpack("<HHH", entrydata)
            entry = [dtry / 8.5 for dtry in entrybe + entryle]
            packet.trends.append(entry)
            if imem == 0:
                print("T%d@%d %s" % (imem, ird, entry))


class MiaoMiaoPacket:
    new_sensor = 0x32
    no_sensor = 0x34
    start_pkt = 0x28
    end_pkt = 0x29
    decoder_ring = "0123456789ACDEFGHJKLMNPQRTUVWXYZ"

    @classmethod
    def from_bytes(cls, data, timestamp=None):
        packet = cls()

        # 18-1 byte envelope packet surrounding a Libre packet
        packet.rawpacket = data

        # E0: a start packet
        if packet.rawpacket[0] != cls.start_pkt:
            raise ValueError("envelope packet does not contain start byte")

        # E1-2: the length of this here packet
        packet.length = struct.unpack(">h", packet.rawpacket[1:3])[0]
        if len(packet.rawpacket) != packet.length:
            raise ValueError(
                "envelope packet not of embedded length: {}".format(packet.length)
            )

        # E3-12: the Libre serial number maybe?
        log.info("E3-12: %s", hexlify(packet.rawpacket[3:13]))

        # E13: the battery level percentage
        packet.battery = packet.rawpacket[13]
        # E14-15: firmware revision
        packet.fw_version = struct.unpack(">h", packet.rawpacket[14:16])[0]
        # E16-17: hardware revision
        packet.hw_version = struct.unpack(">h", packet.rawpacket[16:18])[0]
        # E18-361: the buffered Libre packet (L)
        packet.payload = packet.rawpacket[18:363]
        # E362: an end packet character )
        if packet.rawpacket[packet.length - 1] != cls.end_pkt:
            raise ValueError("envelope packet does not contain end byte")

        packet.librepacket = LibrePacket.from_bytes(packet.payload, timestamp)

        # determine sensor serial number
        # SN 0M00031VE4H
        # 0m0003A74MR

        print(
            "len=%d bat=%d fw=%x hw=%x it=%d ih=%s min=%d st=%s"
            % (
                packet.length,
                packet.battery,
                packet.fw_version,
                packet.hw_version,
                packet.librepacket.index_trend,
                packet.librepacket.index_history,
                packet.librepacket.minutes,
                packet.librepacket.sensor_start,
            )
        )
        return packet
