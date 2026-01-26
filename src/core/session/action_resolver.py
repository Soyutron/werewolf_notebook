"""
ActionResolver - PlayerOutput を解釈し、副作用を決定するクラス

責務:
- PlayerOutput.action ごとの分岐ロジック
- 能力使用時の真実情報（assigned_roles）参照
- 副作用の結果を session 経由で適用

重要:
- このクラス自体は state を直接更新しない
- 副作用の確定は全て session のメソッド経由で行う

設計上の位置づけ:
- GameSession から「解釈ロジック」を分離することで、
  新しい action 追加時の変更箇所を明確化する
- session を引数として受け取ることで、
  state の唯一所有者が GameSession である原則を維持する
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict

from src.core.types import (
    PlayerName,
    RoleName,
    PlayerInput,
    PlayerOutput,
    AbilityResult,
    NoAbility,
    SeerAbility,
    WerewolfAbility,
    ThiefAbility,
    GameEvent,
)

if TYPE_CHECKING:
    from src.core.session.game_session import GameSession


class ActionResolver:
    """
    PlayerOutput を解釈し、ゲーム世界への副作用を決定するクラス。

    責務:
    - PlayerOutput.action ごとの分岐ロジック
    - 能力使用時の真実情報（assigned_roles）参照
    - 副作用の結果を session 経由で適用

    重要:
    - このクラス自体は state を直接更新しない
    - 副作用の確定は全て session のメソッド経由で行う
    """

    def __init__(self, assigned_roles: Dict[PlayerName, RoleName]):
        """
        ActionResolver を初期化する。

        Parameters
        ----------
        assigned_roles : Dict[PlayerName, RoleName]
            各プレイヤーに割り当てられた実際の役職。
            これは GM のみが知る「真実情報」であり、
            占い結果の解決などに使用される。
        """
        self.assigned_roles = assigned_roles

    def resolve(
        self,
        *,
        player: PlayerName,
        output: PlayerOutput,
        session: "GameSession",
    ) -> None:
        """
        PlayerGraph / Controller が返した PlayerOutput を解釈し、
        ゲーム世界（WorldState / PlayerState）に副作用として反映する。

        このメソッドの位置づけ:
        - 「行動の意味づけ（解釈）」と「副作用の確定」を担う
        - PlayerGraph / PlayerController 自体は副作用を一切持たない
        - GameSession が state の唯一の所有者である、という設計を守るため、
          実際の状態更新は必ず session を経由する

        設計上の重要な前提:
        - output.action は GMGraph / PlayerGraph 側で正規化された値である
        - このメソッドが呼ばれる時点で、
          ・誰が行動したか（player）
          ・どんな行動を選んだか（output）
          が確定している
        - 行動の成否判定・影響範囲の決定はこの層で行う

        拡張方針:
        - 新しい行動を追加する場合は、
          1. PlayerOutput.action に値を追加
          2. この resolve 内に分岐を追加
        - if/elif が肥大化した場合は
          action -> handler のディスパッチテーブル化も検討可能
        """
        # =========================================================
        # 各 action ごとの解釈・副作用の確定
        # =========================================================
        if output.action == "use_ability":
            self._resolve_use_ability(player, output.payload, session)
        elif output.action == "speak":
            self._resolve_speak(player, output, session)
        elif output.action == "vote":
            self._resolve_vote(player, output, session)
        elif output.action == "divine":
            self._resolve_divine(player, output, session)
        else:
            raise ValueError(f"Unknown action: {output.action}")

    def _resolve_use_ability(
        self,
        player: PlayerName,
        ability: AbilityResult,
        session: "GameSession",
    ) -> None:
        """
        Player が使用した能力を解釈し、
        ゲーム世界への副作用を確定させる。

        - GM のみが呼ぶ
        - PlayerGraph / PlayerController からは呼ばれない
        """

        match ability:
            case NoAbility():
                # 能力なし（村人など）
                session.gm_internal.night_pending.remove(player)
                return

            case SeerAbility(target=target):
                # 占いの真実を取得
                role = self.assigned_roles[target]

                # 役職定義から「占われた時の見え方」を取得
                # デフォルトは役職名そのものだが、狂人のように偽装する場合がある
                role_def = session.definition.roles.get(role)
                if role_def and role_def.divine_result_as_role:
                    visible_role = role_def.divine_result_as_role
                else:
                    visible_role = role

                # 占い結果は「占い師本人だけ」に返す情報
                session.run_player_turn(
                    player=player,
                    input=PlayerInput(
                        event=GameEvent(
                            event_type="divine_result",
                            payload={
                                "target": target,
                                "role": visible_role,
                            },
                        )
                    ),
                )
                session.gm_internal.night_pending.remove(player)
                return

            case WerewolfAbility():
                # 人狼の夜行動（将来：襲撃対象など）
                # 今は副作用なしでもOK
                session.gm_internal.night_pending.remove(player)
                return

            case ThiefAbility(target=target):
                # 怪盗の役職交換能力
                # 怪盗と対象の役職を交換する
                thief_role = self.assigned_roles[player]
                target_role = self.assigned_roles[target]
                
                print(f"[DEBUG] ActionResolver ThiefAbility: {player}(was {thief_role}) swaps with {target}(was {target_role})")
                
                # assigned_roles を更新（GM の真実情報）
                self.assigned_roles[player] = target_role
                self.assigned_roles[target] = thief_role
                
                print(f"[DEBUG] ActionResolver: After swap - {player} is now {target_role}, {target} is now {thief_role}")
                
                # 怪盗本人に役職交換結果を通知
                # （対象プレイヤーは自分の役職が変わったことを知らない）
                session.run_player_turn(
                    player=player,
                    input=PlayerInput(
                        event=GameEvent(
                            event_type="role_swapped",
                            payload={
                                "target": target,
                                "new_role": target_role,
                            },
                        )
                    ),
                )
                session.gm_internal.night_pending.remove(player)
                return

            case _:
                raise ValueError(f"Unknown AbilityResult: {ability}")

    def _resolve_speak(
        self,
        player: PlayerName,
        output: PlayerOutput,
        session: "GameSession",
    ) -> None:
        """
        発言アクションを解釈する。
        """
        event = GameEvent(
            event_type="speak",
            payload={
                "player": player,
                "text": output.payload["text"],
            },
        )
        session.world_state.pending_events.append(event)
        return

    def _resolve_vote(
        self,
        player: PlayerName,
        output: PlayerOutput,
        session: "GameSession",
    ) -> None:
        """
        投票アクションを解釈する。
        """
        target = output.payload["target"]
        session.gm_internal.votes[player] = target
        
        # 投票イベントを積む（全員に公開）
        event = GameEvent(
            event_type="vote",
            payload={
                "voter": player,
                "target": target,
            },
        )
        session.world_state.pending_events.append(event)

        session.gm_internal.vote_pending.remove(player)
        return

    def _resolve_divine(
        self,
        player: PlayerName,
        output: PlayerOutput,
        session: "GameSession",
    ) -> None:
        """
        占いアクションを解釈する。
        （現時点では未実装のプレースホルダ）
        """
        # 将来実装予定
        pass
