# CoffeeMaster

CoffeeMaster is an NFC-based system to control a Tapo smart plug using a Raspberry Pi. This system allows whitelisted NFC cards to turn on the smart plug for a configurable amount of time.

The whitelisting is done via the configurable master card. It logs all activations and keeps a csv record of how often a tag id has activated the smart plug.

Hardware: 
1. Raspberry PI 3b+
2. PN532 NFC Shield: https://www.waveshare.com/wiki/PN532_NFC_HAT
3. Tapo Smart WLAN P110 https://www.amazon.de/Tapo-P110-Energieverbrauchskontrolle-funktioniert-Sprachsteuerung/dp/B09BFT7NZJ
4. Case File found in the stl folder

## Usage

1. **Learning procedure**
   
   Note: The learning procedure cannot be started when the Coffee Master is currently controlling the power plug.
   1. Tap the Master Card or Tag to the Coffee Master.
   2. If the Master Card is accepted, the device will flash 5 times in 5 seconds. Remove the Master Card within those 5 seconds; otherwise, it will be seen as an attempt to add the Master Card as a user card.
   3. You now have 10 seconds to tap the new card. Please tap the new card.
   4. When a new card has been added to the whitelist, the device will flash 10 times in 5 seconds. Remove the card if you don't want the smart plug to be enabled.
   5. If you are connected to the Raspberry Pi hotspot "CoffeeMaster" and go to http://192.168.4.1/, you can see the latest whitelist.
2. **Usage**
   
   1. Tap a whitelisted RFID card or NFC tag on the Coffee Master. It might take 1 to 2 seconds until the card is recognized and the plug is enabled.
   2. The smart plug connection has a timeout of 3 seconds. If the smart plug cannot be found or there is a connection issue, the device will flash 5 times in 1 second
   3. The device will blink once every 5 seconds to incidate the RFID is waiting for cards and running normally.

## Installation

1. **Install required packages:**
    ```sh
    pip install tapo
    pip install RPi.GPIO pyserial
    ```

2. **Enable SPI Interface:**

   Use `raspi-config` to enable the SPI interface on your Raspberry Pi:
    ```sh
    sudo raspi-config
    ```
   Navigate to `Interfacing Options` -> `SPI` -> `Yes` to enable the SPI interface.

3. **Set Up Network Manager:**

   Configure your Raspberry Pi to act as an access point with a static IP address using the network manager.

4. **Create a systemd Service File:**

   Create the service file with the following command:
    ```sh
    sudo nano /etc/systemd/system/coffee_nfc.service
    ```

5. **Edit the Service File:**

   Add the following content to the service file:
    ```ini
    [Unit]
    Description=Coffee NFC Service
    After=network.target

    [Service]
    ExecStart=/usr/bin/sudo /usr/bin/python3 /home/espresso/coffeemaster/main.py
    WorkingDirectory=/home/espresso/coffeemaster
    StandardOutput=journal
    StandardError=journal
    Restart=always
    User=root

    [Install]
    WantedBy=multi-user.target
    ```

6. **Reload systemd Configuration:**

   Reload the systemd manager configuration and enable the service to start on boot:
    ```sh
    sudo systemctl daemon-reload
    sudo systemctl enable coffee_nfc.service
    sudo systemctl start coffee_nfc.service
    sudo systemctl status coffee_nfc.service
    ```

## Configuration

1. **tapo.ini:**

   Create a `tapo.ini` configuration file in the same directory as your `main.py` script:
    ```ini
    [DEFAULT]
    TAPO_USERNAME = your_tapo_username
    TAPO_PASSWORD = your_tapo_password
    IP_ADDRESS = your_tapo_device_ip
    ON_TIME = 10  # Time in seconds the socket stays on
    MASTER_CARD_UID = your_master_card_uid  # Master card UID for whitelisting
    ```

2. **Whitelist File:**

   Create a `whitelist.txt` file in the same directory as your `main.py` script. This file will store the whitelisted card UIDs, one per line.

## Logging

The service logs each card scan with a timestamp to a `card_scans.log` file and updates a `card_scans.csv` file with the scan count for each card UID. The log files are rotated to prevent them from growing indefinitely.

## Usage

- The script will log each card scan and manage the state of the Tapo smart plug based on the scanned card's UID.
- Master mode allows new cards to be added to the whitelist by first tapping the master card, followed by the new card.
- The script also handles the LED indicators on the Raspberry Pi to signal different states, such as master mode, card recognition, and connection status.

## Troubleshooting

- **Checking Logs:**

  If you need to check the logs for the service, you can use:
    ```sh
    sudo journalctl -u coffee_nfc.service -f
    ```

- **Service Status:**

  To check the status of the service, use:
    ```sh
    sudo systemctl status coffee_nfc.service
    ```

- **Restarting the Service:**

  If you need to restart the service, use:
    ```sh
    sudo systemctl restart coffee_nfc.service
    ```
