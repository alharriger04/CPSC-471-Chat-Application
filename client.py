import socket
import threading
import sys

BUFFER_SIZE = 1024
running = True
username = ""


def receive_messages(sock):
    global running, username

    while running:
        try:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                print("\n[DISCONNECTED] Server closed the connection.")
                running = False
                break

            incoming_text = data.decode("utf-8", errors="replace").strip()

            # clear the current line so incoming text prints cleaner
            sys.stdout.write("\r" + " " * 100 + "\r")
            print(incoming_text)

            # put the prompt back after showing the message
            sys.stdout.write(f"{username}> ")
            sys.stdout.flush()

        except OSError:
            break


def start_client(server_host, server_port, local_port=None):
    global running, username

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        if local_port is not None:
            # lets you bind this client to a specific local port if needed
            sock.bind(("", local_port))

        sock.connect((server_host, server_port))
        print(f"[CONNECTED] Connected to {server_host}:{server_port}")

        username = input("Enter your username: ").strip()
        if not username:
            username = "Anonymous"

        print("Type messages and press Enter to send.")
        print("Type 'quit' to disconnect.\n")

        receiver_thread = threading.Thread(
            target=receive_messages,
            args=(sock,),
            daemon=True
        )
        receiver_thread.start()

        while running:
            try:
                typed_message = input(f"{username}> ").strip()

                if not typed_message:
                    continue

                if typed_message.lower() == "quit":
                    print("[DISCONNECTING] Closing connection...")
                    running = False
                    break

                # send it in username: message format
                outgoing_text = f"{username}: {typed_message}"
                sock.sendall(outgoing_text.encode("utf-8"))

            except (EOFError, KeyboardInterrupt):
                print("\n[DISCONNECTING] Closing connection...")
                running = False
                break

    except ConnectionRefusedError:
        print("[ERROR] Could not connect. Make sure the server is running.")
    except ValueError:
        print("[ERROR] Invalid port number.")
    except OSError as error:
        print(f"[ERROR] {error}")

    finally:
        running = False
        try:
            sock.close()
        except OSError:
            pass


if __name__ == "__main__":
    # this part runs only when the file is started directly
    server_host = "127.0.0.1"
    server_port = 5000
    local_port = None

    try:
        # this lets you optionally pass in host, server port, and local port from the command line
        if len(sys.argv) >= 2:
            server_host = sys.argv[1]
        if len(sys.argv) >= 3:
            server_port = int(sys.argv[2])
        if len(sys.argv) >= 4:
            local_port = int(sys.argv[3])

        start_client(server_host, server_port, local_port)

    except ValueError:
        print("Usage:")
        print("  python client.py")
        print("  python client.py <server_host> <server_port>")
        print("  python client.py <server_host> <server_port> <local_port>")