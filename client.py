import socket
import threading


class Client:
    def __init__(self):
        self.HEADER = 128
        self.PORT = 5050
        self.SERVER = '192.168.1.159'  # Need To Be Specific To Reach The Server.
        self.FORMAT = "utf-8"
        self.ADDRESS = (self.SERVER, self.PORT)
        self.DISCONNECTED = "!EXITING..."
        self.USER_AUTHENTICATED = "User Authenticated"
        self.USER_NOT_AUTHENTICATED = "Incorrect Username Or Password"
        self.is_authenticated = False
        # Setting Up Socket For The Client.
        # Sock_Stream means use TCP/IP Address.
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(self.ADDRESS)  # Connecting To The Server Through Server Socket.
        print("Connected To The Server")
        thread = threading.Thread(target=self.handle_server_responses)  # Creates Another Thrd To Deal With Server Resp.
        thread.start()  # Starting The Thread.
        self.start()

    def start(self):
        # Authenticate The User First.
        self._user_authenticate()
        #  Wait Until Any Confirmation Of Authentication is Received.
        while not self.is_authenticated:
            pass
        print("Enter a message to send to the server (type 'exit' to quit): ")
        while True:
            message = input()  # Gets The Message Input From The User.
            if message.lower() == 'exit':
                message_length = len(self.DISCONNECTED)
                send_length = str(message_length).encode(self.FORMAT)
                send_length += b' ' * (self.HEADER - len(send_length))
                self.client.send(send_length)  # Sending The Length Of Disconnected
                self.client.send(self.DISCONNECTED.encode(self.FORMAT))
                break

            # Always Send 2 messages, 1 For the length And Other For The Message. Need To Pad The Send_Length
            message_length = len(message)
            send_length = str(message_length).encode(self.FORMAT)
            send_length += b' ' * (self.HEADER - len(send_length))
            self.client.send(send_length)
            # Otherwise We Just Encode The Message And Send It To The Server
            self.client.send(message.encode(self.FORMAT))
            print(f"[You: {message} ]")

    def handle_server_responses(self):
        while True:
            message_length = self.client.recv(self.HEADER).decode(self.FORMAT)
            message_length = len(message_length)
            response = self.client.recv(message_length).decode(self.FORMAT)  # Receiving Actual Server Responses.
            sender_address = self.client.recv(self.HEADER).decode(self.FORMAT)  # The Address Of The Sender
            if response == self.DISCONNECTED:
                print(f"Client {self.client.getsockname()} disconnected.")
                break
            if response == self.USER_AUTHENTICATED:
                self.is_authenticated = True
            if response == self.USER_NOT_AUTHENTICATED:
                print(f"[{sender_address}: {self.USER_NOT_AUTHENTICATED}]")
                self._user_authenticate()

            print(f"[{sender_address}: {response}]")

    # Asks User For Login & Password and Passes Info To Appropriate Functions if Needed
    # _ To Imply That This is a private class.
    def _user_authenticate(self):
        print("Do You Want To Log in Or Sign Up?", end="")
        authentication_message = input().lower().replace(" ", "")
        if authentication_message == "login" or authentication_message == "signup":
            pass
        else:
            self._user_authenticate()
            print("Please Choose A Correct Option.")
        print(" Enter Your Username: ", end="")
        username_message = input().lower()
        print("Enter Your Password: ", end="")
        password_message = input().lower()

        if authentication_message == "login":
            self._client_login(username_message, password_message)
        elif authentication_message == "signup":
            self._client_signup(username_message, password_message)

    # If The User Chooses To Log in, call this function.
    def _client_login(self, message, message1):
        # Send Over Unsecure Channels For Now, Need To Change When Adding Encryption Algorithm.
        # Sending Login Message
        send_length = str(5).encode(self.FORMAT)
        send_length += b' ' * (self.HEADER - len(send_length))
        self.client.send(send_length)
        self.client.send("login".encode(self.FORMAT))

        # For Sending Username.
        message_length = len(message)
        send_length = str(message_length).encode("utf-8")
        send_length += b' ' * (128 - len(send_length))
        self.client.send(send_length)
        self.client.send(message.encode("utf-8"))

        # For Sending Password
        message_length = len(message1)
        send_length = str(message_length).encode("utf-8")
        send_length += b' ' * (128 - len(send_length))
        self.client.send(send_length)
        self.client.send(message.encode("utf-8"))

    # If The User Chooses To Sign Up, Call This Function.
    def _client_signup(self, message, message1):
        # Send Over Unsecure Channels For Now, Need To Change When Adding Encryption Algorithm.
        # Sending SignUp Message
        send_length = str(6).encode(self.FORMAT)
        send_length += b' ' * (self.HEADER - len(send_length))
        self.client.send(send_length)
        self.client.send("signup".encode(self.FORMAT))

        # For Sending Username.
        message_length = len(message)
        send_length = str(message_length).encode("utf-8")
        send_length += b' ' * (128 - len(send_length))
        self.client.send(send_length)
        self.client.send(message.encode("utf-8"))

        # For Sending Password
        message_length = len(message1)
        send_length = str(message_length).encode("utf-8")
        send_length += b' ' * (128 - len(send_length))
        self.client.send(send_length)
        self.client.send(message.encode("utf-8"))


if __name__ == "__main__":
    Client()
