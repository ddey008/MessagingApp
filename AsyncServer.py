import asyncio
import socket
import threading
import queue
from databse import Database


def run_async_function(async_func, *args):
    """Run an async function in a new event loop."""
    asyncio.run(async_func(*args))


class Server:
    def __init__(self):
        self.SERVER = socket.gethostbyname(socket.gethostname())
        self.PORT = 8888
        self.HEADER = 128
        self.FORMAT = "utf-8"
        self.DISCONNECTED = "!EXITING..."
        self.USER_AUTHENTICATED = "User Authenticated"
        self.USER_NOT_AUTHENTICATED = "Incorrect Username Or Password"
        self.database = Database()
        self.message_queue = queue.Queue()  # For Adding Messages Onto The Database.
        asyncio.run(self.start())

    # Reads And Returns The Message Sent By Client.
    async def receive_message(self, reader):
        # Read data from the client
        data_length = await reader.read(self.HEADER)  # Reading The Length Of The Message.
        data_length = int(data_length)
        data = await reader.read(data_length)  # Actual Data
        data.decode("utf-8")
        return data

    # Sends The Message To The Respective Client.
    async def send_message(self, writer, response):
        message_length = len(response)
        send_length = str(message_length).encode(self.FORMAT)
        send_length += b' ' * (self.HEADER - len(send_length))
        writer.write(send_length)  # Send The Length Of The Message In Bytes
        await writer.drain()  # Ensure the data is sent
        writer.write(response.encode(self.FORMAT))
        await writer.drain()

    async def handle_client(self, reader, writer, username):
        # // addr = writer.get_extra_info('peername')

        print(f"[NEW CONNECTION] {username} connected.")
        # Ask For User Authentication.
        while True:
            # Read data from the client
            data = await self.receive_message(reader)
            print(f"{username}: {data}")
            # Closing Client Code
            if data == self.DISCONNECTED:
                break
            # Send a response back to the client
            response = "Message received"
            await self.send_message(writer, response)

        writer.close()  # Close the connection
        await writer.wait_closed()  # Wait for the writer to close

    def create_client_connection(self, reader, writer):
        # Authenticate The User Before Even Creating The Thread.
        while True:
            username, continue_connect = self._user_authentication(reader)
            if continue_connect:
                self.send_message(writer, self.USER_AUTHENTICATED)  # Give Confirmation To Client.
                break
            self.send_message(writer, self.USER_NOT_AUTHENTICATED)  # Telling Client Some Mistake Happened.
        # Create a new thread that runs the async function
        thread = threading.Thread(target=run_async_function, args=(self.handle_client, reader, writer, username))
        thread.start()

    # If The User Is Trying To Sign Up, add their credentials to the database.
    # If The User Is Trying To Log In, Check If They Exist and match their password.
    # Server Can only send two Types Of Responses: "successful", "unsuccessful"(Meaning Password Doesn't Match"
    # Don't Need To Check If User Exists Or Not Because The Database Doesn't Accept Duplicate Entries.
    # SINCE SQLITE DATABASE ONLY ACCEPTS EDITS FROM WHERE IT IS CREATED, CHECK IN MAIN THREAD.
    def _user_authentication(self, reader):

        type_message = self.receive_message(reader)  # Receiving Action Type/ Login or Sign Up.
        username_message = self.receive_message(reader)  # Receiving Username.
        password_message = self.receive_message(reader)  # Receiving Password.

        # Adds The User Onto The Database
        if type_message == "signup":
            checker = self.database.add_user(username_message, password_message, None)
            if checker:
                # Allow The Client To Enter The Server And Talk Normally.
                return username_message, True
            else:
                # False Means That The Username Already Exist. Thereby Just Athenticate them.
                type_message = "login"

        # Checks If User Exists
        if type_message == "login":
            checker = self.database.user_authentication(username_message, password_message)
            if checker:
                # Allow The Client To Enter The Server And Talk Normally
                return username_message, True
            else:
                # Implement Logic That Tells The Client That Their Username Or Password Is Faulty.
                return username_message, False

    async def start(self):
        # Starts The Server And The Listening For Incoming Connections.
        server = await asyncio.start_server(self.create_client_connection, self.SERVER, 8888)
        print("[STARTING] server is starting...")
        print(f"[Server Is Listening On:] {self.SERVER}")
        async with server:
            await server.serve_forever()


if __name__ == "__main__":
    Server()
