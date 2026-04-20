# -*- coding: utf-8 -*-
"""
简单的信息管理系统 – PyQt5 GUI 入口
使用方法：python main_gui.py
"""

import sys

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from db import init_db
from gui.login_dialog import LoginDialog, _init_default_admin
from gui.main_window import MainWindow


def main():
    # 高 DPI 适配
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("简单的信息管理系统")
    app.setApplicationVersion("2.0.0")

    # 设置全局字体（兼容中文显示）
    font = QFont("Microsoft YaHei", 10)
    # Set preferred font families for CJK support; fall back to setFamily for Qt < 5.13
    try:
        font.setFamilies(["Microsoft YaHei", "WenQuanYi Micro Hei", "Noto Sans CJK SC", "Sans"])
    except AttributeError:
        font.setFamily("Microsoft YaHei")
    app.setFont(font)

    # 初始化数据库
    try:
        init_db()
        _init_default_admin()
    except Exception as exc:
        QMessageBox.critical(
            None, "数据库错误",
            f"无法连接数据库：{exc}\n\n请检查 config.py 中的数据库配置后重试。"
        )
        sys.exit(1)

    # 登录
    login_dlg = LoginDialog()
    if login_dlg.exec_() != LoginDialog.Accepted:
        sys.exit(0)

    current_user = login_dlg.get_user()
    if not current_user:
        sys.exit(0)

    # 主窗口
    window = MainWindow(current_user)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
