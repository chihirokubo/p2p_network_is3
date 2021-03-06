import signal

from ClientCore import ClientCore

my_p2p_client = None

def signal_handler(signal, frame):
	shutdown_client()

def shutdown_client():
	global my_p2p_client
	my_p2p_client.shutdown()

def main():
	signal.signal(signal.SIGINT, signal_handler)
	global my_p2p_client
	my_p2p_client = ClientCore(50095, '192.168.0.6', 50082)
	my_p2p_client.start()

if __name__ == '__main__':
	main()