"""
scheduler.py
核心分配算法模块

将志愿者分配到各时间段的面试官组中。
支持两种调度模式：
    - time_slot（时间段本位）：以大时间段为核心，优先填满缺口最大的时间段
    - interviewer（面试官核心）：以面试官为核心，优先平衡面试官负载

两轮分配策略：
    第一轮：保底 — 为每位面试官的每个时间段至少分配1名志愿者
    第二轮：按需 — 对剩余志愿者，按当前模式的优先级分配
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
        scheduling_mode: str = "interviewer",
    ):
        """
        Args:
            time_slots: 时间段列表（配置文件定义的顺序）
            slot_interviewers: { 时间段 → [面试官列表] }
            volunteers: 志愿者列表
            slot_weights: 各时间段权重列表（可选）
            scheduling_mode: 调度模式 "time_slot"（时间段本位）或 "interviewer"（面试官核心）
        """
        self.time_slots = time_slots
        self.slot_interviewers = slot_interviewers
        self.volunteers = volunteers
        self.slot_weights = slot_weights
        self.scheduling_mode = scheduling_mode

        # 分配结果
        self.assignments: List[Assignment] = []
        # 未分配的志愿者
        self.unassigned: List[Volunteer] = []
        # 日志消息
        self.log_messages: List[str] = []

    # ------------------------------------------------------------------
    # 计算目标人数
    # ------------------------------------------------------------------

    def _compute_slot_targets(self, total: int) -> Dict[str, int]:
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

    def _compute_pair_targets(self, total: int) -> Dict[Tuple[str, str], int]:
        """根据权重计算每个（时间段, 面试官）对的目标志愿者数。

        每个面试官-时间段对的权重 = 所在时间段权重 / 该时间段面试官数量。
        使用最大余数法（Largest Remainder Method）确保目标之和严格等于 total，
        避免四舍五入导致的总量偏差。

        Args:
            total: 需要分配的志愿者总数

        Returns:
            { (时间段, 面试官) → 目标人数 }
        """
        pairs: List[Tuple[str, str]] = []
        raw_weights: List[float] = []

        for i, slot in enumerate(self.time_slots):
            interviewers = self.slot_interviewers.get(slot, [])
            if not interviewers:
                continue
            slot_weight = (
                self.slot_weights[i]
                if self.slot_weights and len(self.slot_weights) == len(self.time_slots)
                else 1
            )
            per_interviewer_weight = slot_weight / len(interviewers)
            for interviewer in interviewers:
                pairs.append((slot, interviewer))
                raw_weights.append(per_interviewer_weight)

        total_weight = sum(raw_weights)
        if total_weight == 0:
            return {}

        # 最大余数法：先向下取整，然后按余数从大到小补齐差额
        exact = [(weight / total_weight) * total for weight in raw_weights]
        floors = [max(1, int(e)) for e in exact]  # 每对至少 1 人
        remainders = [e - f for e, f in zip(exact, floors)]

        deficit = total - sum(floors)
        if deficit > 0:
            # 按余数从大到小排序，前 deficit 个各 +1
            indices_by_remainder = sorted(
                range(len(pairs)), key=lambda i: remainders[i], reverse=True
            )
            for i in indices_by_remainder[:deficit]:
                floors[i] += 1

        targets: Dict[Tuple[str, str], int] = {}
        for pair, count in zip(pairs, floors):
            targets[pair] = count
        return targets

    # ------------------------------------------------------------------
    # 公共工具
    # ------------------------------------------------------------------

    def _log_slot_interviewers(self) -> None:
        """输出时间段与面试官的基本信息日志"""
        self.log_messages.append(f"时间段数量: {len(self.time_slots)}")
        for slot in self.time_slots:
            interviewers = self.slot_interviewers.get(slot, [])
            self.log_messages.append(
                f"时间段 {slot}: {len(interviewers)} 名面试官 ({', '.join(interviewers)})"
            )

    # ------------------------------------------------------------------
    # 分配算法入口
    # ------------------------------------------------------------------

    def run(self) -> None:
        """根据调度模式执行分配"""
        self.assignments.clear()
        self.unassigned.clear()
        self.log_messages.clear()

        if self.scheduling_mode == "interviewer":
            self._run_interviewer_centric()
        else:
            self._run_time_slot_centric()

    # ------------------------------------------------------------------
    # 模式一：时间段本位（原有逻辑）
    # ------------------------------------------------------------------

    def _run_time_slot_centric(self) -> None:
        """时间段本位调度：优先填满缺口最大的时间段"""
        total_volunteers = len(self.volunteers)
        self.log_messages.append(f"志愿者总数: {total_volunteers}")
        self.log_messages.append(f"调度模式: 时间段本位")
        self._log_slot_interviewers()

        # 按可用时间段数量排序（少的优先分配）
        sorted_volunteers = sorted(
            self.volunteers,
            key=lambda v: (len(v.available_slots), v.name),
        )

        slot_counts: Dict[str, int] = defaultdict(int)
        interviewer_counts: Dict[Tuple[str, str], int] = defaultdict(int)
        assigned_keys: set = set()

        # ---- 第一轮：保底分配 ----
        self.log_messages.append("\n=== 第一轮：保底分配 ===")

        for slot in self.time_slots:
            interviewers = self.slot_interviewers.get(slot, [])
            for interviewer in interviewers:
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
        target_counts = self._compute_slot_targets(total_volunteers)

        for vol in remaining:
            if not vol.available_slots:
                self.unassigned.append(vol)
                continue

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

    # ------------------------------------------------------------------
    # 模式二：面试官核心（以 (时间段, 面试官) 对为原子单位）
    # ------------------------------------------------------------------

    def _run_interviewer_centric(self) -> None:
        """面试官核心调度：以每个 (时间段, 面试官) 对为独立单位，使各单位人数尽可能均等。

        注意：不同时间段的同名面试官视为独立个体，不做跨时间段汇总。

        第一轮（保底）：为每个 (时间段, 面试官) 对保底分配 1 名志愿者。
            - 遍历顺序：先按该时间段可选志愿者数量升序（供给少的对优先保底）。
        第二轮（均衡）：逐个分配剩余志愿者，每次选缺口最大的对。
            - 缺口 = pair_target - pair_count
            - 当缺口相同时，优先选当前人数少的对（更均匀）。
        """
        total_volunteers = len(self.volunteers)
        self.log_messages.append(f"志愿者总数: {total_volunteers}")
        self.log_messages.append(f"调度模式: 面试官核心（按面试官×时间段对均衡）")
        self._log_slot_interviewers()

        # 构建所有 (时间段, 面试官) 对的有序列表
        all_pairs: List[Tuple[str, str]] = []
        for slot in self.time_slots:
            for interviewer in self.slot_interviewers.get(slot, []):
                all_pairs.append((slot, interviewer))

        self.log_messages.append(f"面试官×时间段对总数: {len(all_pairs)}")
        for slot, interviewer in all_pairs:
            self.log_messages.append(f"  ({slot}, {interviewer})")

        # 按可用时间段数量排序（少的优先分配）
        sorted_volunteers = sorted(
            self.volunteers,
            key=lambda v: (len(v.available_slots), v.name),
        )

        # 预计算每个时间段有多少可选志愿者（用于第一轮排序）
        slot_available_count: Dict[str, int] = defaultdict(int)
        for vol in self.volunteers:
            for s in vol.available_slots:
                slot_available_count[s] += 1

        # 计数器
        slot_counts: Dict[str, int] = defaultdict(int)
        pair_counts: Dict[Tuple[str, str], int] = defaultdict(int)
        assigned_keys: set = set()

        # ---- 第一轮：保底分配 ----
        self.log_messages.append("\n=== 第一轮：保底分配（每对至少 1 人）===")

        # 按可选志愿者数量升序排列（供给紧张的对优先保底）
        sorted_pairs_for_guarantee = sorted(
            all_pairs,
            key=lambda p: slot_available_count.get(p[0], 0),
        )

        for slot, interviewer in sorted_pairs_for_guarantee:
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
                    pair_counts[(slot, interviewer)] += 1
                    assigned = True
                    break

            if not assigned:
                self.log_messages.append(
                    f"  警告: ({slot}, {interviewer}) 未能保底分配到志愿者"
                )

        self.log_messages.append(
            f"  第一轮分配完成，已分配 {len(assigned_keys)} 人"
        )

        # ---- 第二轮：绝对均衡分配剩余志愿者 ----
        self.log_messages.append("\n=== 第二轮：绝对均衡分配（人数最少的对优先）===")

        remaining = [v for v in sorted_volunteers if v.key not in assigned_keys]
        num_pairs = len(all_pairs)
        avg_per_pair = total_volunteers / num_pairs if num_pairs > 0 else 0

        self.log_messages.append(
            f"  理想均值: {total_volunteers} 人 / {num_pairs} 对 = {avg_per_pair:.1f} 人/对"
        )

        for vol in remaining:
            if not vol.available_slots:
                self.unassigned.append(vol)
                continue

            # 始终选当前人数最少的对（绝对均衡）
            # 人数相同时优先选可选志愿者供给更少的时间段（帮紧张的先填）
            best_pair: Optional[Tuple[str, str]] = None
            best_count = float("inf")
            best_supply = float("inf")

            for pair in all_pairs:
                slot, interviewer = pair
                if slot not in vol.available_slots:
                    continue

                current = pair_counts[pair]
                supply = slot_available_count.get(slot, 0)

                if current < best_count or (current == best_count and supply < best_supply):
                    best_count = current
                    best_supply = supply
                    best_pair = pair

            if best_pair is None:
                self.unassigned.append(vol)
                continue

            best_slot, best_interviewer = best_pair
            self.assignments.append(
                Assignment(vol, best_slot, best_interviewer)
            )
            assigned_keys.add(vol.key)
            slot_counts[best_slot] += 1
            pair_counts[best_pair] += 1

        # ---- 统计结果 ----
        self.log_messages.append(
            f"  第二轮分配完成，共分配 {len(assigned_keys)} 人"
        )

        self.log_messages.append("\n=== 分配统计（按面试官×时间段对）===")
        counts_list = [pair_counts[p] for p in all_pairs]
        min_c = min(counts_list) if counts_list else 0
        max_c = max(counts_list) if counts_list else 0
        self.log_messages.append(
            f"  均值: {avg_per_pair:.1f}, 最小: {min_c}, 最大: {max_c}, 极差: {max_c - min_c}"
        )
        for pair in all_pairs:
            slot, interviewer = pair
            count = pair_counts[pair]
            self.log_messages.append(
                f"  ({slot}, {interviewer}): {count} 人"
            )

        self.log_messages.append("\n=== 分配统计（按时间段汇总）===")
        for slot in self.time_slots:
            actual = slot_counts[slot]
            pct = (actual / total_volunteers * 100) if total_volunteers > 0 else 0
            self.log_messages.append(
                f"  时间段 {slot}: {actual} 人 (占比: {pct:.1f}%)"
            )
            for interviewer in self.slot_interviewers.get(slot, []):
                count = pair_counts[(slot, interviewer)]
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
