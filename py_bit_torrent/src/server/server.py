import socket
import threading

HOST = '0.0.0.0'
PORT = 6881

def handle_client(conn, addr):
    print(f"Conexión establecida con {addr}")
    try:
        with open('/app/py_bit_torrent/src/server/archivo.torrent', 'rb') as f:
            data = f.read()
            conn.sendall(data)
        print(f"Archivo enviado a {addr}")
    except Exception as e:
        print(f"Error al enviar archivo a {addr}: {e}")
    finally:
        conn.close()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("Servidor listo y escuchando...")
    while True:
        conn, addr = s.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
