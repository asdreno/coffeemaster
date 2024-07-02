import asyncio
import os
from datetime import datetime
import configparser

from tapo import ApiClient

# Read configuration from tapo.config
config = configparser.ConfigParser()
config.read('tapo.config')

tapo_username = config['DEFAULT']['TAPO_USERNAME']
tapo_password = config['DEFAULT']['TAPO_PASSWORD']
ip_address = config['DEFAULT']['IP_ADDRESS']

async def main():
    client = ApiClient(tapo_username, tapo_password)
    device = await client.p110(ip_address)

    print("Turning device on...")
    await device.on()

    print("Waiting 2 seconds...")
    await asyncio.sleep(2)

    print("Turning device off...")
    await device.off()

if __name__ == "__main__":
    asyncio.run(main())
