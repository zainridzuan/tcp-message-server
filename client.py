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

    client_socket.send(bytes(json.dumps(request).encode()))
    while True:
        payload = client_socket.recv(1024)
        response = payload.decode('utf-8')
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
            client_socket.send(bytes(json.dumps(request), encoding='utf-8'))
        elif response == "user blocked":
            print("> Your account has been blocked due to multiple unsuccessful login attempts. Please try again later.")
            exit()
        else:
            print(response)


def connect_to_server(server_name, server_port):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((server_name, server_port))
    initial_login = True
    while True:
        if initial_login == True:
            client_socket.sendall("login".encode())
            initial_login = False
        else:
            sent_message = input("===== Enter one of the following commands [BCM, ATU, SRB, SRM, RDM, OUT] =====\n> ")
            client_socket.sendall(sent_message.encode())

        data = client_socket.recv(1024)
        recv_message = data.decode()

        # parse the message received from server and take corresponding actions
        if recv_message == "":
            print("> [recv] Message from server is empty!")
        elif recv_message == "user credentials request":
            print("> [recv] Please provide username and password to login")
            username = input("username: ")
            password = getpass("password: ")
            user_login(username, password, client_socket)
        elif recv_message == "logout":
            print(f"> Goodbye, {username}")
            break
        elif recv_message == "active users request":
            payload = client_socket.recv(1024)
            everyone_else_userlog = json.loads(payload.decode('utf-8'))
            if everyone_else_userlog == []:
                print("> No other active users...")
            else:
                for i in everyone_else_userlog:
                    print(f"{i['username']}; {i['client IP address'][0]}; active since {i['timestamp']};")
        elif recv_message == "message sent successfully":
            print("> Message sent successfully!")
            payload = client_socket.recv(1024)
            msg = json.loads(payload.decode('utf-8'))
            print(f"> {msg['message_type']}; {msg['sequence_number']}; {msg['timestamp']}")
        elif recv_message == "successful separate room creation":
            payload = client_socket.recv(1024)
            room_info = json.loads(payload.decode('utf-8'))
            print(f"> Separate chat room has been created, room ID: {room_info['room_id']}, users in this room: {room_info['users']}")
        elif recv_message == "unsuccesful room creation":
            print(f"> Unsuccessful room creation. You can't create a room for yourself.")
        elif recv_message == "invalid room creation":
            payload = client_socket.recv(1024)
            offline_invalid = json.loads(payload.decode('utf-8'))
            offline_users = offline_invalid['offline']
            invalid_users = offline_invalid['invalid']
            print(f"Couldn't create room. Offline users: {offline_users}. Invalid users: {invalid_users}")
            print("errors")
        else:
            print(recv_message)
            print("> [recv] Invalid command!")

    client_socket.close()
    # close the socket

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("\n===== Error usage, try python3 client.py <server_IP> <server_port> ======\n")
        exit()
    
    server_IP = sys.argv[1]
    server_port = int(sys.argv[2])
    connect_to_server(server_IP, server_port)
