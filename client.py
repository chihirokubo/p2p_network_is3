import socket

my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
my_socket.connect(('192.168.0.3', 50030))
my_text = 'hello. this is test message from my client'
my_socket.sendall(my_text.encode('utf-8'))
