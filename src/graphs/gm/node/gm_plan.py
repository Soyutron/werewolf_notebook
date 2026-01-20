from src.core.types import GMGraphState
from src.game.gm.gm_plan_generator import GMPlanGenerator
from src.config.llm import create_gm_plan_llm


def gm_plan_node(state: GMGraphState) -> GMGraphState:
    """
    夜フェーズにおける進行計画生成ノード。
    
    責務:
    - まだ進行計画が生成されていなければ、生成して internal state に保存する。
    - 既に存在する場合はスキップする（冪等性）。
    """
    internal = state["internal"]
    world_state = state["world_state"]
    game_def = state["game_def"]

    # 既に計画があれば何もしない
    if internal.progression_plan:
        return state

    # LLMコントローラの初期化
    llm = create_gm_plan_llm()
    generator = GMPlanGenerator(llm)

    # 計画生成
    plan = generator.generate(world_state, game_def)

    # State 更新
    internal.progression_plan = plan
    
    # デバッグログ
    print(f"--- GM Progression Plan Generated ---\n{plan.get_summary_markdown()}\n-------------------------------------")

    return state
