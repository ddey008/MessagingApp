import socket
import threading
from collections import deque
import asyncio
from databse import Database


class Server:
    # Basic Server Initialization
    def __init__(self):
        self.HEADER = 128
        self.PORT = 5050
        self.SERVER = socket.gethostbyname(socket.gethostname())
        self.FORMAT = 'utf-8'
        self.ADDRESS = (self.SERVER, self.PORT)  # Server Ip Address.
        self.DISCONNECTED = "!EXITING..."
        self.USER_AUTHENTICATED = "User Authenticated"
        self.USER_NOT_AUTHENTICATED = "Incorrect Username Or Password"
        self.message_queue = deque()  # Stores All The Messages In A Queue.
        self.clist_list = []
        self.database = Database()  # Holds Access to The DataBase.
        self.asyncronous_loop = asyncio.get_event_loop()
        # Creating A Socket To Open Up This Device To Other Connections.
        # To Do That Bind The PORT and SOCKET onto the Actual Socket.
        # Creating A New Socket That Accepts Only Certain Types Of IP Address.
        # SOCK_STREAM Makes It So That Socket sets a TCP Connection for safe socket connection.

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(self.ADDRESS)

        self.start()  # Starts The Programs.

    # Gets The Socket/Server Started To Send And Receive Data.
    # Ensures All Threads Created Are Safe And Efficient.
    # The Server Thread Is Using Async Programming To Ensure That The Database and client creator works concurrently.
    def start(self):
        self.server.listen()  # Server Is Waiting For Connections.
        print(f"Server is listening on {self.SERVER}:{self.PORT}...")
        #  Creating A Message Sender Thread That Simultaneously Sends All Messages Saved In Server.
        messenger_thread = threading.Thread(target=self.forward_messages)
        messenger_thread.start()
        while True:
            conn, addr = self.server.accept()  # Server Is Accepting Connections.
            # Makes A New Thread To Allow Client Stuff.
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.start()
            self.clist_list.append(conn)  # Adds All The Client Lists Into The Right Spot.
            print(f"[ACTIVE CONNECTIONS:] {threading.active_count() - 1}")


    # Handles All The Singular Clients And Their Threads Of Execution.
    # Mainly Receives All The Messages, And Adds Them Into This Queue.
    # The Queue Would Be Executed By The Forward Messages To The Appropriate Destination.
    def handle_client(self, conn, addr):
        username, user_exists = self._user_authentication(conn)
        if user_exists:
            # Send Confirmation To The Client that user exists.
            message_length = len(self.USER_AUTHENTICATED)
            send_length = str(message_length).encode("utf-8")
            send_length += b' ' * (self.HEADER - len(send_length))
            conn.send(send_length)
            conn.send(self.USER_AUTHENTICATED.encode(self.FORMAT))
            conn.send("SERVER".encode(self.FORMAT))  # Sending Address.
            while True:
                message_length = conn.recv(self.HEADER).decode(self.FORMAT)  # Decoding The Bytes Into A String
                if message_length:
                    message_length = int(message_length)  # Converting Expected Message Length Into An Int.
                    message = conn.recv(message_length).decode(self.FORMAT)  # Receiving The Actual Message
                    if message == self.DISCONNECTED:
                        print(f"{username} disconnected.")
                        break
                    print(f"[{username}:{message} ]")
                    self.message_queue.append((conn, message))  # Creating A Tuple Of The Client_Socket And Message.

            self.clist_list.remove(conn)  # Remove Client From Client List.
            conn.close()  # Close The Connection Cleanly.
            print(f"Connection Closed With: {username}")
        else:
            # User Don't Exist.
            message_length = len(self.USER_NOT_AUTHENTICATED)
            send_length = str(message_length).encode("utf-8")
            send_length += b' ' * (self.HEADER - len(send_length))
            conn.send(send_length)
            conn.send(self.USER_NOT_AUTHENTICATED.encode(self.FORMAT))
            conn.send("SERVER".encode(self.FORMAT))  # Sending Address.

    # Forwards All The Messages In Queue, on a different Thread.
    def forward_messages(self):
        while True:
            # Sending Each Message To Everyone In The Group.
            if len(self.message_queue) > 0:
                message = self.message_queue.popleft()  # Gets (client_socket,message)
                for arr in self.clist_list:
                    if arr == message[0]:
                        continue
                    #  If It's Not Self, Keep Sending Messages.
                    message_length = str(len(message[1])).encode(self.FORMAT)
                    message_length += b' ' * (self.HEADER - len(message_length))
                    arr.send(message_length)  # Sending The Length Of The Actual Message.
                    arr.send(message[1].encode(self.FORMAT))  # Sending The Actual Message.
                    arr.send(str(message[0].getsockname()).encode(self.FORMAT))  # Sending The Message Address

    # If The User Is Trying To Sign Up, add their credentials to the database.
    # If The User Is Trying To Log In, Check If They Exist and match their password.
    # Server Can only send two Types Of Responses: "successful", "unsuccessful"(Meaning Password Doesn't Match"
    def _user_authentication(self, conn):
        # Receiving Action Type/ Login or Sign Up.
        message_length = int(conn.recv(self.HEADER).decode(self.FORMAT))
        type_message = conn.recv(message_length).decode(self.FORMAT)
        # Don't Need To Check If User Exists Or Not Because The Database Doesn't Accept Duplicate Entries.

        # Receiving Username.
        message_length = int(conn.recv(self.HEADER).decode(self.FORMAT))
        username_message = conn.recv(message_length).decode(self.FORMAT)

        # Receiving Password.
        message_length = int(conn.recv(self.HEADER).decode(self.FORMAT))
        password_message = conn.recv(message_length).decode(self.FORMAT)

        # Adds The User Onto The Database
        if type_message == "signup":
            checker = self.database.add_user(username_message, password_message, None)
            if checker:
                # Allow The Client To Enter The Server And Talk Normally.
                # Return Username So That When The Message Is Being Displayed, It will be the Username not the IP Addr.
                return username_message, True
            else:
                # False Means That The Username Already Exist. Thereby Just Athenticate them.
                type_message = "login"

        # Checks If User Exists
        elif type_message == "login":
            checker = self.database.user_authentication(username_message, password_message)
            if checker:
                # Allow The Client To Enter The Server And Talk Normally
                return username_message, True
            else:
                # Implement Logic That Tells The Client That Their Username Or Password Is Faulty.
                return username_message, False


if __name__ == "__main__":
    Server()
