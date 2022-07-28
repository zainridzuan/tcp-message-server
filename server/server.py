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

Easy way to do message types is to use json 
{
   'request_type': 'example_request',
   'info': '...',
   'info1': '...'
}
'''

from socket import * 
from threading import Thread
import json
import sys

def start_server(server_port, number_of_consecutive_failed_attempts):
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('localhost', server_port))
    server_socket.listen(1)

    print("The server is ready to receive...")

    while 1:
        connection_socket, addr = server_socket.accept()
        payload = connection_socket.recv(1024)
        request = json.loads(payload.decode('utf-8'))
        request_type = request['request_type']
        username = request['username']
        password = request['password']

        # creating credentials dictionary with username as key and password as value
        credentials = {}
        with open('credentials.txt') as credential_list:
            for line in credential_list:
                userpass = line.split()
                u = userpass[0]
                p = userpass[1].strip()
                credentials[u] = p

        login_attempts = dict.fromkeys(credentials, 0)

        if request_type == 'login':
            if username in credentials:
                if login_attempts[username] >= number_of_consecutive_failed_attempts:
                    connection_socket.send(bytes('Blocked', encoding='utf-8'))
                elif password == credentials[username]:
                    connection_socket.send(bytes('Success', encoding='utf-8'))
                elif password != credentials[username]:
                    connection_socket.send(bytes('Failure', encoding='utf-8'))
                    login_attempts[username] = login_attempts[username] + 1
                    print(login_attempts)
            else:
                connection_socket.send(bytes('Invalid username', encoding='utf-8'))

    connection_socket.close()
    # Close the connection_socket. Note that the serverSocket is still alive waiting for new clients to connect, we are 
    # only closing the connection_socket.

if __name__ == "__main__":
    server_port = int(sys.argv[1])
    number_of_consecutive_failed_attempts = int(sys.argv[2])
    start_server(server_port, number_of_consecutive_failed_attempts)
