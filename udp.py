import minichat


def send(ip, port, message):
    with minichat.Client(ip, port) as client:
        client.send(message)
