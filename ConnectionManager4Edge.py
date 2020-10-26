import socket
import threading
import pickle
import signal
import codecs
import time
import os
from concurrent.futures import ThreadPoolExecutor

from core_node_list import CoreNodeList
from MessageManager import *

PING_INTERVAL = 10

class ConnectionManager4Edge:
	def __init__(self, host, my_port, my_core_host, my_core_port):
		print('Initializing ConnectionManager4Edge...')
		self.host = host
		self.port = my_port
		self.my_core_host = my_core_host
		self.my_core_port = my_core_port
		self.core_node_set = CoreNodeList()
		self.message_manager = MessageManager()

	def start(self):
		"""
		最初の待受を開始する際に呼び出される
		"""
		t = threading.Thread(target=self.__wait_for_access)
		t.start()

		self.ping_timer = threading.Timer(PING_INTERVAL, self.__send_ping)
		self.ping_timer.start()

	def connect_to_core_node(self):
		"""
		ユーザーが指定した既知のcoreノードへの接続
		"""
		self.__connect_to_P2PNW(self.my_core_host, self.my_core_port)

	def send_msg(self, peer, msg):
		"""
		指定されたノードに対してメッセージを送信
		"""
		print('Sending...', msg)
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((peer))
			s.sendall(msg.encode('utf-8'))
			s.close()
		except:
			print('Connection faild for peer : ', peer)
			self.core_node_set.remove(peer)
			print('Tring to connect into P2P network...')
			current_core_list = self.core_node_set.get_list()

			if len(current_core_list) != 0:
				new_core = self.core_node_set.get_c_node_info()
				self.my_core_host = new_core[0]
				self.my_core_port = new_core[1]
				self.connect_to_core_node()
				# TODO 
				self.send_msg((new_core[0], new_core[1]), msg)
			else: 
				print('No core node found in our list ... ')
				self.ping_timer.cancel()

	def connection_close(self):
		"""終了前の処理としてソケットを閉じる"""
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((self.host, self.port))
		self.socket.close()
		s.close()
		self.ping_timer.cancel()

	def __connect_to_P2PNW(self, host, port):
		"""
		指定したCoreノードへの接続要求メッセージの送信
		"""
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((host, port))
		msg = self.message_manager.build(MSG_ADD_AS_EDGE, self.port)
		print(msg)
		s.sendall(msg.encode('utf-8'))
		s.close()

	def __wait_for_access(self):
		"""
		Serverソケットを用いて待ち受け状態に移行
		"""
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind((self.host, self.port))
		self.socket.listen(0)

		executor = ThreadPoolExecutor(max_workers=10)

		while True:
			print('Waiting for the connection...')
			soc, addr = self.socket.accept()
			print('Connected by .. ', addr)
			data_sum = ''

			params = (soc, addr, data_sum)
			executor.submit(self.__handle_message, params)

	def __handle_message(self, params):
		"""
		受信したメッセージを確認して、内容に応じた処理を行う
		"""
		soc, addr, data_sum = params
		while True:
			data = soc.recv(1024)
			data_sum = data_sum + data.decode('utf-8')

			if not data:
				break

			if not data_sum:
				return

			result, reason, cmd, peer_port, payload = self.message_manager.parse(data_sum)
			print(result, reason, cmd, peer_port, payload)
			status = (result, reason)

			if status == ('error', ERR_PROTOCOL_UNMATCH):
				print('Error: Protocol name is not matched')
				return
			elif status == ('error', ERR_VERSION_UNMATCH):
				print('Error: Protocol version is not matched')
				return
			elif status == ('ok', OK_WITHOUT_PAYLOAD):
				if cmd == MSG_PING:
					pass
				else:
					print('Edge node does not have functions for this message!')
			elif status == ('ok', OK_WITH_PAYLOAD):
				if cmd == MSG_CORE_LIST:
					print('Refresh the core node list ...')
					new_core_set = pickle.loads(payload.encode('utf-8'))
					print('latest core node list: ', new_core_set)
					self.core_node_set.overwrite(new_core_set)
				else :
					self.callback((result, reason, cmd, peer_port, payload))
			else:
				print('Unexpected status', status)

	def __send_ping(self):
		"""
		接続状況確認メッセージの送信処理実体
		中で確認処理は定期的に実行し続けられる
		"""
		peer = (self.my_core_host, self.my_core_port)
		print("waowao")
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((peer))
			msg = self.message_manager.build(MSG_PING)
			s.sendall(msg.encode('utf-8'))
			s.close()
		except:
			print('Connection failed for peer : ', peer)
			self.core_node_set.remove(peer)
			print('Tring to connect into P2P network...')
			current_core_list = self.core_node_set.get_list()
			if len(current_core_list) != 0:
				new_core = self.core_node_set.get_c_node_info()
				self.my_core_host = new_core[0]
				self.my_core_port = new_core[1]
				self.connect_to_core_node()
			else:
				print('No core node found in our list...')
				self.ping_timer.cancel()

		self.ping_timer = threading.Timer(PING_INTERVAL, self.__send_ping)
		self.ping_timer.start()

























