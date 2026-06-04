# TCP Client-Server Application

A Python-based TCP client-server application for CP372 - Computer Networks. The server handles user authentication, message relay, and file transfer with SHA-256 integrity verification.

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only Python standard library: `socket`, `os`, `json`, `hashlib`, `time`)

## Folder Structure

```
.
├── server.py          # TCP server implementation
├── client.py          # TCP client implementation
├── users.json         # Authorized usernames
├── server_storage/    # Directory for received files (auto-created)
└── README.md          # This file
```

## How to Run the Server

1. Open a terminal in the project directory
2. Run the server:
   ```
   python server.py
   ```
3. The server will start listening on `localhost:1111`

## How to Run the Client

1. Make sure the server is running (see above)
2. Open another terminal in the project directory
3. Run the client:
   ```
   python client.py
   ```

## Example Commands

Once connected to the server, use the following commands in the client:

```
LOGIN <username>      # Authenticate with a valid username (Alice, Bob, or Johnny)
MSG <message>         # Send a text message to the server
FILE <filepath>       # Transfer a file to the server
QUIT                  # Disconnect from the server
```

### Example Session

```
LOGIN Alice
Server response: 200 OK: Logged in as Alice

MSG Hello from client!
Server response: 200 OK: Message received

FILE document.txt
Server response: 150 READY: Send 13 bytes
Streaming 'document.txt' (13 bytes)...
Server response: 200 OK: File transfer completed. HASH:315f5bdb...
INTEGRITY CHECK PASSED: Local hash matches server hash perfectly.
SHA-256: 315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3

QUIT
Server response: 200 OK: Goodbye!
Disconnected from the server session.
```

## How It Works

- **Authentication**: Client logs in with a username from `users.json`
- **Message Relay**: Server acknowledges text messages with a success response
- **File Transfer**: Server receives files with SHA-256 hash verification for integrity
- **Storage**: Received files are stored in the `server_storage/` directory
- **Reconnection**: Client can reconnect automatically if the server becomes unavailable

## Link to Demo Video

https://youtu.be/_tMXCVRNe8E?si=zoQtLGgiWoR1fDGT 