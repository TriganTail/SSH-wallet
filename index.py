import os
import sys
import sqlite3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QTableView, QDialog, QVBoxLayout,
                             QLineEdit, QPushButton, QLabel, QMessageBox, QFileDialog, QMenu,
                             QHBoxLayout, QComboBox, QHeaderView)
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QTimer
from cryptography.fernet import Fernet


def encrypt_data(data, key):
    return Fernet(key).encrypt(data.encode())


def decrypt_data(data, key):
    return Fernet(key).decrypt(data).decode()


class DatabaseManager:
    def __init__(self, key, db_path='data_pass.db'):
        self.key = key
        self.db_path = db_path
        self.conn = None
        self.cur = None

    def create_connection(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cur = self.conn.cursor()
            self.cur.execute('''
                CREATE TABLE IF NOT EXISTS ssh_wallet (
                    description TEXT, domain TEXT, ip TEXT,
                    ssh_command TEXT, ssh_password TEXT, ssh_key TEXT
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при создании соединения: {e}")
            QMessageBox.critical(None, 'Ошибка', str(e))

    def load_data(self):
        if not self.conn:
            return []
        self.cur.execute("SELECT * FROM ssh_wallet")
        return [[decrypt_data(item, self.key) if item else "None" for item in row] for row in self.cur.fetchall()]

    def save_data(self, data):
        if not self.conn:
            return
        self.cur.execute("DELETE FROM ssh_wallet")
        self.cur.executemany(
            "INSERT INTO ssh_wallet VALUES (?,?,?,?,?,?)",
            [[encrypt_data(str(item), self.key) if item else encrypt_data("None", self.key) for item in row] for row in data]
        )
        self.conn.commit()


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Авторизация')
        self.resize(400, 200)
        layout = QVBoxLayout()
        self.username, self.password = QLineEdit(), QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        login_btn = QPushButton('Войти')
        login_btn.clicked.connect(self.check_credentials)
        for label, widget in zip(["Логин:", "Пароль:"], [self.username, self.password]):
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)
        layout.addWidget(login_btn)
        self.setLayout(layout)

    def check_credentials(self):
        if self.username.text() == 'admin' and self.password.text() == '1':
            self.accept()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Неверные учетные данные')


class MainWindow(QMainWindow):
    def __init__(self, key):
        super().__init__()
        self.key = key
        self.db = DatabaseManager(key)
        self.db.create_connection()
        self.initUI()



    def initUI(self):
        self.setWindowTitle('SSH кошелёк')
        self.resize(1200, 800)
        self.model = QStandardItemModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        headers = ['Описание', 'Домен', 'IP', 'SSH запрос', 'Пароль', 'Ключ']
        self.model.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        toolbar = QHBoxLayout()
        for name, method in zip(['Создать БД', 'Загрузить БД', 'Обновить', 'Сохранить'],
                                [self.create_db, self.load_db, self.load_data, self.save_data]):
            btn = QPushButton(name)
            btn.clicked.connect(method)
            toolbar.addWidget(btn)

        search_layout = QHBoxLayout()
        self.search_box, self.search_filter = QLineEdit(), QComboBox()
        self.search_filter.addItems(['Все'] + headers)
        search_layout.addWidget(self.search_filter)
        search_layout.addWidget(self.search_box)
        self.search_box.textChanged.connect(self.search)

        add_layout = QHBoxLayout()
        self.add_fields = [QLineEdit() for _ in headers]
        for field in self.add_fields:
            add_layout.addWidget(field)
        add_btn = QPushButton('Добавить')
        add_btn.clicked.connect(self.add_record)
        add_layout.addWidget(add_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(toolbar)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.table)
        main_layout.addLayout(add_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.load_data()

    def create_db(self):
        self.db.create_connection()
        QMessageBox.information(self, 'Успех', 'База создана')

    def load_db(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Выбрать БД', '', 'SQLite DB (*.db)')
        if path:
            self.db = DatabaseManager(self.key, path)
            self.db.create_connection()
            self.load_data()

    def load_data(self):
        self.model.setRowCount(0)
        for row in self.db.load_data():
            self.model.appendRow([QStandardItem(item) for item in row])

    def save_data(self):
        data = [[self.model.item(row, col).text() for col in range(self.model.columnCount())]
                for row in range(self.model.rowCount())]
        self.db.save_data(data)
        QMessageBox.information(self, 'Сохранено', 'Данные успешно сохранены')

    def search(self):
        text, col = self.search_box.text().lower(), self.search_filter.currentIndex() - 1
        for row in range(self.model.rowCount()):
            match = any(text in self.model.item(row, c).text().lower() for c in range(self.model.columnCount())
                        if col == -1 or c == col)
            self.table.setRowHidden(row, not match)

    def add_record(self):
        self.model.appendRow([QStandardItem(field.text() if field.text() else "None") for field in self.add_fields])
        for field in self.add_fields:
            field.clear()
        QMessageBox.information(self, 'Успех', 'Запись успешно добавлена')

    def show_context_menu(self, pos):
        menu = QMenu()
        copy_action, delete_action = menu.addAction("Копировать"), menu.addAction("Удалить строку")
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(self.model.data(self.table.currentIndex())))
        delete_action.triggered.connect(lambda: self.model.removeRow(self.table.currentIndex().row()))
        menu.exec_(self.table.mapToGlobal(pos))


if __name__ == '__main__':
    KEY_FILE = "encryption_key.key"


    def load_or_create_key():
        """Загружает ключ из файла или создает новый, если файла нет."""
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as key_file:
                return key_file.read()
        else:
            key = Fernet.generate_key()
            with open(KEY_FILE, "wb") as key_file:
                key_file.write(key)
            return key


    app = QApplication(sys.argv)
    login = LoginDialog()
    if login.exec_() == QDialog.Accepted:
        key = load_or_create_key()
        main = MainWindow(key)
        main.show()
    sys.exit(app.exec_())
