from typing import TypedDict, List, Dict, Optional

class RoleDefinition(TypedDict):
    name: str
    description: str
    team: str

class GameDefinition(TypedDict):
    roles: Dict[str, RoleDefinition]
    role_distribution: List[str] 
    win_conditions: Dict[str, str]
    player_count: int
    phases: List[str]
    rules: List[str] 

class PlayerMemory(TypedDict):
    self_name: str
    self_role: str
    beliefs: Dict[str, str]        # 他人の役職についての信念
    suspicion: Dict[str, float]    # 疑い度
    history: List[dict]            # 観測したイベント履歴

class PlayerInput(TypedDict, total=False):
    event: dict            # 起きた出来事（speech / vote_result など）
    request: dict          # {"action": "speak"} / {"action": "vote"}

class PlayerState(TypedDict):
    memory: PlayerMemory
    input: PlayerInput
    output: Optional[dict]   # {"message": "..."} / {"vote": "..."} / None