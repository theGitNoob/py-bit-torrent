import socket

HOST = "10.0.11.3"
PORT = 6881

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    with open("archivo_recibido.torrent", "wb") as f:
        while True:
            data = s.recv(1024)
            if not data:
                break
            f.write(data)
    print("Archivo recibido.")
