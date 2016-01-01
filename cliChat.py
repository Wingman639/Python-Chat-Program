import sys
import threading
import socket
import random
import math

if not sys.hexversion > 0x03000000:
    version = 2
else:
    version = 3

isCLI = True


# GLOBALS
conn_array = []  # stores open sockets

# key: the open sockets in conn_array,# value: integers for encryption
secret_array = dict()

# key: the open sockets in conn_array,# value: usernames for the connection
username_array = dict()

# key: ip address as a string, value: [port, username]
contact_array = dict()


LINE_CHAR_LENGTH = 80
SPACE = '                                                            '
CONTACTS_FILE_NAME = "contacts.txt"
DEFAULT_PORT = 5555
LOCAL_DATA_FILE_NAME = 'local.dat'
g_local = {'name': 'Server',
           'port': DEFAULT_PORT,
           'server_ip': None,
           'server_port': None}

location = 0
port = 0
top = ""

main_body_text = 0
# -GLOBALS-

# So,
#  x_encode your message with the key, then pass that to
#  refract to get a string out of it.
# To decrypt, pass the message back to x_encode, and then back to refract

def binWord(word):
    """Converts the string into binary."""
    master = ""
    for letter in word:
        temp = bin(ord(letter))[2:]
        while len(temp) < 7:
            temp = '0' + temp
        master = master + temp
    return master

def xcrypt(message, key):
    """Encrypts the binary message by the binary key."""
    count = 0
    master = ""
    for letter in message:
        if count == len(key):
            count = 0
        master += str(int(letter) ^ int(key[count]))
        count += 1
    return master

def x_encode(string, number):
    """Encrypts the string by the number."""
    return xcrypt(binWord(string), bin(number)[2:])

def refract(binary):
    """Returns the string representation of the binary.
    Has trouble with spaces.

    """
    master = ""
    for x in range(0, int(len(binary) / 7)):
        master += chr(int(binary[x * 7: (x + 1) * 7], 2) + 0)
    return master


def formatNumber(number):
    """Ensures that number is at least length 4 by
    adding extra 0s to the front.

    """
    temp = str(number)
    while len(temp) < 4:
        temp = '0' + temp
    return temp

def netThrow(conn, secret, message):
    """Sends message through the open socket conn with the encryption key
    secret. Sends the length of the incoming message, then sends the actual
    message.

    """
    try:
        conn.send(formatNumber(len(x_encode(message, secret))).encode())
        conn.send(x_encode(message, secret).encode())
    except socket.error:
        if len(conn_array) != 0:
            writeToScreen(
                "Connection issue. Sending message failed.", "System")
            processFlag("-001")


def netCatch(conn, secret):
    """Receive and return the message through open socket conn, decrypting
    using key secret. If the message length begins with - instead of a number,
    process as a flag and return 1.

    """
    try:
        data = conn.recv(4)
        print(data)
        if data.decode()[0] == '-':
            processFlag(data.decode(), conn)
            return 1
        data = conn.recv(int(data.decode()))
        return refract(xcrypt(data.decode(), bin(secret)[2:]))
    except socket.error:
        if len(conn_array) != 0:
            writeToScreen(
                "Connection issue. Receiving message failed.", "System")
        processFlag("-001")

def isPrime(number):
    """Checks to see if a number is prime."""
    x = 1
    if number == 2 or number == 3:
        return True
    while x < math.sqrt(number):
        x += 1
        if number % x == 0:
            return False
    return True

