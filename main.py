import asyncio
import os
from datetime import datetime
import configparser
import RPi.GPIO as GPIO

from tapo import ApiClient
from pn532 import PN532_SPI

# Read configuration from tapo.config
config = configparser.ConfigParser()
config.read('tapo.ini')

tapo_username = config['DEFAULT']['TAPO_USERNAME']
tapo_password = config['DEFAULT']['TAPO_PASSWORD']
ip_address = config['DEFAULT']['IP_ADDRESS']

async def control_tapo():
    client = ApiClient(tapo_username, tapo_password)
    device = await client.p110(ip_address)

    print("Turning device on...")
    await device.on()

    print("Waiting 10 seconds...")
    await asyncio.sleep(10)

    print("Turning device off...")
    await device.off()

def setup_nfc():
    pn532 = PN532_SPI(debug=False, reset=20, cs=4)
    ic, ver, rev, support = pn532.get_firmware_version()
    print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

    # Configure PN532 to communicate with MiFare cards
    pn532.SAM_configuration()

    return pn532

async def main():
    pn532 = setup_nfc()
    print('Waiting for RFID/NFC card...')

    while True:
        # Check if a card is available to read
        uid = pn532.read_passive_target(timeout=0.5)
        print('.', end="")
        # Try again if no card is available.
        if uid is None:
            continue

        print('Found card with UID:', [hex(i) for i in uid])
        await control_tapo()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
