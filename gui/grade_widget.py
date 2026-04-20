# -*- coding: utf-8 -*-
"""
成绩管理 – PyQt5 Widget
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QDoubleSpinBox, QDialog,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialogButtonBox, QGroupBox, QAbstractItemView,
)

from db import execute_query, generate_next_id
from utils import current_timestamp


def _get_grade_level(score: float) -> str:
    if score >= 90:
        return "优秀"
    elif score >= 80:
        return "良好"
    elif score >= 70:
        return "中等"
    elif score >= 60:
        return "及格"
    return "不及格"


class GradeDialog(QDialog):
    """录入 / 编辑成绩对话框"""

    def __init__(self, parent=None, grade=None):
        super().__init__(parent)
        self.grade = grade
        self._setup_ui()
        if grade:
            self._fill_data(grade)

    def _setup_ui(self):
        self.setWindowTitle("编辑成绩" if self.grade else "录入成绩")
        self.setMinimumWidth(380)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(8)

        self.student_edit = QLineEdit()
        self.student_edit.setPlaceholderText("请输入学号")
        form.addRow("学号*：", self.student_edit)

        self.course_edit = QLineEdit()
        self.course_edit.setPlaceholderText("请输入课程编号")
        form.addRow("课程编号*：", self.course_edit)

        self.score_spin = QDoubleSpinBox()
        self.score_spin.setRange(0.0, 100.0)
        self.score_spin.setSingleStep(1.0)
        self.score_spin.setDecimals(1)
        self.score_spin.setValue(60.0)
        form.addRow("成绩*：", self.score_spin)

        self.remark_edit = QLineEdit()
        self.remark_edit.setPlaceholderText("可选")
        form.addRow("备注：", self.remark_edit)

        # 编辑时学号和课程编号只读
        if self.grade:
            self.student_edit.setReadOnly(True)
            self.course_edit.setReadOnly(True)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("确 定")
        buttons.button(QDialogButtonBox.Cancel).setText("取 消")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _fill_data(self, g):
        self.student_edit.setText(g.get("student_id", ""))
        self.course_edit.setText(g.get("course_id", ""))
        self.score_spin.setValue(float(g.get("score", 60.0)))
        self.remark_edit.setText(g.get("remark", "") or "")

    def _validate_and_accept(self):
        student_id = self.student_edit.text().strip()
        course_id = self.course_edit.text().strip()

        if not student_id:
            QMessageBox.warning(self, "提示", "学号不能为空。")
            return
        if not course_id:
            QMessageBox.warning(self, "提示", "课程编号不能为空。")
            return

        student = execute_query(
            "SELECT * FROM students WHERE student_id = %s", (student_id,), fetchone=True
        )
        if not student:
            QMessageBox.warning(self, "错误", f"学号 {student_id} 不存在。")
            return

        course = execute_query(
            "SELECT * FROM courses WHERE course_id = %s", (course_id,), fetchone=True
        )
        if not course:
            QMessageBox.warning(self, "错误", f"课程编号 {course_id} 不存在。")
            return

        # 新增时检查重复
        if not self.grade:
            semester = course["semester"]
            dup = execute_query(
                "SELECT * FROM grades WHERE student_id=%s AND course_id=%s AND semester=%s",
                (student_id, course_id, semester),
                fetchone=True,
            )
            if dup:
                QMessageBox.warning(
                    self, "错误",
                    f"该学生本学期已有 '{course['name']}' 的成绩（{dup['score']}），请使用编辑功能。"
                )
                return

        self._student_obj = student
        self._course_obj = course
        self.accept()

    def get_data(self) -> dict:
        return {
            "student_id": self.student_edit.text().strip(),
            "course_id": self.course_edit.text().strip(),
            "score": self.score_spin.value(),
            "remark": self.remark_edit.text().strip(),
            "semester": getattr(self, "_course_obj", {}).get("semester", ""),
        }


class GradeWidget(QWidget):
    """成绩管理主界面"""

    COLUMNS = ["成绩ID", "学号", "学生姓名", "课程编号", "课程名称", "成绩", "等级", "学期"]
    COL_KEYS = ["grade_id", "student_id", "student_name", "course_id",
                "course_name", "score", "level", "semester"]

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
        self.search_combo.addItems(["全部", "按学号", "按课程编号", "按学期", "按等级"])
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
        self.add_btn = QPushButton("➕ 录入成绩")
        self.edit_btn = QPushButton("✏️ 编辑")
        self.delete_btn = QPushButton("🗑 删除")
        self.refresh_btn = QPushButton("🔄 刷新")
        self.stats_btn = QPushButton("📊 统计")

        for btn in [self.add_btn, self.edit_btn, self.delete_btn,
                    self.refresh_btn, self.stats_btn]:
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

        self.add_btn.clicked.connect(self.add_grade)
        self.edit_btn.clicked.connect(self.edit_grade)
        self.delete_btn.clicked.connect(self.delete_grade)
        self.refresh_btn.clicked.connect(self.refresh)
        self.stats_btn.clicked.connect(self.show_statistics)

    def _populate_table(self, grades):
        self.table.setRowCount(len(grades))
        for row, g in enumerate(grades):
            g_with_level = dict(g)
            g_with_level["level"] = _get_grade_level(float(g.get("score", 0)))
            for col, key in enumerate(self.COL_KEYS):
                val = g_with_level.get(key, "") or ""
                if key == "score":
                    val = f"{float(val):.1f}"
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
        self.status_label.setText(f"共 {len(grades)} 条记录")

    def _fetch_grades(self, where="", params=()):
        base_sql = (
            "SELECT g.*, s.name AS student_name, c.name AS course_name "
            "FROM grades g "
            "JOIN students s ON g.student_id = s.student_id "
            "JOIN courses  c ON g.course_id  = c.course_id "
        )
        sql = base_sql + where + " ORDER BY g.grade_id"
        return execute_query(sql, params, fetch=True)

    def refresh(self):
        self.search_edit.clear()
        self.search_combo.setCurrentIndex(0)
        grades = self._fetch_grades()
        self._populate_table(grades)

    def search(self):
        mode = self.search_combo.currentText()
        keyword = self.search_edit.text().strip()

        if mode == "全部" or not keyword:
            grades = self._fetch_grades()
        elif mode == "按学号":
            grades = self._fetch_grades("WHERE g.student_id = %s", (keyword,))
        elif mode == "按课程编号":
            grades = self._fetch_grades("WHERE g.course_id = %s", (keyword,))
        elif mode == "按学期":
            grades = self._fetch_grades("WHERE g.semester = %s", (keyword,))
        else:  # 按等级
            LEVELS = {
                "优秀": (90, 100), "良好": (80, 89.9),
                "中等": (70, 79.9), "及格": (60, 69.9), "不及格": (0, 59.9),
            }
            if keyword not in LEVELS:
                QMessageBox.warning(self, "提示", f"请输入有效等级：{'/'.join(LEVELS)}")
                return
            lo, hi = LEVELS[keyword]
            grades = self._fetch_grades(
                "WHERE g.score >= %s AND g.score <= %s", (lo, hi)
            )
        self._populate_table(grades)

    def _selected_grade_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).text()

    def _on_double_click(self):
        self.edit_grade()

    def add_grade(self):
        # Check prereqs
        if not execute_query("SELECT COUNT(*) AS cnt FROM students", fetchone=True)["cnt"]:
            QMessageBox.warning(self, "提示", "暂无学生数据，请先添加学生。")
            return
        if not execute_query("SELECT COUNT(*) AS cnt FROM courses", fetchone=True)["cnt"]:
            QMessageBox.warning(self, "提示", "暂无课程数据，请先添加课程。")
            return

        dlg = GradeDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            now = current_timestamp()
            gid = generate_next_id("grades", "grade_id", "G")
            execute_query(
                "INSERT INTO grades "
                "(grade_id, student_id, course_id, score, semester, remark, created_at, updated_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (gid, data["student_id"], data["course_id"], data["score"],
                 data["semester"], data["remark"], now, now),
            )
            level = _get_grade_level(data["score"])
            QMessageBox.information(
                self, "成功",
                f"成绩已录入：{data['score']}（{level}）"
            )
            self.refresh()

    def edit_grade(self):
        gid = self._selected_grade_id()
        if not gid:
            QMessageBox.warning(self, "提示", "请先选择要编辑的成绩记录。")
            return
        grade = execute_query(
            "SELECT * FROM grades WHERE grade_id = %s", (gid,), fetchone=True
        )
        if not grade:
            return
        dlg = GradeDialog(self, grade)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            now = current_timestamp()
            execute_query(
                "UPDATE grades SET score=%s, remark=%s, updated_at=%s WHERE grade_id=%s",
                (data["score"], data["remark"], now, gid),
            )
            QMessageBox.information(self, "成功", "成绩已更新。")
            self.refresh()

    def delete_grade(self):
        gid = self._selected_grade_id()
        if not gid:
            QMessageBox.warning(self, "提示", "请先选择要删除的成绩记录。")
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除成绩记录 {gid} 吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            execute_query("DELETE FROM grades WHERE grade_id = %s", (gid,))
            QMessageBox.information(self, "成功", "成绩记录已删除。")
            self.refresh()

    def show_statistics(self):
        grades = execute_query("SELECT * FROM grades", fetch=True)
        if not grades:
            QMessageBox.information(self, "统计", "暂无成绩数据。")
            return
        total = len(grades)
        scores = [float(g["score"]) for g in grades]
        avg = sum(scores) / total
        max_score = max(scores)
        min_score = min(scores)

        level_counter = {}
        for g in grades:
            lv = _get_grade_level(float(g["score"]))
            level_counter[lv] = level_counter.get(lv, 0) + 1

        pass_count = sum(1 for s in scores if s >= 60)
        fail_count = total - pass_count
        level_lines = "\n".join(
            f"  {k}: {v} 条"
            for k in ["优秀", "良好", "中等", "及格", "不及格"]
            if k in level_counter
            for v in [level_counter[k]]
        )
        msg = (
            f"成绩记录总数：{total}\n"
            f"平均分：{avg:.1f}\n"
            f"最高分：{max_score:.1f}\n"
            f"最低分：{min_score:.1f}\n"
            f"及格人数：{pass_count}\n"
            f"不及格人数：{fail_count}\n\n"
            f"各等级分布：\n{level_lines}"
        )
        QMessageBox.information(self, "成绩统计", msg)
