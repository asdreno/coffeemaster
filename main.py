import asyncio
import os
import configparser
from datetime import datetime
from tapo import ApiClient
from pn532 import PN532_SPI
import time
import logging
from logging.handlers import RotatingFileHandler
import csv

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
master_card_uids = config['DEFAULT']['MASTER_CARD_UIDS'].split(',')

# Whitelist file
whitelist_file = 'whitelist.txt'
log_file = 'card_scans.log'
csv_file = 'card_scans.csv'

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

# Set up logging with rotation
log_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    handlers=[
        log_handler,
        logging.StreamHandler()
    ]
)

# Function to update CSV file with scan counts
def update_csv(uid):
    if not os.path.exists(csv_file):
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['UID', 'Count'])
    
    rows = []
    found = False
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == uid:
                row[1] = str(int(row[1]) + 1)
                found = True
            rows.append(row)
    
    if not found:
        rows.append([uid, '1'])
    
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

async def control_tapo(turn_on=True):
    try:
        client = ApiClient(tapo_username, tapo_password)
        device = await asyncio.wait_for(client.p110(ip_address), timeout=5)
        if turn_on:
            logging.info("Turning device on...")
            await device.on()
        else:
            logging.info("Turning device off...")
            await device.off()
    except (asyncio.TimeoutError, Exception) as e:
        logging.error(f"Failed to connect to the Tapo device: {e}")
        flash_led('PWR', times=5, duration=0.2)

def setup_nfc():
    pn532 = PN532_SPI(debug=False, reset=20, cs=4)
    ic, ver, rev, support = pn532.get_firmware_version()
    logging.info(f'Found PN532 with firmware version: {ver}.{rev}')

    # Configure PN532 to communicate with MiFare cards
    pn532.SAM_configuration()

    return pn532

def flash_led(led, times=3, duration=0.2):
    led_trigger_path = f'/sys/class/leds/{led}/trigger'
    led_brightness_path = f'/sys/class/leds/{led}/brightness'

    if not os.path.exists(led_trigger_path) or not os.path.exists(led_brightness_path):
        logging.error(f"LED paths for {led} do not exist, cannot flash LED.")
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
    
    # Set LED control back to default
    with open(led_trigger_path, 'w') as f:
        f.write('default-on' if led == 'PWR' else 'mmc0')

async def main():
    pn532 = setup_nfc()
    logging.info('Waiting for RFID/NFC card...')
    
    master_mode = False
    master_mode_start = None
    master_mode_event = asyncio.Event()

    # Try to turn off the plug initially
    try:
        await control_tapo(turn_on=False)
    except Exception as e:
        logging.error(f"Failed to connect to the Tapo device initially: {e}")

    loop_counter = 0

    while True:
        # Check if a card is available to read
        uid = pn532.read_passive_target(timeout=0.5)

        # Increment loop counter and flash PWR LED every 10 loops
        loop_counter += 1
        if loop_counter >= 10:
            flash_led('PWR', times=1, duration=0.1)
            loop_counter = 0

        # Try again if no card is available.
        if uid is None:
            # If in master mode, check if it should time out
            if master_mode and (datetime.now() - master_mode_start).total_seconds() > 10:
                master_mode = False
                master_mode_event.set()  # Signal to stop master mode flashing
                logging.info('Master mode timed out.')
            continue

        uid_hex = ''.join([hex(i)[2:].zfill(2) for i in uid])
        logging.info(f'Found card with UID: {uid_hex}')
        update_csv(uid_hex)

        if master_mode:
            logging.info('Adding new card to whitelist...')
            whitelist.add(uid_hex)
            save_whitelist(whitelist)
            flash_led('PWR', times=10, duration=0.1)
            master_mode = False
            logging.info('New card added successfully!')
        elif uid_hex in master_card_uids:
            logging.info('Master card detected. Entering master mode...')
            master_mode = True
            flash_led('PWR', times=5, duration=0.5)
            master_mode_start = datetime.now()
        elif uid_hex in whitelist:
            logging.info('Whitelisted card detected. Controlling Tapo device...')
            flash_led('ACT', times=2, duration=0.1)
            try:
                await control_tapo()
                await asyncio.sleep(on_time)
            except Exception as e:
                logging.error(f"Failed to control the Tapo device: {e}")
            try:
                await control_tapo(turn_on=False)
            except Exception as e:
                logging.error(f"Failed to control the Tapo device: {e}")
        else:
            logging.info('Card not recognized.')
            flash_led('PWR', times=2, duration=0.2)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(e)
    finally:
        GPIO.cleanup()
