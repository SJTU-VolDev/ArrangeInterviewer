import pandas as pd
from collections import Counter, defaultdict

# 1. 读取 raw.xlsx 文件
df = pd.read_excel('tables/raw.xlsx')

# 获取四个部门的名单并去除空值
dept_lists = {
    '人资': df['人资'].dropna().tolist(),
    '外联': df['外联'].dropna().tolist(),
    '策划': df['策划'].dropna().tolist(),
    '宣传': df['宣传'].dropna().tolist()
}

# 2. 统计所有人员并找出双部门人员
all_candidates = sum(dept_lists.values(), [])  # 合并所有部门的名单
candidate_count = Counter(all_candidates)      # 统计每个人出现的次数
double_candidates = [candidate for candidate, count in candidate_count.items() if count == 2]  # 筛选出现两次的人员

# 3. 为每个双部门人员记录面试部门
double_dept_info = {}
for candidate in double_candidates:
    depts = [dept for dept, candidates in dept_lists.items() if candidate in candidates]
    double_dept_info[candidate] = depts

# 4. 统计每种部门组合的人数及其人员名单
combo_counter = defaultdict(list)  # 使用 list 存储人员名单
for candidate, depts in double_dept_info.items():
    # 对部门名称进行排序，确保组合顺序一致
    sorted_depts = tuple(sorted(depts))
    combo_counter[sorted_depts].append(candidate)

# 5. 将结果写入 double_interview.txt 文件
with open('output/double_interview.txt', 'w', encoding='utf-8') as f:
    # 写入双部门人员信息
    f.write("需要面试两个部门的人员名单：\n")
    for candidate, depts in double_dept_info.items():
        f.write(f"{candidate} - {', '.join(depts)}\n")
    
    # 添加空行分隔
    f.write("\n")
    
    # 写入每种部门组合的人数及人员名单
    f.write("每种部门组合的人数及人员名单：\n")
    for combo, candidates in combo_counter.items():
        f.write(f"{combo[0]} - {combo[1]}: {len(candidates)} 人 - {', '.join(candidates)}\n")

print("双部门面试人员信息及部门组合详情已保存到 'double_interview.txt'")