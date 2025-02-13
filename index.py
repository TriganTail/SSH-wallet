import os
import sys
import sqlite3
import json

from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QTableView, QDialog, QVBoxLayout,
                             QLineEdit, QPushButton, QLabel, QMessageBox, QFileDialog, QMenu,
                             QHBoxLayout, QComboBox, QHeaderView)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
from cryptography.fernet import Fernet

# Функции шифрования и дешифрования
def encrypt_data(data, key):
    return Fernet(key).encrypt(data.encode())

def decrypt_data(data, key):
    return Fernet(key).decrypt(data).decode()

# Класс для управления базой данных
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
        except sqlite3.Error as e:
            QMessageBox.critical(None, 'Ошибка', str(e))

    def initialize_table(self):
        if not self.conn:
            return
        try:
            self.cur.execute('''
            CREATE TABLE IF NOT EXISTS ssh_wallet (
                description TEXT, domain TEXT, ip TEXT,
                ssh_command TEXT, ssh_password TEXT, ssh_key TEXT
            )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
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

# Диалог авторизации
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setStyleSheet("""
           QDialog {
               background-color: #09122C;
           }
           QLabel {
               font-size: 14px;
               color: white;
           }
           QLineEdit {
               border: 1px solid #E17564;
               padding: 5px;
               font-size: 14px;
               background-color: #09122C;
               color: white;
           }
           QPushButton {
               background-color: #BE3144;
               color: white;
               border: none;
               padding: 10px;
               font-size: 14px;
           }
           QPushButton:hover {
               background-color: #872341;
           }
           QMessageBox {
    background-color: #09122C;
    color: white;
}
QMessageBox QPushButton {
    background-color: #BE3144;
    color: white;
    border: none;
    padding: 5px 10px;
    font-size: 14px;
}
QMessageBox QPushButton:hover {
    background-color: #872341;
}
QMessageBox QLabel {
    color: white;
    font-size: 14px;
}
           """)

    def setup_ui(self):
        self.setWindowTitle('Авторизация')
        self.resize(400, 200)
        self.setWindowIcon(QtGui.QIcon("favicon.ico"))
        layout = QVBoxLayout()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        login_btn = QPushButton('Войти')
        login_btn.clicked.connect(self.check_credentials)
        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.username)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password)
        layout.addWidget(login_btn)
        self.setLayout(layout)

    def check_credentials(self):
        if self.username.text() == 'admin' and self.password.text() == '1':
            self.accept()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Неверные учетные данные')

# Главное окно приложения
class MainWindow(QMainWindow):
    def __init__(self, key, key_path):
        super().__init__()
        self.key = key
        self.key_path = key_path
        self.db = DatabaseManager(key)
        self.db_path = self.db.db_path
        self.initUI()
        self.load_paths_from_json()

    def initUI(self):
        self.setWindowTitle('SSH-WALLET')
        self.resize(1200, 800)
        self.setWindowIcon(QtGui.QIcon("favicon.ico"))
        self.setStyleSheet("""
            QMainWindow {
                background-color: #09122C;
            }

            QComboBox {
                background-color: #09122C;
                font-size: 14px;
                padding: 10px;
                color: white;
                border: 1px solid #E17564;
            }

            QComboBox QAbstractItemView {
                background-color: #09122C;
                color: white;
                selection-background-color: #BE3144;
                selection-color: white;
            }

            QComboBox::drop-down {
                background-color: #BE3144;
                border: none;
            }

            QComboBox::down-arrow {
                image: url(down_arrow.png); /* Замените на ваш путь к изображению стрелки */
            }

            QPushButton {
                background-color: #BE3144;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
            }

            QPushButton:hover {
                background-color: #872341;
            }

            QPushButton:pressed {
                background-color: #09122C;
                color: white;
            }

            QLineEdit, QTableView {
                border: 1px solid #E17564;
                padding: 5px;
                font-size: 14px;
                background-color: #09122C;
                color: white;
            }

            QLineEdit:focus, QTableView:focus {
                border: 1px solid #BE3144;
            }

            QLabel {
                font-size: 14px;
                color: white;
            }

            QTableView {
                gridline-color: #E17564;
                background-color: #09122C;
                selection-background-color: #BE3144;
                selection-color: white;
            }

            QTableView::item:hover {
                background-color: #872341;
            }

            QHeaderView::section {
                background-color: #BE3144;
                color: white;
                padding: 5px;
                font-size: 14px;
                border: 1px solid #E17564;
            }

            QHeaderView::section:horizontal {
                border-left: none;
            }

            QHeaderView::section:vertical {
                border-top: none;
            }

            QHeaderView::section:checked {
                background-color: #872341;
            }

            QTableView QTableCornerButton::section {
                background-color: #BE3144;
                border: 1px solid #E17564;
            }

            QScrollBar:vertical {
                background: #09122C;
                width: 12px;
                margin: 0px 0px 0px 0px;
            }

            QScrollBar::handle:vertical {
                background: #BE3144;
                min-height: 20px;
                border-radius: 5px;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

            QMenu {
                background-color: #09122C;
                color: white;
                border: 1px solid #E17564;
            }

            QMenu::item {
                padding: 5px 20px;
            }

            QMenu::item:selected {
                background-color: #BE3144;
                color: white;
            }

            QMenu::separator {
                height: 1px;
                background: #E17564;
                margin: 5px 0px;
            }
            QMessageBox {
    background-color: #09122C;
    color: white;
}
QMessageBox QPushButton {
    background-color: #BE3144;
    color: white;
    border: none;
    padding: 5px 10px;
    font-size: 14px;
}
QMessageBox QPushButton:hover {
    background-color: #872341;
}
QMessageBox QLabel {
    color: white;
    font-size: 14px;
}
        """)

        self.setup_toolbar()
        self.setup_status_bar()
        self.setup_table()
        self.setup_search()
        self.setup_context_menu()
        self.setup_add_layout()

    def setup_toolbar(self):
        toolbar = QHBoxLayout()
        buttons = [
            ('Создать БД', self.create_db),
            ('Загрузить БД', self.load_db),
            ('Загрузить ключ', self.load_key),
            ('Обновить', self.load_data),
            ('Сохранить', self.save_data),
            ('Создать JSON', self.save_paths_to_json),
            ('Загрузить JSON', self.load_paths_from_json)  # Добавляем обработчик
        ]
        for name, method in buttons:
            btn = QPushButton(name)
            btn.clicked.connect(method)
            toolbar.addWidget(btn)
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addLayout(toolbar)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def setup_status_bar(self):
        status_layout = QHBoxLayout()
        self.db_label = QLabel("DB: Не загружена")
        self.key_label = QLabel("Ключ: Не загружен")
        self.count_label = QLabel("Записей: 0")
        status_layout.addWidget(self.db_label)
        status_layout.addWidget(self.key_label)
        status_layout.addWidget(self.count_label)

        central_widget = self.centralWidget()
        central_widget.layout().insertLayout(1, status_layout)

    def setup_table(self):
        self.model = QStandardItemModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        headers = ['Описание', 'Домен', 'IP', 'SSH запрос', 'Пароль', 'Ключ']
        self.model.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        central_widget = self.centralWidget()
        central_widget.layout().addWidget(self.table)

    def setup_search(self):
        search_layout = QHBoxLayout()
        self.search_filter = QComboBox()
        self.search_filter.addItems(
            ['Все'] + [self.model.headerData(i, Qt.Horizontal) for i in range(self.model.columnCount())])
        self.search_box = QLineEdit()
        self.search_box.textChanged.connect(self.search)  # Добавляем обработчик изменения текста
        search_clear_btn = QPushButton('Очистить')
        search_clear_btn.clicked.connect(self.search_box.clear)
        search_layout.addWidget(self.search_filter)
        search_layout.addWidget(self.search_box)
        search_layout.addWidget(search_clear_btn)
        central_widget = self.centralWidget()
        central_widget.layout().addLayout(search_layout)

    def setup_add_layout(self):
        add_layout = QHBoxLayout()
        self.add_fields = [QLineEdit() for _ in range(6)]
        for field in self.add_fields:
            field.setMinimumHeight(30)
            add_layout.addWidget(field)
        add_btn = QPushButton('Добавить')
        add_btn.clicked.connect(self.add_record)
        add_layout.addWidget(add_btn)
        self.centralWidget().layout().addLayout(add_layout)

    def create_db(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Создать БД', '', 'SQLite DB (*.db)')
        if path:
            self.db = DatabaseManager(self.key, path)
            self.db.create_connection()
            self.db.initialize_table()
            self.db_path = path
            self.db_label.setText(f"DB: {path}")
            QMessageBox.information(self, 'Успех', 'База создана')

    def load_db(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Выбрать БД', '', 'SQLite DB (*.db)')
        if path:
            self.db = DatabaseManager(self.key, path)
            self.db.create_connection()
            self.load_data()
            self.db_path = path
            self.db_label.setText(f"DB: {path}")

    def load_key(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Выбрать ключ', '', 'Key files (*.key)')
        if path:
            with open(path, 'rb') as f:
                self.key = f.read()
            self.key_path = path
            self.key_label.setText(f"Ключ: {path}")
            self.db = DatabaseManager(self.key, self.db_path)
            self.load_data()

    def load_data(self):
        self.db.create_connection()
        self.model.setRowCount(0)
        data = self.db.load_data()
        for row in data:
            self.model.appendRow([QStandardItem(item) for item in row])
        self.update_count()

    def save_data(self):
        data = [[self.model.item(row, col).text() for col in range(6)] for row in range(self.model.rowCount())]
        self.db.save_data(data)
        QMessageBox.information(self, 'Сохранено', 'Данные успешно сохранены')

    def search(self):
        text = self.search_box.text().lower()
        col = self.search_filter.currentIndex() - 1  # -1 означает "Все"
        for row in range(self.model.rowCount()):
            if col == -1:  # Если выбрано "Все"
                match = any(text in self.model.item(row, c).text().lower() for c in range(self.model.columnCount()))
            else:  # Если выбран конкретный столбец
                match = text in self.model.item(row, col).text().lower()
            self.table.setRowHidden(row, not match)

    def add_record(self):
        self.model.appendRow([QStandardItem(field.text() or "None") for field in self.add_fields])
        for field in self.add_fields:
            field.clear()
        self.update_count()
        QMessageBox.information(self, 'Успех', 'Запись добавлена')

    def show_context_menu(self, pos):
        # Создаем контекстное меню
        menu = QMenu()
        copy_action = menu.addAction("Копировать")
        delete_action = menu.addAction("Удалить строку")

        # Подключаем действия к методам
        copy_action.triggered.connect(self.copy_data)
        delete_action.triggered.connect(self.delete_row)

        # Отображаем меню в позиции курсора
        menu.exec_(self.table.mapToGlobal(pos))

    def setup_context_menu(self):
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
    def delete_row(self):
        # Получаем текущий индекс строки
        current_index = self.table.currentIndex()
        if not current_index.isValid():
            QMessageBox.warning(self, 'Ошибка', 'Строка не выбрана')
            return

        # Удаляем строку из модели
        self.model.removeRow(current_index.row())

        # Обновляем счетчик записей
        self.update_count()

        QMessageBox.information(self, 'Успех', 'Строка успешно удалена')
    def copy_data(self):
        index = self.table.currentIndex()
        QApplication.clipboard().setText(self.model.data(index))

    def update_count(self):
        self.count_label.setText(f"Записей: {self.model.rowCount()}")

    def save_paths_to_json(self):
        if not self.key:
            QMessageBox.warning(self, 'Ошибка', 'Ключ не загружен')
            return
        paths = {'db_path': self.db.db_path, 'key_path': self.key_path}
        try:
            encrypted = encrypt_data(json.dumps(paths), self.key)
            with open('paths.json.enc', 'wb') as f:
                f.write(encrypted)
            QMessageBox.information(self, 'Успех', 'Пути сохранены')
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', f'Ошибка: {e}')

    def load_paths_from_json(self):
        if not self.key:
            QMessageBox.warning(self, 'Ошибка', 'Ключ не загружен')
            return

        # Открываем диалог выбора файла
        path, _ = QFileDialog.getOpenFileName(self, 'Выбрать JSON', '', 'Encrypted JSON (*.json.enc)')
        if not path:
            return

        try:
            with open(path, 'rb') as f:
                data = decrypt_data(f.read(), self.key)
            paths = json.loads(data)
            self.db = DatabaseManager(self.key, paths['db_path'])
            self.db.create_connection()
            self.db_label.setText(f"DB: {paths['db_path']}")
            self.key_path = paths['key_path']
            self.key_label.setText(f"Ключ: {self.key_path}")
            self.load_data()
            QMessageBox.information(self, 'Успех', 'JSON успешно загружен')
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', f'Ошибка загрузки JSON: {e}')


def load_or_create_key():
    key_path = "encryption_key.key"
    if not os.path.exists(key_path):
        key = Fernet.generate_key()
        with open(key_path, "wb") as f:
            f.write(key)
        return key
    with open(key_path, "rb") as f:
        return f.read()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login = LoginDialog()
    if login.exec_() == QDialog.Accepted:
        key = load_or_create_key()
        key_path = "encryption_key.key"
        main = MainWindow(key, key_path)
        main.show()
    sys.exit(app.exec_())