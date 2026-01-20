# src/game/player/milestone_status_updater.py
"""
マイルストーン状態更新コンポーネント。

責務:
- 観測イベントに基づいてマイルストーン状態を更新する
- milestone_plan の各マイルストーンについて trigger_condition を評価
- 状態は not_occurred → occurred / strong / weak に遷移
"""
from typing import List

from src.core.memory.strategy import (
    PlayerMilestonePlan,
    PlayerMilestoneStatus,
)
from src.core.types.events import GameEvent


class MilestoneStatusUpdater:
    """
    観測イベントに基づいてマイルストーン状態を更新する。

    設計原則:
    - milestone_plan（固定）は読み取りのみ
    - milestone_status（可変）のみを更新
    - 各マイルストーンは独立して評価
    """

    def update(
        self,
        milestone_plan: PlayerMilestonePlan,
        current_status: PlayerMilestoneStatus,
        new_events: List[GameEvent],
    ) -> PlayerMilestoneStatus:
        """
        新しいイベントに基づいてマイルストーン状態を更新する。

        Args:
            milestone_plan: 監視すべきマイルストーンの一覧（固定）
            current_status: 現在のマイルストーン状態（可変）
            new_events: 新しく観測されたイベント

        Returns:
            更新されたマイルストーン状態
        """
        if not milestone_plan.milestones or not new_events:
            return current_status

        # 現在の状態をコピーして更新
        updated_status = current_status.status.copy()

        for milestone in milestone_plan.milestones:
            # 既に発生済みの場合はスキップ（状態は不可逆）
            current = updated_status.get(milestone.id, "not_occurred")
            if current in ("occurred", "strong"):
                continue

            # 各イベントをチェック
            for event in new_events:
                if self._matches_trigger(milestone.trigger_condition, event):
                    # マイルストーンの重要度に応じて状態を設定
                    if milestone.importance == "high":
                        updated_status[milestone.id] = "strong"
                    else:
                        updated_status[milestone.id] = "occurred"
                    break

        return PlayerMilestoneStatus(status=updated_status)

    def _matches_trigger(self, trigger_condition: str, event: GameEvent) -> bool:
        """
        トリガ条件とイベントのマッチングを行う。

        現在はシンプルなキーワードマッチング。
        将来的にはLLMベースの評価に拡張可能。
        
        マッチングルール:
        1. イベントタイプと同じパターンカテゴリのキーワードがトリガ条件にあるかチェック
        2. より具体的なパターン（例: counter）を先にチェックして誤マッチを防ぐ
        """
        trigger_lower = trigger_condition.lower()
        event_type = event.event_type.lower()

        # イベントタイプに基づくマッチング
        # 順序が重要: より具体的なパターンを先にチェック（counter > co）
        trigger_patterns = [
            ("counter", ["対抗", "counter", "対抗co"]),
            ("co", ["co", "カミングアウト", "宣言"]),
            ("divine_result", ["占い", "divine", "結果"]),
            ("vote", ["投票", "vote"]),
            ("speak", ["発言", "speak", "議論"]),
            ("accusation", ["疑い", "accusation", "怪しい", "疑惑"]),
        ]

        # イベントタイプに最もマッチするパターンを見つける
        matched_pattern = None
        for pattern_type, keywords in trigger_patterns:
            if event_type == pattern_type:
                matched_pattern = (pattern_type, keywords)
                break

        # マッチするパターンが見つかった場合、トリガ条件にもキーワードがあるかチェック
        if matched_pattern:
            pattern_type, keywords = matched_pattern
            # 特別処理: "co" イベントの場合、"対抗" が含まれるトリガには反応しない
            if pattern_type == "co" and ("対抗" in trigger_lower or "counter" in trigger_lower):
                return False
            return any(kw in trigger_lower for kw in keywords)

        # フォールバック: トリガ条件にイベントタイプが含まれるか
        if event_type in trigger_lower:
            return True

        return False

    def initialize_status(
        self,
        milestone_plan: PlayerMilestonePlan,
    ) -> PlayerMilestoneStatus:
        """
        マイルストーン計画から初期状態を生成する。

        全てのマイルストーンを not_occurred で初期化。
        """
        status = {
            milestone.id: "not_occurred"
            for milestone in milestone_plan.milestones
        }
        return PlayerMilestoneStatus(status=status)


# --- グローバルインスタンス ---
milestone_status_updater = MilestoneStatusUpdater()
