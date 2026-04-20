# -*- coding: utf-8 -*-
"""
主窗口 – QMainWindow，包含菜单栏、工具栏、标签页内容区及状态栏
"""

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QAction, QToolBar, QStatusBar,
    QLabel, QDialog, QMessageBox, QWidget, QVBoxLayout,
    QFormLayout, QLineEdit, QDialogButtonBox,
)

from db import execute_query
from utils import current_timestamp
from user_manager import ROLE_ADMIN, ROLE_LABELS, _hash_password

from gui.student_widget import StudentWidget
from gui.course_widget import CourseWidget
from gui.teacher_widget import TeacherWidget
from gui.grade_widget import GradeWidget
from gui.user_widget import UserWidget, ChangePasswordDialog

SYSTEM_NAME = "简单的信息管理系统"
VERSION = "2.0.0"


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self.setWindowTitle(f"{SYSTEM_NAME}  v{VERSION}")
        self.resize(1100, 700)

    # ─── UI 构建 ─────────────────────────────────────────────

    def _setup_ui(self):
        """构建标签页内容区"""
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        font = QFont()
        font.setPointSize(10)
        self.tabs.setFont(font)

        self.student_tab = StudentWidget(self.current_user)
        self.course_tab = CourseWidget(self.current_user)
        self.teacher_tab = TeacherWidget(self.current_user)
        self.grade_tab = GradeWidget(self.current_user)

        self.tabs.addTab(self.student_tab, "🎓 学生管理")
        self.tabs.addTab(self.course_tab,  "📚 课程管理")
        self.tabs.addTab(self.teacher_tab, "👩‍🏫 教师管理")
        self.tabs.addTab(self.grade_tab,   "📝 成绩管理")

        if self.current_user["role"] == ROLE_ADMIN:
            self.user_tab = UserWidget(self.current_user)
            self.tabs.addTab(self.user_tab, "👤 用户管理")
        else:
            self.user_tab = None

        self.setCentralWidget(self.tabs)

    def _setup_menu(self):
        """构建菜单栏"""
        menubar = self.menuBar()

        # ── 系统菜单 ──
        sys_menu = menubar.addMenu("系统(&S)")

        act_overview = QAction("数据概览(&O)", self)
        act_overview.setShortcut("Ctrl+D")
        act_overview.triggered.connect(self.show_overview)
        sys_menu.addAction(act_overview)

        act_sysinfo = QAction("系统信息(&I)", self)
        act_sysinfo.triggered.connect(self.show_sysinfo)
        sys_menu.addAction(act_sysinfo)

        sys_menu.addSeparator()

        act_changepwd = QAction("修改我的密码(&P)", self)
        act_changepwd.setShortcut("Ctrl+Shift+P")
        act_changepwd.triggered.connect(self.change_own_password)
        sys_menu.addAction(act_changepwd)

        sys_menu.addSeparator()

        act_exit = QAction("退出(&Q)", self)
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)
        sys_menu.addAction(act_exit)

        # ── 学生管理菜单 ──
        student_menu = menubar.addMenu("学生管理(&T)")
        act_add_s = QAction("添加学生", self)
        act_add_s.triggered.connect(lambda: (self.tabs.setCurrentWidget(self.student_tab),
                                              self.student_tab.add_student()))
        student_menu.addAction(act_add_s)

        act_list_s = QAction("学生列表", self)
        act_list_s.triggered.connect(lambda: (self.tabs.setCurrentWidget(self.student_tab),
                                               self.student_tab.refresh()))
        student_menu.addAction(act_list_s)

        act_stats_s = QAction("学生统计", self)
        act_stats_s.triggered.connect(lambda: self.student_tab.show_statistics())
        student_menu.addAction(act_stats_s)

        # ── 课程管理菜单 ──
        course_menu = menubar.addMenu("课程管理(&C)")
        act_add_c = QAction("添加课程", self)
        act_add_c.triggered.connect(lambda: (self.tabs.setCurrentWidget(self.course_tab),
                                              self.course_tab.add_course()))
        course_menu.addAction(act_add_c)

        act_list_c = QAction("课程列表", self)
        act_list_c.triggered.connect(lambda: (self.tabs.setCurrentWidget(self.course_tab),
                                               self.course_tab.refresh()))
        course_menu.addAction(act_list_c)

        act_stats_c = QAction("课程统计", self)
        act_stats_c.triggered.connect(lambda: self.course_tab.show_statistics())
        course_menu.addAction(act_stats_c)

        # ── 教师管理菜单 ──
        teacher_menu = menubar.addMenu("教师管理(&E)")
        act_add_t = QAction("添加教师", self)
        act_add_t.triggered.connect(lambda: (self.tabs.setCurrentWidget(self.teacher_tab),
                                              self.teacher_tab.add_teacher()))
        teacher_menu.addAction(act_add_t)

        act_list_t = QAction("教师列表", self)
        act_list_t.triggered.connect(lambda: (self.tabs.setCurrentWidget(self.teacher_tab),
                                               self.teacher_tab.refresh()))
        teacher_menu.addAction(act_list_t)

        act_stats_t = QAction("教师统计", self)
        act_stats_t.triggered.connect(lambda: self.teacher_tab.show_statistics())
        teacher_menu.addAction(act_stats_t)

        # ── 成绩管理菜单 ──
        grade_menu = menubar.addMenu("成绩管理(&G)")
        act_add_g = QAction("录入成绩", self)
        act_add_g.triggered.connect(lambda: (self.tabs.setCurrentWidget(self.grade_tab),
                                              self.grade_tab.add_grade()))
        grade_menu.addAction(act_add_g)

        act_list_g = QAction("成绩列表", self)
        act_list_g.triggered.connect(lambda: (self.tabs.setCurrentWidget(self.grade_tab),
                                               self.grade_tab.refresh()))
        grade_menu.addAction(act_list_g)

        act_stats_g = QAction("成绩统计", self)
        act_stats_g.triggered.connect(lambda: self.grade_tab.show_statistics())
        grade_menu.addAction(act_stats_g)

        # ── 用户管理菜单（仅管理员） ──
        if self.current_user["role"] == ROLE_ADMIN:
            user_menu = menubar.addMenu("用户管理(&U)")
            act_add_u = QAction("添加用户", self)
            act_add_u.triggered.connect(lambda: (self.tabs.setCurrentWidget(self.user_tab),
                                                  self.user_tab.add_user()))
            user_menu.addAction(act_add_u)

            act_list_u = QAction("用户列表", self)
            act_list_u.triggered.connect(lambda: (self.tabs.setCurrentWidget(self.user_tab),
                                                   self.user_tab.refresh()))
            user_menu.addAction(act_list_u)

        # ── 帮助菜单 ──
        help_menu = menubar.addMenu("帮助(&H)")
        act_about = QAction("关于系统(&A)", self)
        act_about.triggered.connect(self.show_about)
        help_menu.addAction(act_about)

    def _setup_toolbar(self):
        """构建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        act_student = QAction("学生管理", self)
        act_student.setStatusTip("切换到学生管理")
        act_student.triggered.connect(lambda: self.tabs.setCurrentWidget(self.student_tab))
        toolbar.addAction(act_student)

        act_course = QAction("课程管理", self)
        act_course.setStatusTip("切换到课程管理")
        act_course.triggered.connect(lambda: self.tabs.setCurrentWidget(self.course_tab))
        toolbar.addAction(act_course)

        act_teacher = QAction("教师管理", self)
        act_teacher.setStatusTip("切换到教师管理")
        act_teacher.triggered.connect(lambda: self.tabs.setCurrentWidget(self.teacher_tab))
        toolbar.addAction(act_teacher)

        act_grade = QAction("成绩管理", self)
        act_grade.setStatusTip("切换到成绩管理")
        act_grade.triggered.connect(lambda: self.tabs.setCurrentWidget(self.grade_tab))
        toolbar.addAction(act_grade)

        if self.current_user["role"] == ROLE_ADMIN:
            act_user = QAction("用户管理", self)
            act_user.setStatusTip("切换到用户管理")
            act_user.triggered.connect(lambda: self.tabs.setCurrentWidget(self.user_tab))
            toolbar.addAction(act_user)

        toolbar.addSeparator()

        act_overview = QAction("数据概览", self)
        act_overview.setStatusTip("查看各模块数据量")
        act_overview.triggered.connect(self.show_overview)
        toolbar.addAction(act_overview)

        act_changepwd = QAction("修改密码", self)
        act_changepwd.setStatusTip("修改当前账号密码")
        act_changepwd.triggered.connect(self.change_own_password)
        toolbar.addAction(act_changepwd)

        toolbar.addSeparator()

        act_exit = QAction("退出", self)
        act_exit.setStatusTip("退出系统")
        act_exit.triggered.connect(self.close)
        toolbar.addAction(act_exit)

    def _setup_statusbar(self):
        """构建状态栏"""
        sb = QStatusBar()
        role_label = ROLE_LABELS.get(self.current_user["role"], self.current_user["role"])
        sb.showMessage(
            f"当前用户：{self.current_user['name']}（{self.current_user['username']}）  "
            f"角色：{role_label}  |  {SYSTEM_NAME} v{VERSION}"
        )
        self.setStatusBar(sb)

    # ─── 功能函数 ─────────────────────────────────────────────

    def show_overview(self):
        """数据概览"""
        # Use pre-constructed queries per table to avoid any string concatenation risks.
        _QUERIES = {
            "students": ("学生",      "SELECT COUNT(*) AS cnt FROM students"),
            "courses":  ("课程",      "SELECT COUNT(*) AS cnt FROM courses"),
            "teachers": ("教师",      "SELECT COUNT(*) AS cnt FROM teachers"),
            "grades":   ("成绩记录",  "SELECT COUNT(*) AS cnt FROM grades"),
            "users":    ("用户",      "SELECT COUNT(*) AS cnt FROM users"),
        }
        lines = []
        for _table, (label, sql) in _QUERIES.items():
            count = execute_query(sql, fetchone=True)["cnt"]
            lines.append(f"{label}：{count} 条")
        QMessageBox.information(self, "数据概览", "\n".join(lines))

    def show_sysinfo(self):
        """系统信息"""
        from config import DB_CONFIG
        role_label = ROLE_LABELS.get(self.current_user["role"], self.current_user["role"])
        info = (
            f"系统名称：{SYSTEM_NAME}\n"
            f"版本号：{VERSION}\n"
            f"当前用户：{self.current_user['name']}（{self.current_user['username']}）\n"
            f"用户角色：{role_label}\n"
            f"当前时间：{current_timestamp()}\n\n"
            f"数据库主机：{DB_CONFIG['host']}:{DB_CONFIG['port']}\n"
            f"数据库名称：{DB_CONFIG['database']}\n\n"
            f"数据表：users / students / courses / teachers / grades"
        )
        QMessageBox.information(self, "系统信息", info)

    def change_own_password(self):
        """修改当前用户密码"""
        target = execute_query(
            "SELECT * FROM users WHERE user_id = %s",
            (self.current_user["user_id"],), fetchone=True,
        )
        if not target:
            QMessageBox.warning(self, "错误", "账户数据异常。")
            return
        dlg = ChangePasswordDialog(target, is_admin_reset=False, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            new_pwd = dlg.get_new_password()
            execute_query(
                "UPDATE users SET password = %s WHERE user_id = %s",
                (_hash_password(new_pwd), target["user_id"]),
            )
            QMessageBox.information(self, "成功", "密码已修改成功。")

    def show_about(self):
        QMessageBox.about(
            self, "关于系统",
            f"<b>{SYSTEM_NAME}</b><br>"
            f"版本：{VERSION}<br><br>"
            "功能模块：学生管理、课程管理、教师管理、成绩管理、用户管理<br>"
            "数据库：MySQL<br>"
            "界面框架：PyQt5",
        )

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "退出确认",
            "确定要退出系统吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
