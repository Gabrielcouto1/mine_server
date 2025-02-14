from flask import Flask, Response, send_from_directory, request
import subprocess
import os
import signal
import time
import re

app = Flask(__name__, static_folder="static")

MINECRAFT_COMMAND = "nohup java -Xmx24G -Xms24G -jar fabric-server-mc.1.19.2-loader.0.16.10-launcher.1.0.1.jar nogui > server.log 2>&1 &"
LOG_FILE = "server.log"

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
        # Define a regex pattern to match the desired log messages
        log_pattern = re.compile(r'\[\d{2}:\d{2}:\d{2}\] \[Server thread/INFO\]: (?:'
                                 r'\[.*?: Teleported .*?\]|'  # Matches teleport messages
                                 r'.*? (joined|left) the game|'  # Matches join/leave messages
                                 r'.*? lost connection: .*?|'  # Matches disconnect messages
                                 r'\[Not Secure\] .*?)')  # Matches in-game chat messages

        with open("server.log", "r") as file:
            # Read and filter existing logs
            log_data = file.readlines()
            for line in log_data:
                if log_pattern.search(line):  # Send only relevant logs
                    yield f"data: {line.strip()}\n\n"

            # Seek to the end and stream new logs
            file.seek(0, os.SEEK_END)
            while True:
                line = file.readline()
                if log_pattern.search(line):  # Only send matching lines
                    yield f"data: {line.strip()}\n\n"
                time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")

@app.route('/say', methods=['POST'])
def send_message():
    """Send a message to the Minecraft server as the server."""
    message = request.json.get("message", "").strip()

    if not message:
        return "Message cannot be empty!", 400

    command = f'echo "/me {message}" > server_input.txt'
    subprocess.run(command, shell=True, check=True)

    return f"Sent message: {message}", 200

if __name__ == '__main__':
    print("Serving files from:", app.static_folder)
    app.run(host='0.0.0.0', port=5000, threaded=True)


