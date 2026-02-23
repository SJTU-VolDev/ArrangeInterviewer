"""
scheduler.py
核心分配算法模块

将志愿者分配到各时间段的面试官组中。
两轮分配策略：
    第一轮：保底 — 为每个时间段每位面试官至少分配1名志愿者
    第二轮：按权重 — 对剩余志愿者，分配到缺口最大的时间段
"""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from volunteer_parser import Volunteer


class Assignment:
    """表示一条分配结果：志愿者 → 时间段 + 面试官"""

    def __init__(self, volunteer: Optional[Volunteer], time_slot: str, interviewer: str):
        self.volunteer = volunteer
        self.time_slot = time_slot
        self.interviewer = interviewer
        # 后处理阶段填充
        self.sub_slot: str = ""      # 小时间段（如 "14:00-14:15"）
        self.number: int = 0         # 编号（同面试官下从1开始）

    @property
    def is_placeholder(self) -> bool:
        """是否为空置占位行（无志愿者）"""
        return self.volunteer is None

    def __repr__(self) -> str:
        name = self.volunteer.name if self.volunteer else "(空)"
        return (
            f"Assignment({name} → "
            f"{self.time_slot} / {self.interviewer})"
        )


class Scheduler:
    """分配调度器"""

    def __init__(
        self,
        time_slots: List[str],
        slot_interviewers: Dict[str, List[str]],
        volunteers: List[Volunteer],
        slot_weights: Optional[List[int]] = None,
    ):
        """
        Args:
            time_slots: 时间段列表（配置文件定义的顺序）
            slot_interviewers: { 时间段 → [面试官列表] }
            volunteers: 志愿者列表
            slot_weights: 各时间段权重列表（可选）
        """
        self.time_slots = time_slots
        self.slot_interviewers = slot_interviewers
        self.volunteers = volunteers
        self.slot_weights = slot_weights

        # 分配结果
        self.assignments: List[Assignment] = []
        # 未分配的志愿者
        self.unassigned: List[Volunteer] = []
        # 日志消息
        self.log_messages: List[str] = []

    # ------------------------------------------------------------------
    # 计算目标人数
    # ------------------------------------------------------------------

    def _compute_target_counts(self, total: int) -> Dict[str, int]:
        """根据权重计算每个时间段的目标志愿者数。

        Args:
            total: 需要分配的志愿者总数

        Returns:
            { 时间段 → 目标人数 }
        """
        if self.slot_weights and len(self.slot_weights) == len(self.time_slots):
            total_weight = sum(self.slot_weights)
            targets = {}
            for slot, weight in zip(self.time_slots, self.slot_weights):
                targets[slot] = int(round((weight / total_weight) * total))
            return targets
        else:
            per_slot = total // len(self.time_slots)
            return {slot: per_slot for slot in self.time_slots}

    # ------------------------------------------------------------------
    # 分配算法
    # ------------------------------------------------------------------

    def run(self) -> None:
        """执行两轮分配"""
        self.assignments.clear()
        self.unassigned.clear()
        self.log_messages.clear()

        total_volunteers = len(self.volunteers)
        self.log_messages.append(f"志愿者总数: {total_volunteers}")
        self.log_messages.append(f"时间段数量: {len(self.time_slots)}")

        # 校验时间段与面试官映射
        for slot in self.time_slots:
            interviewers = self.slot_interviewers.get(slot, [])
            self.log_messages.append(
                f"时间段 {slot}: {len(interviewers)} 名面试官 ({', '.join(interviewers)})"
            )

        # 按可用时间段数量排序（少的优先分配）
        sorted_volunteers = sorted(
            self.volunteers,
            key=lambda v: (len(v.available_slots), v.name),
        )

        # 记录每个时间段已分配人数
        slot_counts: Dict[str, int] = defaultdict(int)
        # 记录每位面试官已分配人数
        interviewer_counts: Dict[Tuple[str, str], int] = defaultdict(int)
        # 已分配的志愿者集合
        assigned_keys = set()

        # ---- 第一轮：保底分配 ----
        self.log_messages.append("\n=== 第一轮：保底分配 ===")

        for slot in self.time_slots:
            interviewers = self.slot_interviewers.get(slot, [])
            for interviewer in interviewers:
                # 找一个可用且未分配的志愿者
                assigned = False
                for vol in sorted_volunteers:
                    if vol.key in assigned_keys:
                        continue
                    if slot in vol.available_slots:
                        self.assignments.append(
                            Assignment(vol, slot, interviewer)
                        )
                        assigned_keys.add(vol.key)
                        slot_counts[slot] += 1
                        interviewer_counts[(slot, interviewer)] += 1
                        assigned = True
                        break

                if not assigned:
                    self.log_messages.append(
                        f"  警告: 时间段 {slot} 面试官 {interviewer} "
                        f"未能保底分配到志愿者"
                    )

        self.log_messages.append(
            f"  第一轮分配完成，已分配 {len(assigned_keys)} 人"
        )

        # ---- 第二轮：按权重分配剩余志愿者 ----
        self.log_messages.append("\n=== 第二轮：按权重分配 ===")

        remaining = [v for v in sorted_volunteers if v.key not in assigned_keys]
        target_counts = self._compute_target_counts(total_volunteers)

        for vol in remaining:
            if not vol.available_slots:
                self.unassigned.append(vol)
                continue

            # 在可用时间段中找缺口最大的
            best_slot = None
            max_gap = -float("inf")
            for slot in vol.available_slots:
                if slot not in target_counts:
                    continue
                gap = target_counts[slot] - slot_counts[slot]
                if gap > max_gap:
                    max_gap = gap
                    best_slot = slot

            if best_slot is None:
                self.unassigned.append(vol)
                continue

            # 在该时间段中，选面试人数最少的面试官
            interviewers = self.slot_interviewers.get(best_slot, [])
            if not interviewers:
                self.unassigned.append(vol)
                continue

            best_interviewer = min(
                interviewers,
                key=lambda i: interviewer_counts[(best_slot, i)],
            )

            self.assignments.append(
                Assignment(vol, best_slot, best_interviewer)
            )
            assigned_keys.add(vol.key)
            slot_counts[best_slot] += 1
            interviewer_counts[(best_slot, best_interviewer)] += 1

        # ---- 统计结果 ----
        self.log_messages.append(
            f"  第二轮分配完成，共分配 {len(assigned_keys)} 人"
        )

        self.log_messages.append("\n=== 分配统计 ===")
        for slot in self.time_slots:
            actual = slot_counts[slot]
            target = target_counts[slot]
            pct = (actual / total_volunteers * 100) if total_volunteers > 0 else 0
            self.log_messages.append(
                f"  时间段 {slot}: {actual} 人 "
                f"(目标: {target}, 占比: {pct:.1f}%)"
            )
            # 每位面试官分配详情
            for interviewer in self.slot_interviewers.get(slot, []):
                count = interviewer_counts[(slot, interviewer)]
                self.log_messages.append(
                    f"    面试官 {interviewer}: {count} 人"
                )

        if self.unassigned:
            self.log_messages.append(
                f"\n警告: {len(self.unassigned)} 名志愿者未能分配："
            )
            for vol in self.unassigned:
                self.log_messages.append(
                    f"  - {vol.name} (可选时间: {', '.join(vol.available_slots)})"
                )
