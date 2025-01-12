import socket
import threading
import json

class Server:
    def __init__(self, host="0.0.0.0", port=54320):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []  # To store connected clients
        self.client_lock = threading.Lock()

    def start(self) -> None:
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(2)  # Only allow two connections
        print(f"[LISTENING] Server is listening on {self.host}:{self.port}")

        while len(self.clients) < 2:
            client_socket, client_address = self.server_socket.accept()
            with self.client_lock:
                username = client_socket.recv(1024).decode("utf-8").strip()
                self.clients.append((client_socket, client_address, username))
            print(f"[NEW CONNECTION] {client_address} connected.")

        print("[GAME STARTING] Two players connected. Starting the game!")
        threading.Thread().start()


    def broadcast(self, message: str) -> None:
        """Send a message to all connected clients."""
        with self.client_lock:
            for client_socket, _, _ in self.clients:
                try:
                    client_socket.send(message.encode("utf-8"))
                except Exception as e:
                    print(f"[ERROR] Could not send message: {e}")

    def close_connections(self) -> None:
        """Close all client connections and the server socket."""
        with self.client_lock:
            for client_socket, client_address, username in self.clients:
                try:
                    client_socket.close()
                    print(f"[DISCONNECTED] {username}({client_address}) disconnected.")
                except Exception as e:
                    print(f"[ERROR] Closing connection {client_address}: {e}")

        self.server_socket.close()
        print("[SERVER SHUTDOWN] Server has been shut down.")

    def send_list_to_clients(self, list: list) -> None:
        """Send a list of items to all connected clients."""
        list_json = json.dumps(list)
        self.broadcast(list_json)

    def get_answer_from_clients(self) -> list:
        """Receive answers from all connected clients."""
        answers = []
        with self.client_lock:
            for client_socket, client_address, username in self.clients:
                try:
                    answer = client_socket.recv(1024).decode("utf-8")
                    answers.append((username, answer))
                except Exception as e:
                    print(f"[ERROR] Receiving answer from {username}: {e}")
        return answers
    
    def get_ready_from_clients(self) -> None:
        """Wait for all clients to be ready."""
        with self.client_lock:
            for client_socket, _, username in self.clients:
                try:
                    client_socket.recv(1024)
                except Exception as e:
                    print(f"[ERROR] Receiving ready message from {username}: {e}")

if __name__ == "__main__":
    server = Server()
    server.start()
