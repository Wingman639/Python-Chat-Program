import socket


def send(host, message):
    udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_client.sendto(message, host)
    udp_client.close()
