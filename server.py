import socket
import threading
import signal

HOST = "127.0.0.1"  # localhost IP address
PORT = 5000  # port to listen on

clients = []  # List to keep track of connected clients
clients_lock = threading.Lock() # prevents concurrent access to the client list, preventing race conditions
shutdown_event = threading.Event()


def broadcast(message, sender_socket=None): # every connected client receives message except the sender
    with clients_lock:
        target_clients = list(clients)

    for client in target_clients:
        if client != sender_socket:  # Don't send the message back to the sender
            try:
                client.sendall(message)
            except OSError:
                remove_client(client)


def remove_client(client_socket): 
    with clients_lock:  
        if client_socket in clients:
            clients.remove(client_socket)

    try:
        client_socket.close()
    except OSError: # in case socket is already closed
        pass


def handle_client(client_socket, client_address):
    print(f"[NEW CONNECTION] {client_address} connected.")
    with clients_lock:
        clients.append(client_socket)

    try:
        while True:
            message = client_socket.recv(1024)  # Receive 1024 byte segments of data until the client disconnects or an error occurs
            if not message:
                print(f"[{client_address}] Client has disconnected.")
                break

            decoded_message = message.decode("utf-8", errors="replace")
            print(f"[{client_address}] {decoded_message}")
            broadcast(message, sender_socket=client_socket)
    except OSError:
        print(f"[{client_address}] Connection error.")
    finally:
        remove_client(client_socket)
        print(f"[{client_address}] Connection closed.")


def start_server(): # creates a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    server_socket.settimeout(1.0)

    def request_shutdown(signum=None, frame=None):
        shutdown_event.set()
        print("\n[SHUTDOWN] Server shutting down.")

    signal.signal(signal.SIGINT, request_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_shutdown)

    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")

    try:
        while not shutdown_event.is_set():
            try:
                client_socket, client_address = server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True,
            )
            client_thread.start()
    except KeyboardInterrupt: # Ctrl+C to stop the server
        request_shutdown()
    finally: # closes remaining client connections and the server socket
        shutdown_event.set()
        with clients_lock:
            open_clients = list(clients)
            clients.clear()

        for client in open_clients:
            try:
                client.close()
            except OSError:
                pass

        server_socket.close()


if __name__ == "__main__":
    start_server()
