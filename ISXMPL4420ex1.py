# ISXMPL4420ex1 - Raspberry Pi UART Current Loop Receiver Using the IS4420 Module
# https://inacks.com/is4420
#
# The IS4420-M1 sends one text line per measurement, about every 103 ms:
#     12.34mA_+052.1%_+025deg_IS4420M1_ver0 <CR><LF>
# This example reads each line and prints the loop current, the percentage of
# the 4-20 mA span and the temperature inside the module.
#
# Wiring (IS4420-M1 pad -> Raspberry Pi header pin):
#     3V3 -> pin 1  (3.3 V)
#     GND -> pin 6  (GND)
#     TX  -> pin 10 (GPIO15, RXD)
#     TX  -> 2.2 kOhm resistor -> pin 17 (3.3 V). The TX output needs this
#            pull-up. On a Raspberry Pi pull it up to 3.3 V, never to 5 V.
#     SDA, SCL, ADR and SPD -> GND (the I2C is not used in this example).
#     CIN -> current loop: the loop current flows into CIN and returns through
#            GND. Never connect the loop supply straight to CIN.
#
# Raspberry Pi set-up (once):
#     sudo raspi-config -> Interface Options -> Serial Port
#         login shell over serial: No, serial port hardware: Yes. Reboot.
#     Raspberry Pi 5 only: add "dtparam=uart0=on" to /boot/firmware/config.txt,
#         reboot, and set PORT = "/dev/ttyAMA0" below.
#     sudo apt install python3-serial
#
# Run: python3 ISXMPL4420ex1.py      (Ctrl+C to stop)

import serial

PORT = "/dev/serial0"    # UART on pins 8, 10 (Raspberry Pi 5: "/dev/ttyAMA0")

with serial.Serial(PORT, 115200, timeout=1) as uart:     # 115200 baud, 8N1
    while True:
        line = uart.readline()                 # Bytes up to and including LF

        if not line:                           # Nothing received for 1 s
            print("No data: check the TX wire and its pull-up")
            continue

        # Keep only complete lines: 37 characters + CR LF = 39 bytes.
        # This drops the partial first line and any stray byte.
        if len(line) != 39 or not line.endswith(b"\r\n"):
            continue

        # Split at "_": "12.34mA", "+052.1%", "+025deg", "IS4420M1", "ver0"
        fields = line.decode("ascii", "replace").strip().split("_")
        if len(fields) != 5:
            continue
        current, percent, temperature, model, version = fields

        if current == "ERRORmA":               # No valid measurement
            print("No measurement")
            continue

        degC = int(temperature[:-3])           # "+025deg" -> 25 (whole degC)

        if current == "EOVERmA":               # Current above the range
            print(f"Over-range            {degC:+d} degC")
        else:
            mA = float(current[:-2])           # "12.34mA" -> 12.34
            pct = float(percent[:-1])          # "+052.1%" -> 52.1
            print(f"{mA:5.2f} mA  {pct:+6.1f} %  {degC:+d} degC")
