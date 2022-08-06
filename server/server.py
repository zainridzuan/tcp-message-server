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
import json, sys, select, re

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
        print(f"===== New connection created for: {client_address} =====")
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
                if re.match("BCM\s+(?![a-zA-Z!@#$%.?,])", message): 
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
            elif message == "SRM":
                self.process_srm()
            elif message == "RDM":
                self.process_rdm()
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
        client_request = json.loads(payload.decode('utf-8'))

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
                    "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
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
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "username": dict['username'],
            "message": message
        }
        msg_confirm = add_messsagelog(msg_details)
        server_message = "message sent successfully"
        self.client_socket.sendall(server_message.encode())
        self.client_socket.send(bytes(json.dumps(msg_confirm).encode()))
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
        self.client_socket.send(bytes(json.dumps(everyone_else_log).encode()))

    # handle separate room building
    def process_srb(self, user_list):
        global rooms
        checked_users = are_they_online(user_list)
        offline = []
        invalid = []
        for user in checked_users:
            if checked_users[user] == "offline":
                offline.append(user)
            elif checked_users[user] == "invalid":
                invalid.append(user)
        
        requesting_user = address_to_userlog_dict(userlog, self.client_address)['username']
        if user_list == [requesting_user]:
            server_message = "unsuccessful room creation"
            print(f"[send] new room could not be created for {self.client_address}")
            self.client_socket.sendall(server_message.encode())
            return 
        else:
            user_list.append(requesting_user)
        
        if not offline and not invalid:
            room_info = {
                "room_id": len(rooms) + 1,
                "users": user_list
            }
            rooms.append(room_info)
            filename = f"SR_{room_info['room_id']}_messagelog.txt"
            f = open(filename, 'x')
            f.close
            server_message = "successful separate room creation"
            self.client_socket.sendall(server_message.encode('utf-8'))
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
    def process_srm(self):
        return None 

    # handles read message
    def process_rdm(self):
        return None

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
