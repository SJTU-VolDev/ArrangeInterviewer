"""
post_processor.py
后处理模块

对分配结果进行二次处理：
    - 分时段（均分策略）：将大时间段按 n 分钟切分为小时间段，志愿者等分
    - 分时段（头部聚集策略）：优先填满最早的小时间段，奇偶位有不同上限
    - 编号：为每个面试官下的志愿者从 1 开始编号
"""

import re
from collections import defaultdict
from typing import List, Optional, Tuple

from scheduler import Assignment


def _parse_time_range(slot_name: str) -> Optional[Tuple[int, int]]:
    """从时间段名称中提取 HH:MM-HH:MM，返回 (起始分钟, 结束分钟)。

    例如 "2月25日 14:00-17:00" → (840, 1020)

    Returns:
        (start_minutes, end_minutes) 或 None（无法解析时）
    """
    match = re.search(r"(\d{1,2}):(\d{2})\s*[-–—]\s*(\d{1,2}):(\d{2})", slot_name)
    if not match:
        return None
    h1, m1, h2, m2 = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
    start = h1 * 60 + m1
    end = h2 * 60 + m2
    if end <= start:
        return None
    return start, end


def _generate_sub_slots(start: int, end: int, n: int) -> List[str]:
    """将 [start, end) 按 n 分钟切分为小时间段字符串列表。

    Args:
        start: 起始分钟数
        end:   结束分钟数
        n:     每段分钟数

    Returns:
        如 ["14:00-14:15", "14:15-14:30", ...]
    """
    sub_slots = []
    cursor = start
    while cursor < end:
        seg_end = min(cursor + n, end)
        s_str = f"{cursor // 60:d}:{cursor % 60:02d}"
        e_str = f"{seg_end // 60:d}:{seg_end % 60:02d}"
        sub_slots.append(f"{s_str}-{e_str}")
        cursor = seg_end
    return sub_slots


def apply_sub_slots(
    assignments: List[Assignment],
    sub_slot_minutes: int,
    log_messages: List[str],
) -> None:
    """为分配结果填充小时间段（就地修改 Assignment.sub_slot）。

    逻辑：对每个 (time_slot, interviewer) 分组，将志愿者按顺序等分到小时间段中。
    同一小时间段的志愿者排列在一起（连续），便于后续合并单元格和编号。
    - 若志愿者数 ≤ 小时间段数：每人分配一个小时间段（按顺序）
    - 若志愿者数 > 小时间段数：均匀分配，前面的小时间段可能多分一人
    """
    log_messages.append(f"\n=== 后处理：分时段（每 {sub_slot_minutes} 分钟）===")

    # 按 (time_slot, interviewer) 分组，保持原有顺序
    groups: defaultdict[Tuple[str, str], List[Assignment]] = defaultdict(list)
    for a in assignments:
        groups[(a.time_slot, a.interviewer)].append(a)

    # 缓存每个时间段的小时间段列表
    sub_slot_cache: dict[str, List[str]] = {}

    # 用于重排 assignments 列表：按小时间段聚拢
    reordered: List[Assignment] = []

    for (slot, interviewer), group in groups.items():
        if slot not in sub_slot_cache:
            time_range = _parse_time_range(slot)
            if time_range is None:
                log_messages.append(
                    f"  警告: 无法从时间段 \"{slot}\" 中解析 HH:MM-HH:MM，跳过分时段"
                )
                sub_slot_cache[slot] = []
            else:
                sub_slot_cache[slot] = _generate_sub_slots(
                    time_range[0], time_range[1], sub_slot_minutes
                )

        sub_slots = sub_slot_cache[slot]
        if not sub_slots:
            reordered.extend(group)
            continue

        n_subs = len(sub_slots)
        n_vols = len(group)

        # 计算每个小时间段分配多少名志愿者
        # base = 每段基础人数, extra = 前 extra 个小时间段各多1人
        base = n_vols // n_subs if n_subs > 0 else 0
        extra = n_vols % n_subs if n_subs > 0 else 0

        vol_idx = 0
        for sub_idx, sub_slot_name in enumerate(sub_slots):
            count = base + (1 if sub_idx < extra else 0)
            for _ in range(count):
                if vol_idx < n_vols:
                    group[vol_idx].sub_slot = sub_slot_name
                    reordered.append(group[vol_idx])
                    vol_idx += 1

        log_messages.append(
            f"  {slot} / {interviewer}: "
            f"{n_vols} 名志愿者 → {n_subs} 个小时间段"
        )

    # 用重排后的列表替换原 assignments（同一小时间段的志愿者连续排列）
    assignments.clear()
    assignments.extend(reordered)


