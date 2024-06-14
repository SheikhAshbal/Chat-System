import socket
import threading
import json

def enter_server():
    while True:
        try:
            with open('servers.json') as f:
                data = json.load(f)
            print('[*]Your servers: ', end="")
            # Print the servers that are stored in the servers.json file
            for servers in data:
                print(servers, end=" ")
            
             # Ask user for the name of the server to join
            server_name = input("\n[*] Enter the server name: ").capitalize()
            if server_name not in data:
                print("[*] Invalid server name. Please try again.")
                continue
            global nickname
            global password
            nickname = input("[*] Choose Your Nickname:")
            if not nickname:
                print("[*]Nickname cannot be empty. Please try again.")
                continue
            if nickname == 'admin':
                password = input("[*] Enter Password for Admin:")
                if not password:
                    print("[*]Password cannot be empty. Please try again.")
                    continue
                
            # Store the ip and port number for connection
            ip = data[server_name]["ip"]
            port = data[server_name]["port"]
            global client
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                # Connect to a host
                client.connect((ip, port))
            except ConnectionRefusedError:
                print("[*] Connection to the server failed. The server may not be running or is unreachable.")
                return False
            return True
        except KeyboardInterrupt:
            print("[*] Input interrupted. Exiting.")
            return False

def add_server():
    while True:
        try:
            server_name = input("[*] Enter a name for the server:")
            if not server_name:
                print("[*] Server name cannot be empty. Please try again.")
                continue
            server_ip = input("[*] Enter the ip address of the server:")
            if not server_ip:
                print("[*] Server IP cannot be empty. Please try again.")
                continue
            server_port_str = input("[*] Enter the port number of the server:")
            if not server_port_str.isdigit():
                print("[*] Port number must be a positive integer. Please try again.")
                continue
            server_port = int(server_port_str)
            if server_port <= 0 or server_port > 65535:
                print("[*] Port number must be in the range 1-65535. Please try again.")
                continue
            with open('servers.json', 'r') as f:
                data = json.load(f)
            if server_name in data:
                print("[*] Server name already exists. Please choose a different name.")
                continue
            
            # Store the info of the new server in servers.json
            with open('servers.json', 'w') as f:
                data[server_name] = {"ip": server_ip, "port": server_port}
                json.dump(data, f, indent=4)
            break
        except ValueError:
            print("[*] Invalid port number. Please enter a valid integer.")
        except KeyboardInterrupt:
            print("[*] Input interrupted. Exiting.")
            return

def receive():
    while True:
        global stop_thread
        if stop_thread:
            break
        try:
            message = client.recv(1024).decode('ascii')
            if message == 'NICK':
                client.send(nickname.encode('ascii'))
                next_message = client.recv(1024).decode('ascii')
                if next_message == 'PASS':
                    client.send(password.encode('ascii'))
                    if client.recv(1024).decode('ascii') == 'REFUSE':
                        print("[*]Connection is Refused !! Wrong Password")
                        stop_thread = True
                
                # Clients those are banned can't reconnect
                elif next_message == 'BAN':
                    print('[*] Connection Refused due to Ban')
                    client.close()
                    stop_thread = True
            else:
                print(message)
        except socket.error:
            print('[*] Error Occured while Connecting')
            break
            client.close()

def write():
    try:
        while True:
            if stop_thread:
                break
            
            # Getting Messages
            message = f'{nickname}: {input("")}'
            if message[len(nickname) + 2:].startswith('/'):
                if nickname == 'admin':
                    if message[len(nickname) + 2:].startswith('/kick'):
                        # 2 for : and whitespace and 6 for /KICK_
                        client.send(f'KICK {message[len(nickname) + 2 + 6:]}'.encode('ascii'))
                    elif message[len(nickname) + 2:].startswith('/ban'):
                        # 2 for : and whitespace and 6 for /KICK_
                        client.send(f'BAN {message[len(nickname) + 2 + 5:]}'.encode('ascii'))
                else:
                    print("[*] Commands can be executed by Admins only !!")
            else:
                client.send(message.encode('ascii'))
    except EOFError:
        print("[*] Input stream closed. Exiting write loop.")
    except KeyboardInterrupt:
        print("[*] KeyboardInterrupt received. Exiting write loop.")
        
        
# Menu loop, it will loop until the user choose to enter a server
while True:
    print("[*][*] Choose what you want")
    option = input("[*][*] \t1.Enter server\n\t2.Add server: ")
    if option == '1':
        if enter_server():
            break
    elif option == '2':
        add_server()

stop_thread = False

receive_thread = threading.Thread(target=receive)
receive_thread.start()
write_thread = threading.Thread(target=write)
write_thread.start()
