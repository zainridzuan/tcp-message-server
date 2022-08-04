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
            print("Login Successful!")
            authenticated = True
            curr_time = datetime.now()
            print(curr_time.strftime("%d/%m/%Y %H:%M:%S"))
            hostname = gethostname()
            IP_addr = gethostbyname(hostname)
            print(IP_addr)
            payload = client_socket.recv(1024)
            login_info = json.loads(payload.decode('utf-8'))
            print(login_info)
            break
        elif response == "login failure":
            print("Invalid password. Please try again.")
            request["password"] = getpass()
            client_socket.sendall("login".encode())
            client_socket.recv(1024)
            client_socket.send(bytes(json.dumps(request), encoding='utf-8'))
        elif response == "user blocked":
            print("Your account has been blocked due to multiple unsuccessful login attempts. Please try again later.")
            exit()
        else:
            print(response)


def connect_to_server(server_name, server_port):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((server_name, server_port))

    while True:
        sent_message = input("===== Please type any messsage you want to send to server: =====\n")
        client_socket.sendall(sent_message.encode())

        data = client_socket.recv(1024)
        recv_message = data.decode()

        # parse the message received from server and take corresponding actions
        if recv_message == "":
            print("[recv] Message from server is empty!")
        elif recv_message == "user credentials request":
            print("[recv] Please provide username and password to login")
            username = input("Username: ")
            password = getpass()
            user_login(username, password, client_socket)
            #if authenticated is True:
        else:
            print("[recv] Message makes no sense")
            
        ans = input("Do you want to continue (y/n): ")
        if ans == 'y':
            continue
        else:
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
