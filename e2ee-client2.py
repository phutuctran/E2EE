import socket
import threading
import requests
import rsa
import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO

app = Flask(__name__)
app.config["SECRET_KEY"] = "e2ee123"
PORT = 9999
server_ip = "172.17.23.30"
socketio = SocketIO(app)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
public_key, private_key = rsa.newkeys(1024)
public_partner = None
myname = None

def connect_to_host():
    client.connect((server_ip, PORT))
    client.send(public_key.save_pkcs1(format='PEM'))
    client.send(myname.encode())

def receiving_messages():
    global client, public_partner, private_key
    while True:
        if(public_partner == None):
            public_partner = rsa.PublicKey.load_pkcs1(client.recv(1024))
        else:
            message = rsa.decrypt(client.recv(1024), private_key).decode()
            messageformat = message.split(":")
            socketio.emit("message", {"name": messageformat[0], "message": messageformat[1]})

            
def sending_messages(message):
    global client, public_partner, myname
    client.send(rsa.encrypt(f"{myname}: {message}".encode(), public_partner))

@app.route("/", methods = ["POST", "GET"])
def index():
    global client, myname
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            return render_template("index.html", error="Please enter a name.", name=name)
        

        myname = name
        connect_to_host()
        #socketio.start_background_task(target=receiving_messages)
        receivie_thread = threading.Thread(target=receiving_messages, args=()).start()
        #send_thread = threading.Thread(target=sending_messages, args=()).start()
        # eventlet.spawn(receiving_messages())



        return render_template("room.html", code=None)
    return render_template("index.html")

@socketio.on('message')
def handle_message(data):
    sending_messages(data["message"])
    message = data["message"]
    socketio.emit("message", {"name": myname, "message": message})

if __name__ == "__main__":
    socketio.run(app,port = 5001, debug=True)
    # socketio.start_background_task(target=receiving_messages)
