import asyncio
import os
import configparser
from tapo import ApiClient
from pn532 import PN532_SPI
import time

# Read configuration from tapo.ini
config = configparser.ConfigParser()
config_file = 'tapo.ini'  # Path to your tapo.ini

if not os.path.exists(config_file):
    raise FileNotFoundError(f"Configuration file not found: {config_file}")

config.read(config_file)

tapo_username = config['DEFAULT']['TAPO_USERNAME']
tapo_password = config['DEFAULT']['TAPO_PASSWORD']
ip_address = config['DEFAULT']['IP_ADDRESS']
on_time = int(config['DEFAULT']['ON_TIME'])
master_card_uid = config['DEFAULT']['MASTER_CARD_UID']

# Whitelist file
whitelist_file = 'whitelist.txt'

# Function to load whitelist
def load_whitelist():
    if not os.path.exists(whitelist_file):
        return set()
    with open(whitelist_file, 'r') as f:
        return set(line.strip() for line in f)

# Function to save whitelist
def save_whitelist(whitelist):
    with open(whitelist_file, 'w') as f:
        for uid in whitelist:
            f.write(f"{uid}\n")

# Initialize whitelist
whitelist = load_whitelist()

async def control_tapo():
    client = ApiClient(tapo_username, tapo_password)
    device = await client.p110(ip_address)

    print("Turning device on...")
    await device.on()

    print(f"Waiting {on_time} seconds...")
    await asyncio.sleep(on_time)

    print("Turning device off...")
    await device.off()

def setup_nfc():
    pn532 = PN532_SPI(debug=False, reset=20, cs=4)
    ic, ver, rev, support = pn532.get_firmware_version()
    print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

    # Configure PN532 to communicate with MiFare cards
    pn532.SAM_configuration()

    return pn532

def flash_led(times=10, duration=0.2):
    led_trigger_path = '/sys/class/leds/ACT/trigger'
    led_brightness_path = '/sys/class/leds/ACT/brightness'
    
    if not os.path.exists(led_trigger_path) or not os.path.exists(led_brightness_path):
        print("LED paths do not exist, cannot flash LED.")
        return
    
    # Set LED control to none
    with open(led_trigger_path, 'w') as f:
        f.write('none')
    
    # Flash the LED
    for _ in range(times):
        with open(led_brightness_path, 'w') as f:
            f.write('1')  # Turn on the LED
        time.sleep(duration)
        with open(led_brightness_path, 'w') as f:
            f.write('0')  # Turn off the LED
        time.sleep(duration)

async def main():
    pn532 = setup_nfc()
    print('Waiting for RFID/NFC card...')
    
    master_mode = False
    
    while True:
        # Check if a card is available to read
        uid = pn532.read_passive_target(timeout=0.5)
        print('.', end="")
        # Try again if no card is available.
        if uid is None:
            continue

        uid_hex = ''.join([hex(i)[2:].zfill(2) for i in uid])
        print('Found card with UID:', uid_hex)

        if master_mode:
            print('Adding new card to whitelist...')
            whitelist.add(uid_hex)
            save_whitelist(whitelist)
            flash_led()
            master_mode = False
            print('New card added successfully!')
        elif uid_hex == master_card_uid:
            print('Master card detected. Entering master mode...')
            master_mode = True
        elif uid_hex in whitelist:
            print('Whitelisted card detected. Controlling Tapo device...')
            await control_tapo()
        else:
            print('Card not recognized.')

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
