# -*- coding: utf-8 -*-
"""
登录对话框
"""

import hashlib

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QFrame,
)

from db import execute_query, init_db
from utils import current_timestamp
from user_manager import ROLE_ADMIN, ROLE_TEACHER, ROLE_STUDENT, ROLE_LABELS


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _init_default_admin():
    """若 users 表为空则创建默认管理员账号"""
    count = execute_query("SELECT COUNT(*) AS cnt FROM users", fetchone=True)["cnt"]
    if count == 0:
        from db import generate_next_id
        uid = generate_next_id("users", "user_id", "U")
        execute_query(
            "INSERT INTO users (user_id, username, password, role, name, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (uid, "admin", _hash_password("admin123"), ROLE_ADMIN, "系统管理员",
             current_timestamp()),
        )


class LoginDialog(QDialog):
    """用户登录对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user = None
        self._fail_count = 0
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("简单的信息管理系统 – 登录")
        self.setFixedSize(380, 260)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 24, 30, 24)
        root.setSpacing(12)

        # ── 标题 ──
        title = QLabel("简单的信息管理系统")
        title.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        root.addWidget(title)

        subtitle = QLabel("请登录后使用系统")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666;")
        root.addWidget(subtitle)

        # ── 分隔线 ──
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        root.addWidget(line)

        # ── 表单 ──
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        form.addRow("用户名：", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("请输入密码")
        form.addRow("密  码：", self.password_edit)

        root.addLayout(form)

        # ── 按钮 ──
        btn_row = QHBoxLayout()
        self.login_btn = QPushButton("登 录")
        self.login_btn.setDefault(True)
        self.login_btn.setMinimumHeight(32)
        cancel_btn = QPushButton("退 出")
        cancel_btn.setMinimumHeight(32)
        btn_row.addWidget(self.login_btn)
        btn_row.addWidget(cancel_btn)
        root.addLayout(btn_row)

        self.login_btn.clicked.connect(self._do_login)
        cancel_btn.clicked.connect(self.reject)
        self.password_edit.returnPressed.connect(self._do_login)

        # 提示默认账号
        hint = QLabel("默认管理员账号：admin / admin123")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #999; font-size: 11px;")
        root.addWidget(hint)

    def _do_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "提示", "用户名和密码不能为空。")
            return

        hashed = _hash_password(password)
        user = execute_query(
            "SELECT * FROM users WHERE username = %s AND password = %s",
            (username, hashed),
            fetchone=True,
        )

        if user:
            self.current_user = user
            self.accept()
        else:
            self._fail_count += 1
            if self._fail_count >= 3:
                QMessageBox.critical(self, "错误", "登录失败次数过多，程序退出。")
                self.reject()
            else:
                remaining = 3 - self._fail_count
                QMessageBox.warning(
                    self, "登录失败",
                    f"用户名或密码不正确，还有 {remaining} 次机会。"
                )
                self.password_edit.clear()
                self.password_edit.setFocus()

    def get_user(self):
        return self.current_user
