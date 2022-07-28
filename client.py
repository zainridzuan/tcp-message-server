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
import json
import sys

def login(username, password, client_socket):
    request = {
        'request_type': 'login',
        'username': username,
        'password': password
    }

    while 1:
        client_socket.send(bytes(json.dumps(request).encode('utf-8')))

        response = client_socket.recv(1024)
        response = response.decode('utf-8')
        # We wait to receive the reply from the server, store it in response
        
        if response == 'Success':
            print("Login Successful!")
            break
        elif response == 'Failure':
            print('Invalid username and/or password. Please try again.')
            request['username'] = input('Enter username: ')
            request['password'] = input('Enter password: ')
        elif response == 'Blocked':
            print('Invalid password. Your account has been blocked due to multiple unsuccessful login attempts. Please try again later.')
            exit()
        else:
            print(response)


def connect_to_server(server_name, server_port):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((server_name, server_port))

    login_success = 0


    username = input('Enter username: ')
    password = input('Enter password: ')
    login(username, password, client_socket)

    client_socket.close()
    # and close the socket

if __name__ == '__main__':
    #if len(sys.argv) != 3:
    #    print('Try python3 client.py <server_IP> <server_port>')
    #    exit()
    
    server_IP = sys.argv[1]
    server_port = int(sys.argv[2])
    connect_to_server(server_IP, server_port)
