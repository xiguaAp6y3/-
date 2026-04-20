# -*- coding: utf-8 -*-
"""
课程管理 – PyQt5 Widget
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QDialog,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialogButtonBox, QGroupBox, QAbstractItemView,
    QTextEdit,
)

from db import execute_query, generate_next_id
from utils import current_timestamp

COURSE_TYPES = ["必修", "选修", "公共基础"]


class CourseDialog(QDialog):
    """添加 / 编辑课程对话框"""

    def __init__(self, parent=None, course=None):
        super().__init__(parent)
        self.course = course
        self._setup_ui()
        if course:
            self._fill_data(course)

    def _setup_ui(self):
        self.setWindowTitle("编辑课程信息" if self.course else "添加课程")
        self.setMinimumWidth(420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(8)

        self.name_edit = QLineEdit()
        form.addRow("课程名称*：", self.name_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(COURSE_TYPES)
        form.addRow("课程类型*：", self.type_combo)

        self.credits_spin = QDoubleSpinBox()
        self.credits_spin.setRange(0.5, 20.0)
        self.credits_spin.setSingleStep(0.5)
        self.credits_spin.setValue(3.0)
        form.addRow("学分*：", self.credits_spin)

        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(8, 256)
        self.hours_spin.setValue(48)
        form.addRow("学时*：", self.hours_spin)

        self.semester_edit = QLineEdit()
        self.semester_edit.setPlaceholderText("如 2023-2024-1")
        form.addRow("开课学期*：", self.semester_edit)

        self.teacher_edit = QLineEdit()
        form.addRow("授课教师*：", self.teacher_edit)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText("可选")
        form.addRow("课程描述：", self.desc_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("确 定")
        buttons.button(QDialogButtonBox.Cancel).setText("取 消")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _fill_data(self, c):
        self.name_edit.setText(c.get("name", ""))
        idx = self.type_combo.findText(c.get("course_type", "必修"))
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.credits_spin.setValue(float(c.get("credits", 3.0)))
        self.hours_spin.setValue(int(c.get("hours", 48)))
        self.semester_edit.setText(c.get("semester", ""))
        self.teacher_edit.setText(c.get("teacher_name", ""))
        self.desc_edit.setPlainText(c.get("description", "") or "")

    def _validate_and_accept(self):
        name = self.name_edit.text().strip()
        semester = self.semester_edit.text().strip()
        teacher = self.teacher_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "提示", "课程名称不能为空。")
            return
        if not semester:
            QMessageBox.warning(self, "提示", "开课学期不能为空。")
            return
        if not teacher:
            QMessageBox.warning(self, "提示", "授课教师不能为空。")
            return

        # 新增时检查名称重复
        if not self.course:
            dup = execute_query(
                "SELECT 1 FROM courses WHERE name = %s", (name,), fetchone=True
            )
            if dup:
                QMessageBox.warning(self, "错误", "该课程名称已存在。")
                return

        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "course_type": self.type_combo.currentText(),
            "credits": self.credits_spin.value(),
            "hours": self.hours_spin.value(),
            "semester": self.semester_edit.text().strip(),
            "teacher_name": self.teacher_edit.text().strip(),
            "description": self.desc_edit.toPlainText().strip(),
        }


class CourseWidget(QWidget):
    """课程管理主界面"""

    COLUMNS = ["课程编号", "课程名称", "类型", "学分", "学时", "开课学期", "授课教师"]
    COL_KEYS = ["course_id", "name", "course_type", "credits", "hours", "semester", "teacher_name"]

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
        self.search_combo = QComboBox()
        self.search_combo.addItems(["全部", "按名称", "按教师", "按类型", "按学期", "按编号"])
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入关键词后按回车或点击搜索")
        self.search_edit.returnPressed.connect(self.search)
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.search)
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self.refresh)
        search_layout.addWidget(QLabel("搜索方式："))
        search_layout.addWidget(self.search_combo)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(search_btn)
        search_layout.addWidget(reset_btn)
        layout.addWidget(search_group)

        # ── 工具栏 ──
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ 添加课程")
        self.edit_btn = QPushButton("✏️ 编辑")
        self.delete_btn = QPushButton("🗑 删除")
        self.refresh_btn = QPushButton("🔄 刷新")
        self.import_btn = QPushButton("📥 导入示例数据")
        self.stats_btn = QPushButton("📊 统计")

        for btn in [self.add_btn, self.edit_btn, self.delete_btn,
                    self.refresh_btn, self.import_btn, self.stats_btn]:
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
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

        self.status_label = QLabel("共 0 条记录")
        layout.addWidget(self.status_label)

        self.add_btn.clicked.connect(self.add_course)
        self.edit_btn.clicked.connect(self.edit_course)
        self.delete_btn.clicked.connect(self.delete_course)
        self.refresh_btn.clicked.connect(self.refresh)
        self.import_btn.clicked.connect(self.batch_import)
        self.stats_btn.clicked.connect(self.show_statistics)

    def _populate_table(self, courses):
        self.table.setRowCount(len(courses))
        for row, c in enumerate(courses):
            for col, key in enumerate(self.COL_KEYS):
                item = QTableWidgetItem(str(c.get(key, "") or ""))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
        self.status_label.setText(f"共 {len(courses)} 条记录")

    def refresh(self):
        self.search_edit.clear()
        self.search_combo.setCurrentIndex(0)
        courses = execute_query("SELECT * FROM courses ORDER BY course_id", fetch=True)
        self._populate_table(courses)

    def search(self):
        mode = self.search_combo.currentText()
        keyword = self.search_edit.text().strip()

        if mode == "全部" or not keyword:
            courses = execute_query("SELECT * FROM courses ORDER BY course_id", fetch=True)
        elif mode == "按名称":
            courses = execute_query(
                "SELECT * FROM courses WHERE name LIKE %s ORDER BY course_id",
                (f"%{keyword}%",), fetch=True,
            )
        elif mode == "按教师":
            courses = execute_query(
                "SELECT * FROM courses WHERE teacher_name LIKE %s ORDER BY course_id",
                (f"%{keyword}%",), fetch=True,
            )
        elif mode == "按类型":
            courses = execute_query(
                "SELECT * FROM courses WHERE course_type = %s ORDER BY course_id",
                (keyword,), fetch=True,
            )
        elif mode == "按学期":
            courses = execute_query(
                "SELECT * FROM courses WHERE semester = %s ORDER BY course_id",
                (keyword,), fetch=True,
            )
        else:  # 按编号
            courses = execute_query(
                "SELECT * FROM courses WHERE course_id = %s", (keyword,), fetch=True
            )
        self._populate_table(courses)

    def _selected_course_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).text()

    def _on_double_click(self):
        self.edit_course()

    def add_course(self):
        dlg = CourseDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            now = current_timestamp()
            cid = generate_next_id("courses", "course_id", "C")
            execute_query(
                "INSERT INTO courses "
                "(course_id, name, course_type, credits, hours, semester, "
                " teacher_name, description, created_at, updated_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (cid, data["name"], data["course_type"], data["credits"],
                 data["hours"], data["semester"], data["teacher_name"],
                 data["description"], now, now),
            )
            QMessageBox.information(self, "成功", f"课程 '{data['name']}' 已添加，编号：{cid}")
            self.refresh()

    def edit_course(self):
        cid = self._selected_course_id()
        if not cid:
            QMessageBox.warning(self, "提示", "请先选择要编辑的课程。")
            return
        course = execute_query(
            "SELECT * FROM courses WHERE course_id = %s", (cid,), fetchone=True
        )
        if not course:
            QMessageBox.warning(self, "错误", "未找到该课程。")
            return
        dlg = CourseDialog(self, course)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            now = current_timestamp()
            execute_query(
                "UPDATE courses SET name=%s, course_type=%s, credits=%s, hours=%s, "
                "semester=%s, teacher_name=%s, description=%s, updated_at=%s "
                "WHERE course_id=%s",
                (data["name"], data["course_type"], data["credits"], data["hours"],
                 data["semester"], data["teacher_name"], data["description"], now, cid),
            )
            QMessageBox.information(self, "成功", "课程信息已更新。")
            self.refresh()

    def delete_course(self):
        cid = self._selected_course_id()
        if not cid:
            QMessageBox.warning(self, "提示", "请先选择要删除的课程。")
            return
        course = execute_query(
            "SELECT * FROM courses WHERE course_id = %s", (cid,), fetchone=True
        )
        if not course:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除课程 {course['name']}（{cid}）吗？\n相关成绩记录将同步删除。",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            execute_query("DELETE FROM courses WHERE course_id = %s", (cid,))
            QMessageBox.information(self, "成功", "课程已删除。")
            self.refresh()

    def batch_import(self):
        reply = QMessageBox.question(
            self, "确认导入",
            "将导入10门示例课程数据（已存在的将跳过），是否继续？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        now = current_timestamp()
        sample_data = [
            ("高等数学",       "必修", 4.0, 64, "2023-2024-1", "张老师", "微积分、线代等基础数学课程"),
            ("大学英语",       "必修", 3.0, 48, "2023-2024-1", "李老师", "大学英语听说读写"),
            ("Python程序设计", "必修", 3.0, 48, "2023-2024-1", "王老师", "Python基础编程"),
            ("数据结构",       "必修", 3.5, 56, "2023-2024-2", "刘老师", "基本数据结构与算法"),
            ("操作系统",       "必修", 3.0, 48, "2023-2024-2", "陈老师", "操作系统原理"),
            ("计算机网络",     "必修", 3.0, 48, "2024-2025-1", "赵老师", "TCP/IP等网络基础"),
            ("数据库原理",     "必修", 3.0, 48, "2024-2025-1", "孙老师", "关系型数据库理论与应用"),
            ("人工智能导论",   "选修", 2.0, 32, "2024-2025-1", "周老师", "AI基本概念与应用"),
            ("软件工程",       "必修", 3.0, 48, "2024-2025-2", "吴老师", "软件开发生命周期管理"),
            ("体育",           "公共基础", 1.0, 32, "2023-2024-1", "郑老师", "体能训练与运动技能"),
        ]
        added = 0
        for name, ctype, credits, hours, semester, teacher, desc in sample_data:
            dup = execute_query(
                "SELECT 1 FROM courses WHERE name = %s", (name,), fetchone=True
            )
            if dup:
                continue
            cid = generate_next_id("courses", "course_id", "C")
            execute_query(
                "INSERT INTO courses "
                "(course_id, name, course_type, credits, hours, semester, "
                " teacher_name, description, created_at, updated_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (cid, name, ctype, credits, hours, semester, teacher, desc, now, now),
            )
            added += 1
        QMessageBox.information(self, "导入完成", f"成功导入 {added} 门课程数据。")
        self.refresh()

    def show_statistics(self):
        courses = execute_query("SELECT * FROM courses", fetch=True)
        if not courses:
            QMessageBox.information(self, "统计", "暂无课程数据。")
            return
        total = len(courses)
        total_credits = sum(c["credits"] for c in courses)
        total_hours = sum(c["hours"] for c in courses)

        type_counter = {}
        for c in courses:
            type_counter[c["course_type"]] = type_counter.get(c["course_type"], 0) + 1
        type_lines = "\n".join(f"  {k}: {v} 门" for k, v in sorted(type_counter.items()))
        msg = (
            f"课程总数：{total}\n"
            f"总学分：{total_credits}\n"
            f"总学时：{total_hours}\n\n"
            f"各类型课程数量：\n{type_lines}"
        )
        QMessageBox.information(self, "课程统计", msg)
