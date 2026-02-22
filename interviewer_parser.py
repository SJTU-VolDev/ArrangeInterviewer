"""
interviewer_parser.py
面试官信息解析模块

读取面试官信息Excel，提取时间段和面试官分组。

表格格式:
  - 第一行（表头）= 各时间段名称，每列代表一个时间段
  - 每列下方逐行列出该时间段的面试官姓名
  - 不同列长度可以不同（空单元格自动忽略）

示例:
  | 周六上午 | 周六下午 | 周日上午 |
  | 张明     | 王芳     | 刘洋     |
  | 李华     | 赵强     | 陈静     |
  | 杨帆     |          | 杨帆     |

输出数据结构：{ 时间段 → [面试官姓名列表] }
"""

import pandas as pd
from typing import Dict, List


class InterviewerParser:
    """解析面试官信息表，提取时间段与面试官的映射关系"""

    def __init__(self, file_path: str):
        """
        Args:
            file_path: 面试官信息Excel文件路径
        """
        self.file_path = file_path

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def parse(self) -> Dict[str, List[str]]:
        """解析面试官信息表。

        表头的每一列即为一个时间段名称，列下的非空行为该时间段的面试官。

        Returns:
            字典 { 时间段 → [面试官姓名, ...] }，按列从左到右保持顺序。
        """
        df = pd.read_excel(self.file_path, dtype=str)

        slot_interviewers: Dict[str, List[str]] = {}

        for col in df.columns:
            slot_name = str(col).strip()
            if not slot_name or slot_name.startswith("Unnamed"):
                continue

            interviewers: List[str] = []
            for value in df[col]:
                name = str(value).strip() if pd.notna(value) else ""
                if name and name != "nan":
                    if name not in interviewers:
                        interviewers.append(name)

            if interviewers:
                slot_interviewers[slot_name] = interviewers

        return slot_interviewers
