"""
volunteer_parser.py
志愿者信息解析模块

读取志愿者总表Excel，提取每位志愿者的基本信息和可选时间段。
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple


class Volunteer:
    """表示一名志愿者"""

    def __init__(self, info: Dict[str, str], available_slots: List[str]):
        """
        Args:
            info: 关键字段字典，如 {"姓名": "王五", "学号": "202500001", "微信号": "wx123"}
            available_slots: 该志愿者可选的时间段列表
        """
        self.info = info
        self.available_slots = available_slots

    @property
    def name(self) -> str:
        """返回姓名（取 info 中第一个值）"""
        return next(iter(self.info.values()), "未知")

    @property
    def key(self) -> tuple:
        """返回用于唯一标识的元组"""
        return tuple(self.info.values())

    def __repr__(self) -> str:
        return f"Volunteer({self.info}, slots={self.available_slots})"


class VolunteerParser:
    """解析志愿者总表，提取志愿者信息和可选时间段"""

    def __init__(
        self,
        file_path: str,
        key_words: Optional[List[str]] = None,
        time_column_keyword: str = "面试时间",
    ):
        """
        Args:
            file_path: 志愿者总表Excel文件路径
            key_words: 关键字段列表，用于模糊匹配列名；默认 ["姓名", "学号", "微信号"]
            time_column_keyword: 可选时间列的模糊匹配关键字
        """
        self.file_path = file_path
        self.key_words = key_words or ["姓名", "学号", "微信号"]
        self.time_column_keyword = time_column_keyword

    # ------------------------------------------------------------------
    # 内部工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _fuzzy_find_column(columns: pd.Index, keyword: str) -> Optional[str]:
        """模糊匹配列名（子串包含即匹配）"""
        for col in columns:
            if keyword in str(col):
                return col
        return None

    @staticmethod
    def _split_time_slots(time_str: str) -> List[str]:
        """将顿号分隔的时间段字符串拆分为列表"""
        if pd.isna(time_str):
            return []
        return [t.strip() for t in str(time_str).split("、") if t.strip()]

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def parse(self) -> List[Volunteer]:
        """解析志愿者总表。

        Returns:
            Volunteer 对象列表
        """
        df = pd.read_excel(self.file_path, dtype=str)

        # 模糊匹配关键字段列
        keyword_col_map: List[Tuple[str, str]] = []  # [(keyword, actual_col_name)]
        for kw in self.key_words:
            col = self._fuzzy_find_column(df.columns, kw)
            if col is None:
                raise ValueError(
                    f"志愿者总表中未找到包含 [{kw}] 的列。"
                    f"当前列名: {list(df.columns)}"
                )
            keyword_col_map.append((kw, col))

        # 模糊匹配时间列
        time_col = self._fuzzy_find_column(df.columns, self.time_column_keyword)
        if time_col is None:
            raise ValueError(
                f"志愿者总表中未找到包含 [{self.time_column_keyword}] 的列。"
                f"当前列名: {list(df.columns)}"
            )

        # 构建志愿者列表
        volunteers: List[Volunteer] = []
        for _, row in df.iterrows():
            # 提取关键字段信息
            info = {}
            skip = False
            for kw, col in keyword_col_map:
                value = row[col]
                if pd.isna(value) or str(value).strip() == "" or str(value).strip() == "nan":
                    # 第一个关键字段（姓名）为空则跳过该行
                    if kw == self.key_words[0]:
                        skip = True
                        break
                    info[kw] = ""
                else:
                    info[kw] = str(value).strip()

            if skip:
                continue

            # 提取可选时间段
            available_slots = self._split_time_slots(row[time_col])

            volunteers.append(Volunteer(info=info, available_slots=available_slots))

        return volunteers
