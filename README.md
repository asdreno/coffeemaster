# coffeemaster
# Installation
```
pip install tapo
pip install RPi.GPIO pyserial
```

1. Enable SPI Interface.

2. Create a systemd Service File
`sudo nano /etc/systemd/system/coffee_nfc.service`

3. Edit the Service File
```
[Unit]
Description=Coffee NFC Service
After=network.target

[Service]
ExecStart=/usr/bin/sudo /usr/bin/python3 /home/espresso/coffeemaster/main.py
WorkingDirectory=/home/espresso/coffeemaster
StandardOutput=inherit
StandardError=inherit
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```

4. Reload systemd Configuration
`sudo systemctl daemon-reload`
`sudo systemctl enable coffee_nfc.service`
`sudo systemctl start coffee_nfc.service`
`sudo systemctl status coffee_nfc.service`