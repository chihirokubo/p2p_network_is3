# 
from distutils.version import StrictVersion
import json

PROTOCOL_NAME = 'simple_bitcoin_protocol'
MY_VERSION = '0.1.0'


# メッセージタイプの定義
MSG_ADD = 0
MSG_REMOVE = 1
MSG_CORE_LIST = 2
MSG_REQUEST_CORE_LIST = 3
MSG_PING = 4
MSG_ADD_AS_EDGE = 5
MSG_REMOVE_EDGE = 6

# エラーの定義
## プロトコルエラー
ERR_PROTOCOL_UNMATCH = 0
## バージョンエラー
ERR_VERSION_UNMATCH = 1
## ペイロードの有無
OK_WITH_PAYLOAD = 2
OK_WITHOUT_PAYLOAD = 3

class MessageManager:
	"""
	通信されるメッセージのフォーマットを定義	
	"""
	def __init__(self):
		print('initializing message manager...')

	def build(self, msg_type,my_port=50082, payload=None):
		"""
		メッセージの組み立て関数

		Parameters
		----------
		msg_type: int
			メッセージタイプ
		payload: str
			メッセージのペイロード

		Returns
		-------
		message: JSON object
			フォーマットに従ったメッセージ
		"""
		message_dict = {
			'protocol': PROTOCOL_NAME,
			'version': MY_VERSION,
			'msg_type': msg_type,
			'my_port':my_port,
		}

		if payload is not None :
			message_dict['payload'] = payload

		message = json.dumps(message_dict)
		return message

	def parse(self, msg):
		"""
		メッセージのパースを行う

		Parameters
		----------
		msg : JSON object
			フォーマットに従ったメッセージ

		Returns
		-------
		result : str
			正しくパースが行われたか,'ok' or 'error'
		reason: int
			メッセージの状態
		cmd: int
			メッセージのタイプ
		my_port: int
			ポート番号
		payload: str
			メッセージのペイロード
		"""
		msg_dict = json.loads(msg)
		msg_ver = StrictVersion(msg_dict['version'])

		cmd = msg_dict['msg_type']
		my_port = msg_dict['my_port']

		if msg_dict['protocol'] != PROTOCOL_NAME:
			return ('error', ERR_PROTOCOL_UNMATCH, None, None, None)
		elif msg_ver > StrictVersion(MY_VERSION):
			return ('error', ERR_VERSION_UNMATCH, None, None, None)
		elif cmd == MSG_CORE_LIST:
			payload = msg_dict['payload']
			return ('ok', OK_WITH_PAYLOAD, cmd, my_port, payload)
		else:
			return ('ok', OK_WITHOUT_PAYLOAD, cmd, my_port, None)





















