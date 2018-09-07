# miaomiaopy
Python3 driver for MiaoMiao reader, a NFC-BTLE Freestyle Libre transceiver

## Scripts

- `mmr-decode` for directly reading a device and interpreting the read
- `mmr-mqp` for sending device reads to a MQTT broker
- `mmr-mqs` for reading device reads from a MQTT broker
- `mmr-mqscan` for finding MiaoMiaos via BTLE advertising

Example:
```
$ mmr-decode ff:ff:ff:ff:ff:ff
ff:ff:ff:ff:ff:ff: sensor was read
<MiaoMiaoPacket battery=100 fw=36 hw=1 librepacket=<LibrePacket ih=26 it=1 minutes=5286 start='2018-09-03 08:34:17.479560'>> ff:ff:ff:ff:ff:ff: sensor was read
<MiaoMiaoPacket battery=100 fw=36 hw=1 librepacket=<LibrePacket ih=26 it=2 minutes=5286 start='2018-09-03 08:35:25.046661'>>
```
