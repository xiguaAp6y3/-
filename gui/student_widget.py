# -*- coding: utf-8 -*-
"""
学生管理 – PyQt5 Widget
"""

import re

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDialog,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialogButtonBox, QGroupBox, QSplitter,
    QAbstractItemView,
)

from db import execute_query, generate_next_id
from utils import current_timestamp, validate_phone, validate_id_number

GENDER_OPTIONS = ["男", "女"]


class StudentDialog(QDialog):
    """添加 / 编辑学生对话框"""

    def __init__(self, parent=None, student=None):
        super().__init__(parent)
        self.student = student  # None → 新增，dict → 编辑
        self._setup_ui()
        if student:
            self._fill_data(student)

    def _setup_ui(self):
        title = "编辑学生信息" if self.student else "添加学生"
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(8)

        self.name_edit = QLineEdit()
        form.addRow("姓名*：", self.name_edit)

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(GENDER_OPTIONS)
        form.addRow("性别*：", self.gender_combo)

        self.age_spin = QSpinBox()
        self.age_spin.setRange(1, 100)
        self.age_spin.setValue(18)
        form.addRow("年龄*：", self.age_spin)

        self.class_edit = QLineEdit()
        form.addRow("班级*：", self.class_edit)

        self.major_edit = QLineEdit()
        form.addRow("专业*：", self.major_edit)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("11位手机号")
        form.addRow("手机号*：", self.phone_edit)

        self.id_number_edit = QLineEdit()
        self.id_number_edit.setPlaceholderText("18位身份证号")
        form.addRow("身份证号*：", self.id_number_edit)
        # 编辑时身份证号不可修改
        if self.student:
            self.id_number_edit.setReadOnly(True)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("可选")
        form.addRow("邮箱：", self.email_edit)

        self.enrollment_edit = QLineEdit()
        self.enrollment_edit.setPlaceholderText("如 2023-09-01，可选")
        form.addRow("入学日期：", self.enrollment_edit)

        self.remark_edit = QLineEdit()
        self.remark_edit.setPlaceholderText("可选")
        form.addRow("备注：", self.remark_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("确 定")
        buttons.button(QDialogButtonBox.Cancel).setText("取 消")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _fill_data(self, s):
        self.name_edit.setText(s.get("name", ""))
        idx = self.gender_combo.findText(s.get("gender", "男"))
        if idx >= 0:
            self.gender_combo.setCurrentIndex(idx)
        self.age_spin.setValue(int(s.get("age", 18)))
        self.class_edit.setText(s.get("class_name", ""))
        self.major_edit.setText(s.get("major", ""))
        self.phone_edit.setText(s.get("phone", ""))
        self.id_number_edit.setText(s.get("id_number", ""))
        self.email_edit.setText(s.get("email", ""))
        self.enrollment_edit.setText(s.get("enrollment_date", ""))
        self.remark_edit.setText(s.get("remark", "") or "")

    def _validate_and_accept(self):
        name = self.name_edit.text().strip()
        phone = self.phone_edit.text().strip()
        id_number = self.id_number_edit.text().strip()
        class_name = self.class_edit.text().strip()
        major = self.major_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "提示", "姓名不能为空。")
            return
        if not class_name:
            QMessageBox.warning(self, "提示", "班级不能为空。")
            return
        if not major:
            QMessageBox.warning(self, "提示", "专业不能为空。")
            return
        if not validate_phone(phone):
            QMessageBox.warning(self, "提示", "手机号格式不正确（需为11位数字且以1开头）。")
            return
        if not validate_id_number(id_number):
            QMessageBox.warning(self, "提示", "身份证号格式不正确（需为18位）。")
            return

        # 新增时检查身份证号是否重复
        if not self.student:
            dup = execute_query(
                "SELECT 1 FROM students WHERE id_number = %s", (id_number,), fetchone=True
            )
            if dup:
                QMessageBox.warning(self, "错误", "该身份证号已存在，学生可能已被录入。")
                return

        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "gender": self.gender_combo.currentText(),
            "age": self.age_spin.value(),
            "class_name": self.class_edit.text().strip(),
            "major": self.major_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "id_number": self.id_number_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "enrollment_date": self.enrollment_edit.text().strip(),
            "remark": self.remark_edit.text().strip(),
        }


