import socket
import threading

class Server(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port

    def run(self):
        pass



class Client(object):
    def __init__(self, host, port):
        self.address = (host, port)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.udp_socket.close()

    def send(self, message):
        self.udp_socket.sendto(message, self.address)

if __name__ == '__main__':
    def test_client():
        with Client('127.0.0.1', 31500) as client:
            client.send('Hello, I am a client')
            client.send('my 2nd words.')

    def test():
        test_client()

    test()