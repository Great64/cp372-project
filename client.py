import socket, os, time, hashlib, json


HOST = "localhost"
PORT = 1111


def setup():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((HOST, PORT))
        print(f"Successfully connected to server at {HOST}:{PORT}")
        return client_socket
    except ConnectionRefusedError:
        # Server is not running yet
        return None
    except Exception as e:
        # Catch other network quirks (like network down)
        return None



def run_client_loop(client_socket):
    while True:
        # Prompt user matching the required CLI format
        message = input("\n> ").strip()

        # Parse the input to check if it's a special action command
        parts = message.split(" ", 1)
        command = parts[0].upper()
        argument = parts[1] if len(parts) > 1 else ""

        # Check for QUIT command
        if command == "QUIT":
            client_socket.sendall(message.encode())
            try:
                data = client_socket.recv(1024)
                print("Server response:", data.decode().strip())
            except Exception:
                pass # If server closed immediately, skip printing response
            break

        # Check for FILE command
        elif command == "FILE":
            send_file(client_socket, argument)

        # Handle all other standard traffic (LOGIN, MSG, or invalid commands)
        else:
            try:
                client_socket.sendall(message.encode())
                data = client_socket.recv(1024)
                if not data:
                    print("Server closed connection.")
                    break
                print("Server response:", data.decode().strip())
            except Exception as e:
                print(f"Network error: {e}")
                break

    client_socket.close()
    print("Disconnected from the server session.")

def send_file(client_socket, file_path):

    # 1. Error check: Does the file exist locally?
    if not os.path.exists(file_path):
        print(f"Error: Local file '{file_path}' not found.")
        return

    # 2. Error check: Does it have an extension? (e.g., test.txt)
    filename = os.path.basename(file_path)
    name, extension = os.path.splitext(filename)
    if not extension or extension == ".":
        print(f"Error: '{filename}' is missing a file extension.")
        return

    # 3. Gather metadata
    file_size = os.path.getsize(file_path)

   

    # 5. Phase 1: Send metadata request (FILE filename filesize)
    metadata_command = f"FILE {filename} {file_size}"
    client_socket.sendall(metadata_command.encode())

    # 6. Wait for the server's readiness acknowledgement
    server_response = client_socket.recv(1024).decode().strip()
    print("Server response:", server_response)

    # If server says anything other than READY (like a 403 or 400 error), abort
    if "150 READY" not in server_response:
        return

    sha256_hash = hashlib.sha256()

    # 7. Phase 2: Stream the raw binary chunks and calculate the file hash
    print(f"Streaming '{filename}' ({file_size} bytes)...")
    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break  # Finished reading file
                
                sha256_hash.update(chunk)
                client_socket.sendall(chunk)
        
        client_hash = sha256_hash.hexdigest()
        
        # Phase 3: Wait for final server confirmation containing its calculated hash
        final_response = client_socket.recv(1024).decode().strip()
        print("Server response:", final_response)

        # Verification Step
        if "HASH:" in final_response:
            server_hash = final_response.split("HASH:")[1].strip()
            if client_hash == server_hash:
                print("INTEGRITY CHECK PASSED: Local hash matches server hash perfectly.")
                print(f"SHA-256: {client_hash}")
                
            else:
                print("INTEGRITY CHECK FAILED: The file contents were altered or corrupted over the network!")
                print(f"Client Hash: {client_hash}")
                print(f"Server Hash: {server_hash}")




        

    except Exception as e:
        print(f"An error occurred during transmission: {e}")

def main():
    print("Starting client application...")
    
    while True:
        main_socket = setup()
        
        if main_socket is not None:
            # We are connected! Enter the message loop.
            run_client_loop(main_socket)
            
            # If run_client_loop finishes, it means we typed QUIT 
            # OR the server disconnected us unexpectedly.
            print("\nConnection lost or closed.")
            
            # Ask the user if they want to exit entirely or attempt a reconnect
            choice = input("Do you want to reconnect? (y/n): ").strip().lower()
            if choice != 'y':
                print("Exiting application. Goodbye!")
                break
        else:
            # If setup() returned None, the server is down. 
            # Print a status message and retry after a short delay.
            print(f"Server at {HOST}:{PORT} is unavailable. Retrying in 3 seconds... (Press Ctrl+C to quit)")
            time.sleep(3)

if __name__ == "__main__":
    main()