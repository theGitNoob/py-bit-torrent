import socket

HOST = '0.0.0.0'
PORT = 6881

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("Servidor listo y escuchando...")
    conn, addr = s.accept()
    with conn:
        print(f"Conexión establecida con {addr}")
        with open('archivo.torrent', 'rb') as f:
            data = f.read()
            conn.sendall(data)
        print("Archivo enviado.")