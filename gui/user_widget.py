# -*- coding: utf-8 -*-
"""
用户管理 – PyQt5 Widget（仅管理员可见）
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QDialog,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialogButtonBox, QGroupBox, QAbstractItemView,
)

from db import execute_query, generate_next_id
from utils import current_timestamp
from user_manager import ROLE_ADMIN, ROLE_TEACHER, ROLE_STUDENT, ROLE_LABELS, _hash_password

ROLE_OPTIONS = [ROLE_ADMIN, ROLE_TEACHER, ROLE_STUDENT]
ROLE_DISPLAY = {ROLE_ADMIN: "管理员", ROLE_TEACHER: "教师", ROLE_STUDENT: "学生"}


class UserDialog(QDialog):
    """添加用户对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("添加用户")
        self.setMinimumWidth(360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(8)

        self.username_edit = QLineEdit()
        form.addRow("用户名*：", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        form.addRow("密码*：", self.password_edit)

        self.name_edit = QLineEdit()
        form.addRow("姓名*：", self.name_edit)

        self.role_combo = QComboBox()
        for r in ROLE_OPTIONS:
            self.role_combo.addItem(ROLE_DISPLAY[r], r)
        form.addRow("角色*：", self.role_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("确 定")
        buttons.button(QDialogButtonBox.Cancel).setText("取 消")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        name = self.name_edit.text().strip()

        if not username:
            QMessageBox.warning(self, "提示", "用户名不能为空。")
            return
        if not password:
            QMessageBox.warning(self, "提示", "密码不能为空。")
            return
        if not name:
            QMessageBox.warning(self, "提示", "姓名不能为空。")
            return

        dup = execute_query(
            "SELECT 1 FROM users WHERE username = %s", (username,), fetchone=True
        )
        if dup:
            QMessageBox.warning(self, "错误", "用户名已存在。")
            return

        self.accept()

    def get_data(self) -> dict:
        return {
            "username": self.username_edit.text().strip(),
            "password": self.password_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "role": self.role_combo.currentData(),
        }


class ChangePasswordDialog(QDialog):
    """修改密码对话框"""

    def __init__(self, target_user: dict, is_admin_reset: bool = False, parent=None):
        super().__init__(parent)
        self.target_user = target_user
        self.is_admin_reset = is_admin_reset
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("重置密码" if self.is_admin_reset else "修改密码")
        self.setMinimumWidth(340)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(8)

        if not self.is_admin_reset:
            self.old_pwd_edit = QLineEdit()
            self.old_pwd_edit.setEchoMode(QLineEdit.Password)
            form.addRow("当前密码*：", self.old_pwd_edit)

        self.new_pwd_edit = QLineEdit()
        self.new_pwd_edit.setEchoMode(QLineEdit.Password)
        form.addRow("新密码*：", self.new_pwd_edit)

        self.confirm_pwd_edit = QLineEdit()
        self.confirm_pwd_edit.setEchoMode(QLineEdit.Password)
        form.addRow("确认新密码*：", self.confirm_pwd_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("确 定")
        buttons.button(QDialogButtonBox.Cancel).setText("取 消")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self):
        new_pwd = self.new_pwd_edit.text().strip()
        confirm_pwd = self.confirm_pwd_edit.text().strip()

        if not new_pwd:
            QMessageBox.warning(self, "提示", "新密码不能为空。")
            return
        if new_pwd != confirm_pwd:
            QMessageBox.warning(self, "错误", "两次输入的密码不一致。")
            return

        if not self.is_admin_reset:
            old_pwd = self.old_pwd_edit.text().strip()
            stored = execute_query(
                "SELECT password FROM users WHERE user_id = %s",
                (self.target_user["user_id"],), fetchone=True,
            )
            if not stored or stored["password"] != _hash_password(old_pwd):
                QMessageBox.warning(self, "错误", "当前密码不正确。")
                return

        self.accept()

    def get_new_password(self) -> str:
        return self.new_pwd_edit.text().strip()


class UserWidget(QWidget):
    """用户管理主界面（仅管理员可见）"""

    COLUMNS = ["用户ID", "用户名", "姓名", "角色", "创建时间"]
    COL_KEYS = ["user_id", "username", "name", "role_label", "created_at"]

    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # ── 搜索栏 ──
        search_group = QGroupBox("搜索")
        search_layout = QHBoxLayout(search_group)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入用户名或姓名关键词后按回车搜索")
        self.search_edit.returnPressed.connect(self.search)
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.search)
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self.refresh)
        search_layout.addWidget(QLabel("关键词："))
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(search_btn)
        search_layout.addWidget(reset_btn)
        layout.addWidget(search_group)

        # ── 工具栏 ──
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ 添加用户")
        self.reset_pwd_btn = QPushButton("🔑 重置密码")
        self.delete_btn = QPushButton("🗑 删除用户")
        self.refresh_btn = QPushButton("🔄 刷新")

        for btn in [self.add_btn, self.reset_pwd_btn, self.delete_btn, self.refresh_btn]:
            btn.setMinimumHeight(28)
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # ── 表格 ──
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.status_label = QLabel("共 0 条记录")
        layout.addWidget(self.status_label)

        self.add_btn.clicked.connect(self.add_user)
        self.reset_pwd_btn.clicked.connect(self.reset_password)
        self.delete_btn.clicked.connect(self.delete_user)
        self.refresh_btn.clicked.connect(self.refresh)

    def _populate_table(self, users):
        self.table.setRowCount(len(users))
        for row, u in enumerate(users):
            row_data = dict(u)
            row_data["role_label"] = ROLE_DISPLAY.get(u["role"], u["role"])
            for col, key in enumerate(self.COL_KEYS):
                item = QTableWidgetItem(str(row_data.get(key, "") or ""))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
        self.status_label.setText(f"共 {len(users)} 条记录")

    def refresh(self):
        self.search_edit.clear()
        users = execute_query("SELECT * FROM users ORDER BY user_id", fetch=True)
        self._populate_table(users)

    def search(self):
        keyword = self.search_edit.text().strip()
        if not keyword:
            self.refresh()
            return
        like = f"%{keyword}%"
        users = execute_query(
            "SELECT * FROM users WHERE username LIKE %s OR name LIKE %s",
            (like, like), fetch=True,
        )
        self._populate_table(users)

    def _selected_user_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).text()

    def add_user(self):
        dlg = UserDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            now = current_timestamp()
            uid = generate_next_id("users", "user_id", "U")
            execute_query(
                "INSERT INTO users (user_id, username, password, role, name, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (uid, data["username"], _hash_password(data["password"]),
                 data["role"], data["name"], now),
            )
            QMessageBox.information(self, "成功", f"用户 '{data['username']}' 已添加，ID：{uid}")
            self.refresh()

    def reset_password(self):
        uid = self._selected_user_id()
        if not uid:
            QMessageBox.warning(self, "提示", "请先选择要重置密码的用户。")
            return
        target = execute_query(
            "SELECT * FROM users WHERE user_id = %s", (uid,), fetchone=True
        )
        if not target:
            return
        dlg = ChangePasswordDialog(target, is_admin_reset=True, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            new_pwd = dlg.get_new_password()
            execute_query(
                "UPDATE users SET password = %s WHERE user_id = %s",
                (_hash_password(new_pwd), uid),
            )
            QMessageBox.information(self, "成功", f"用户 '{target['username']}' 的密码已重置。")

    def delete_user(self):
        uid = self._selected_user_id()
        if not uid:
            QMessageBox.warning(self, "提示", "请先选择要删除的用户。")
            return
        if uid == self.current_user["user_id"]:
            QMessageBox.warning(self, "错误", "不能删除当前登录的账号。")
            return
        target = execute_query(
            "SELECT * FROM users WHERE user_id = %s", (uid,), fetchone=True
        )
        if not target:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除用户 '{target['username']}'（{target['name']}）吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            execute_query("DELETE FROM users WHERE user_id = %s", (uid,))
            QMessageBox.information(self, "成功", "用户已删除。")
            self.refresh()
