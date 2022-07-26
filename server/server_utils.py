import os, re

def read_credentials():
    credentials = {}
    with open('credentials.txt') as credential_list:
        for line in credential_list:
            userpass = line.split()
            u = userpass[0]
            p = userpass[1].strip()
            credentials[u] = p

    return credentials

def append_credentials(username, password):
    with open("credentials.txt", "a") as credentials:
        credentials.write("\n")
        credentials.write(f"{username} {password}")

def do_they_exist(username):
    with open("credentials.txt", "r") as f:
        credentials = f.readlines()
        for credential in credentials:
            credential_user = credential.split()[0]
            if credential_user == username:
                return True
    return False

# used to clear userlog on server startup
def clear_userlog():
    with open("userlog.txt", "w+") as f:
        f.truncate()

#    login_info = {
#    "active user sequence number":
#    "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
#    "username": username,
#    "client IP address": self.client_address
#    "client UDP server port number":
#    }
# used to append user to userlog
def add_userlog(login_info):
    f = open("userlog.txt", "a")
    f.write(f"{login_info['active user sequence number']}; {login_info['timestamp']}; {login_info['username']}; {login_info['client IP address'][0]};\n")
    f.close

# finding a userlog_dict from client_address
def address_to_userlog_dict(dicts, addr):
    dict = next((item for item in dicts if item["client IP address"] == addr), None)
    return dict

# updating userlog after a user disconnects
def update_userlog(login_info):
    f = open("userlog.txt", "w")
    for dict in login_info:
        f.write(f"{dict['active user sequence number']}; {dict['timestamp']}; {dict['username']}; {dict['client IP address'][0]};\n")
    f.close()
    
# used to clear messagelog on server startup
def clear_messagelog():
    with open("messagelog.txt", "w+") as f:
        f.truncate()

def add_messsagelog(msg_details):
    f = open("messagelog.txt", "a")
    f.write(f"{msg_details['message sequence number']}; {msg_details['timestamp']}; {msg_details['username']}; {msg_details['message']};\n")
    f.close

    confirmation = {
        "message_type": "Broadcast Message",
        "sequence_number": msg_details['message sequence number'],
        "timestamp": msg_details['timestamp']
    }

    return confirmation

# used to check if a list of users are currently online, if they are online they also must be registered users
# returns a dictionary with 'username': 'online' | 'offline' | 'invalid'
def are_they_online(user_list):
    online = []
    with open("userlog.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            online.append(line.split("; ")[2])

    valid_users = []
    with open("credentials.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            valid_users.append(line.split()[0])   

    dict = {}
    for user in user_list:
        if user in online:
            dict[user] = "online"
        else:
            if user in valid_users:
                dict[user] = "offline"
            else:
                dict[user] = "invalid"
    return dict

# utility function to reset rooms and delete all logs
def reset_rooms():
    for f in os.listdir("."):
        if re.match("^SR_[0-9]*_messagelog.txt", f):
            os.remove(f)

# helper function to add message to separate room 
def add_messages_r(filename, msg_details):
    f = open(filename, "a")
    f.write(f"{msg_details['message sequence number']}; {msg_details['timestamp']}; {msg_details['username']}; {msg_details['message']};\n")
    f.close

    confirmation = {
        "message_type": "Separate room message",
        "sequence_number": msg_details['message sequence number'],
        "timestamp": msg_details['timestamp']
    }

    return confirmation
