# -*- coding: utf-8 -*-
"""
教师管理 – PyQt5 Widget
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDialog,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialogButtonBox, QGroupBox, QAbstractItemView,
    QTextEdit,
)

from db import execute_query, generate_next_id
from utils import current_timestamp, validate_phone, validate_email

GENDER_OPTIONS = ["男", "女"]
TITLE_OPTIONS = ["助教", "讲师", "副教授", "教授"]


class TeacherDialog(QDialog):
    """添加 / 编辑教师对话框"""

    def __init__(self, parent=None, teacher=None):
        super().__init__(parent)
        self.teacher = teacher
        self._setup_ui()
        if teacher:
            self._fill_data(teacher)

    def _setup_ui(self):
        self.setWindowTitle("编辑教师信息" if self.teacher else "添加教师")
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
        self.age_spin.setRange(22, 80)
        self.age_spin.setValue(35)
        form.addRow("年龄*：", self.age_spin)

        self.title_combo = QComboBox()
        self.title_combo.addItems(TITLE_OPTIONS)
        form.addRow("职称*：", self.title_combo)

        self.dept_edit = QLineEdit()
        form.addRow("所属院系*：", self.dept_edit)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("11位手机号")
        form.addRow("手机号*：", self.phone_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("可选")
        form.addRow("邮箱：", self.email_edit)

        self.research_edit = QLineEdit()
        self.research_edit.setPlaceholderText("可选")
        form.addRow("研究方向：", self.research_edit)

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

    def _fill_data(self, t):
        self.name_edit.setText(t.get("name", ""))
        idx = self.gender_combo.findText(t.get("gender", "男"))
        if idx >= 0:
            self.gender_combo.setCurrentIndex(idx)
        self.age_spin.setValue(int(t.get("age", 35)))
        idx = self.title_combo.findText(t.get("title", "讲师"))
        if idx >= 0:
            self.title_combo.setCurrentIndex(idx)
        self.dept_edit.setText(t.get("department", ""))
        self.phone_edit.setText(t.get("phone", ""))
        self.email_edit.setText(t.get("email", "") or "")
        self.research_edit.setText(t.get("research", "") or "")
        self.remark_edit.setText(t.get("remark", "") or "")

    def _validate_and_accept(self):
        name = self.name_edit.text().strip()
        dept = self.dept_edit.text().strip()
        phone = self.phone_edit.text().strip()
        email = self.email_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "提示", "姓名不能为空。")
            return
        if not dept:
            QMessageBox.warning(self, "提示", "所属院系不能为空。")
            return
        if not validate_phone(phone):
            QMessageBox.warning(self, "提示", "手机号格式不正确（需为11位数字且以1开头）。")
            return
        if email and not validate_email(email):
            QMessageBox.warning(self, "提示", "邮箱格式不正确。")
            return

        # 新增时检查手机号重复
        if not self.teacher:
            dup = execute_query(
                "SELECT 1 FROM teachers WHERE phone = %s", (phone,), fetchone=True
            )
            if dup:
                QMessageBox.warning(self, "错误", "该手机号已存在，教师可能已被录入。")
                return

        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "gender": self.gender_combo.currentText(),
            "age": self.age_spin.value(),
            "title": self.title_combo.currentText(),
            "department": self.dept_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "research": self.research_edit.text().strip(),
            "remark": self.remark_edit.text().strip(),
        }


class TeacherWidget(QWidget):
    """教师管理主界面"""

    COLUMNS = ["教师编号", "姓名", "性别", "年龄", "职称", "所属院系", "手机号"]
    COL_KEYS = ["teacher_id", "name", "gender", "age", "title", "department", "phone"]

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
        self.search_combo.addItems(["全部", "按姓名", "按院系", "按职称", "按编号"])
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
        self.add_btn = QPushButton("➕ 添加教师")
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

        self.add_btn.clicked.connect(self.add_teacher)
        self.edit_btn.clicked.connect(self.edit_teacher)
        self.delete_btn.clicked.connect(self.delete_teacher)
        self.refresh_btn.clicked.connect(self.refresh)
        self.import_btn.clicked.connect(self.batch_import)
        self.stats_btn.clicked.connect(self.show_statistics)

    def _populate_table(self, teachers):
        self.table.setRowCount(len(teachers))
        for row, t in enumerate(teachers):
            for col, key in enumerate(self.COL_KEYS):
                item = QTableWidgetItem(str(t.get(key, "") or ""))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
        self.status_label.setText(f"共 {len(teachers)} 条记录")

    def refresh(self):
        self.search_edit.clear()
        self.search_combo.setCurrentIndex(0)
        teachers = execute_query("SELECT * FROM teachers ORDER BY teacher_id", fetch=True)
        self._populate_table(teachers)

    def search(self):
        mode = self.search_combo.currentText()
        keyword = self.search_edit.text().strip()

        if mode == "全部" or not keyword:
            teachers = execute_query("SELECT * FROM teachers ORDER BY teacher_id", fetch=True)
        elif mode == "按姓名":
            teachers = execute_query(
                "SELECT * FROM teachers WHERE name LIKE %s ORDER BY teacher_id",
                (f"%{keyword}%",), fetch=True,
            )
        elif mode == "按院系":
            teachers = execute_query(
                "SELECT * FROM teachers WHERE department LIKE %s ORDER BY teacher_id",
                (f"%{keyword}%",), fetch=True,
            )
        elif mode == "按职称":
            teachers = execute_query(
                "SELECT * FROM teachers WHERE title = %s ORDER BY teacher_id",
                (keyword,), fetch=True,
            )
        else:  # 按编号
            teachers = execute_query(
                "SELECT * FROM teachers WHERE teacher_id = %s", (keyword,), fetch=True
            )
        self._populate_table(teachers)

    def _selected_teacher_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).text()

    def _on_double_click(self):
        self.edit_teacher()

    def add_teacher(self):
        dlg = TeacherDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            now = current_timestamp()
            tid = generate_next_id("teachers", "teacher_id", "T")
            execute_query(
                "INSERT INTO teachers "
                "(teacher_id, name, gender, age, title, department, phone, "
                " email, research, remark, created_at, updated_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (tid, data["name"], data["gender"], data["age"], data["title"],
                 data["department"], data["phone"], data["email"],
                 data["research"], data["remark"], now, now),
            )
            QMessageBox.information(self, "成功", f"教师 '{data['name']}' 已添加，编号：{tid}")
            self.refresh()

    def edit_teacher(self):
        tid = self._selected_teacher_id()
        if not tid:
            QMessageBox.warning(self, "提示", "请先选择要编辑的教师。")
            return
        teacher = execute_query(
            "SELECT * FROM teachers WHERE teacher_id = %s", (tid,), fetchone=True
        )
        if not teacher:
            QMessageBox.warning(self, "错误", "未找到该教师。")
            return
        dlg = TeacherDialog(self, teacher)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            now = current_timestamp()
            execute_query(
                "UPDATE teachers SET name=%s, gender=%s, age=%s, title=%s, "
                "department=%s, phone=%s, email=%s, research=%s, remark=%s, updated_at=%s "
                "WHERE teacher_id=%s",
                (data["name"], data["gender"], data["age"], data["title"],
                 data["department"], data["phone"], data["email"],
                 data["research"], data["remark"], now, tid),
            )
            QMessageBox.information(self, "成功", "教师信息已更新。")
            self.refresh()

    def delete_teacher(self):
        tid = self._selected_teacher_id()
        if not tid:
            QMessageBox.warning(self, "提示", "请先选择要删除的教师。")
            return
        teacher = execute_query(
            "SELECT * FROM teachers WHERE teacher_id = %s", (tid,), fetchone=True
        )
        if not teacher:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除教师 {teacher['name']}（{tid}）吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            execute_query("DELETE FROM teachers WHERE teacher_id = %s", (tid,))
            QMessageBox.information(self, "成功", "教师已删除。")
            self.refresh()

    def batch_import(self):
        reply = QMessageBox.question(
            self, "确认导入",
            "将导入10位示例教师数据（已存在的将跳过），是否继续？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        now = current_timestamp()
        sample_data = [
            ("张老师", "男", 45, "教授",   "计算机学院",   "13900010001", "zhangls@university.edu.cn", "机器学习"),
            ("李老师", "女", 38, "副教授", "外语学院",     "13900010002", "lils@university.edu.cn",    "语言学"),
            ("王老师", "男", 32, "讲师",   "计算机学院",   "13900010003", "wangls@university.edu.cn",  "Python开发"),
            ("刘老师", "男", 40, "副教授", "计算机学院",   "13900010004", "liuls@university.edu.cn",   "算法"),
            ("陈老师", "女", 50, "教授",   "计算机学院",   "13900010005", "chenls@university.edu.cn",  "操作系统"),
            ("赵老师", "男", 35, "讲师",   "通信学院",     "13900010006", "zhaols@university.edu.cn",  "网络协议"),
            ("孙老师", "女", 42, "副教授", "计算机学院",   "13900010007", "sunls@university.edu.cn",   "数据库"),
            ("周老师", "男", 48, "教授",   "人工智能学院", "13900010008", "zhouls@university.edu.cn",  "深度学习"),
            ("吴老师", "女", 37, "讲师",   "软件学院",     "13900010009", "wuls@university.edu.cn",    "软件架构"),
            ("郑老师", "男", 30, "助教",   "体育学院",     "13900010010", "zhengls@university.edu.cn", "运动训练"),
        ]
        added = 0
        for name, gender, age, title, dept, phone, email, research in sample_data:
            dup = execute_query(
                "SELECT 1 FROM teachers WHERE phone = %s", (phone,), fetchone=True
            )
            if dup:
                continue
            tid = generate_next_id("teachers", "teacher_id", "T")
            execute_query(
                "INSERT INTO teachers "
                "(teacher_id, name, gender, age, title, department, phone, "
                " email, research, remark, created_at, updated_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (tid, name, gender, age, title, dept, phone, email, research, "", now, now),
            )
            added += 1
        QMessageBox.information(self, "导入完成", f"成功导入 {added} 位教师数据。")
        self.refresh()

    def show_statistics(self):
        teachers = execute_query("SELECT * FROM teachers", fetch=True)
        if not teachers:
            QMessageBox.information(self, "统计", "暂无教师数据。")
            return
        total = len(teachers)
        male = sum(1 for t in teachers if t["gender"] == "男")
        female = total - male
        avg_age = sum(t["age"] for t in teachers) / total

        title_counter = {}
        for t in teachers:
            title_counter[t["title"]] = title_counter.get(t["title"], 0) + 1
        dept_counter = {}
        for t in teachers:
            dept_counter[t["department"]] = dept_counter.get(t["department"], 0) + 1

        title_lines = "\n".join(f"  {k}: {v} 人" for k, v in sorted(title_counter.items()))
        dept_lines = "\n".join(f"  {k}: {v} 人" for k, v in sorted(dept_counter.items()))
        msg = (
            f"教师总数：{total}\n"
            f"男教师：{male}\n"
            f"女教师：{female}\n"
            f"平均年龄：{avg_age:.1f} 岁\n\n"
            f"各职称人数：\n{title_lines}\n\n"
            f"各院系人数：\n{dept_lines}"
        )
        QMessageBox.information(self, "教师统计", msg)
