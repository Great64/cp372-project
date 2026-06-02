'''
CP372 – Computer Networks, Spring 2026
Assignment 1: TCP Client-Server Application

Script Name: client.py
Description: TCP client built with Python Socket API. Connects to the server, 
             sends text commands, transfers files with integrity checks, and 
             supports automatic reconnection.
Capabilities:
    - Interactive CLI command parsing (LOGIN, MSG, FILE, QUIT)
    - Binary file streaming with client-side SHA-256 hashing
    - Server response display and integrity verification
    - Graceful disconnect with optional reconnect loop

Authors:
    Obeidi, Bassil
    Barghouti, Alaa
    Ozog, Philip
    Soja, Max
    Yamin, Noah
'''


# Core libraries: socket (Python TCP communication), os (file checks), time (retry delay), hashlib (SHA-256)
import socket, os, time, hashlib

# Server address configuration 
HOST = "localhost"
PORT = 1111


def setup():
    """
    Attempts to create a TCP socket and connect to the server.
    Returns the connected socket on success, or None if the server is unreachable.
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        #Initiate 3-way handshake with server
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
    """
    Main interactive loop: reads user input, parses commands, and routes
    traffic to the server. Runs until the user types QUIT or the connection drops.
    """
    while True:
        # Display prompt and read raw user input from the terminal
        message = input("\n> ").strip()

        # Split the input into command token and the remainder (argument)
        # e.g., "LOGIN Alice" -> command="LOGIN", argument="Alice"
        parts = message.split(" ", 1)
        command = parts[0].upper()
        argument = parts[1] if len(parts) > 1 else ""

        # ---------------- QUIT ----------------
        # Graceful termination: notify server before closing the socket
        if command == "QUIT":
            client_socket.sendall(message.encode())
            try:
                data = client_socket.recv(1024)
                print("Server response:", data.decode().strip())
            except Exception:
                pass # If server closed immediately, skip printing response
            break

        # ---------------- FILE ----------------
        # Hand off to send_file() for multi-phase binary transfer with hashing
        elif command == "FILE":
            send_file(client_socket, argument)

        # ---------------- LOGIN / MSG / Invalid ----------------
        # All other commands are sent as plain text and await a server response
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
    # Clean up: close the socket and release the local port back to the OS
    client_socket.close()
    print("Disconnected from the server session.")

def send_file(client_socket, file_path):
    """
    Implements the custom FILE transfer protocol:
      Phase 1: Send metadata (filename + size) and wait for 150 READY.
      Phase 2: Stream the file in 4096-byte binary chunks.
      Phase 3: Receive server's calculated hash and verify integrity.
    """

    # ---- Pre-flight client-side validation ----

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


    

    # 3. Determine the total byte size to announce to the server
    file_size = os.path.getsize(file_path)


    # ---- Metadata handshake ----

    # 4. Phase 1: Send metadata request (FILE <filename> <filesize>)
    metadata_command = f"FILE {filename} {file_size}"
    client_socket.sendall(metadata_command.encode())

    # 5. Wait for the server's readiness acknowledgement
    server_response = client_socket.recv(1024).decode().strip()
    print("Server response:", server_response)

    # If server says anything other than READY (like a 403 or 400 error), abort
    if "150 READY" not in server_response:
        return

    #Intialized hash value for a new file transfer.
    sha256_hash = hashlib.sha256()

    # 6. Phase 2: Stream the raw binary chunks and calculate the file hash
    print(f"Streaming '{filename}' ({file_size} bytes)...")
    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break  # Finished reading file
                # Update the running hash with this chunk
                sha256_hash.update(chunk)
                #Send the current chunk to the server
                client_socket.sendall(chunk)
        # Finalize the client-side hash
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
    """
    Entry point: repeatedly attempts to connect to the server.
    On success, hands control to the interactive loop.
    On failure, waits 3 seconds and retries until the user gives up.
    """

    print("Starting client application...")
    
    while True:
        # Attempt to establish a TCP session
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