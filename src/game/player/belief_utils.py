# src/game/player/belief_utils.py
"""
role_beliefs を活用するための共通ユーティリティ関数。

発言生成・レビュー・リファインの各フェーズで
一貫した belief 分析を行うために使用する。
LLMが自然に解釈できる文脈表現への変換を担当する。
"""

from src.core.types import PlayerMemory

# 役職名の日本語マッピング
ROLE_NAMES_JA = {
    "villager": "村人",
    "seer": "占い師",
    "werewolf": "人狼",
    "madman": "狂人",
}


def build_belief_analysis_section(memory: PlayerMemory) -> str:
    """
    role_beliefs を分析し、LLMが自然に解釈できるサマリーを構築する。
    
    内部データ構造をそのまま渡すのではなく、
    推論に必要な情報（誰を疑っているか、誰を信じているか）を
    自然言語で整理して提示する。
    """
    analysis_lines = []
    
    # 信頼・疑惑のカテゴリ分け
    trusted = []
    suspicious = []
    uncertain = []
    
    for player, belief in memory.role_beliefs.items():
        if player == memory.self_name:
            continue  # 自分自身はスキップ
        
        # 確率が高い順にソート
        sorted_roles = sorted(
            belief.probs.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        top_role, top_prob = sorted_roles[0]
        top_role_ja = ROLE_NAMES_JA.get(top_role, top_role)
        
        # 状況の言語化
        if top_prob >= 0.6:
            # 確信度が高い場合
            if top_role in ["werewolf", "madman"]:
                suspicious.append(f"{player} is likely {top_role_ja} ({top_prob:.0%})")
            else:
                trusted.append(f"{player} seems to be {top_role_ja} ({top_prob:.0%})")
        
        elif top_prob >= 0.4:
            # ある程度傾向が見える場合
            second_role, second_prob = sorted_roles[1]
            second_role_ja = ROLE_NAMES_JA.get(second_role, second_role)
            uncertain.append(f"{player}: Leaning {top_role_ja} ({top_prob:.0%}), maybe {second_role_ja} ({second_prob:.0%})")
            
        else:
            # よくわからない場合
            uncertain.append(f"{player}: Unclear (top: {top_role_ja} {top_prob:.0%})")

    # セクション構築
    if trusted:
        analysis_lines.append("Trusted Players:")
        for line in trusted:
            analysis_lines.append(f"- {line}")
    
    if suspicious:
        analysis_lines.append("Suspicious Players:")
        for line in suspicious:
            analysis_lines.append(f"- {line}")
            
    if uncertain:
        analysis_lines.append("Uncertain / Observation Needed:")
        for line in uncertain:
            analysis_lines.append(f"- {line}")
    
    if not analysis_lines:
        return "(No strong beliefs regarding other players yet. Continue observing.)"
    
    return "\n".join(analysis_lines)


def get_high_suspicion_players(memory: PlayerMemory, threshold: float = 0.5) -> list[tuple[str, float]]:
    """
    人狼・狂人として高い確率で疑われているプレイヤーを取得する。
    
    Returns:
        List of (player_name, suspicion_probability) tuples
    """
    suspicious = []
    
    for player, belief in memory.role_beliefs.items():
        if player == memory.self_name:
            continue
        
        werewolf_prob = belief.probs.get("werewolf", 0)
        madman_prob = belief.probs.get("madman", 0)
        enemy_prob = werewolf_prob + madman_prob
        
        if enemy_prob >= threshold:
            suspicious.append((player, enemy_prob))
    
    return sorted(suspicious, key=lambda x: x[1], reverse=True)
