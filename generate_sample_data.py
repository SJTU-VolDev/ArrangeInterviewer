"""
生成示例输入文件，用于验证分配算法。
运行后在 tables/ 目录下生成：
  - 面试官信息.xlsx
  - 志愿者总表.xlsx
"""

import os
import random

import pandas as pd

os.makedirs("tables", exist_ok=True)

# =======================================================
# 1. 面试官信息表
# =======================================================
# 5 个时间段（带具体日期和小时），面试官有交叉
interviewer_columns = {
    "3月1日 14:00-17:00": ["张明", "李华", "杨帆", "王芳"],
    "3月1日 19:00-22:00": ["赵强"],
    "3月2日 09:00-12:00": ["陈静", "杨帆"],
    "3月2日 14:00-17:00": ["张明", "刘洋", "陈静"],
    "3月2日 19:00-21:30": ["王芳", "马飞", "李华", "周磊"],
}

# 补齐列长度
max_len = max(len(v) for v in interviewer_columns.values())
for key in interviewer_columns:
    interviewer_columns[key] += [None] * (max_len - len(interviewer_columns[key]))

df_interviewer = pd.DataFrame(interviewer_columns)
df_interviewer.to_excel("tables/面试官信息.xlsx", index=False)
print("✅ 已生成 tables/面试官信息.xlsx")
print(f"   列名(时间段): {list(df_interviewer.columns)}")
print()
print(df_interviewer.to_string(index=False))
print()

# =======================================================
# 2. 志愿者总表
# =======================================================
# 60 名志愿者，可选时间段随机生成（1~4 个），覆盖各种组合

time_slot_list = list(interviewer_columns.keys())

# 百家姓 + 数字编号
surnames = [
    "陈", "林", "黄", "周", "吴", "郑", "孙", "马", "胡", "朱",
    "何", "罗", "梁", "宋", "唐", "韩", "冯", "董", "程", "曹",
    "袁", "邓", "许", "傅", "沈", "曾", "彭", "吕", "苏", "卢",
    "蒋", "蔡", "贾", "丁", "魏", "薛", "叶", "阎", "余", "潘",
    "杜", "戴", "夏", "钟", "汪", "田", "任", "姜", "范", "方",
    "石", "姚", "谭", "廖", "邹", "熊", "金", "陆", "郝", "孔",
]

random.seed(42)  # 可复现

volunteer_data = []
for i in range(240):
    name = surnames[i % len(surnames)] + f"同学{i + 1:02d}"
    student_id = f"20250{i + 1:04d}"
    wechat = f"vol{i + 1:02d}_wx"

    # 随机选 1~4 个时间段
    n_slots = random.randint(1, min(4, len(time_slot_list)))
    chosen_slots = random.sample(time_slot_list, n_slots)
    time_str = "、".join(chosen_slots)

    volunteer_data.append({
        "你的姓名": name,
        "你的学号": student_id,
        "你的微信号": wechat,
        "你可以参加的面试时间": time_str,
    })

df_volunteer = pd.DataFrame(volunteer_data)
df_volunteer.to_excel("tables/志愿者总表.xlsx", index=False)
print("✅ 已生成 tables/志愿者总表.xlsx")
print(f"   列名: {list(df_volunteer.columns)}")
print(f"   志愿者数: {len(df_volunteer)}")
print()
# 只打印前 10 行
print(df_volunteer.head(10).to_string(index=False))
print(f"   ... 共 {len(df_volunteer)} 行")

# =======================================================
# 统计概览
# =======================================================
print("\n" + "=" * 50)
print("数据概览:")
print("=" * 50)

from collections import Counter

slot_counter = Counter()
for v in volunteer_data:
    slots = [s.strip() for s in v["你可以参加的面试时间"].split("、")]
    for s in slots:
        slot_counter[s] += 1

for slot in time_slot_list:
    n_interviewers = len([x for x in interviewer_columns[slot] if x is not None])
    print(f"  {slot}: {n_interviewers} 名面试官, {slot_counter[slot]} 名可选志愿者")
