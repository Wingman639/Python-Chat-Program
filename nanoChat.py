from __future__ import print_function
import threading
import time
from nanomsg import Socket, PAIR

STOP_COMMAND = '[connection]:stop'
LINE_CHAR_LENGTH = 60
SPACE = '                                                            '
LOCAL_DATA_FILE_NAME = 'local.dat'
g_local = {'name': 'nobody', 'port' : 5555}
g_target = None




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

def wait_for_command():
    while True:
        cmd = raw_input('>')
        if cmd == 'exit':
            return
        if cmd:
            exit = run_command(cmd)
            if exit:
                return


def run_command(cmd):
    if cmd == '?':
        show_command_help()
    elif cmd == 'name':
        set_name()
    elif cmd == 'show':
        show_local()
    elif cmd == 'chat':
        start_client()
    elif cmd == 'server':
        start_server()
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


def show_local():
    print(g_local)


def show_command_help():
    print('show: show configuare')
    print('name: set my name')
    print('chat: start chat to a friend')
    print('server: wait for friend chat with me')



# -------------------------------------------------------------------------


def start_server():
    global g_local
    if not g_local['name']:
        if not set_name():
            return
    with Socket(PAIR) as server:
        address = 'tcp://127.0.0.1:%d' % g_local['port']
        print(address)
        server.bind(address)
        wait_for_chat_input(server)



def start_client():
    global g_target
    g_target = raw_input('chat with who: ')
    if g_target:
        with Socket(PAIR) as client:
            address = 'tcp://127.0.0.1:%d' % g_local['port']
            print(address)
            client.connect(address)
            wait_for_chat_input(client)

# -------------------------------------------------------------------------


def my_word_to_screen(text):
    """Places my words to main text body in format " text :my_nick"."""
    global g_local
    global LINE_CHAR_LENGTH

    count = LINE_CHAR_LENGTH - len(text) - 5 - len(g_local['name'])
    new_text = "%s%s :[%s]" % (SPACE[0:count], text, g_local['name'])
    print(new_text)

# -------------------------------------------------------------------------



def wait_for_chat_input(connection):
    receive = Receiver(connection)
    receive.start()
    while True:
        text = raw_input('')
        if text == 'exit':
            connection.send(STOP_COMMAND)
            receive.stop_receive()
            receive.join()
            return
        else:
            send_text(connection, text)

# -------------------------------------------------------------------------


def send_text(connection, text):
    extend_text = '[%s]:%s' % (g_local['name'], text)
    connection.send(extend_text)
    my_word_to_screen(text)




# -------------------------------------------------------------------------

class Receiver(threading.Thread):
    def __init__(self, connection):
        threading.Thread.__init__(self)
        self.connection = connection
        self.stop_flag = False

    def run(self):
        while not self.stop_flag:
            time.sleep(0.5)
            self.receive()

    def receive(self):
        #print('start receive...')
        text = self.connection.recv()
        print(text)

    def stop_receive(self):
        self.stop_flag = True


def main():
    print("Starting command line chat")
    load_local_data()
    wait_for_command()


if __name__ == '__main__':
    main()

