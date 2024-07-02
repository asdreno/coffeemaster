import asyncio
import os
from datetime import datetime
import configparser
import RPi.GPIO as GPIO

from tapo import ApiClient
from pn532 import PN532_SPI

# Determine the directory where the script is located
script_dir = os.path.dirname(os.path.realpath(__file__))

# Construct the absolute path to the tapo.config file
config_path = os.path.join(script_dir, 'tapo.ini')
config = configparser.ConfigParser()
try:
    with open(config_path) as f:
        config.read_file(f)
        print(f"Configuration file {config_path} read successfully")
except IOError as e:
    print(f"Error opening configuration file: {e}")
    raise FileNotFoundError(f"Configuration file not found: {config_path}")

tapo_username = config['DEFAULT']['TAPO_USERNAME']
tapo_password = config['DEFAULT']['TAPO_PASSWORD']
ip_address = config['DEFAULT']['IP_ADDRESS']
print("IP:", ip_address)
print("Account:", tapo_username)

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
        print(f"Error running main: {e}")
        traceback.print_exc()
    finally:
        GPIO.cleanup()