class StudentWidget(QWidget):
    """学生管理主界面"""

    COLUMNS = ["学号", "姓名", "性别", "年龄", "班级", "专业", "手机号", "入学日期"]
    COL_KEYS = ["student_id", "name", "gender", "age", "class_name", "major", "phone", "enrollment_date"]

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
        self.search_combo.addItems(["全部", "按姓名", "按班级", "按专业", "按学号"])
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
        self.add_btn = QPushButton("➕ 添加学生")
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

        # ── 状态栏 ──
        self.status_label = QLabel("共 0 条记录")
        layout.addWidget(self.status_label)

        # 信号连接
        self.add_btn.clicked.connect(self.add_student)
        self.edit_btn.clicked.connect(self.edit_student)
        self.delete_btn.clicked.connect(self.delete_student)
        self.refresh_btn.clicked.connect(self.refresh)
        self.import_btn.clicked.connect(self.batch_import)
        self.stats_btn.clicked.connect(self.show_statistics)

    def _populate_table(self, students):
        self.table.setRowCount(len(students))
        for row, s in enumerate(students):
            for col, key in enumerate(self.COL_KEYS):
                item = QTableWidgetItem(str(s.get(key, "") or ""))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
        self.status_label.setText(f"共 {len(students)} 条记录")

    def refresh(self):
        self.search_edit.clear()
        self.search_combo.setCurrentIndex(0)
        students = execute_query(
            "SELECT * FROM students ORDER BY student_id", fetch=True
        )
        self._populate_table(students)

    def search(self):
        mode = self.search_combo.currentText()
        keyword = self.search_edit.text().strip()

        if mode == "全部" or not keyword:
            students = execute_query(
                "SELECT * FROM students ORDER BY student_id", fetch=True
            )
        elif mode == "按姓名":
            students = execute_query(
                "SELECT * FROM students WHERE name LIKE %s ORDER BY student_id",
                (f"%{keyword}%",), fetch=True,
            )
        elif mode == "按班级":
            students = execute_query(
                "SELECT * FROM students WHERE class_name LIKE %s ORDER BY student_id",
                (f"%{keyword}%",), fetch=True,
            )
        elif mode == "按专业":
            students = execute_query(
                "SELECT * FROM students WHERE major LIKE %s ORDER BY student_id",
                (f"%{keyword}%",), fetch=True,
            )
        else:  # 按学号
            students = execute_query(
                "SELECT * FROM students WHERE student_id = %s", (keyword,), fetch=True
            )
        self._populate_table(students)

    def _selected_student_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).text()

    def _on_double_click(self):
        self.edit_student()

    def add_student(self):
        dlg = StudentDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            now = current_timestamp()
            sid = generate_next_id("students", "student_id", "S")
            execute_query(
                "INSERT INTO students "
                "(student_id, name, gender, age, class_name, major, phone, "
                " id_number, email, enrollment_date, remark, created_at, updated_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (sid, data["name"], data["gender"], data["age"],
                 data["class_name"], data["major"], data["phone"],
                 data["id_number"], data["email"], data["enrollment_date"],
                 data["remark"], now, now),
            )
            QMessageBox.information(self, "成功", f"学生 '{data['name']}' 已添加，学号：{sid}")
            self.refresh()

    def edit_student(self):
        sid = self._selected_student_id()
        if not sid:
            QMessageBox.warning(self, "提示", "请先选择要编辑的学生。")
            return
        student = execute_query(
            "SELECT * FROM students WHERE student_id = %s", (sid,), fetchone=True
        )
        if not student:
            QMessageBox.warning(self, "错误", "未找到该学生。")
            return
        dlg = StudentDialog(self, student)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            now = current_timestamp()
            execute_query(
                "UPDATE students SET name=%s, gender=%s, age=%s, class_name=%s, "
                "major=%s, phone=%s, email=%s, enrollment_date=%s, remark=%s, updated_at=%s "
                "WHERE student_id=%s",
                (data["name"], data["gender"], data["age"], data["class_name"],
                 data["major"], data["phone"], data["email"],
                 data["enrollment_date"], data["remark"], now, sid),
            )
            QMessageBox.information(self, "成功", "学生信息已更新。")
            self.refresh()

    def delete_student(self):
        sid = self._selected_student_id()
        if not sid:
            QMessageBox.warning(self, "提示", "请先选择要删除的学生。")
            return
        student = execute_query(
            "SELECT * FROM students WHERE student_id = %s", (sid,), fetchone=True
        )
        if not student:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除学生 {student['name']}（{sid}）吗？\n相关成绩记录将同步删除。",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            execute_query("DELETE FROM students WHERE student_id = %s", (sid,))
            QMessageBox.information(self, "成功", "学生已删除。")
            self.refresh()

    def batch_import(self):
        reply = QMessageBox.question(
            self, "确认导入",
            "将导入10条示例学生数据（已存在的将跳过），是否继续？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        now = current_timestamp()
        sample_data = [
            ("张伟", "男", 20, "计科2101", "计算机科学与技术", "13800010001", "110101200300010001"),
            ("李娜", "女", 19, "计科2101", "计算机科学与技术", "13800010002", "110101200400020002"),
            ("王芳", "女", 21, "软工2102", "软件工程",         "13800010003", "110101200200030003"),
            ("刘洋", "男", 20, "软工2102", "软件工程",         "13800010004", "110101200300040004"),
            ("陈静", "女", 22, "网络2103", "网络工程",         "13800010005", "110101200100050005"),
            ("赵磊", "男", 19, "网络2103", "网络工程",         "13800010006", "110101200400060006"),
            ("孙丽", "女", 20, "数据2104", "数据科学与大数据技术", "13800010007", "110101200300070007"),
            ("周杰", "男", 21, "数据2104", "数据科学与大数据技术", "13800010008", "110101200200080008"),
            ("吴敏", "女", 20, "计科2101", "计算机科学与技术", "13800010009", "110101200300090009"),
            ("郑强", "男", 22, "软工2102", "软件工程",         "13800010010", "110101200100100010"),
        ]
        added = 0
        for name, gender, age, cls, major, phone, id_num in sample_data:
            dup = execute_query(
                "SELECT 1 FROM students WHERE id_number = %s", (id_num,), fetchone=True
            )
            if dup:
                continue
            sid = generate_next_id("students", "student_id", "S")
            execute_query(
                "INSERT INTO students "
                "(student_id, name, gender, age, class_name, major, phone, "
                " id_number, email, enrollment_date, remark, created_at, updated_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (sid, name, gender, age, cls, major, phone,
                 id_num, f"{phone}@example.com", "2021-09-01", "", now, now),
            )
            added += 1
        QMessageBox.information(self, "导入完成", f"成功导入 {added} 条学生数据。")
        self.refresh()

    def show_statistics(self):
        students = execute_query("SELECT * FROM students", fetch=True)
        if not students:
            QMessageBox.information(self, "统计", "暂无学生数据。")
            return
        total = len(students)
        male = sum(1 for s in students if s["gender"] == "男")
        female = total - male
        avg_age = sum(s["age"] for s in students) / total

        class_counter = {}
        for s in students:
            class_counter[s["class_name"]] = class_counter.get(s["class_name"], 0) + 1
        major_counter = {}
        for s in students:
            major_counter[s["major"]] = major_counter.get(s["major"], 0) + 1

        class_lines = "\n".join(f"  {k}: {v} 人" for k, v in sorted(class_counter.items()))
        major_lines = "\n".join(f"  {k}: {v} 人" for k, v in sorted(major_counter.items()))
        msg = (
            f"学生总数：{total}\n"
            f"男生人数：{male}\n"
            f"女生人数：{female}\n"
            f"平均年龄：{avg_age:.1f} 岁\n\n"
            f"各班级人数：\n{class_lines}\n\n"
            f"各专业人数：\n{major_lines}"
        )
        QMessageBox.information(self, "学生统计", msg)
