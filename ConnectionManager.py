import threading
import socket
import pickle
from concurrent.futures import ThreadPoolExecutor

from MessageManager import *
from core_node_list import CoreNodeList

PING_INTERVAL = 1800  #30分

class ConnectionManager:
	def __init__(self, host, my_port):
		print('Initializing ConnectionManager...')
		self.host = host
		self.port = my_port
		self.core_node_set = CoreNodeList()
		self.__add_peer((host,my_port))
		self.message_manager = MessageManager()


	def start(self):
		"""
		待受を開始する
		"""
		t = threading.Thread(target=self.__wait_for_access)
		t.start()

		self.ping_timer = threading.Timer(PING_INTERVAL, self.__check_peers_connection)
		self.ping_timer.start()

	def join_network(self, host, port):
		"""
		ユーザーが指定した既知のCoreノードへの接続
		"""
		self.my_c_host = host
		self.my_c_port = port
		self.__connect_to_P2PNW(host, port)

	def __connect_to_P2PNW(self, host, port):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((host, port))
		msg = self.message_manager.build(MSG_ADD, self.port)
		s.sendall(msg.encode('utf-8'))
		s.close()

	def connection_close(self):
		"""
		終了前の処理としてソケットを閉じる
		"""
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((self.host, self.port))
		self.socket.close()
		s.close()
		# 接続確認のスレッドの停止
		self.ping_timer.cancel()
		# 離脱要求の送信
		msg = self.message_manager.build(MSG_REMOVE, self.port)
		self.send_msg((self.my_c_host, self.my_c_port), msg)
		

	def send_msg(self,peer, msg):
		"""
		指定されたノードに対してメッセージ送信
		"""
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((peer))
			s.sendall(msg.encode('utf-8'))
			s.close()
		except OSError:
			print('Connection failed for peer : ', peer)
			self.__remove_peer(peer)


	def send_msg_to_all_peer(self,msg):
		"""
		Coreノードリストに登録されている全てのノードに対して
		同じメッセージをブロードキャスト
		"""
		print('send_msg_to_all_peer was called')
		current_list = self.core_node_set.get_list()
		for peer in current_list:
			if peer != (self.host, self.port):
				print('message will be sent to ... ', peer)
				self.send_msg(peer,msg)

	def __handle_message(self,params):
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
		print(cmd)
		status = (result, reason)

		if status == ('error', ERR_PROTOCOL_UNMATCH):
			print('Error: Protocol name is not matched')
			return
		elif status == ('error', ERR_VERSION_UNMATCH):
			print('Error: Protocol version is not matched')
			return
		elif status == ('ok', OK_WITHOUT_PAYLOAD):
			if cmd == MSG_ADD:
				print('ADD node request was received!!')
				self.__add_peer((addr[0], peer_port))
				if(addr[0],peer_port) == (self.host, self.port):
					return
				else:
					cl = pickle.dumps(self.core_node_set.get_list(), 0).decode()
					msg = self.message_manager.build(MSG_CORE_LIST, self.port, cl)
					print(msg)
					self.send_msg_to_all_peer(msg)
			elif cmd == MSG_REMOVE:
				print('REMOVE request was received!! from ', addr[0], peer_port)
				self.__remove_peer((addr[0],peer_port))
				cl = pickle.dumps(self.core_node_set.get_list(), 0).decode()
				msg = self.message_manager.build(MSG_CORE_LIST, self.port, cl)
				self.send_msg_to_all_peer(msg)
			elif cmd == MSG_PING:
				return
			elif cmd == MSG_REQUEST_CORE_LIST:
				print('List for Core nodes was requested!!')
				cl = pickle.dumps(self.core_node_set.get_list(), 0).decode()
				msg = self.message_manager.build(MSG_CORE_LIST, self.port, cl)
				self.send_msg((addr[0], peer_port), msg)
			else:
				print('received unknown command', cmd)
				return
		elif status == ('ok', OK_WITH_PAYLOAD):
			if cmd == MSG_CORE_LIST:
				## TODO: 受信したリストをただ上書きするのは
				## 本来セキュリティ的に良くない
				## 信頼できるノードの鍵などをセットしておく必要あり
				print('Refresh the core node list...')
				new_core_set = pickle.loads(payload.encode('utf-8'))
				print('lates core node list: ', new_core_set)
				self.core_node_set = new_core_set
			else:
				print('received unknown command', cmd)
				return
		else:
			print('Unexpected status', status)


	def __add_peer(self, peer):
		"""
		新たに接続されたcoreノードをリストに追加する
		"""
		print('Adding peer : ',peer)
		self.core_node_set.add((peer))


	def __remove_peer(self, peer):
		"""
		離脱したCoreノードをリストから削除する
		"""
		self.core_node_set.remove(peer)


	def __check_peers_connection(self):
		"""
		接続されているcoreノード全ての接続状況確認を行う
		"""
		print('check_peers_connection was called')
		current_core_list = self.core_node_set.get_list()
		changed = False
		dead_c_node_set = list(filter(lambda p: not self.__is_alive(p), current_core_list))

		if dead_c_node_set:
			changed = True
			print('Removing ', dead_c_node_set)
			current_core_list = current_core_list - set(dead_c_node_set)
			self.core_node_set.overwrite(current_core_list)

		current_core_list = self.core_node_set.get_list()
		print('current core node list : ', current_core_list)

		if changed:
			cl = pickle.dumps(current_core_list,0).decode()
			msg = self.message_manager.build(MSG_CORE_LIST, self.port, cl)
			self.send_msg_to_all_peer(msg)

		self.ping_timer = threading.Timer(PING_INTERVAL, self.__check_peers_connection)
		self.ping_timer.start()

	def __is_alive(self, target):
		"""
		有効ノード確認メッセージの送信

		Parameters
		----------
		target : 
			有効ノード確認メッセージの送り先となるノードの接続情報(IPアドレスとポート番号)
		"""
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((target))
			msg_type = MSG_PING
			msg = self.message_manager.build(msg_type)
			s.sendall(msg.encode('utf-8'))
			s.close()
			return True
		except OSError:
			return False


	def __wait_for_access(self):
		"""
		他のコアノードから送られてくるメッセージを待機する
		"""
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind((self.host, self.port))
		self.socket.listen(0)

		executor = ThreadPoolExecutor(max_workers=10)

		while True:
			print('Waiting for the connection')
			soc, addr = self.socket.accept()
			print('Connected by .. ', addr)
			data_sum = ''

			params = (soc, addr, data_sum)
			executor.submit(self.__handle_message, params)



