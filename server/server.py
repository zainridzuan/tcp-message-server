# python 3.9.4
'''
Server needs to accept the following arguments:
-  server_port is the port number that the server will use to communicate with 
   clients. 
-  number_of_consecutive_failed_attempts is an integer from 1 to 5 which is the 
   number of consecutive unsuccessful authentication attempts before a user 
   should be blocked for 10 second.
The server needs to be ran before the clients. Needs to be initiated as:
-  python3 server.py server_port number_of_consecutive_failed_attempts
'''

from socket import * 
from server_utils import *
from threading import Thread
from numpy import number
from datetime import datetime, timedelta
import json, sys, re

number_of_consecutive_failed_attempts = 0
login_attempts = {}
blocked = {}
when_blocked = {}
active_users = []
userlog = []
rooms = []
message_count = 0

class ClientThread(Thread):
    def __init__(self, client_address, client_socket):
        Thread.__init__(self)
        self.client_address = client_address
        self.client_socket = client_socket
        self.client_alive = False        
        print(f"===== new connection created for: {client_address} =====")
        self.client_alive = True

    def run(self): 
        global userlog
    
        message=""
        while self.client_alive:
            # use recv() to receive message from the client
            data = self.client_socket.recv(4096)
            message = data.decode()

            # if the message from client is empty, the client would be off-line then set the client as offline (alive=Flase)
            if message == "":
                self.client_alive = False
                print(f"===== the user disconnected - {self.client_address}")
                
                # remove user off active_users and userlog and then update userlog.txt
                dict = address_to_userlog_dict(userlog, self.client_address)
                if dict is not None:
                    username = dict["username"]
                    index = active_users.index(username)
                    active_users.remove(username)
                    seq_no = dict["active user sequence number"]
                    userlog[:] = [d for d in userlog if d.get("active user sequence number") != seq_no]

                    for i in range(index, len(userlog)):
                        userlog[i]["active user sequence number"] = userlog[i]["active user sequence number"] - 1
                    update_userlog(userlog)
                break
            elif message == "login":
                print(f"[recv] new login request from {self.client_address}")
                self.process_login()
            elif re.match("BCM *", message):
                if re.match("BCM\s+(?![a-zA-Z0-9!@#$%.?,])", message): 
                    print(f"[recv] invalid BCM request from {self.client_address}")
                    server_message = "invalid BCM request"
                    self.client_socket.sendall(server_message.encode()) 
                else:
                    print(f"[recv] new BCM request from {self.client_address}")
                    bcm_msg = message.split(" ", 1)
                    msg = bcm_msg[1]
                    self.process_bcm(msg)             
            elif message == "ATU":
                print(f"[recv] new ATU request from {self.client_address}")
                self.process_atu()
            elif re.match("SRB [^ ].*", message):
                print(f"[recv] new SRB request from {self.client_address}")
                users_str = message.split(" ", 1)[1]
                users_list = users_str.split()
                self.process_srb(users_list)
            elif re.match("SRM.*", message):
                args = message.split()
                if len(args) != 3:
                    print(f"[recv] invalid SRM request from {self.client_address}")
                    server_message = "invalid SRM request"
                    self.client_socket.sendall(server_message.encode()) 
                else:
                    room_id = int(args[1])
                    message = args[2]
                    if isinstance(room_id, int) and isinstance(message, str):
                        print(f"[recv] SRM request from {self.client_address}")
                        self.process_srm(room_id, message)
                    else:
                        print(f"[recv] invalid SRM request from {self.client_address}")
                        server_message = "invalid SRM request"
                        self.client_socket.sendall(server_message.encode()) 
            elif re.match("RDM.*", message):
                args = message.split(" ", 2)
                print(f"{type(args[2])}, {args[2]}")
                print(args[1])
                if len(args) != 3:
                    print(f"[recv] invalid RDM request from {self.client_address}")
                    server_message = "invalid RDM request"
                    self.client_socket.sendall(server_message.encode()) 
                if ( args[1] == 'b' or args[1] == 's') and isinstance(args[2], str):
                    print(f"[recv] RDM request from {self.client_address}")
                    self.process_rdm(args[1], args[2])
                else: 
                    print(f"[recv] invalid RDM request from {self.client_address}")
                    server_message = "invalid RDM request"
                    self.client_socket.sendall(server_message.encode()) 
            elif message == "OUT":
                print(f"[recv] new logout request from {self.client_address}")
                self.process_out()
            else:
                print(f"[recv] unknown input from {self.client_address}")
                server_message = "unknown input"
                self.client_socket.sendall(server_message.encode())
            
    # handle client login
    def process_login(self):
        global login_attempts
        global number_of_consecutive_failed_attempts
        global blocked
        global when_blocked
        global active_users
        global userlog
        
        server_message = "user credentials request"
        print(f"[send] {server_message} for {self.client_address}")
        self.client_socket.sendall(server_message.encode())

        payload = self.client_socket.recv(1024)
        client_request = json.loads(payload.decode())

        credentials = read_credentials()
        username = client_request['username']
        password = client_request['password']

        # checking if the user is blocked
        if username in blocked:
            curr_time = datetime.now()
            time_blocked = curr_time - when_blocked[username]
            if time_blocked.total_seconds() > 10:
                blocked.pop(username)
                when_blocked.pop(username)
                login_attempts[username] = 0
            else:
                print(f"[send] user blocked - {username}")
                self.client_socket.send('user blocked'.encode())
                exit()

        # checking if the user has previous login attempts
        if username in login_attempts:
            if login_attempts[username] >= (number_of_consecutive_failed_attempts - 1):
                # blocking the user and storing when the user was blocked
                curr_time = datetime.now()
                when_blocked[username] = curr_time
                blocked[username] = True
                print(f"[send] user blocked - {username}")
                self.client_socket.send('user blocked'.encode())
        
        # checking if the user information is in credentials.txt 
        # checks if password is correct after
        if username in credentials:
            if credentials[username] == password:
                active_users.append(username)
                print(f"[send] login success {self.client_address}")
                # send json with following information
                # active user sequence number; timestamp; username; client IP address; client UDP server port number
                login_info = {
                    "active user sequence number": active_users.index(username) + 1,
                    "timestamp": datetime.now().strftime("%d %b %Y %H:%M:%S"),
                    "username": username,                        
                    "client IP address": self.client_address                  
                    #"client UDP server port number": ""           
                }
                userlog.append(login_info)
                add_userlog(login_info)
                if username in login_attempts:
                    login_attempts[username] = 0
                self.client_socket.send('login success'.encode())
            elif credentials[username] != password:
                if username not in login_attempts:
                    login_attempts[username] = 0
                login_attempts[username] = login_attempts[username] + 1
                print("[send] login failure")
                self.client_socket.send('login failure'.encode())
        else:
            self.client_socket.send('invalid username'.encode())

    # handles broadcast message
    def process_bcm(self, message):
        global message_count
        message_count = message_count + 1
        dict = address_to_userlog_dict(userlog, self.client_address)
        msg_details = { 
            "message sequence number": message_count,
            "timestamp": datetime.now().strftime("%d %b %Y %H:%M:%S"),
            "username": dict['username'],
            "message": message
        }
        msg_confirm = add_messsagelog(msg_details)
        server_message = "message sent successfully"
        self.client_socket.sendall(server_message.encode())
        payload = json.dumps(msg_confirm)
        self.client_socket.send(bytes(payload.encode()))
        print(f"[send] message sent successfully for {self.client_address}")

    # handles download active users
    def process_atu(self):
        everyone_else_log = []
        for i in userlog:
            if i['client IP address'] != self.client_address:
                everyone_else_log.append(i)
        server_message = "active users request"
        print(f"[send] {server_message} for {self.client_address}") 
        self.client_socket.sendall(server_message.encode())
        payload = json.dumps(everyone_else_log)
        self.client_socket.send(bytes(payload.encode()))

    # handle separate room building
    def process_srb(self, user_list):
        global rooms  
        # checking if user is trying to create a room for themselves
        requesting_user = address_to_userlog_dict(userlog, self.client_address)['username']
        if user_list == [requesting_user]:
            server_message = "unsuccessful room creation"
            print(f"[send] new room could not be created for {self.client_address}")
            self.client_socket.sendall(server_message.encode())
            return 
        else:
            user_list.append(requesting_user)

        # checking if room already exists
        for room in rooms:
            if set(user_list) == set(room['users']):
                print(f"[send] new room could not be created for {self.client_address}")
                server_message = "room exists"
                self.client_socket.sendall(server_message.encode())
                payload = json.dumps(room)
                self.client_socket.sendall(bytes(payload.encode()))
                return

        checked_users = are_they_online(user_list)
        offline = []
        invalid = []
        for user in checked_users:
            if checked_users[user] == "offline":
                offline.append(user)
            elif checked_users[user] == "invalid":
                invalid.append(user)
        
        if not offline and not invalid:
            room_info = {
                "room_id": len(rooms) + 1,
                "users": user_list,
                "message_count": 0
            }
            rooms.append(room_info)
            filename = f"SR_{room_info['room_id']}_messagelog.txt"
            f = open(filename, 'x')
            f.close
            server_message = "successful separate room creation"
            self.client_socket.sendall(server_message.encode())
            print(f"[send] new room created for {self.client_address}")
            self.client_socket.send(bytes(json.dumps(room_info).encode()))
        else:
            server_message = "invalid room creation"
            self.client_socket.sendall(server_message.encode())
            print(f"[send] new room could not be created for {self.client_address}")
            invalid_users = {
                "offline": offline,
                "invalid": invalid
            }
            self.client_socket.send(bytes(json.dumps(invalid_users).encode()))


    # handle separate room message
    def process_srm(self, room_id, message):
        global rooms
        username = address_to_userlog_dict(userlog, self.client_address)['username']
        index = int(room_id) - 1
        if len(rooms) >= index:
            if rooms[index]["room_id"] == room_id:
                if username in rooms[index]["users"]:
                    log = f"SR_{room_id}_messagelog.txt"
                    msg_details = {
                        "message sequence number": rooms[index]["message_count"] + 1,
                        "timestamp": datetime.now().strftime("%d %b %Y %H:%M:%S"),
                        "username": username,
                        "message": message
                    }
                    msg_confirm = add_messagesr(log, msg_details)
                    server_message = "successful separate room message"
                    self.client_socket.sendall(server_message.encode())
                    payload = json.dumps(msg_confirm)
                    self.client_socket.send(bytes(payload.encode()))
                    print(f"[send] successful separate room message request for {self.client_address}")
                else: 
                    print(f"[send] invalid separate room message request for {self.client_address}")
                    server_message = "user not in room"
                    self.client_socket.sendall(server_message.encode())
            else:
                print(f"[send] invalid separate room message request for {self.client_address}")
                server_message = "room doesn't exist"
                self.client_socket.sendall(server_message.encode())
        else: 
            print(f"[send] invalid separate room message request for {self.client_address}")
            server_message = "room doesn't exist"
            self.client_socket.sendall(server_message.encode())

    # handles read message
    def process_rdm(self, message_type, datetime_string):
        # time string to time variable
        timestamp = datetime.strptime(datetime_string, "%d %b %Y %H:%M:%S")
        # 
        msg_to_read = []
        if message_type == 'b':
            with open("messagelog.txt", "r") as file:
                for line in file:
                    strip = line.split("; ")
                    seq_no = strip[0]
                    line_date_str = strip[1]
                    #line_date_str = line_date_str[:-1]
                    user = strip[2]
                    message = strip[3]
                    message = message[:-2]
                    line_date = datetime.strptime(line_date_str, "%d %b %Y %H:%M:%S")
                    if line_date > timestamp:
                        msg_to_read.append(f"{seq_no}; {user}: {message} at {line_date_str}")            
            read_messages_info = {
                "messages": msg_to_read,
                "datetime": datetime_string
            }
            server_message = "read bc messages success"
            self.client_socket.sendall(server_message.encode())
            payload = json.dumps(read_messages_info)
            self.client_socket.send(bytes(payload.encode()))
        elif message_type == 's':
            read_messages_info = []
            requesting_user = address_to_userlog_dict(userlog, self.client_address)
            for room in rooms:
                if requesting_user in room["users"]:
                    fname = f"SR_{room['room_id']}_messagelog.txt"
                    with open(fname, "r") as file:
                        for line in file:
                            strip = line.split("; ")
                            seq_no = strip[0]
                            line_date_str = strip[1]
                            user = strip[2]
                            message = strip[3]
                            message = message[:-2]
                            line_date = datetime.strptime(line_date_str, "%d %b %Y %H:%M:%S")
                            if line_date > timestamp:
                                msg_to_read.append(f"{seq_no}; {user}: {message} at {line_date_str}")
                                tmp = {
                                    'room_id': room['room_id'],
                                    'messages': msg_to_read,
                                    'datetime': datetime_string
                                }
                                read_messages_info.append(tmp)     
            server_message = "read sr messages success"
            self.client_socket.sendall(server_message.encode())
            payload = json.dumps(read_messages_info)
            self.client_socket.send(bytes(payload.encode()))
    
    # handles logout
    def process_out(self):
        server_message = "logout request"
        print(f"[send] {server_message} for {self.client_address}")
        self.client_socket.sendall("logout".encode())

def start_server(server_host, server_port):
    server_address = (server_host, server_port)
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(server_address)
    print(f"The server is running on {gethostbyname(gethostname())}")

    while True:
        server_socket.listen(1)
        client_socket, client_address = server_socket.accept()
        client_thread = ClientThread(client_address, client_socket)
        client_thread.start()

if __name__ == "__main__":
    # acquire server host and port from command line parameter
    if len(sys.argv) != 3:
        print("\n===== Error usage, python3 server.py <server_port> <number_of_consecutive_login_attempts> ======\n")
        exit(0)
    server_host = gethostname()
    server_port = int(sys.argv[1])
    number_of_consecutive_failed_attempts = int(sys.argv[2])
    if number_of_consecutive_failed_attempts not in range(1,6):
        print("\n===== Invalid number of allowed failed consecutive attempt ======\n")
        exit()
    
    clear_userlog()
    clear_messagelog()
    reset_rooms()
    start_server(server_host, server_port)
