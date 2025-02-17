from flask import Flask, Response, send_from_directory, request
import subprocess
import os
import signal
import time
import re
from datetime import datetime

app = Flask(__name__, static_folder="static")

MINECRAFT_COMMAND = ["java", "-Xmx24G", "-Xms24G", "-jar", "fabric-server-mc.1.19.2-loader.0.16.10-launcher.1.0.1.jar", "nogui"]
LOG_FILE = "server.log"
server_process = None  # Store the Minecraft process

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

def get_server_pid():
    """Check if the server process is running."""
    return server_process is not None and server_process.poll() is None

@app.route('/start', methods=['POST'])
def start_server():
    """Start the Minecraft server."""
    global server_process
    if get_server_pid():
        return "JA TA LIGADO!!!!!", 400

    with open(LOG_FILE, "a") as log_file:
        server_process = subprocess.Popen(
            MINECRAFT_COMMAND, stdin=subprocess.PIPE, stdout=log_file, stderr=log_file, text=True
        )
    
    return "Minecraft server started!", 200

@app.route('/stop', methods=['POST'])
def stop_server():
    """Stop the Minecraft server."""
    global server_process
    if get_server_pid():
        server_process.terminate()  # Send SIGTERM
        server_process.wait()
        server_process = None
        return "PARADO!!!!", 200
    return "JA TA PARADO!!!!", 400

@app.route('/restart', methods=['POST'])
def restart_server():
    """Restart the Minecraft server."""
    stop_server()
    time.sleep(2)
    start_server()
    return "RESTARTADO!!!!", 200

@app.route('/backup', methods=['POST'])
def backup_server():
    """Run the backup script."""
    try:
        subprocess.Popen(['./backup.sh'], shell=True)
        return "Backup started!", 200
    except Exception as e:
        return f"Error starting backup: {str(e)}", 500

@app.route('/send-command', methods=['POST'])
def send_command():
    """Send a command to the Minecraft server."""
    global server_process
    if not get_server_pid():
        return "Server is not running!", 400

    command = request.form.get('command')
    if not command:
        return "No command provided!", 400

    try:
        server_process.stdin.write(command + "\n")
        server_process.stdin.flush()
        return f"Command sent: {command}", 200
    except Exception as e:
        return f"Error sending command: {str(e)}", 500

@app.route('/logs')
def stream_logs():
    def generate():
        log_pattern = re.compile(r'\[\d{2}:\d{2}:\d{2}\] \[Server thread/INFO\]: (?:'
                                 r'\[.*?: Teleported .*?\]|'
                                 r'.*? (joined|left) the game|'
                                 r'.*? lost connection: .*?|'
                                 r'\[Not Secure\] .*?)')

        with open("server.log", "r") as file:
            log_data = file.readlines()
            for line in log_data:
                if log_pattern.search(line):
                    yield f"data: {line.strip()}\n\n"

            file.seek(0, os.SEEK_END)
            while True:
                line = file.readline()
                if log_pattern.search(line):
                    yield f"data: {line.strip()}\n\n"
                time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")

if __name__ == '__main__':
    print("Serving files from:", app.static_folder)
    app.run(host='0.0.0.0', port=5000, threaded=True)

