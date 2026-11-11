# Raspberry Pi UART Current Loop Receiver Using the IS4420 Module

<p align="center">
  <a href="https://inacks.com/product/4-20ma-receiver-is4420-m1/">
    <img src="https://inacks.com/wp-content/uploads/IS4420-M1-I2C-UART-Current-Loop-Receiver-1.jpg" alt="IS4420-M1 I2C/UART 4-20 mA current loop receiver module" width="250">
  </a>
</p>

This example is powered by the **IS4420-M1**, a 4-20 mA current loop receiver module that sends every measurement as a line of text on its TX pad. A Raspberry Pi reads it on its serial port with a few lines of Python.

No analog circuitry to design. No calibration needed: INACKS calibrates every module at 4 mA and 20 mA.  
The IS4420-M1 contains the complete measurement side of the receiver: the loop current flows into its CIN pad, and about every 100 ms the module sends the current in mA, the percentage of the 4-20 mA span and the module temperature.

Perfect for reading pressure, temperature, flow, level and weight transmitters from a Raspberry Pi, for adding 4-20 mA inputs to your own data loggers and gateways, and for monitoring a current loop from any Linux computer.

### 🛒 [Buy the IS4420-M1 and learn more](https://inacks.com/product/4-20ma-receiver-is4420-m1/)

---

## What this example does

- Reads the text line that the IS4420-M1 sends on its TX pad, at 115200 baud.
- Prints the current, the percentage of the 4-20 mA span and the module temperature in the terminal.
- Prints `Over-range` when the current is above 21.50 mA, and `No measurement` when the module has no valid measurement.
- Skips incomplete lines, such as the one caught halfway when the script starts.