def processFlag(number, conn=None):
    """Process the flag corresponding to number, using open socket conn
    if necessary.

    """
    global conn_array
    global secret_array
    global username_array
    global contact_array
    global isCLI
    t = int(number[1:])
    if t == 1:  # disconnect
        # in the event of single connection being left or if we're just a
        # client
        if len(conn_array) == 1:
            writeToScreen("Connection closed.", "System")
            dump = secret_array.pop(conn_array[0])
            dump = conn_array.pop()
            try:
                dump.close()
            except socket.error:
                print("Issue with someone being bad about disconnecting")
            return

        if conn != None:
            writeToScreen("Connect to " + conn.getsockname()
                          [0] + " closed.", "System")
            dump = secret_array.pop(conn)
            conn_array.remove(conn)
            conn.close()

    if t == 2:  # username change
        name = netCatch(conn, secret_array[conn])
        if(isUsernameFree(name)):
            writeToScreen(
                "User " + username_array[conn] + " has changed their username to " + name, "System")
            username_array[conn] = name
            contact_array[
                conn.getpeername()[0]] = [conn.getpeername()[1], name]

    # passing a friend who this should connect to (I am assuming it will be
    # running on the same port as the other session)
    if t == 4:
        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        Client(data.decode(),
               int(contact_array[conn.getpeername()[0]][0])).start()

def processUserCommands(command, param):
    """Processes commands passed in via the / text input."""
    global conn_array
    global secret_array
    global g_local

    if command == "nick":  # change nickname
        for letter in param[0]:
            if letter == " " or letter == "\n":
                if isCLI:
                    error_window(0, "Invalid username. No spaces allowed.")
                else:
                    error_window(root, "Invalid username. No spaces allowed.")
                return
        if isUsernameFree(param[0]):
            writeToScreen("Username is being changed to " + param[0], "System")
            for conn in conn_array:
                conn.send("-002".encode())
                netThrow(conn, secret_array[conn], param[0])
            g_local['name'] = param[0]
        else:
            writeToScreen(param[0] +
                          " is already taken as a username", "System")
    if command == "disconnect":  # disconnects from current connection
        for conn in conn_array:
            conn.send("-001".encode())
        processFlag("-001")
    if command == "connect":  # connects to passed in host port
        if(options_sanitation(param[1], param[0])):
            Client(param[0], int(param[1])).start()
    if command == "host":  # starts server on passed in port
        if(options_sanitation(param[0])):
            Server(int(param[0])).start()


def isUsernameFree(name):
    """Checks to see if the username name is free for use."""
    global username_array
    global g_local
    if name == g_local['name']:
        return False
    if name in username_array.values():
        return False
    return True


def passFriends(conn):
    """Sends conn all of the people currently in conn_array so they can connect
    to them.

    """
    global conn_array
    for connection in conn_array:
        if conn != connection:
            conn.send("-004".encode())
            conn.send(
                formatNumber(len(connection.getpeername()[0])).encode())  # pass the ip address
            conn.send(connection.getpeername()[0].encode())
            # conn.send(formatNumber(len(connection.getpeername()[1])).encode()) #pass the port number
            # conn.send(connection.getpeername()[1].encode())

#--------------------------------------------------------------------------

def client_options_window(master):
    """Launches client options window for getting destination hostname
    and port.

    """
    top = Toplevel(master)
    top.title("Connection options")
    top.protocol("WM_DELETE_WINDOW", lambda: optionDelete(top))
    top.grab_set()
    Label(top, text="Server IP:").grid(row=0)
    location = Entry(top)
    location.grid(row=0, column=1)
    location.focus_set()
    Label(top, text="Port:").grid(row=1)
    port = Entry(top)
    port.grid(row=1, column=1)
    go = Button(top, text="Connect", command=lambda:
                client_options_go(location.get(), port.get(), top))
    go.grid(row=2, column=1)

def client_options_go(dest, port, window):
    "Processes the options entered by the user in the client options window."""
    if options_sanitation(port, dest):
        if not isCLI:
            window.destroy()
        Client(dest, int(port)).start()
    elif isCLI:
        sys.exit(1)

def options_sanitation(por, loc=""):
    """Checks to make sure the port and destination ip are both valid.
    Launches error windows if there are any issues.

    """
    global root
    if version == 2:
        por = unicode(por)
    if isCLI:
        root = 0
    if not por.isnumeric():
        error_window(root, "Please input a port number.")
        return False
    if int(por) < 0 or 65555 < int(por):
        error_window(root, "Please input a port number between 0 and 65555")
        return False
    if loc != "":
        if not ip_process(loc.split(".")):
            error_window(root, "Please input a valid ip address.")
            return False
    return True

