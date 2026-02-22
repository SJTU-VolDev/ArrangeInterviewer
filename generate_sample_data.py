"""
生成示例输入文件，用于验证分配算法。
运行后在 tables/ 目录下生成：
  - 面试官信息.xlsx
  - 志愿者总表.xlsx
"""

import os
import pandas as pd

os.makedirs("tables", exist_ok=True)

# =======================================================
# 1. 面试官信息表
# =======================================================
# 格式：每列 = 一个时间段，列下逐行列出该时间段的面试官
# 3个时间段，各列面试官数量可以不同
interviewer_columns = {
    "周六上午": ["张明", "李华", "杨帆"],
    "周六下午": ["王芳", "李华", "赵强"],
    "周日上午": ["刘洋", "陈静", "赵强", "杨帆"],
}

# 补齐列长度（短的用 None 填充），以便构造 DataFrame
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
# 20名志愿者，可选时间段各不相同（用顿号分隔）
# 列名故意用"你的姓名"/"你的学号"等，验证模糊匹配
volunteer_data = [
    {"你的姓名": "陈一",   "你的学号": "202500001", "你的微信号": "chenyi_wx",     "你可以参加的面试时间": "周六上午、周六下午、周日上午"},
    {"你的姓名": "林二",   "你的学号": "202500002", "你的微信号": "liner_wx",      "你可以参加的面试时间": "周六上午、周六下午"},
    {"你的姓名": "黄三",   "你的学号": "202500003", "你的微信号": "huangsan_wx",   "你可以参加的面试时间": "周六下午、周日上午"},
    {"你的姓名": "周四",   "你的学号": "202500004", "你的微信号": "zhousi_wx",     "你可以参加的面试时间": "周六上午"},
    {"你的姓名": "吴五",   "你的学号": "202500005", "你的微信号": "wuwu_wx",       "你可以参加的面试时间": "周日上午"},
    {"你的姓名": "郑六",   "你的学号": "202500006", "你的微信号": "zhengliu_wx",   "你可以参加的面试时间": "周六上午、周日上午"},
    {"你的姓名": "孙七",   "你的学号": "202500007", "你的微信号": "sunqi_wx",      "你可以参加的面试时间": "周六下午"},
    {"你的姓名": "马八",   "你的学号": "202500008", "你的微信号": "maba_wx",       "你可以参加的面试时间": "周六上午、周六下午、周日上午"},
    {"你的姓名": "胡九",   "你的学号": "202500009", "你的微信号": "hujiu_wx",      "你可以参加的面试时间": "周六上午、周六下午"},
    {"你的姓名": "朱十",   "你的学号": "202500010", "你的微信号": "zhushi_wx",     "你可以参加的面试时间": "周日上午"},
    {"你的姓名": "何十一", "你的学号": "202500011", "你的微信号": "heshiyi_wx",    "你可以参加的面试时间": "周六上午、周日上午"},
    {"你的姓名": "罗十二", "你的学号": "202500012", "你的微信号": "luoshier_wx",   "你可以参加的面试时间": "周六下午、周日上午"},
    {"你的姓名": "梁十三", "你的学号": "202500013", "你的微信号": "liangshisan_wx","你可以参加的面试时间": "周六上午、周六下午"},
    {"你的姓名": "宋十四", "你的学号": "202500014", "你的微信号": "songshisi_wx",  "你可以参加的面试时间": "周六上午"},
    {"你的姓名": "唐十五", "你的学号": "202500015", "你的微信号": "tangshiwu_wx",  "你可以参加的面试时间": "周六下午、周日上午"},
    {"你的姓名": "韩十六", "你的学号": "202500016", "你的微信号": "hanshiliu_wx",  "你可以参加的面试时间": "周六上午、周六下午、周日上午"},
    {"你的姓名": "冯十七", "你的学号": "202500017", "你的微信号": "fengshiqi_wx",  "你可以参加的面试时间": "周日上午"},
    {"你的姓名": "董十八", "你的学号": "202500018", "你的微信号": "dongshiba_wx",  "你可以参加的面试时间": "周六上午、周六下午"},
    {"你的姓名": "程十九", "你的学号": "202500019", "你的微信号": "chengshijiu_wx","你可以参加的面试时间": "周六下午"},
    {"你的姓名": "曹二十", "你的学号": "202500020", "你的微信号": "caoershi_wx",   "你可以参加的面试时间": "周六上午、周日上午"},
]

df_volunteer = pd.DataFrame(volunteer_data)
df_volunteer.to_excel("tables/志愿者总表.xlsx", index=False)
print("✅ 已生成 tables/志愿者总表.xlsx")
print(f"   列名: {list(df_volunteer.columns)}")
print(f"   志愿者数: {len(df_volunteer)}")
print()
print(df_volunteer.to_string(index=False))

# =======================================================
# 统计概览
# =======================================================
print("\n" + "=" * 50)
print("数据概览:")
print("=" * 50)
# 统计各时间段可用志愿者人数
from collections import Counter
slot_counter = Counter()
for v in volunteer_data:
    slots = [s.strip() for s in v["你可以参加的面试时间"].split("、")]
    for s in slots:
        slot_counter[s] += 1

# 统计各时间段面试官人数
interviewer_slots = {}
for slot, names in {"周六上午": ["张明", "李华", "杨帆"], "周六下午": ["王芳", "李华", "赵强"], "周日上午": ["刘洋", "陈静", "赵强", "杨帆"]}.items():
    interviewer_slots[slot] = len(names)

for slot in sorted(slot_counter.keys()):
    print(f"  {slot}: {interviewer_slots.get(slot, 0)} 名面试官, {slot_counter[slot]} 名可选志愿者")
