def read_credentials():
    credentials = {}
    with open('credentials.txt') as credential_list:
        for line in credential_list:
            userpass = line.split()
            u = userpass[0]
            p = userpass[1].strip()
            credentials[u] = p

    return credentials