"""
output_generator.py
输出生成模块

将分配结果写入格式化的Excel排班表和日志文件。
"""

import os
from typing import List

import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from scheduler import Assignment


# 10 种浅色交替背景
_LIGHT_COLORS = [
    "FFE6E6",  # 浅红
    "E6FFE6",  # 浅绿
    "E6E6FF",  # 浅蓝
    "FFFFD9",  # 浅黄
    "FFE6FF",  # 浅紫
    "E6FFFF",  # 浅青
    "FFF0E6",  # 浅橙
    "F2FFE6",  # 浅黄绿
    "E6F2FF",  # 浅天蓝
    "FFE6F2",  # 浅粉
]


class OutputGenerator:
    """将分配结果输出为 Excel 排班表和日志文件"""

    def __init__(
        self,
        assignments: List[Assignment],
        time_slots: List[str],
        key_words: List[str],
        log_messages: List[str],
    ):
        """
        Args:
            assignments: 分配结果列表
            time_slots: 按配置顺序排列的时间段列表
            key_words: 志愿者关键字段名列表（如 ["姓名", "学号", "微信号"]）
            log_messages: 日志消息列表
        """
        self.assignments = assignments
        self.time_slots = time_slots
        self.key_words = key_words
        self.log_messages = log_messages

    # ------------------------------------------------------------------
    # Excel 输出
    # ------------------------------------------------------------------

    def save_schedule(self, output_file: str) -> None:
        """保存排班表到 Excel 文件"""
        out_dir = os.path.dirname(output_file)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        # 构建行数据
        rows = []
        for a in self.assignments:
            row = {"时间段": a.time_slot, "面试官": a.interviewer}
            for kw in self.key_words:
                value = a.volunteer.info.get(kw, "")
                row[kw] = str(value) if value else ""
            rows.append(row)

        df = pd.DataFrame(rows)

        if df.empty:
            # 无分配结果时输出空表
            columns = ["时间段", "面试官"] + self.key_words
            df = pd.DataFrame(columns=columns)

        # 按时间段配置顺序 + 面试官名称排序
        time_order = {slot: i for i, slot in enumerate(self.time_slots)}
        df["_sort"] = df["时间段"].map(time_order).fillna(len(self.time_slots))
        df = df.sort_values(["_sort", "面试官"]).drop("_sort", axis=1)
        df = df.fillna("")

        # 写入 Excel
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="排班表")
            self._format_worksheet(writer, "排班表", df)

    def _format_worksheet(self, writer, sheet_name: str, df: pd.DataFrame) -> None:
        """格式化工作表：边框、颜色、合并单元格"""
        ws = writer.sheets[sheet_name]
        max_row = len(df) + 1  # +1 标题行
        max_col = len(df.columns)

        if max_col == 0:
            return

        # 颜色映射
        color_map = {
            slot: _LIGHT_COLORS[i % len(_LIGHT_COLORS)]
            for i, slot in enumerate(self.time_slots)
        }

        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
        bold_font = Font(bold=True)
        center_align = Alignment(horizontal="center", vertical="center")

        # 标题行格式
        for col_idx in range(1, max_col + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = bold_font
            cell.border = thin_border
            cell.alignment = center_align

        # 学号列文本格式
        student_id_col = None
        for i, col_name in enumerate(df.columns):
            if "学号" in str(col_name):
                student_id_col = i + 1
                break

        # 数据行格式与背景色
        for row_idx in range(2, max_row + 1):
            time_value = ws.cell(row=row_idx, column=1).value
            fill_color = color_map.get(time_value)
            fill = (
                PatternFill(
                    start_color=fill_color, end_color=fill_color, fill_type="solid"
                )
                if fill_color
                else None
            )
            for col_idx in range(1, max_col + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.border = thin_border
                cell.alignment = center_align
                if fill:
                    cell.fill = fill
                # 学号列文本格式
                if student_id_col and col_idx == student_id_col:
                    cell.number_format = "@"

        # 先合并面试官列（第2列，在同一时间段内），再合并时间段列
        # 顺序不可颠倒：合并第1列后其非首行值变为None，会破坏分组判断
        self._merge_same_values_grouped(ws, group_col=1, merge_col=2, start_row=2, end_row=max_row)
        self._merge_same_values(ws, col=1, start_row=2, end_row=max_row)

        # 列宽
        ws.column_dimensions["A"].width = 22  # 时间段
        ws.column_dimensions["B"].width = 12  # 面试官
        col_letters = "CDEFGHIJKLMNOP"
        for i, kw in enumerate(self.key_words):
            if i < len(col_letters):
                ws.column_dimensions[col_letters[i]].width = 15

    @staticmethod
    def _merge_same_values(ws, col: int, start_row: int, end_row: int) -> None:
        """合并同一列中连续相同值的单元格"""
        if start_row > end_row:
            return
        current_val = ws.cell(row=start_row, column=col).value
        merge_start = start_row

        for row in range(start_row + 1, end_row + 1):
            val = ws.cell(row=row, column=col).value
            if val != current_val:
                if merge_start < row - 1:
                    ws.merge_cells(
                        start_row=merge_start, start_column=col,
                        end_row=row - 1, end_column=col,
                    )
                current_val = val
                merge_start = row

        # 最后一组
        if merge_start < end_row:
            ws.merge_cells(
                start_row=merge_start, start_column=col,
                end_row=end_row, end_column=col,
            )

    @staticmethod
    def _merge_same_values_grouped(
        ws, group_col: int, merge_col: int, start_row: int, end_row: int
    ) -> None:
        """在相同分组列值的范围内，合并另一列的连续相同值"""
        if start_row > end_row:
            return

        group_val = ws.cell(row=start_row, column=group_col).value
        merge_val = ws.cell(row=start_row, column=merge_col).value
        merge_start = start_row

        for row in range(start_row + 1, end_row + 1):
            g_val = ws.cell(row=row, column=group_col).value
            m_val = ws.cell(row=row, column=merge_col).value

            # 分组变化或合并列值变化
            if g_val != group_val or m_val != merge_val:
                if merge_start < row - 1:
                    ws.merge_cells(
                        start_row=merge_start, start_column=merge_col,
                        end_row=row - 1, end_column=merge_col,
                    )
                group_val = g_val
                merge_val = m_val
                merge_start = row

        if merge_start < end_row:
            ws.merge_cells(
                start_row=merge_start, start_column=merge_col,
                end_row=end_row, end_column=merge_col,
            )

    # ------------------------------------------------------------------
    # 日志输出
    # ------------------------------------------------------------------

    def save_log(self, log_file: str) -> None:
        """保存日志到文件并打印到控制台"""
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        content = "\n".join(self.log_messages)

        with open(log_file, "w", encoding="utf-8") as f:
            f.write("线上志愿者面试排表 - 执行日志\n")
            f.write("=" * 50 + "\n\n")
            f.write(content)
            f.write("\n\n" + "=" * 50 + "\n")
            f.write("日志生成完成\n")

        print(content)
        print(f"\n日志已保存至: {log_file}")
