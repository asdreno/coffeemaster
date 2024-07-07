# Coffee Master UI

This project sets up a web interface on a Raspberry Pi to manage a service, download a CSV file, and view/edit a whitelist text file. Additionally, it provides real-time access to the service logs.

## Requirements

- Raspberry Pi 3B running Debian Bookworm
- Python 3
- Nginx

## Installation Instructions

### Step 1: Update and Upgrade the System

Update and upgrade your system packages:

```
sudo apt update
sudo apt upgrade -y
```

### Step 2: Install Necessary Packages

Install Python, pip, Nginx, and Git:

```
sudo apt install python3 python3-pip nginx git -y
```

### Step 3: Install Python Packages Globally

Install Flask, Flask-SocketIO, and Eventlet globally:

```
pip3 install flask flask-socketio eventlet
```

### Step 4: Project Directory Structure

Ensure your project directory has the following structure:

```
coffee_master_ui/
├── app.py
├── static/
│   └── styles.css
├── templates/
│   ├── index.html
│   └── logs.html
├── webui.ini
├── wsgi.py
```

### Step 5: Configuration File

Create a `webui.ini` file with the following content:

```
[Settings]
csv_path = /path/to/card_log.csv
whitelist_path = /path/to/whitelist.txt
service_name = your_service_name
```

Replace `/path/to/card_log.csv`, `/path/to/whitelist.txt`, and `your_service_name` with appropriate values.

### Step 6: Configure Nginx

1. **Create a new Nginx configuration file**:

```
sudo nano /etc/nginx/sites-available/coffee_master_ui
```

2. **Add the following configuration**:

```
server {
    listen 80;
    server_name _;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/espresso/coffeemaster/webui/coffee_master_ui.sock;
    }

    location /static {
        alias /home/espresso/coffeemaster/webui/static;
    }
}
```

Replace `/home/espresso/coffeemaster/webui` with the actual path to your project directory.

3. **Enable the Nginx configuration**:

```
sudo ln -s /etc/nginx/sites-available/coffee_master_ui /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: Ensure the Service Runs on Boot

1. **Create a systemd service file**:

```
sudo nano /etc/systemd/system/coffee_master_ui.service
```

2. **Add the following content**:

```
[Unit]
Description=Gunicorn instance to serve Coffee Master UI
After=network.target

[Service]
User=espresso
Group=www-data
WorkingDirectory=/home/espresso/coffeemaster/webui
ExecStart=/usr/local/bin/gunicorn --workers 3 --bind unix:/home/espresso/coffeemaster/webui/coffee_master_ui.sock wsgi:app
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=gunicorn_coffee_master_ui

[Install]
WantedBy=multi-user.target
```

Replace `/home/espresso/coffeemaster/webui` with the actual path to your project directory.

3. **Reload Systemd and Restart the Service**:

```
sudo systemctl daemon-reload
sudo systemctl restart coffee_master_ui
sudo systemctl enable coffee_master_ui
```

### Step 8: Set Correct Permissions

Ensure the directories and the socket file have the correct permissions:

```
sudo chown -R espresso:www-data /home/espresso
sudo chmod 755 /home/espresso
sudo chmod -R 775 /home/espresso/coffeemaster
sudo chmod -R 775 /home/espresso/coffeemaster/webui
sudo chmod 770 /home/espresso/coffeemaster/webui/coffee_master_ui.sock
```

### Final Steps

1. **Reboot the Raspberry Pi** to ensure everything starts correctly:

```
sudo reboot
```

2. **Access the Web Interface**:

Open a web browser and navigate to your Raspberry Pi’s IP address to access the Coffee Master UI.

## Features

- **Restart Service**: Restart a defined service on the Raspberry Pi.
- **Download CSV**: Download a specified CSV file.
- **Upload Whitelist**: View and upload a whitelist text file.
- **View Logs**: View real-time logs of the specified service.

## Notes

- Ensure the paths in `webui.ini` are correctly set.
- Ensure Nginx is properly configured to support WebSockets.

For further customization, modify the files in the `templates` and `static` directories.
