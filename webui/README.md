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

Install Python, pip, virtual environment, Nginx, and Git:

```
sudo apt install python3 python3-pip python3-venv nginx git -y
```

### Step 3: Set Up the Python Environment

1. **Create a Virtual Environment**:

```
python3 -m venv coffee_master_ui_env
source coffee_master_ui_env/bin/activate
```

2. **Install Flask and Other Packages**:

```
pip install flask flask-socketio eventlet
```


### Step 4: Configuration File

Modify `webui.ini` file with the following content:

```
[Settings]
csv_path = /path/to/card_log.csv
whitelist_path = /path/to/whitelist.txt
service_name = your_service_name
```

Replace `/path/to/card_log.csv`, `/path/to/whitelist.txt`, and `your_service_name` with appropriate values.

### Step 5: Configure Nginx

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
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /path/to/coffee_master_ui/static;
    }
}
```

Replace `/path/to/coffee_master_ui` with the actual path to your project directory.

3. **Enable the Nginx configuration**:

\```
sudo ln -s /etc/nginx/sites-available/coffee_master_ui /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
\```

### Step 6: Ensure the Service Runs on Boot

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
User=pi
Group=www-data
WorkingDirectory=/path/to/coffee_master_ui
Environment="PATH=/path/to/coffee_master_ui/coffee_master_ui_env/bin"
ExecStart=/path/to/coffee_master_ui/coffee_master_ui_env/bin/gunicorn --workers 3 --bind unix:coffee_master_ui.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```

Replace `/path/to/coffee_master_ui` and `coffee_master_ui_env` with the actual paths.

3. **Enable and start the service**:

```
sudo systemctl start coffee_master_ui
sudo systemctl enable coffee_master_ui
```

### Final Steps

1. **Reboot the Raspberry Pi** to ensure everything starts correctly:

```
sudo reboot
```

2. **Access the Web Interface**:

Open a web browser and navigate to your Raspberry Pi's IP address to access the Coffee Master UI.

## Features

- **Restart Service**: Restart a defined service on the Raspberry Pi.
- **Download CSV**: Download a specified CSV file.
- **Upload Whitelist**: View and upload a whitelist text file.
- **View Logs**: View real-time logs of the specified service.

## Notes

- Ensure the paths in `webui.ini` are correctly set.
- Ensure Nginx is properly configured to support WebSockets.

For further customization, modify the files in the `templates` and `static` directories.
