# src/game/player/belief_utils.py
"""
role_beliefs を活用するための共通ユーティリティ関数。

発言生成・レビュー・リファインの各フェーズで
一貫した belief 分析を行うために使用する。
"""
from typing import Dict

from src.core.types import PlayerMemory, PlayerName, RoleProb


# 役職名の日本語マッピング
ROLE_NAMES_JA = {
    "villager": "村人",
    "seer": "占い師",
    "werewolf": "人狼",
    "madman": "狂人",
}

# 役職ペアごとの判断ガイド
ROLE_IMPLICATIONS = {
    ("werewolf", "madman"): "人狼なら今日処理必須、狂人なら吊り損",
    ("madman", "werewolf"): "狂人なら吊り損、人狼なら今日処理必須",
    ("werewolf", "villager"): "人狼なら処理必須、村人なら吊りは致命的",
    ("villager", "werewolf"): "村人なら吊りは致命的、人狼なら処理必須",
    ("seer", "madman"): "本物占い師なら信用すべき、狂人なら偽情報",
    ("madman", "seer"): "狂人なら偽情報、本物占い師なら信用すべき",
    ("seer", "werewolf"): "本物占い師なら信用すべき、人狼なら騙り",
    ("werewolf", "seer"): "人狼の騙りか本物占い師か見極めが必要",
    ("villager", "madman"): "村人か狂人かで投票価値が変わる",
    ("madman", "villager"): "狂人か村人かで投票価値が変わる",
    ("villager", "seer"): "村人か占い師かで発言の信頼度が変わる",
    ("seer", "villager"): "占い師か村人かで発言の信頼度が変わる",
}

# 役職ごとの行動ガイド
ROLE_GUIDANCE = {
    "seer": "事実（占い結果）を共有し、矛盾を指摘すべき。自信を持って発言する。",
    "werewolf": "疑いをそらし、他者に投票を誘導すべき。自分を疑わせる発言は避ける。",
    "madman": "混乱を作り、偽情報を流すべき。村を助ける発言は避ける。",
    "villager": "観察と分析に基づき、人狼を見つけるべき。根拠なく他者を庇わない。",
}


def build_belief_analysis_section(memory: PlayerMemory) -> str:
    """
    role_beliefs を分析可能な形式に変換し、
    発言で役職推定を明示するためのサマリーを構築する。
    
    各プレイヤーについて上位2つの役職候補を抽出し、
    判断に使いやすい形式で提示する。
    """
    analysis_lines = []
    
    for player, belief in memory.role_beliefs.items():
        if player == memory.self_name:
            continue  # 自分自身はスキップ
        
        # 確率が高い順にソート
        sorted_roles = sorted(
            belief.probs.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # 上位2つの役職候補を抽出（15%以上のもののみ）
        top_roles = [(role, prob) for role, prob in sorted_roles if prob >= 0.15][:2]
        
        if len(top_roles) >= 2:
            role1, prob1 = top_roles[0]
            role2, prob2 = top_roles[1]
            role1_ja = ROLE_NAMES_JA.get(role1, role1)
            role2_ja = ROLE_NAMES_JA.get(role2, role2)
            
            # 役職ごとの判断ガイドを追加
            implications = get_role_implications(role1, role2)
            
            analysis_lines.append(
                f"- {player}: {role1_ja}({prob1:.0%}) or {role2_ja}({prob2:.0%})\n"
                f"  → {implications}"
            )
        elif len(top_roles) == 1:
            role1, prob1 = top_roles[0]
            role1_ja = ROLE_NAMES_JA.get(role1, role1)
            analysis_lines.append(f"- {player}: likely {role1_ja}({prob1:.0%})")
    
    if not analysis_lines:
        return "(No strong beliefs about other players yet)"
    
    return "\n".join(analysis_lines)


def get_role_implications(role1: str, role2: str) -> str:
    """
    2つの役職候補がある場合の判断ガイドを生成する。
    """
    return ROLE_IMPLICATIONS.get(
        (role1, role2), 
        f"{role1}と{role2}の可能性を考慮して判断"
    )


def get_role_guidance(role: str) -> str:
    """
    役職に応じた行動ガイドを取得する。
    """
    return ROLE_GUIDANCE.get(role, "状況に応じて判断すべき")


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


def get_trusted_players(memory: PlayerMemory, threshold: float = 0.6) -> list[tuple[str, float]]:
    """
    村人・占い師として信頼されているプレイヤーを取得する。
    
    Returns:
        List of (player_name, trust_probability) tuples
    """
    trusted = []
    
    for player, belief in memory.role_beliefs.items():
        if player == memory.self_name:
            continue
        
        villager_prob = belief.probs.get("villager", 0)
        seer_prob = belief.probs.get("seer", 0)
        ally_prob = villager_prob + seer_prob
        
        if ally_prob >= threshold:
            trusted.append((player, ally_prob))
    
    return sorted(trusted, key=lambda x: x[1], reverse=True)
