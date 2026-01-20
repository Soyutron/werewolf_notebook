# src/game/player/belief_utils.py
"""
role_beliefs を活用するための共通ユーティリティ関数。

発言生成・レビュー・リファインの各フェーズで
一貫した belief 分析を行うために使用する。
LLMが自然に解釈できる文脈表現への変換を担当する。
"""

from src.core.types import PlayerMemory
from src.core.roles import get_role_display_name

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
        top_role_ja = get_role_display_name(top_role, "ja")
        
        # 状況の言語化
        if top_prob >= 0.6:
            # 確信度が高い場合
            if top_role in ["werewolf", "madman"]:
                suspicious.append(f"{player} は {top_role_ja} の可能性が高い ({top_prob:.0%})")
            else:
                trusted.append(f"{player} は {top_role_ja} と思われる ({top_prob:.0%})")
        
        elif top_prob >= 0.4:
            # ある程度傾向が見える場合
            second_role, second_prob = sorted_roles[1]
            second_role_ja = get_role_display_name(second_role, "ja")
            uncertain.append(f"{player}: {top_role_ja} の傾向 ({top_prob:.0%}), 次点 {second_role_ja} ({second_prob:.0%})")
            
        else:
            # よくわからない場合
            uncertain.append(f"{player}: 不明 (最有力: {top_role_ja} {top_prob:.0%})")

    # セクション構築
    if trusted:
        analysis_lines.append("信頼できるプレイヤー:")
        for line in trusted:
            analysis_lines.append(f"- {line}")
    
    if suspicious:
        analysis_lines.append("疑わしいプレイヤー:")
        for line in suspicious:
            analysis_lines.append(f"- {line}")
            
    if uncertain:
        analysis_lines.append("判断保留 / 要観察:")
        for line in uncertain:
            analysis_lines.append(f"- {line}")
    
    if not analysis_lines:
        return "(他プレイヤーに関する確信はまだありません。観察を続けてください。)"
    
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
