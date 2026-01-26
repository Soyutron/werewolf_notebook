"""
ゲームシリアライザー

責務:
- GameSession の各コンポーネントを辞書に変換
- 辞書からドメインモデルへの復元
"""

from typing import Dict, Any
from src.core.types import (
    PlayerState,
    WorldState,
    GameDefinition,
    GameEvent,
    PlayerRequest,
    RoleProb,
    PlayerMemory,
    PlayerInput,
    PlayerOutput,
    PlayerInternalState,
    RoleDefinition,
    GMInternalState,
)


class GameSerializer:
    """ゲーム状態のシリアライズ/デシリアライズ"""

    @staticmethod
    def serialize_world_state(world_state: WorldState) -> Dict[str, Any]:
        """WorldState を辞書に変換"""
        return {
            "phase": world_state.phase,
            "players": list(world_state.players),
            "public_events": [
                {
                    "event_type": event.event_type,
                    "payload": event.payload,
                }
                for event in world_state.public_events
            ],
            "pending_events": [
                {
                    "event_type": event.event_type,
                    "payload": event.payload,
                }
                for event in world_state.pending_events
            ],
        }

    @staticmethod
    def serialize_game_definition(definition: GameDefinition) -> Dict[str, Any]:
        """GameDefinition を辞書に変換"""
        return {
            "roles": {
                role_name: {
                    "day_side": role_def.day_side,
                    "win_side": role_def.win_side,
                    "ability_type": role_def.ability_type,
                    "divine_result_as_role": role_def.divine_result_as_role,
                }
                for role_name, role_def in definition.roles.items()
            },
            "role_distribution": list(definition.role_distribution),
            "phases": list(definition.phases),
        }

    @staticmethod
    def serialize_player_state(player_state: PlayerState) -> Dict[str, Any]:
        """PlayerState を辞書に変換"""
        memory = player_state["memory"]
        return {
            "memory": {
                "self_name": memory.self_name,
                "self_role": memory.self_role,
                "players": list(memory.players),
                "observed_events": [
                    {"event_type": e.event_type, "payload": e.payload}
                    for e in memory.observed_events
                ],
                "role_beliefs": {
                    player: belief.probs
                    for player, belief in memory.role_beliefs.items()
                },
                "history": [
                    {
                        "type": type(item).__name__,
                        "content": item.model_dump() if hasattr(item, "model_dump") else str(item),
                    }
                    for item in memory.history
                ],
                "strategy_plan": (
                    memory.strategy_plan.model_dump() if memory.strategy_plan else None
                ),
                "log_summary": memory.log_summary,
                "last_summarized_event_index": memory.last_summarized_event_index,
            },
            "input": {
                "request": (
                    {
                        "request_type": player_state["input"].request.request_type,
                        "payload": player_state["input"].request.payload,
                    }
                    if player_state["input"].request
                    else None
                ),
                "event": (
                    {
                        "event_type": player_state["input"].event.event_type,
                        "payload": player_state["input"].event.payload,
                    }
                    if player_state["input"].event
                    else None
                ),
            },
            "output": (
                {
                    "action": player_state["output"].action,
                    "payload": player_state["output"].payload,
                }
                if player_state["output"]
                else None
            ),
        }

    @staticmethod
    def deserialize_game_definition(data: Dict[str, Any]) -> GameDefinition:
        """辞書から GameDefinition を復元"""
        roles = {
            name: RoleDefinition(**role_def)
            for name, role_def in data.get("roles", {}).items()
        }
        return GameDefinition(
            roles=roles,
            role_distribution=data.get("role_distribution", []),
            phases=data.get("phases", []),
        )

    @staticmethod
    def deserialize_world_state(data: Dict[str, Any]) -> WorldState:
        """辞書から WorldState を復元"""
        return WorldState(
            phase=data["phase"],
            players=data.get("players", []),
            public_events=[GameEvent(**e) for e in data.get("public_events", [])],
            pending_events=[GameEvent(**e) for e in data.get("pending_events", [])],
            result=data.get("result"),
        )

    @staticmethod
    def deserialize_player_state(data: Dict[str, Any]) -> PlayerState:
        """辞書から PlayerState を復元"""
        memory_data = data.get("memory", {})

        # GameEvent / RoleProb はモデルに戻す
        observed_events = [GameEvent(**e) for e in memory_data.get("observed_events", [])]
        role_beliefs = {
            player: RoleProb(probs=belief)
            for player, belief in memory_data.get("role_beliefs", {}).items()
        }

        # 履歴・戦略などは最低限復元（足りない場合は空にして継続可能にする）
        history = []
        strategy_plan = None

        memory = PlayerMemory(
            self_name=memory_data.get("self_name"),
            self_role=memory_data.get("self_role"),
            players=memory_data.get("players", []),
            observed_events=observed_events,
            role_beliefs=role_beliefs,
            history=history,
            strategy_plan=strategy_plan,
            log_summary=memory_data.get("log_summary", ""),
            last_summarized_event_index=memory_data.get("last_summarized_event_index", 0),
            milestone_status=memory_data.get("milestone_status"),
            policy_weights=memory_data.get("policy_weights"),
        )

        input_data = data.get("input", {})
        player_input = PlayerInput(
            request=PlayerRequest(**input_data["request"]) if input_data.get("request") else None,
            event=GameEvent(**input_data["event"]) if input_data.get("event") else None,
        )

        output_data = data.get("output")
        player_output = (
            PlayerOutput(
                action=output_data.get("action"),
                payload=output_data.get("payload"),
            )
            if output_data
            else None
        )

        internal = PlayerInternalState()

        # TypedDict は辞書として初期化
        player_state: PlayerState = {
            "memory": memory,
            "input": player_input,
            "output": player_output,
            "internal": internal,
            "game_def": None,  # GameSession から後で注入される
        }
        return player_state

    @staticmethod
    def deserialize_gm_internal(data: Dict[str, Any]) -> GMInternalState:
        """辞書から GMInternalState を復元"""
        return GMInternalState(**data)
