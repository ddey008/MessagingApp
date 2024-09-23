import bcrypt
import aiosqlite


# PUT EVERYTHING ON AWAIT BECAUSE THAT HELPS WITH ASYNCH
# Handling Multiple Users Concurrently
# Bcrypt Is A One Way Password Creator so there is no reverse Hashing.
# The salt is added onto the password to make the hash more complex, and then they are hashed together.
def create_new_password(password):
    salt = bcrypt.gensalt()
    #  Hashing The Password.
    hash_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hash_password


# Returns True If The Password Matches and False If Otherwise.
def check_password(stored_password, password_being_checked):
    return bcrypt.checkpw(stored_password, password_being_checked)


class Database:
    #  Initializing Constructors
    def __init__(self):
        self.conn = None  # Connecting To The Database
        self.cursor = None
        self.GROUP_RECEIVER_ID = "ALL"

    #  Predefined Function To Allow User To Enter The Database.
    async def __aenter__(self):
        self.conn = await aiosqlite.connect("example.db")
        self.cursor = await self.conn.cursor()
        await self.__private_start()
        return self

    # Exit Out Of The Code When Necessary.
    async def __aexit__(self):
        self.conn.close()

    # Used During Initialization To Help Construct The Database
    async def __private_start(self):
        # SQL command to create userList table
        # UserList cannot hold any duplicates.
        # UserList holds userid, username, password and their email address
        # Used mainly for password and user Authentication
        self.cursor.excecute('''
              CREATE TABLE IF NOT EXISTS userList (
                  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL UNIQUE,
                  password TEXT NOT NULL UNIQUE,
                  nickname TEXT NOT NULL NOT UNIQUE,
                  email TEXT UNIQUE
              )
              ''')
        # Creating A Chat List.
        # ChatList Cannot Hold Duplicate Chat_Ids.
        # ChatList holds The MetaDat for all chats.
        # Used Mainly To Create And Manage Multiple Chats Of The User, Affectively.
        self.cursor.execute('''
           CREATE TABLE IF NOT EXISTS chatList (
                chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Holds The Chat Participants For Every Single Chat
        # Link It With Every Chat To Create A Chain
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatParticipants (
                chat_id INTEGER,
                user_id INTEGER,
                PRIMARY KEY (chat_id, user_id),
                FOREIGN KEY (chat_id) REFERENCES chatList(chat_id),
                FOREIGN KEY (user_id) REFERENCES userList(user_id)
                )
        ''')

        # Holds All Messages/Chats Across All Chats.
        # Used Mainly for message History and Chat Loadings.
        # Foreign Key Is Primarily Used For Connecting Multiple Tables.
        # DATETIME DEFAULT automatically adds the timestamp of each message.
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messageList (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                message_text TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chatList(chat_id),
                FOREIGN KEY (sender_id) REFERENCES userList(user_id)
            )
            ''')
        await self.conn.commit()

    # Adds All The Messages That Are Sent In A Database For Further Database retrieval.
    async def add_message(self, sender_username, chat_id):
        pass

    # Allows The User To Edit Messages.
    async def edit_message(self, sender_username, chat_id, message):
        pass

    # Allows The User To Delete Sent Messages.
    async def delete_message(self, sender_username, chat_id, message):
        pass

    async def create_new_chat(self):
        pass

    # Add User With Username And Password In The userList.
    # Additionally, Ensures The Password Is Encrypted With Bcrypt.
    # Checks If user inputted email, else put in null in the database.
    # Returns A Message Indicating Success Or Failure.
    async def add_user(self, username, password, email):
        # Store The Hashed Password
        password = create_new_password(password)
        try:
            await self.cursor.execute('''
                INSERT INTO userList (username, email, password)
                VALUES(?,?,?)
            ''', (username, password, email))
            await self.conn.commit()  # Actually Implements The Changes.
            return True
        # Error When Username Already Exists
        except aiosqlite.IntegrityError:
            await self.conn.rollback()  # Reverse The Changes As Its Very Error Prone.
            return False

    # Returns The Message History Of The User If Needed.
    async def message_history(self, chat_id):
        pass

    async def edit_email(self, username):
        pass

    # Authenticates The User.
    # Used For Login.
    # True Means User Exists And His Password Is Correct, False Means Username or Password Is Wrong.
    async def user_authentication(self, username, password):
        try:
            await self.cursor.execute('''
                            SELECT * FROM userList WHERE username = ?
                        ''', (username,))
            #   Holds userid, username, password and email as data
            user_data = await self.cursor.fetchone()  # Fetch The First Row In Result Set.
            if user_data:
                stored_password = user_data[2]  # Gets Only The Password
                if check_password(stored_password, password):
                    return True
            return False
        except aiosqlite.Error:
            return False
