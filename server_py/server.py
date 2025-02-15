from flask import Flask, Response, send_from_directory, request
import subprocess
import os
import signal
import time
import re
from datetime import datetime

app = Flask(__name__, static_folder="static")

MINECRAFT_COMMAND = "nohup java -Xmx24G -Xms24G -jar fabric-server-mc.1.19.2-loader.0.16.10-launcher.1.0.1.jar nogui > server.log 2>&1 &"
LOG_FILE = "server.log"
GIT_DIR = "github/mine_server"

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

def get_server_pid():
    """Get the Minecraft server process ID."""
    try:
        result = subprocess.check_output("pgrep -f fabric-server-mc", shell=True, universal_newlines=True).strip()
        return int(result) if result else None
    except subprocess.CalledProcessError:
        return None

@app.route('/start', methods=['POST'])
def start_server():
    """Start the Minecraft server."""
    if get_server_pid():
        return "JA TA LIGADO!!!!!", 400
    
    subprocess.Popen(MINECRAFT_COMMAND, shell=True)
    return "Minecraft server started!", 200

@app.route('/stop', methods=['POST'])
def stop_server():
    """Stop the Minecraft server."""
    pid = get_server_pid()
    if pid:
        os.kill(pid, signal.SIGTERM)
        return "PARADO!!!!", 200
    return "JA TA PARADO!!!!", 400

@app.route('/restart', methods=['POST'])
def restart_server():
    """Restart the Minecraft server."""
    pid = get_server_pid()
    if pid:
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)  # Small delay before restarting
    subprocess.Popen(MINECRAFT_COMMAND, shell=True)
    return "RESTARTADO!!!!", 200

@app.route('/logs')
def stream_logs():
    def generate():
        log_pattern = re.compile(r'\[\d{2}:\d{2}:\d{2}\] \[Server thread/INFO\]: (?:'
                                 r'\[.*?: Teleported .*?\]|'  # Matches teleport messages
                                 r'.*? (joined|left) the game|'  # Matches join/leave messages
                                 r'.*? lost connection: .*?|'  # Matches disconnect messages
                                 r'\[Not Secure\] .*?)')  # Matches in-game chat messages

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

@app.route('/backup', methods=['POST'])
def backup_world():
    """Backup the world and push it to GitHub."""
    try:
        # Remove old backup
        subprocess.run("rm -rf github/mine_server/world/", shell=True, check=True)

        # Copy new world files
        subprocess.run("cp -r world/ github/mine_server/", shell=True, check=True)

        # Change directory to Git repo
        os.chdir(GIT_DIR)

        # Get the current date and time
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Git commands
        subprocess.run("git add .", shell=True, check=True)
        subprocess.run(f'git commit -m "World backup {timestamp}"', shell=True, check=True)
        subprocess.run("git push", shell=True, check=True)

        return "Backup completed and pushed to GitHub!", 200
    except subprocess.CalledProcessError as e:
        return f"Backup failed: {e}", 500
    finally:
        os.chdir("..")  # Change back to original directory

if __name__ == '__main__':
    print("Serving files from:", app.static_folder)
    app.run(host='0.0.0.0', port=5000, threaded=True)

