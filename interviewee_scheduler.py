import pandas as pd
import sys
from collections import defaultdict
from typing import List, Dict, Tuple
import openpyxl
from openpyxl.styles import Alignment, Font, Border, Side
from openpyxl.styles import PatternFill

class IntervieweeScheduler:
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.df = None
        self.time_slots = set()
        self.time_slot_assignments = defaultdict(list)
        
    def identify_columns(self) -> Tuple[str, str, str]:
        """识别包含关键信息的列名"""
        df = pd.read_excel(self.input_file)
        name_col = next(col for col in df.columns if '姓名' in col)
        student_id_col = next(col for col in df.columns if '学号' in col)
        time_col = next(col for col in df.columns if '面试时间' in col)
        return name_col, student_id_col, time_col
    
    def extract_time_slots(self, time_str: str) -> List[str]:
        """从时间字符串中提取所有时间段"""
        if pd.isna(time_str):
            return []
        return [t.strip() for t in str(time_str).split('、')]
    
    def process_data(self):
        """处理输入数据，收集所有可用时间段"""
        name_col, student_id_col, time_col = self.identify_columns()
        self.df = pd.read_excel(self.input_file)
        
        # 收集所有时间段
        all_time_slots = set()
        for _, row in self.df.iterrows():
            time_slots = self.extract_time_slots(row[time_col])
            all_time_slots.update(time_slots)
        self.time_slots = sorted(all_time_slots)
        
        # 为每个学生收集可用时间段
        self.student_available_times = {}
        for _, row in self.df.iterrows():
            name = row[name_col]
            student_id = row[student_id_col]
            time_slots = self.extract_time_slots(row[time_col])
            self.student_available_times[(name, student_id)] = time_slots
    
    def assign_time_slots(self):
        """为每个学生分配时间段，确保所有时间段都被使用"""
        # 用于收集所有输出信息
        log_messages = []
        
        # 按可用时间段数量排序学生（优先安排时间段少的学生）
        students_by_availability = sorted(
            self.student_available_times.items(),
            key=lambda x: (len(x[1]), x[0])
        )
        
        # 记录每个时间段的已分配人数
        slot_assignments = defaultdict(int)
        
        # 第一轮：确保每个时间段至少分配一个学生
        unassigned_students = []
        assigned_students = set()
        
        # 首先，尝试为每个时间段分配至少一个学生
        for time_slot in self.time_slots:
            assigned = False
            # 寻找可以在这个时间段面试的学生
            for (name, student_id), available_times in students_by_availability:
                if (name, student_id) not in assigned_students and time_slot in available_times:
                    self.time_slot_assignments[time_slot].append((name, student_id))
                    slot_assignments[time_slot] += 1
                    assigned_students.add((name, student_id))
                    assigned = True
                    break
            
            if not assigned:
                log_messages.append(f"警告：时间段 {time_slot} 没有找到可用的学生！")
        
        # 第二轮：分配剩余的学生
        for (name, student_id), available_times in students_by_availability:
            if (name, student_id) in assigned_students:
                continue
                
            # 在该学生的可用时间段中找人数最少的时间段
            best_slot = None
            min_assigned = float('inf')
            
            for time_slot in available_times:
                current_assigned = slot_assignments[time_slot]
                if current_assigned < min_assigned:
                    min_assigned = current_assigned
                    best_slot = time_slot
            
            if best_slot:
                self.time_slot_assignments[best_slot].append((name, student_id))
                slot_assignments[best_slot] += 1
                assigned_students.add((name, student_id))
            else:
                unassigned_students.append((name, student_id))
        
        # 输出分配结果统计
        log_messages.append("\n时间段分配情况：")
        for time_slot in sorted(self.time_slots):
            count = len(self.time_slot_assignments[time_slot])
            log_messages.append(f"时间段 {time_slot}: {count} 人")
        
        # 处理未分配的学生
        if unassigned_students:
            log_messages.append(f"\n警告：有 {len(unassigned_students)} 名学生未能按照其可用时间段分配：")
            for name, student_id in unassigned_students:
                log_messages.append(f"- {name} ({student_id})")
                # 输出这些学生的可用时间段，方便手动调整
                available_times = self.student_available_times[(name, student_id)]
                log_messages.append(f"  可用时间段: {', '.join(available_times)}")
        
        # 保存日志信息到文件
        self.save_log(log_messages)
    
    def save_log(self, log_messages: List[str]):
        """保存日志信息到文件"""
        log_file = 'output/interviewee_schedule_log.txt'
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("面试时间安排 - 执行日志\n")
            f.write("=" * 50 + "\n\n")
            f.write("\n".join(log_messages))
            f.write("\n\n" + "=" * 50 + "\n")
            f.write("日志生成完成")
        
        # 同时在控制台显示日志信息
        print("\n".join(log_messages))
        print(f"\n日志已保存至：{log_file}")
    
    def save_schedule(self, output_file: str):
        """保存排班表到Excel文件，并合并相同时间单元格"""
        # 准备数据
        schedule_data = []
        for time_slot in sorted(self.time_slots):
            assignments = self.time_slot_assignments[time_slot]
            if assignments:
                for name, student_id in sorted(assignments):
                    schedule_data.append({
                        '时间': time_slot,
                        '姓名': name,
                        '学号': str(student_id)  # 确保学号是字符串类型
                    })
        
        # 创建DataFrame，并指定学号列为字符串类型
        schedule_df = pd.DataFrame(schedule_data)
        schedule_df['学号'] = schedule_df['学号'].astype(str)  # 将学号列转换为字符串类型
        
        # 保存到Excel，设置学号列的格式为文本
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 将DataFrame写入Excel，并设置学号列为文本格式
            schedule_df.to_excel(writer, index=False, sheet_name='面试者安排')
            
            # 获取工作表
            worksheet = writer.sheets['面试者安排']
            max_row = len(schedule_df) + 1  # 加1是因为有标题行
            
            # 设置学号列为文本格式
            for row in range(2, max_row + 1):
                cell = worksheet.cell(row=row, column=3)  # 第3列是学号列
                cell.number_format = '@'  # 设置单元格格式为文本
            
            # 设置标题行格式
            bold_font = Font(bold=True)
            for col in range(1, 4):  # A, B, C三列
                cell = worksheet.cell(row=1, column=col)
                cell.font = bold_font
            
            # 定义一组浅色背景颜色（RGB格式）
            light_colors = [
                'FFE6E6',  # 浅红
                'E6FFE6',  # 浅绿
                'E6E6FF',  # 浅蓝
                'FFFFD9',  # 浅黄
                'FFE6FF',  # 浅紫
                'E6FFFF',  # 浅青
                'FFF0E6',  # 浅橙
                'F2FFE6',  # 浅黄绿
                'E6F2FF',  # 浅天蓝
                'FFE6F2',  # 浅粉
            ]
            
            # 为每个时间段分配颜色
            time_slots = sorted(set(schedule_df['时间']))
            color_map = {
                time_slot: light_colors[i % len(light_colors)]
                for i, time_slot in enumerate(time_slots)
            }
            
            # 设置所有单元格的边框、对齐方式和背景颜色
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            # 设置标题行
            for col in range(1, 4):
                cell = worksheet.cell(row=1, column=col)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # 设置数据行的格式
            current_time = None
            for row in range(2, max_row + 1):
                time_value = worksheet.cell(row=row, column=1).value
                # 获取当前时间段的背景颜色
                fill = PatternFill(start_color=color_map[time_value],
                                 end_color=color_map[time_value],
                                 fill_type='solid')
                
                # 为该行的所有单元格设置格式
                for col in range(1, 4):
                    cell = worksheet.cell(row=row, column=col)
                    cell.border = thin_border
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    cell.fill = fill
            
            # 合并相同时间的单元格
            current_time = None
            time_start_row = 2
            
            for row in range(2, max_row + 1):
                time_value = worksheet.cell(row=row, column=1).value
                if time_value != current_time:
                    if current_time is not None:
                        worksheet.merge_cells(f'A{time_start_row}:A{row-1}')
                    current_time = time_value
                    time_start_row = row
            
            # 处理最后一组时间
            if time_start_row < max_row:
                worksheet.merge_cells(f'A{time_start_row}:A{max_row}')
            
            # 调整列宽
            worksheet.column_dimensions['A'].width = 15  # 时间列
            worksheet.column_dimensions['B'].width = 12  # 姓名列
            worksheet.column_dimensions['C'].width = 15  # 学号列

def main():
    if len(sys.argv) != 1:
        print("使用方法: python interviewee_scheduler.py")
        sys.exit(1)
    
    scheduler = IntervieweeScheduler('tables/interviewee.xlsx')
    scheduler.process_data()
    scheduler.assign_time_slots()
    scheduler.save_schedule('output/interviewee_schedule.xlsx')

if __name__ == "__main__":
    main() 