import socket, os, time, hashlib, json

HOST = "localhost"
PORT = 1111

USER_FILE = "users.json"
VALID_USERS = []
STORAGE_DIR = "server_storage"

# Create the storage directory if it doesn't exist
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

def load_valid_users():
    global VALID_USERS
    # Clear current users by default
    VALID_USERS = []

    if not os.path.exists(USER_FILE):
        print(f"Warning: {USER_FILE} not found. No users loaded.")
        print(f"Create {USER_FILE} containing a JSON array of usernames, e.g. [\"alice\", \"bob\"] to enable LOGIN.")
        return

    try:
        with open(USER_FILE, 'r') as file:
            data = json.load(file)

        if not isinstance(data, list):
            print(f"Error: {USER_FILE} must contain a JSON array of usernames (got {type(data).__name__}). No users loaded.")
            return

        # Ensure all entries are strings
        VALID_USERS = [str(u) for u in data]
        print(f"Loaded {len(VALID_USERS)} user(s) from {USER_FILE}.")

    except json.JSONDecodeError:
        print(f"Error: {USER_FILE} is not valid JSON. No users loaded.")
    except Exception as e:
        print(f"An unexpected error occurred while loading {USER_FILE}: {e}")


def setup():
    # Create TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind socket to address and port
    server_socket.bind((HOST, PORT))

    # Listen for incoming connections
    server_socket.listen(1)

    print(f"TCP Echo Server running on {HOST}:{PORT}")

    return server_socket

def run_server_loop(server_socket):

    server_socket.settimeout(1.0)

    print("\nTCP Echo Server running. Press Ctrl+C at any time to shut down.")
    try:
        while True:
            try:
                print("\nWaiting for a client to connect...")
                client_socket, client_address = server_socket.accept()
                print(f"Client connected from {client_address}")
                client_socket.settimeout(1.0)
                # Keep track of this specific client's authentication state
                is_authenticated = False
                current_user = None

                while True:
                    try:
                        data = client_socket.recv(1024)
                        if not data:
                            break
                        raw_message = data.decode().strip()
                        print(f"Received raw command: {raw_message}")

                        parts = raw_message.split(" ", 1)
                        command = parts[0].upper()
                        argument = parts[1] if len(parts) > 1 else ""


                        if command == "LOGIN":
                            if argument in VALID_USERS:
                                is_authenticated = True
                                current_user = argument
                                client_socket.sendall(f"200 OK: Logged in as {current_user}\n".encode())
                                print(f"Status: User {current_user} successfully logged in.")
                            else:
                                client_socket.sendall("401 ERROR: Invalid username\n".encode())
                                print(f"Status: Failed login attempt for username: '{argument}'")
                        elif command == "MSG":
                            if not is_authenticated:
                                client_socket.sendall("403 ERROR: Please LOGIN first\n".encode())
                            else:
                                print(f"[MSG] {current_user}: {argument}")
                                client_socket.sendall(f"200 OK: Message received\n".encode())

                        
                        elif command == "FILE":
                            if not is_authenticated:
                                client_socket.sendall("403 ERROR: Please LOGIN first\n".encode())
                            else:
                                receive_file(client_socket, argument)

                        elif command == "QUIT":
                            client_socket.sendall("200 OK: Goodbye!\n".encode())
                            is_authenticated = False
                            break
                        else:
                            client_socket.sendall("400 ERROR: Unknown command\n".encode())

                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"Error handling client data: {e}")
                        break

                client_socket.close()
                print("Client disconnected gracefully.")
                
            except socket.timeout:
                continue
                
            except Exception as e:
                print(f"Server encountered an unexpected error: {e}")
                break

    except KeyboardInterrupt:
        # This catch-all completely covers the entire loop lifetime
        print("\nShutting down server gracefully. Goodbye!")

def receive_file(client_socket, arguments):
    try:
        # Parse out filename and filesize from the arguments
        parts = arguments.split(" ", 1)
        if len(parts) < 2:
            client_socket.sendall("400 ERROR: Missing filename or file size\n".encode())
            return


        path = os.path.basename(parts[0]) 
        file_size = int(parts[1])

        # Extract the base name and extension
        name, extension = os.path.splitext(path)

        # Check if the extension is completely missing, or just a lone dot
        if not extension or extension == "." or not name:
            client_socket.sendall("400 ERROR: Invalid file format. Must include a name and extension (e.g., file.txt)\n".encode())
            return
        
        save_path = os.path.join(STORAGE_DIR, path)

        client_socket.sendall(f"150 READY: Send {file_size} bytes\n".encode())

        sha256_hash = hashlib.sha256()
        bytes_received = 0

        with open(save_path, "wb") as f:
            while bytes_received < file_size:
                chunk = client_socket.recv(min(4096, file_size - bytes_received))
                if not chunk:
                    raise ConnectionError("Client disconnected during file transfer.")
                f.write(chunk)
                bytes_received += len(chunk)
                sha256_hash.update(chunk)
                
        server_hash = sha256_hash.hexdigest()
        print(f"File received and saved: {save_path} ({bytes_received} bytes)")
        print(f"Calculated Server Hash: {server_hash}")

        client_socket.sendall(f"200 OK: File transfer completed successfully. HASH:{server_hash}\n".encode())

    except ValueError:
        client_socket.sendall("400 ERROR: Invalid file size format\n".encode())
    except Exception as e:
        print(f"Error during file transfer: {e}")
        client_socket.sendall(f"500 ERROR: File save failed: {e}\n".encode())


def main():

    load_valid_users()

    main_socket = setup()

    run_server_loop(main_socket)



if __name__ == "__main__":
    main()
