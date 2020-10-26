import threading

class EdgeNodeList:
	def __init__(self):
		self.lock = threading.Lock()
		self.list = set()

	def add(self, edge):
		"""
		edgeノードをリストに追加する
		"""
		with self.lock:
			print("Adding edge: ", edge)
			self.list.add((edge))
			print('Current Edge List: ', self.list)

	def remove(self, edge):
		"""
		離脱したと判断されるedgeノードをリストから削除する
		"""
		with self.lock:
			if edge in self.list:
				print('Removing edge: ', edge)
				self.list.remove(edge)
				print('Current Edge list: ', self.list)

		def overwrite(self, new_list):
			"""
			複数のedgeノードの接続状況確認を行ったあとで一括での上書き処理をしたい場合
			"""
			with self.lock:
				print('edge node list will be going to overwrite')
				self.list = new_list
				print('Current Edge list: ', self.list)

		def get_list(self):
			"""
			現在接続状況にあるEdgeノードの一覧を返却
			"""
			return self.list