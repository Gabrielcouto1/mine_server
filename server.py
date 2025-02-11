from flask import Flask, Response, send_from_directory
import subprocess
import os
import signal
import time

print("Current working directory:", os.getcwd())

print("Static folder contents:", os.listdir("/home/opc/static"))

app = Flask(__name__, static_folder="static")

MINECRAFT_COMMAND = "nohup java -Xmx24G -Xms24G -jar fabric-server-mc.1.19.2-loader.0.16.10-launcher.1.0.1.jar nogui > server.log 2>&1 &"

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

def get_server_pid():
    try:
        result = subprocess.check_output("pgrep -f fabric-server-mc", shell=True, universal_newlines=True).strip()
        return int(result) if result else None
    except subprocess.CalledProcessError:
        return None

@app.route('/start', methods=['POST'])
def start_server():
    if get_server_pid():
        return "Server is already running!", 400
    
    subprocess.Popen(MINECRAFT_COMMAND, shell=True)
    return "Minecraft server started!", 200

@app.route('/restart', methods=['POST'])
def restart_server():
    pid = get_server_pid()
    if pid:
        os.kill(pid, signal.SIGTERM)
    subprocess.Popen(MINECRAFT_COMMAND, shell=True)
    return "Minecraft server restarted!", 200

@app.route('/logs')
def stream_logs():
    def generate():
        with open("server.log", "r") as file:
            file.seek(0, os.SEEK_END)
            while True:
                line = file.readline()
                if line:
                    yield f"data: {line.strip()}\n\n"
                time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")

if __name__ == '__main__':
    print("Serving files from:", app.static_folder)
    app.run(host='0.0.0.0', port=5000, threaded=True)

