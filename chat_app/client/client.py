import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTextEdit, QLabel, QListWidget
from PyQt5.QtCore import pyqtSlot
import requests
import socketio

class ChatClient(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.sio = socketio.Client()
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('message', self.on_message)
        self.sio.on('private_message', self.on_private_message)
        self.authenticated = False
        self.username = None

        # 自动登录
        self.auto_login()

    def initUI(self):
        self.setGeometry(100, 100, 400, 300)
        self.setWindowTitle('聊天客户端')

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.login_layout = QVBoxLayout()
        self.layout.addLayout(self.login_layout)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('账号（四位数字）')
        self.login_layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('密码（十二位及以下的纯数字或数字加英文字母）')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.login_layout.addWidget(self.password_input)

        self.login_button = QPushButton('登录')
        self.login_button.clicked.connect(self.login)
        self.login_layout.addWidget(self.login_button)

        self.register_button = QPushButton('注册')
        self.register_button.clicked.connect(self.register)
        self.login_layout.addWidget(self.register_button)

        self.chat_layout = QVBoxLayout()
        self.layout.addLayout(self.chat_layout)

        self.chatBox = QTextEdit()
        self.chatBox.setReadOnly(True)
        self.chat_layout.addWidget(self.chatBox)

        self.friendsList = QListWidget()
        self.chat_layout.addWidget(self.friendsList)

        self.inputLayout = QHBoxLayout()
        self.chat_layout.addLayout(self.inputLayout)

        self.messageInput = QLineEdit()
        self.inputLayout.addWidget(self.messageInput)

        self.sendButton = QPushButton('发送')
        self.sendButton.clicked.connect(self.sendMessage)
        self.inputLayout.addWidget(self.sendButton)

        self.chat_layout.setEnabled(False)

    def auto_login(self):
        if os.path.exists('credentials.json'):
            with open('credentials.json', 'r') as file:
                credentials = json.load(file)
                self.username_input.setText(credentials['username'])
                self.password_input.setText(credentials['password'])
                self.login()

    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        response = requests.post('https://your-app-name.onrender.com/register', json={'username': username, 'password': password})
        if response.status_code == 201:
            self.chatBox.append('注册成功，请登录！')
        else:
            self.chatBox.append(response.json()['message'])

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        response = requests.post('https://your-app-name.onrender.com/login', json={'username': username, 'password': password})
        if response.status_code == 200:
            self.authenticated = True
            self.username = username
            self.login_layout.setEnabled(False)
            self.chat_layout.setEnabled(True)
            self.get_friends()
            self.sio.connect('https://your-app-name.onrender.com')
            self.sio.emit('join', {'username': username})
            with open('credentials.json', 'w') as file:
                json.dump({'username': username, 'password': password}, file)
        else:
            self.chatBox.append(response.json()['message'])

    def get_friends(self):
        response = requests.get('https://your-app-name.onrender.com/friends', cookies={'session': requests.Session().cookies})
        if response.status_code == 200:
            friends = response.json()['friends']
            self.friendsList.clear()
            for friend in friends:
                self.friendsList.addItem(friend['username'])

    def sendMessage(self):
        message = self.messageInput.text()
        if message:
            self.sio.emit('message', message)
            self.messageInput.clear()

    def send_private_message(self, recipient_username, message):
        recipient_session_id = ...  # 获取好友的session_id
        self.sio.emit('private_message', {'recipient_session_id': recipient_session_id, 'message': message})

    def on_connect(self):
        self.chatBox.append("连接到服务器")

    def on_disconnect(self):
        self.chatBox.append("与服务器断开连接")

    def on_message(self, msg):
        self.chatBox.append(msg)

    def on_private_message(self, data):
        self.chatBox.append(f"私信来自 {data['sender']}: {data['message']}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    client = ChatClient()
    client.show()
    sys.exit(app.exec_())