"""
main.py
线上志愿者面试排表系统 - 程序入口

流程:
  1. 读取 config.json 配置
  2. 解析面试官信息表 → 时间段 & 面试官分组
  3. 解析志愿者总表 → 志愿者信息 & 可选时间
  4. 执行两轮分配算法
  5. 输出排班表 Excel + 日志文件
"""

import json
import os
import sys

from interviewer_parser import InterviewerParser
from volunteer_parser import VolunteerParser
from scheduler import Scheduler
from post_processor import apply_sub_slots, apply_sub_slots_head_gather, apply_numbering
from output_generator import OutputGenerator


def load_config(config_path: str = "config.json") -> dict:
    """读取配置文件"""
    if not os.path.exists(config_path):
        print(f"错误: 找不到配置文件 {config_path}")
        sys.exit(1)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误: 配置文件格式不正确 — {e}")
        sys.exit(1)


def main():
    config = load_config()

    # ---- 必填项 ----
    interviewer_file = config.get("interviewer_file")
    volunteer_file = config.get("volunteer_file")

    if not interviewer_file or not volunteer_file:
        print("错误: 配置文件缺少必填项 (interviewer_file / volunteer_file)")
        sys.exit(1)

    # ---- 选填项 ----
    time_slots_override = config.get("time_slots")  # 可选，用于覆盖自动提取的顺序
    slot_weights = config.get("slot_weights")
    key_words = config.get("key_words", ["姓名", "学号", "微信号"])
    interview_time_column = config.get("interview_time_column", "面试时间")
    sub_slot_minutes = config.get("sub_slot_minutes", False)
    enable_numbering = config.get("enable_numbering", False)
    distribution_strategy = config.get("distribution_strategy", 1)
    head_gather_odd_max = config.get("head_gather_odd_max", 3)
    head_gather_even_max = config.get("head_gather_even_max", 2)

    # ---- 1. 解析面试官信息 ----
    if not os.path.exists(interviewer_file):
        print(f"错误: 找不到面试官信息文件 {interviewer_file}")
        sys.exit(1)

    print(f"正在解析面试官信息: {interviewer_file}")
    interviewer_parser = InterviewerParser(file_path=interviewer_file)
    slot_interviewers = interviewer_parser.parse()

    # 确定时间段列表：优先使用配置中的 time_slots，否则自动从面试官表提取
    if time_slots_override:
        time_slots = time_slots_override
        # 校验配置与面试官表的时间段一致性
        excel_slots = set(slot_interviewers.keys())
        config_slots = set(time_slots)
        missing_in_config = excel_slots - config_slots
        missing_in_excel = config_slots - excel_slots
        if missing_in_config:
            print(f"警告: 面试官表中存在配置未定义的时间段: {missing_in_config}")
        if missing_in_excel:
            print(f"警告: 配置中定义的时间段在面试官表中未找到: {missing_in_excel}")
        print(f"  使用配置文件中定义的时间段顺序: {time_slots}")
    else:
        # 自动从面试官表提取，保持读取顺序
        time_slots = list(slot_interviewers.keys())
        print(f"  自动从面试官信息表提取时间段: {time_slots}")

    # 校验权重数量
    if slot_weights and len(slot_weights) != len(time_slots):
        print(
            f"错误: slot_weights 数量({len(slot_weights)}) "
            f"与时间段数量({len(time_slots)}) 不匹配"
        )
        sys.exit(1)

    total_interviewers = sum(len(v) for v in slot_interviewers.values())
    print(f"  共识别 {len(time_slots)} 个时间段, {total_interviewers} 人次面试官")

    # ---- 2. 解析志愿者信息 ----
    if not os.path.exists(volunteer_file):
        print(f"错误: 找不到志愿者总表文件 {volunteer_file}")
        sys.exit(1)

    print(f"正在解析志愿者总表: {volunteer_file}")
    volunteer_parser = VolunteerParser(
        file_path=volunteer_file,
        key_words=key_words,
        time_column_keyword=interview_time_column,
    )
    volunteers = volunteer_parser.parse()
    print(f"  共识别 {len(volunteers)} 名志愿者")

    # 校验志愿者可选时间段与时间段列表
    volunteer_slots = set()
    for v in volunteers:
        volunteer_slots.update(v.available_slots)

    known_slots = set(time_slots)
    unknown_slots = volunteer_slots - known_slots
    if unknown_slots:
        print(f"警告: 志愿者表中存在未识别的时间段: {unknown_slots}")

    # ---- 3. 执行分配 ----
    print("\n开始分配...")
    scheduler = Scheduler(
        time_slots=time_slots,
        slot_interviewers=slot_interviewers,
        volunteers=volunteers,
        slot_weights=slot_weights,
    )
    scheduler.run()

    # ---- 4. 后处理 ----
    has_sub_slots = bool(sub_slot_minutes and isinstance(sub_slot_minutes, int) and sub_slot_minutes > 0)
    has_numbering = bool(enable_numbering)

    if has_sub_slots:
        if distribution_strategy == 2:
            # 头部聚集策略
            print(f"\n执行后处理：头部聚集分时段（每 {sub_slot_minutes} 分钟, 奇数位上限 {head_gather_odd_max}, 偶数位上限 {head_gather_even_max}）...")
            apply_sub_slots_head_gather(
                scheduler.assignments,
                sub_slot_minutes,
                head_gather_odd_max,
                head_gather_even_max,
                scheduler.log_messages,
            )
        else:
            # 默认均分策略
            print(f"\n执行后处理：均分分时段（每 {sub_slot_minutes} 分钟）...")
            apply_sub_slots(scheduler.assignments, sub_slot_minutes, scheduler.log_messages)

    if has_numbering:
        print("执行后处理：编号...")
        apply_numbering(scheduler.assignments, scheduler.log_messages)

    # ---- 5. 输出结果 ----
    output_excel = "output/schedule.xlsx"
    output_log = "output/schedule_log.txt"

    output_gen = OutputGenerator(
        assignments=scheduler.assignments,
        time_slots=time_slots,
        key_words=key_words,
        log_messages=scheduler.log_messages,
        has_sub_slots=has_sub_slots,
        has_numbering=has_numbering,
    )

    output_gen.save_schedule(output_excel)
    print(f"\n排班表已保存至: {output_excel}")

    output_gen.save_log(output_log)


if __name__ == "__main__":
    main()
