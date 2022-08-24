# python 3.9.4
'''
Client needs to accept the following three arguments:
-  server_IP: IP address of the machine the server is running
-  server_port: the port number being used by the server, same as the first
   argument of the server
-  client_udp_port: the port number that the client will listen to for the UDP 
   traffic from the other clients
Each client needs to be initiated as:
-  python3 client.py server_IP server_port client_udp_server_port
'''

from socket import *
from datetime import datetime
from getpass import getpass
import json
import sys

authenticated = False

def user_login(username, password, client_socket):
    global authenticated
    request = {
        "username": username,
        "password": password
    }

    payload = json.dumps(request)
    client_socket.sendall(bytes(payload.encode()))
    while True:
        payload = client_socket.recv(1024)
        response = payload.decode()
        # We wait to receive the reply from the server, store it in response
        if response == "login success":
            print("> Login Successful!")
            authenticated = True
            break
        elif response == "login failure":
            print("> Invalid password. Please try again.")
            request["password"] = getpass()
            client_socket.sendall("login".encode())
            client_socket.recv(1024)
            payload = json.dumps(request)
            client_socket.sendall(bytes(payload.encode()))
        elif response == "user blocked":
            print("> Your account has been blocked due to multiple unsuccessful login attempts. Please try again later.")
            exit()
        else:
            print(response)

def user_register(username, password, client_socket):
   global authenticated
   request = {
       "username": username,
       "password": password
   }

   payload = json.dumps(request)
   client_socket.sendall(bytes(payload.encode()))
   while True:
       payload = client_socket.recv(1024)
       response = payload.decode()
       # We wait to receive the reply from the server, store it in response
       if response == "registration success":
           print("> Registration Successful!")
           authenticated = True
           return True
       elif response == "registration failure: username":
           print("> Username already exists. Please try a different username.")
           return False
       else:
           print(response)
           return False

def connect_to_server(server_name, server_port):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((server_name, server_port))
    initial_login = True
    while True:
        try: 
            if initial_login == True:
                sent_message = input("===== Enter one of the following commands [Login, Register] =====\n> ")
                client_socket.sendall(sent_message.encode())
            else:
                sent_message = input("===== Enter one of the following commands [BCM, ATU, SRB, SRM, RDM, OUT] =====\n> ")
                client_socket.sendall(sent_message.encode())

            data = client_socket.recv(2048)
            recv_message = data.decode()

            # parse the message received from server and take corresponding actions
            if recv_message == "":
                print("> [recv] Message from server is empty!")
            elif recv_message == "user login request":
                print("> [recv] Please provide username and password to login")
                username = input("username: ")
                password = getpass("password: ")
                user_login(username, password, client_socket)
                initial_login = False
            elif recv_message == "user register request":
                print("> [recv] Please provide username and password to register")
                username = input("username: ")
                password = getpass("password: ")
                password_2 = getpass("confirm password: ")
                while (password != password_2):
                    print("Passwords do not match. Please try again...")
                    username = input("username: ")
                    password = getpass("password: ")
                    password_2 = getpass("confirm password: ")
                if user_register(username, password, client_socket) is True:
                    initial_login = False
            elif recv_message == "logout":
                print(f"> Goodbye, {username}")
                break
            elif recv_message == "active users request":
                payload = client_socket.recv(1024)
                everyone_else_userlog = json.loads(payload.decode())
                if everyone_else_userlog == []:
                    print("> No other active users...")
                else:
                    for i in everyone_else_userlog:
                        print(f"{i['username']}; {i['client IP address'][0]}; active since {i['timestamp']};")
            elif recv_message == "message sent successfully":
                print("> Message sent successfully!")
                payload = client_socket.recv(1024)
                msg = json.loads(payload.decode())
                print(f"> {msg['message_type']}; {msg['sequence_number']}; {msg['timestamp']}")
            elif recv_message == "successful separate room creation":
                payload = client_socket.recv(1024)
                room_info = json.loads(payload.decode())
                print(f"> Separate chat room has been created, room ID: {room_info['room_id']}, users in this room: {room_info['users']}")
            elif recv_message == "unsuccessful room creation":
                print(f"> Unsuccessful room creation. You can't create a room for yourself.")
            elif recv_message == "invalid room creation":
                payload = client_socket.recv(1024)
                offline_invalid = json.loads(payload.decode())
                offline_users = offline_invalid['offline']
                invalid_users = offline_invalid['invalid']
                print(f"> Couldn't create room. Offline users: {offline_users}. Invalid users: {invalid_users}")
            elif recv_message == "room exists":
                payload = client_socket.recv(1024)
                room = json.loads(payload.decode())
                print(f"> Couldn't create room. A room (ID: {room['room_id']}) with these users already exits!")
            elif recv_message == "successful separate room message":
                print("> Message sent successfully!")
                payload = client_socket.recv(1024)
                msg = json.loads(payload.decode())
                print(f"> {msg['message_type']}; {msg['sequence_number']}; {msg['timestamp']}")
            elif recv_message == "user not in room":
                print("> Message usuccessful! User is not in this room")
            elif recv_message == "room doesn't exist":
                print("> Message usuccessful! This room doesn't exist")
            elif recv_message == "read bc messages success":
                print("> Reading messages...")
                payload = client_socket.recv(1024)
                read_this = json.loads(payload.decode())
                if read_this['messages'] is None:
                    print("> No messages to be read...")
                else:
                    print(f"Broadcasted messages since {read_this['datetime']}:")
                    for msg in read_this['messages']:
                        print(msg)
            elif recv_message == "read sr messages success":
                print("> Reading messages...")
                payload = client_socket.recv(1024)
                read_this = json.loads(payload.decode())
                if not read_this:
                    print("> No messages to be read...")
                else:
                    print(f"Messages in separate room since {read_this[0]['datetime']}:")
                    for room in read_this:
                        print(f"Room {room['room_id']}:")
                        for msg in room['messages']:
                            print(msg)
            else:
                print(recv_message)
                print("> [recv] Invalid command!")
        except KeyboardInterrupt:
            print("\n===== Keyboard interrupt received. Client has been closed =====")
            break

    client_socket.close()
    # close the socket

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("\n===== Error usage, try python3 client.py <server_IP> <server_port> ======\n")
        exit()
    
    server_IP = sys.argv[1]
    server_port = int(sys.argv[2])
    connect_to_server(server_IP, server_port)