def ip_process(ipArray):
    """Checks to make sure every section of the ip is a valid number."""
    if len(ipArray) != 4:
        return False
    for ip in ipArray:
        if version == 2:
            ip = unicode(ip)
        if not ip.isnumeric():
            return False
        t = int(ip)
        if t < 0 or 255 < t:
            return False
    return True

#------------------------------------------------------------------------------

def server_options_window(master):
    """Launches server options window for getting port."""
    top = Toplevel(master)
    top.title("Connection options")
    top.grab_set()
    top.protocol("WM_DELETE_WINDOW", lambda: optionDelete(top))
    Label(top, text="Port:").grid(row=0)
    port = Entry(top)
    port.grid(row=0, column=1)
    port.focus_set()
    go = Button(top, text="Launch", command=lambda:
                server_options_go(port.get(), top))
    go.grid(row=1, column=1)

def server_options_go(port, window):
    """Processes the options entered by the user in the
    server options window.

    """
    if options_sanitation(port):
        if not isCLI:
            window.destroy()
        Server(int(port)).start()
    elif isCLI:
        sys.exit(1)

#-------------------------------------------------------------------------

def username_options_window(master):
    """Launches username options window for setting username."""
    top = Toplevel(master)
    top.title("Username options")
    top.grab_set()
    Label(top, text="Username:").grid(row=0)
    name = Entry(top)
    name.focus_set()
    name.grid(row=0, column=1)
    go = Button(top, text="Change", command=lambda:
                username_options_go(name.get(), top))
    go.grid(row=1, column=1)


def username_options_go(name, window):
    """Processes the options entered by the user in the
    server options window.

    """
    processUserCommands("nick", [name])
    window.destroy()

#-------------------------------------------------------------------------

def error_window(master, texty):
    """Launches a new window to display the message texty."""
    global isCLI
    if isCLI:
        writeToScreen(texty, "System")
    else:
        window = Toplevel(master)
        window.title("ERROR")
        window.grab_set()
        Label(window, text=texty).pack()
        go = Button(window, text="OK", command=window.destroy)
        go.pack()
        go.focus_set()


#-----------------------------------------------------------------------------
# Contacts window

