import threading

class CoreNodeList:
	def __init__(self):
		self.lock = threading.Lock()
		self.list = set()

	def add(self,peer):
		"""
		Coreノードをリストに追加
		"""
		with self.lock:
			self.list.add((peer))
			print('Current Core List: ', self.list)

	def remove(self, peer):
		"""
		離脱したと判断されるCoreノードをリストから削除
		"""
		with self.lock:
			if peer in self.list:
				print('Removing peer: ',peer)
				self.list.remove(peer)
				print('Current Core list: ', self.list)

	def overwrite(self, new_list):
		"""
		複数のpeerの接続状況確認を行ったあとで一括の上書き処理をしたいような場合
		"""
		with self.lock:
			print('core node list will be going to overwrite')
			self.list = new_list
			print('Current Core list: ',self.list)

	def get_c_node_info(self):
		"""
		リストのトップにあるpeerを返却
		"""
		return list(self.list)[0]

	def get_list(self):
		"""
		現在接続状況にあるpeerの一覧を返す
		"""
		return self.list
