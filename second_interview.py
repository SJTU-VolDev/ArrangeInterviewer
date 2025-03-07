import pandas as pd
import xlsxwriter
import json
from collections import defaultdict, Counter

# 读取配置文件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    second_interview_config = config['second_interview_config']

# 1. 读取输入文件并初始化部门名单
df = pd.read_excel(second_interview_config['input_file'])
dept_lists = {
    '人资': df['人资'].dropna().tolist(),
    '外联': df['外联'].dropna().tolist(),
    '策划': df['策划'].dropna().tolist(),
    '宣传': df['宣传'].dropna().tolist()
}

# 2. 计算每个部门在四个时间段的预留人数
def split_into_four(total):
    """将总数尽量平均分成四份"""
    base = total // 4
    remainder = total % 4
    return [base + 1 if i < remainder else base for i in range(4)]

# 为每个部门计算预留人数
dept_targets = {dept: split_into_four(len(candidates)) for dept, candidates in dept_lists.items()}

# 3. 初始化时间段和部门的空数组
times = second_interview_config['times']
assignments = {}
for i, time in enumerate(times):
    assignments[time] = {dept: [''] * dept_targets[dept][i] for dept in dept_lists}

# 4. 识别双部门人员并分组
all_candidates = sum(dept_lists.values(), [])
candidate_count = Counter(all_candidates)
double_candidates = [candidate for candidate, count in candidate_count.items() if count == 2]

# 为双部门人员记录部门组合
double_dept_info = {}
for candidate in double_candidates:
    depts = [dept for dept, candidates in dept_lists.items() if candidate in candidates]
    double_dept_info[candidate] = sorted(depts)  # 排序确保组合唯一

# 输出双部门面试人员信息到文件
with open('output/double_interviewee.txt', 'w', encoding='utf-8') as f:
    # 写入双部门人员信息
    f.write("需要面试两个部门的人员名单：\n")
    for candidate, depts in double_dept_info.items():
        f.write(f"{candidate} - {', '.join(depts)}\n")
    
    # 添加空行分隔
    f.write("\n")
    
    # 写入每种部门组合的人数及人员名单
    f.write("每种部门组合的人员名单：\n")
    combo_counter = defaultdict(list)
    for candidate, depts in double_dept_info.items():
        sorted_depts = tuple(depts)  # depts已经排序过了
        combo_counter[sorted_depts].append(candidate)
    
    for combo, candidates in combo_counter.items():
        f.write(f"{combo[0]} - {combo[1]}: {len(candidates)} 人 - {', '.join(candidates)}\n")

print("双部门面试人员信息已保存到 'output/double_interviewee.txt'")

# 按部门组合分组
combo_candidates = defaultdict(list)
for candidate, depts in double_dept_info.items():
    combo_candidates[tuple(depts)].append(candidate)

# 5. 分配双部门人员
def assign_double_candidates(combo, candidates, assignments):
    dept1, dept2 = combo
    n = len(candidates)
    group1_size = (n + 1) // 2  # 前两场人数（向上取整）
    group1 = candidates[:group1_size]  # 前两场
    group2 = candidates[group1_size:]  # 后两场

    # 分配前两场
    for i, candidate in enumerate(group1):
        time1, time2 = times[0], times[1]
        if i % 2 == 0:
            assign_to_slots(assignments, candidate, time1, dept1, time2, dept2)
        else:
            assign_to_slots(assignments, candidate, time1, dept2, time2, dept1)

    # 分配后两场
    for i, candidate in enumerate(group2):
        time1, time2 = times[2], times[3]
        if i % 2 == 0:
            assign_to_slots(assignments, candidate, time1, dept1, time2, dept2)
        else:
            assign_to_slots(assignments, candidate, time1, dept2, time2, dept1)

def assign_to_slots(assignments, candidate, time1, dept1, time2, dept2):
    """将候选人分配到指定时间和部门的第一个空位"""
    for i in range(len(assignments[time1][dept1])):
        if assignments[time1][dept1][i] == '' and assignments[time2][dept2][i] == '':
            assignments[time1][dept1][i] = candidate
            assignments[time2][dept2][i] = candidate
            break

# 对每个组合分配
for combo, candidates in combo_candidates.items():
    assign_double_candidates(combo, candidates, assignments)

# 6. 分配单部门人员
single_candidates = {
    dept: [c for c in candidates if c not in double_candidates]
    for dept, candidates in dept_lists.items()
}

for dept, candidates in single_candidates.items():
    candidate_idx = 0
    for time in times:
        slots = assignments[time][dept]
        for i in range(len(slots)):
            if slots[i] == '' and candidate_idx < len(candidates):
                slots[i] = candidates[candidate_idx]
                candidate_idx += 1

# 7. 将调试信息写入txt文件
with open('output/second_interview_log.txt', 'w', encoding='utf-8') as f:
    for time in times:
        f.write(f"时间段: {time}\n")
        for dept in dept_lists:
            assigned = [name for name in assignments[time][dept] if name != '']
            f.write(f"  {dept}: {len(assigned)} 人, 名单: {assigned}\n")
        f.write("\n")

# 8. 生成Excel文件
# 计算每个时间段的最大行数
time_rows = {}
for time in times:
    max_rows = max(len(assignments[time][dept]) for dept in dept_lists)
    time_rows[time] = max_rows

# 构建输出数据
data = []
for time, rows in time_rows.items():
    for i in range(rows):
        row = [time if i == 0 else '']
        for dept in dept_lists:
            if i < len(assignments[time][dept]):
                row.append(assignments[time][dept][i])
            else:
                row.append('')
        data.append(row)

# 创建DataFrame并指定列名
df_output = pd.DataFrame(data, columns=['时间', '人资', '外联', '策划', '宣传'])

# 写入Excel并合并时间列单元格
writer = pd.ExcelWriter('output/second_schedule.xlsx', engine='xlsxwriter')
df_output.to_excel(writer, index=False, sheet_name='Sheet1')

workbook = writer.book
worksheet = writer.sheets['Sheet1']

# 创建一个居中对齐的格式
center_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})

# 应用居中格式到所有单元格
for col_num, col_data in enumerate(df_output.columns):
    worksheet.set_column(col_num, col_num, None, center_format)

# 合并时间列
row_index = 1
for time, rows in time_rows.items():
    if rows > 1:
        worksheet.merge_range(row_index, 0, row_index + rows - 1, 0, time)
    else:
        worksheet.write(row_index, 0, time)
    row_index += rows

writer.close()

print("排表已生成，输出文件为 'second_schedule.xlsx'，调试信息已保存到 'second_schedule_log.txt'")