def contacts_window(master):
    """Displays the contacts window, allowing the user to select a recent
    connection to reuse.

    """
    global contact_array
    cWindow = Toplevel(master)
    cWindow.title("Contacts")
    cWindow.grab_set()
    scrollbar = Scrollbar(cWindow, orient=VERTICAL)
    listbox = Listbox(cWindow, yscrollcommand=scrollbar.set)
    scrollbar.config(command=listbox.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    buttons = Frame(cWindow)
    cBut = Button(buttons, text="Connect",
                  command=lambda: contacts_connect(
                                      listbox.get(ACTIVE).split(" ")))
    cBut.pack(side=LEFT)
    dBut = Button(buttons, text="Remove",
                  command=lambda: contacts_remove(
                                      listbox.get(ACTIVE).split(" "), listbox))
    dBut.pack(side=LEFT)
    aBut = Button(buttons, text="Add",
                  command=lambda: contacts_add(listbox, cWindow))
    aBut.pack(side=LEFT)
    buttons.pack(side=BOTTOM)

    for person in contact_array:
        listbox.insert(END, contact_array[person][1] + " " +
                       person + " " + contact_array[person][0])
    listbox.pack(side=LEFT, fill=BOTH, expand=1)

def contacts_connect(item):
    """Establish a connection between two contacts."""
    Client(item[1], int(item[2])).start()

def contacts_remove(item, listbox):
    """Remove a contact."""
    if listbox.size() != 0:
        listbox.delete(ACTIVE)
        global contact_array
        h = contact_array.pop(item[1])


def contacts_add(listbox, master):
    """Add a contact."""
    aWindow = Toplevel(master)
    aWindow.title("Contact add")
    Label(aWindow, text="Username:").grid(row=0)
    name = Entry(aWindow)
    name.focus_set()
    name.grid(row=0, column=1)
    Label(aWindow, text="IP:").grid(row=1)
    ip = Entry(aWindow)
    ip.grid(row=1, column=1)
    Label(aWindow, text="Port:").grid(row=2)
    port = Entry(aWindow)
    port.grid(row=2, column=1)
    go = Button(aWindow, text="Add", command=lambda:
                contacts_add_helper(name.get(), ip.get(), port.get(),
                                    aWindow, listbox))
    go.grid(row=3, column=1)


def contacts_add_helper(username, ip, port, window, listbox):
    """Contact adding helper function. Recognizes invalid usernames and
    adds contact to listbox and contact_array.

    """
    for letter in username:
        if letter == " " or letter == "\n":
            error_window(root, "Invalid username. No spaces allowed.")
            return
    if options_sanitation(port, ip):
        listbox.insert(END, username + " " + ip + " " + port)
        contact_array[ip] = [port, username]
        window.destroy()
        return

def load_contacts():
    """Loads the recent chats out of the persistent file contacts.txt."""
    global contact_array
    global CONTACTS_FILE_NAME
    try:
        filehandle = open(CONTACTS_FILE_NAME, "r")
    except IOError:
        return
    line = filehandle.readline()
    while len(line) != 0:
        temp = (line.rstrip('\n')).split(" ")  # format: ip, port, name
        contact_array[temp[0]] = temp[1:]
        line = filehandle.readline()
    filehandle.close()

def dump_contacts():
    """Saves the recent chats to the persistent file contacts.txt."""
    global contact_array
    global CONTACTS_FILE_NAME
    try:
        filehandle = open(CONTACTS_FILE_NAME, "w")
    except IOError:
        print("Can't dump contacts.")
        return
    for contact in contact_array:
        filehandle.write(
            contact + " " + str(contact_array[contact][0]) + " " +
            contact_array[contact][1] + "\n")
    filehandle.close()

# -----------------------------------------------------------------------------

# places the text from the text bar on to the screen and sends it to
# everyone this program is connected to


def placeText(text):
    """Places the text from the text bar on to the screen and sends it to
    everyone this program is connected to.

    """
    global conn_array
    global secret_array
    myWordsToScreen(text)
    for person in conn_array:
        netThrow(person, secret_array[person], text)


def writeToScreen(text, username=""):
    """Places text to main text body in format "username: text"."""
    if username:
        print('%s: %s' %(username, text))
    else:
        print(text)


def myWordsToScreen(text):
    """Places my words to main text body in format " text :my_nick"."""
    global g_local
    global LINE_CHAR_LENGTH

    count = LINE_CHAR_LENGTH - len(text) - 2 - len(g_local['name'])
    new_text = SPACE[0:count] + text + " :" + g_local['name']
    print(new_text)


def processUserText(event):
    """Takes text from text bar input and calls processUserCommands if it
    begins with '/'.

    """
    data = text_input.get()
    if data[0] != "/":  # is not a command
        placeText(data)
    else:
        if data.find(" ") == -1:
            command = data[1:]
        else:
            command = data[1:data.find(" ")]
        params = data[data.find(" ") + 1:].split(" ")
        processUserCommands(command, params)
    text_input.delete(0, END)


def processUserInput(text):
    """ClI version of processUserText."""
    if text[0] != "/":
        placeText(text)
    else:
        if text.find(" ") == -1:
            command = text[1:]
        else:
            command = text[1:text.find(" ")]
        params = text[text.find(" ") + 1:].split(" ")
        processUserCommands(command, params)


# -------------------------------------------------------------------------

class Server (threading.Thread):
    "A class for a Server instance."""
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port

    def run(self):
        print('Server run function')
        global conn_array
        global g_local
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', self.port))

        if len(conn_array) == 0:
            writeToScreen(
                "Socket is good, waiting for connections on port: " +
                str(self.port), "System")
        s.listen(1)
        global conn_init
        conn_init, addr_init = s.accept()
        serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serv.bind(('', 0))  # get a random empty port
        serv.listen(1)

        portVal = str(serv.getsockname()[1])
        if len(portVal) == 5:
            conn_init.send(portVal.encode())
        else:
            conn_init.send(("0" + portVal).encode())

        conn_init.close()
        conn, addr = serv.accept()
        conn_array.append(conn)  # add an array entry for this connection
        writeToScreen("Connected by " + str(addr[0]), "System")

        # create the numbers for my encryption
        prime = random.randint(1000, 9000)
        while not isPrime(prime):
            prime = random.randint(1000, 9000)
        base = random.randint(20, 100)
        a = random.randint(20, 100)

        # send the numbers (base, prime, A)
        conn.send(formatNumber(len(str(base))).encode())
        conn.send(str(base).encode())

        conn.send(formatNumber(len(str(prime))).encode())
        conn.send(str(prime).encode())

        conn.send(formatNumber(len(str(pow(base, a) % prime))).encode())
        conn.send(str(pow(base, a) % prime).encode())

        # get B
        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        b = int(data.decode())

        # calculate the encryption key
        global secret_array
        secret = pow(b, a) % prime
        # store the encryption key by the connection
        secret_array[conn] = secret

        conn.send(formatNumber(len(g_local['name'])).encode())
        conn.send(g_local['name'].encode())

        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        if data.decode() != "Self":
            username_array[conn] = data.decode()
            contact_array[str(addr[0])] = [str(self.port), data.decode()]
        else:
            username_array[conn] = addr[0]
            contact_array[str(addr[0])] = [str(self.port), "No_nick"]

        passFriends(conn)
        threading.Thread(target=Runner, args=(conn, secret)).start()
        Server(self.port).start()


class Client (threading.Thread):
    """A class for a Client instance."""
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.port = port
        self.host = host

    def run(self):
        global conn_array
        global secret_array
        conn_init = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn_init.settimeout(5.0)
        try:
            conn_init.connect((self.host, self.port))
        except socket.timeout:
            writeToScreen("Timeout issue. Host possible not there.", "System")
            raise SystemExit(0)
        except socket.error:
            writeToScreen(
                "Connection issue. Host actively refused connection.", "System")
            raise SystemExit(0)
        porta = conn_init.recv(5)
        porte = int(porta.decode())
        conn_init.close()
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((self.host, porte))

        writeToScreen("Connected to: " + self.host +
                      " on port: " + str(porte), "System")

        conn_array.append(conn)
        # get my base, prime, and A values
        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        base = int(data.decode())
        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        prime = int(data.decode())
        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        a = int(data.decode())
        b = random.randint(20, 100)
        # send the B value
        conn.send(formatNumber(len(str(pow(base, b) % prime))).encode())
        conn.send(str(pow(base, b) % prime).encode())
        secret = pow(a, b) % prime
        secret_array[conn] = secret

        conn.send(formatNumber(len(g_local['name'])).encode())
        conn.send(g_local['name'].encode())

        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        if data.decode() != "Self":
            username_array[conn] = data.decode()
            contact_array[
                conn.getpeername()[0]] = [str(self.port), data.decode()]
        else:
            username_array[conn] = self.host
            contact_array[conn.getpeername()[0]] = [str(self.port), "No_nick"]
        threading.Thread(target=Runner, args=(conn, secret)).start()
        # Server(self.port).start()
        # ##########################################################################THIS
        # IS GOOD, BUT I CAN'T TEST ON ONE MACHINE


def Runner(conn, secret):
    global username_array
    while 1:
        data = netCatch(conn, secret)
        if data and data != 1:
            writeToScreen(data, username_array[conn])

# -------------------------------------------------------------------------
# Menu helpers


def QuickClient():
    """Menu window for connection options."""
    window = Toplevel(root)
    window.title("Connection options")
    window.grab_set()
    Label(window, text="Server IP:").grid(row=0)
    destination = Entry(window)
    destination.grid(row=0, column=1)
    go = Button(window, text="Connect", command=lambda:
                client_options_go(destination.get(), "DEFAULT_PORT", window))
    go.grid(row=1, column=1)


def QuickServer():
    """Quickstarts a server."""
    Server(DEFAULT_PORT).start()


def saveHistory():
    """Saves history with Tkinter's asksaveasfilename dialog."""
    global main_body_text
    file_name = asksaveasfilename(
        title="Choose save location",
        filetypes=[('Plain text', '*.txt'), ('Any File', '*.*')])
    try:
        filehandle = open(file_name + ".txt", "w")
    except IOError:
        print("Can't save history.")
        return
    contents = main_body_text.get(1.0, END)
    for line in contents:
        filehandle.write(line)
    filehandle.close()


def connects(clientType):
    global conn_array
    if len(conn_array) == 0:
        if clientType == 0:
            client_options_window(root)
        if clientType == 1:
            server_options_window(root)
    else:
        for connection in conn_array:
            connection.send("-001".encode())
        processFlag("-001")


def toOne():
    global clientType
    clientType = 0


def toTwo():
    global clientType
    clientType = 1

# -------------------------------------------------------------------------


def save_local_data():
    with open(LOCAL_DATA_FILE_NAME, 'w') as f:
        f.write(unicode(g_local))


def load_local_data():
    global g_local
    try:
        with open(LOCAL_DATA_FILE_NAME, 'r') as f:
            text = f.read()
            g_local = eval(text)
    except:
        pass

# -------------------------------------------------------------------------


def wait_for_input():
    while True:
        text = raw_input(':')
        if text == '>':
            wait_for_command()
        elif text == 'exit':
            release_all()
            return
        else:
            placeText(text)


def wait_for_command():
    while True:
        cmd = raw_input('>')
        if cmd == 'exit':
            return
        if cmd:
            exit = run_command(cmd)
            if exit:
                return


def release_all():
    pass


def run_command(cmd):
    if cmd == '?':
        show_command_help()
    elif cmd == 'name':
        set_name()
    elif cmd == 'show':
        show_local()
    elif cmd == 'port':
        try_set_my_port()
    elif cmd == 'server':
        start_server()
        return True
    elif cmd == 'client':
        start_client()
        return True
    elif cmd == 'server ip':
        set_server_ip()
    elif cmd == 'server port':
        set_server_port()
    else:
        print('unknown command: %s' % cmd)


def set_name():
    try:
        text = raw_input('name: ')
        g_local['name'] = text
        save_local_data()
        print('Set name = %s. Success.' % text)
        return True
    except:
        pass
    print('not valid IP address')


def set_server_ip():
    try:
        ip = raw_input('server IP: ')
        g_local['server_ip'] = ip
        save_local_data()
        print('Set server IP = %s. Success.' % ip)
        return True
    except:
        pass
    print('not valid IP address')


def set_server_port():
    try:
        port = input('server port: ')
        if isinstance(port, int):
            g_local['server_port'] = port
            save_local_data()
            print('Set server port = %d. Success.' % port)
            return True
    except:
        pass
    print('not valid port number')


def start_client():
    if not g_local['server_ip']:
        set_server_ip()
    if not g_local['server_port']:
        set_server_port()
    if g_local['server_ip'] and g_local['server_port']:
        Client(g_local['server_ip'], g_local['server_port']).start()


def start_server():
    if not g_local['port']:
        try_set_my_port()
    if not g_local['port']:
        print ('listen port = %d' % DEFAULT_PORT)
        g_local['port'] = DEFAULT_PORT
    Server(g_local['port']).start()
    print('Start server on port: %d' % g_local['port'])


def show_local():
    print(g_local)


def try_set_my_port():
    retry_times = 3
    for i in range(retry_times):
        if set_my_port():
            return
    print('port setting canceled')


def set_my_port():
    try:
        port = input('listen port: ')
        if isinstance(port, int):
            g_local['port'] = port
            save_local_data()
            print('Set listen port = %d. Success.' % port)
            return True
    except:
        pass
    print('not valid port number')


def show_command_help():
    print('show: show current nickname')
    print('name: set new nickname')
    print('port: set server listen port number')
    print('server: start a server')
    print('client: start a client')
    print('server ip: set server ip to connect for client')
    print('server port: set server port to connect for client')



def main():
    print("Starting command line chat")
    load_local_data()
    wait_for_input()


if __name__ == '__main__':
    main()
