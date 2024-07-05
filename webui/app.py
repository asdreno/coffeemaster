from flask import Flask, request, send_file, render_template, redirect, url_for
from flask_socketio import SocketIO
import configparser
import os
import subprocess
import threading

app = Flask(__name__)
socketio = SocketIO(app)

config = configparser.ConfigParser()
config.read('webui.ini')

CSV_PATH = config['Settings']['csv_path']
WHITELIST_PATH = config['Settings']['whitelist_path']
SERVICE_NAME = config['Settings']['service_name']

@app.route('/')
def index():
    with open(WHITELIST_PATH, 'r') as file:
        whitelist_content = file.read()
    return render_template('index.html', whitelist_content=whitelist_content)

@app.route('/restart-service', methods=['POST'])
def restart_service():
    subprocess.run(['sudo', 'systemctl', 'restart', SERVICE_NAME])
    return redirect(url_for('index'))

@app.route('/download-csv')
def download_csv():
    return send_file(CSV_PATH, as_attachment=True)

@app.route('/upload-whitelist', methods=['POST'])
def upload_whitelist():
    file = request.files['whitelist_file']
    if file:
        file.save(WHITELIST_PATH)
    return redirect(url_for('index'))

@app.route('/logs')
def logs():
    return render_template('logs.html')

def stream_logs():
    process = subprocess.Popen(['journalctl', '-u', SERVICE_NAME, '-f'], stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        if output:
            socketio.emit('log_update', {'log': output.decode('utf-8').strip()})
        else:
            break

@socketio.on('connect')
def handle_connect():
    thread = threading.Thread(target=stream_logs)
    thread.start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=80)
