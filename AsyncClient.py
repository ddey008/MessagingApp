import asyncio
import aioconsole


class AsyncClient:
    def __init__(self, server, port):
        self.SERVER = server
        self.PORT = port
        self.HEADER = 128
        self.FORMAT = "utf-8"
        self.ADDRESS = (self.SERVER, self.PORT)
        self.DISCONNECTED = "!EXITING..."
        self.USER_AUTHENTICATED = "User Authenticated"
        self.USER_NOT_AUTHENTICATED = "Incorrect Username Or Password"
        self.reader = None
        self.writer = None

    # Send Message To The Server.
    async def send_message(self, writer, message):
        if message.lower() == "exit":
            message_length = len(self.DISCONNECTED)
            send_length = str(message_length).encode(self.FORMAT)
            send_length += b' ' * (self.HEADER - len(send_length))
            writer.write(send_length)  # Sending Bytes.
            await writer.drain()  # Ensure the message is sent
            writer.write(self.DISCONNECTED.encode(self.FORMAT))  # Sending String.
            await writer.drain()
            return True  # Return This Only When You Want To End The Conversation.
        else:
            # Sends A Normal Message.
            message_length = len(message)
            send_length = str(message_length).encode(self.FORMAT)
            send_length += b' ' * (self.HEADER - len(send_length))
            writer.write(send_length)  # Sending Bytes.
            await writer.drain()  # Ensure the message is sent
            writer.write(message.encode(self.FORMAT))  # Sending String.
            await writer.drain()
            return False  # If Everything Is Normal.

    # Reads And Returns The Received Message.
    async def receive_message(self, reader):
        data_length = await reader.read(self.HEADER)  # Reading The Length Of The Message.
        data_length = int(data_length)
        data = await reader.read(data_length)  # Actual Data
        data.decode(self.FORMAT)
        return data

    def _user_authenticate(self):
        print("Do You Want To Log in Or Sign Up?", end="")
        authentication_message = input().lower().replace(" ", "")
        if authentication_message == "login" or authentication_message == "signup":
            pass
        else:
            print("Please Choose A Correct Option.")
            self._user_authenticate()
        print(" Enter Your Username: ", end="")
        username_message = input().lower()
        print("Enter Your Password: ", end="")
        password_message = input().lower()

        # Sending Login Credentials.
        if authentication_message == "login":
            self.send_message(self.writer, "login")
            self.send_message(self.writer, username_message)
            self.send_message(self.writer, password_message)
        # Sending Signup Credentials.
        if authentication_message == "signup":
            self.send_message(self.writer, "signup")
            self.send_message(self.writer, username_message)
            self.send_message(self.writer, password_message)

        # After Sending User Credentials, Wait For The Server To Respond Continue Or Not.
        data = self.receive_message(self.reader)  # Server Response Data.
        if data == self.USER_AUTHENTICATED:
            return
        elif data == self.USER_NOT_AUTHENTICATED:
            print(self.USER_NOT_AUTHENTICATED)
        self._user_authenticate()

    async def server_connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.SERVER, self.PORT)
        print(f"Connected to server at {self.SERVER}:{self.PORT}")
        self._user_authenticate()  # Must Be Checked Before Continuing.
        print("Enter a message to send to the server (type 'exit' to quit): ")
        while True:
            # Send a Exit message
            # input() is a blocking statement, cannot use it here.
            message = await aioconsole.ainput()  # Non Blocking, Suitable For Async Programming.
            # Sends The Message And Checks If Can_Exit The Loop.
            can_exit = await self.send_message(self.writer, message)
            # Allows For Loop Breakage.
            if can_exit:
                break
            # Wait for a response
            data = await self.receive_message(self.reader)
            print(f"Server: {data}")

        # Close the connection
        self.writer.close()
        await self.writer.wait_closed()
        print("Connection closed.")


async def main():
    client = AsyncClient('192.168.1.159', 8888)  # Adjust the host and port as necessary
    await client.server_connect()
    # After Done With Connection, Could Be Useful For UI stuff.


if __name__ == "__main__":
    asyncio.run(main())