def apply_sub_slots_head_gather(
    assignments: List[Assignment],
    sub_slot_minutes: int,
    odd_max: int,
    even_max: int,
    log_messages: List[str],
) -> None:
    """头部聚集策略：优先填满最早的小时间段，然后依次向后填充。

    奇数位小时间段（第1、3、5…个）最多放 odd_max 人，
    偶数位小时间段（第2、4、6…个）最多放 even_max 人。
    若所有小时间段填满后仍有志愿者未分配，输出错误信息。

    Args:
        assignments: 分配结果列表（就地修改）
        sub_slot_minutes: 每个小时间段的分钟数
        odd_max: 奇数位小时间段的最大人数
        even_max: 偶数位小时间段的最大人数
        log_messages: 日志消息列表
    """
    log_messages.append(
        f"\n=== 后处理：头部聚集分时段（每 {sub_slot_minutes} 分钟, "
        f"奇数位上限 {odd_max}, 偶数位上限 {even_max}）==="
    )

    # 按 (time_slot, interviewer) 分组，保持原有顺序
    groups: defaultdict[Tuple[str, str], List[Assignment]] = defaultdict(list)
    for a in assignments:
        groups[(a.time_slot, a.interviewer)].append(a)

    # 缓存每个时间段的小时间段列表
    sub_slot_cache: dict[str, List[str]] = {}

    # 用于重排 assignments 列表：按小时间段聚拢
    reordered: List[Assignment] = []

    has_error = False

    for (slot, interviewer), group in groups.items():
        if slot not in sub_slot_cache:
            time_range = _parse_time_range(slot)
            if time_range is None:
                log_messages.append(
                    f"  警告: 无法从时间段 \"{slot}\" 中解析 HH:MM-HH:MM，跳过分时段"
                )
                sub_slot_cache[slot] = []
            else:
                sub_slot_cache[slot] = _generate_sub_slots(
                    time_range[0], time_range[1], sub_slot_minutes
                )

        sub_slots = sub_slot_cache[slot]
        if not sub_slots:
            reordered.extend(group)
            continue

        n_subs = len(sub_slots)
        n_vols = len(group)

        # 计算总容量
        total_capacity = 0
        for sub_idx in range(n_subs):
            cap = odd_max if (sub_idx % 2 == 0) else even_max  # 第1个=index 0=奇数位
            total_capacity += cap

        # 容量校验
        if n_vols > total_capacity:
            error_msg = (
                f"错误: 时间段 '{slot}' 面试官 '{interviewer}' 名额不足 "
                f"(需分配 {n_vols} 人, 总容量 {total_capacity} 人)"
            )
            log_messages.append(f"  {error_msg}")
            print(error_msg)
            has_error = True
            # 仍然尽力分配（填满所有小时间段）

        # 从第1个小时间段开始，按顺序填充
        vol_idx = 0
        for sub_idx, sub_slot_name in enumerate(sub_slots):
            # 奇数位 = index 0, 2, 4, ... ; 偶数位 = index 1, 3, 5, ...
            cap = odd_max if (sub_idx % 2 == 0) else even_max
            filled = 0
            while filled < cap and vol_idx < n_vols:
                group[vol_idx].sub_slot = sub_slot_name
                reordered.append(group[vol_idx])
                vol_idx += 1
                filled += 1

            if vol_idx >= n_vols:
                # 所有志愿者已分配完毕，为后续空置小时间段生成占位行
                for empty_idx in range(sub_idx + (1 if filled > 0 else 0), n_subs):
                    placeholder = Assignment(
                        volunteer=None,
                        time_slot=slot,
                        interviewer=interviewer,
                    )
                    placeholder.sub_slot = sub_slots[empty_idx]
                    reordered.append(placeholder)
                break  # 退出小时间段循环

        log_messages.append(
            f"  {slot} / {interviewer}: "
            f"{n_vols} 名志愿者 → {n_subs} 个小时间段 "
            f"(总容量 {total_capacity}, 已用 {min(n_vols, total_capacity)})"
        )

    if has_error:
        log_messages.append(
            "\n警告: 存在面试官名额不足的情况，请检查上述错误信息"
        )

    # 用重排后的列表替换原 assignments
    assignments.clear()
    assignments.extend(reordered)


def apply_numbering(
    assignments: List[Assignment],
    log_messages: List[str],
) -> None:
    """为分配结果填充编号（就地修改 Assignment.number）。

    编号规则：每个 (time_slot, interviewer) 分组内从 1 开始编号。
    """
    log_messages.append("\n=== 后处理：编号 ===")

    groups: defaultdict[Tuple[str, str], List[Assignment]] = defaultdict(list)
    for a in assignments:
        groups[(a.time_slot, a.interviewer)].append(a)

    for (slot, interviewer), group in groups.items():
        num = 1
        for a in group:
            if a.is_placeholder:
                a.number = 0  # 占位行不编号
            else:
                a.number = num
                num += 1
