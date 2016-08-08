import socket
import threading
import time

class Server(threading.Thread):
    def __init__(self, host, port, call_back):
        threading.Thread.__init__(self)
        self.address = (host, port)
        self.call_back = call_back
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(self.address)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        # self.udp_socket.close()
        pass

    def run(self):
        while True:
            data, addr = self.udp_socket.recvfrom(2048)
            if data:
                self.call_back(data)
            time.sleep(0.1)



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

    def test_server():
        with Server('127.0.0.1', 31500, call_back) as server:
            server.start()


    def call_back(data):
        print data

    def test():
        # test_client()
        test_server()

    test()