To read the module through the I2C-serial interface instead, see [ISXMPL4420ex2](https://github.com/inacks/ISXMPL4420ex2).

---

## What you need

- An [IS4420-M1 module](https://inacks.com/product/4-20ma-receiver-is4420-m1/)
- A Raspberry Pi with the 40-pin header, such as a Raspberry Pi 4, a Raspberry Pi 5 or a Raspberry Pi Zero 2 W, running Raspberry Pi OS
- A 2.2 kΩ resistor
- A 4-20 mA transmitter (2-wire or 3-wire) and its loop power supply, or a 4-20 mA current source
- Python 3 and pyserial (`sudo apt install python3-serial`)

---

## Wiring

| IS4420-M1 pad | Connect to |
|---|---|
| 3V3 | Raspberry Pi pin 1 (3.3 V) |
| GND | Raspberry Pi pin 6 (GND) and the loop power supply 0 V |
| TX | Raspberry Pi pin 10 (GPIO15, RXD), and a 2.2 kΩ pull-up to pin 17 (3.3 V) |
| CIN | Current loop input: the loop current flows into CIN and returns through GND |
| SDA, SCL, SPD, ADR | GND (not used in this example) |

- The IS4420-M1 takes its 3.3 V supply from the Raspberry Pi.
- The TX pad only pulls the line low, so it needs a pull-up. On a Raspberry Pi, always pull it up to 3.3 V: the Raspberry Pi pins work at 3.3 V only, and 5 V would damage them.
- You only use the UART here, so connect SDA, SCL, SPD and ADR to GND. Left open, they could pick up noise.
- With a 2-wire transmitter: loop power supply + to the transmitter +, the transmitter - to CIN, and the loop power supply 0 V to GND.
- With a 3-wire transmitter: the transmitter output to CIN, and the transmitter 0 V and the loop power supply 0 V to GND.
- The current loop input isn't isolated: the loop power supply 0 V, the IS4420-M1 GND and the Raspberry Pi GND are connected together.

---

## Setting up the Raspberry Pi

1. Run `sudo raspi-config` and go to **Interface Options** → **Serial Port**. Answer **No** to the login shell over serial, and **Yes** to the serial port hardware. Reboot.
2. **Raspberry Pi 5 only:** on the Raspberry Pi 5, `/dev/serial0` is the small 3-pin debug connector, not pins 8 and 10. Add this line to `/boot/firmware/config.txt`, reboot, and set `PORT = "/dev/ttyAMA0"` at the top of the script:
   ```
   dtparam=uart0=on
   ```
3. Install pyserial:
   ```
   sudo apt install python3-serial
   ```

---

## Running the example

1. Wire the circuit.
2. Copy `ISXMPL4420ex1.py` to the Raspberry Pi.
3. Run it:
   ```
   python3 ISXMPL4420ex1.py
   ```
4. Press Ctrl+C to stop it.

You should see a new line about every 100 ms. With 12 mA in the loop:

```
12.00 mA   +50.0 %  +26 degC
12.00 mA   +50.0 %  +26 degC
12.00 mA   +50.0 %  +26 degC
...
```

The percentage is the position of the current in the 4-20 mA span:

| Loop current | Percentage |
|:---:|:---:|
| Below 4 mA | Negative |
| 4 mA | 0.0 % |
| 12 mA | 50.0 % |
| 20 mA | 100.0 % |
| 21.50 mA | 109.4 % |
| Above 21.50 mA | `Over-range` |

---

## How it works

The IS4420-M1 sends one line per measurement, about every 100 ms, at 115200 baud, 8 data bits, no parity, 1 stop bit (8N1):

```
12.34mA_+052.1%_+025deg_IS4420M1_ver0
```

Every line has exactly 37 characters, followed by CR LF (39 bytes in total):

| Characters | Content | Example |
|:---:|---|:---:|
| 1–5 | Current in mA | `12.34` |
| 6–8 | `mA_` | |
| 9–14 | Percentage of the 4-20 mA span, with its sign | `+052.1` |
| 15–16 | `%_` | |
| 17–20 | Module temperature in °C, with its sign | `+025` |
| 21–24 | `deg_` | |
| 25–32 | Model | `IS4420M1` |
| 33–37 | `_ver` and the module revision | `_ver0` |

Two special lines keep the same length:

| Line | Meaning |
|---|---|
| `EOVERmA_+EOVER%_+025deg_IS4420M1_ver0` | The current is above 21.50 mA (over-range). The temperature is still valid. |
| `ERRORmA_+ERROR%_+ERRdeg_IS4420M1_ver0` | The module has no valid measurement. |

The script keeps a line only if it is exactly 39 bytes long and ends in CR LF, and then splits it at every `_`:

```python
line = uart.readline()                         # bytes up to and including LF
if len(line) != 39 or not line.endswith(b"\r\n"):
    continue                                   # skip incomplete lines

current, percent, temperature, model, version = line.decode().strip().split("_")
mA = float(current[:-2])                       # "12.34mA" -> 12.34
pct = float(percent[:-1])                      # "+052.1%" -> 52.1
degC = int(temperature[:-3])                   # "+025deg" -> 25
```

Any computer with a serial port can read the same line, and so can a PC through a USB-to-UART adapter: set `PORT` to the adapter's port, for example `/dev/ttyUSB0`.

---

## Notes

- **Serial console:** Linux must not use the serial port for its login shell, or it would share pin 10 with the script. That's what step 1 of the setup turns off.
- **Pull-up voltage:** the IS4420-M1 accepts a TX pull-up to 3.3 V or 5 V, but on a Raspberry Pi it must be 3.3 V.
- **Temperature:** it's the temperature inside the module, which can be above the ambient temperature.
- **Protection:** CIN has no protection. Never connect the loop power supply straight to CIN, and never reverse the loop: both destroy the module.

---

## Troubleshooting

| The terminal shows | What to check |
|---|---|
| `No data: check the TX wire and its pull-up` | The TX wire on pin 10, the 2.2 kΩ pull-up to 3.3 V, and the 3V3 and GND connections. That the serial port hardware is enabled (setup step 1), and on a Raspberry Pi 5 that the script uses `/dev/ttyAMA0`. The first line comes about 0.6 s after power-up. |
| An error opening the serial port | The serial port hardware is not enabled (setup step 1). If it says permission denied, add your user to the `dialout` group with `sudo usermod -aG dialout $USER` and log in again. |
| About `0.00 mA   -25.0 %` | There's no loop current. Check the CIN connection, the transmitter and its loop power supply, and that the loop power supply 0 V goes to GND. |
| `Over-range` | The loop current is above 21.50 mA. Check the transmitter. |
| `No measurement` | The module couldn't measure during the last 100 ms. Check the 3V3 supply (3.3 V). |

---

## Get the IS4420-M1

- 🛒 **[Buy the IS4420-M1](https://inacks.com/product/4-20ma-receiver-is4420-m1/)**: I2C/UART 4-20 mA Current Loop Receiver Module

ℹ️ For more information: [www.inacks.com](https://www.inacks.com)
