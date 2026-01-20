# src/game/log_summarizer.py
"""
ゲームログの差分要約を行うモジュール。

責務:
- 前回の要約以降に追加されたイベントのみを対象とした差分要約
- Player用とGM用で共通のロジックを提供
"""

from typing import Optional

from src.core.llm.prompts.roles import get_role_name_ja

from src.core.llm.client import LLMClient
from src.core.memory.log_summary import LogSummaryOutput
from src.core.types import GameEvent


LOG_SUMMARY_SYSTEM_PROMPT = """あなたは人狼ゲームのログ要約システムです。

# 役割
ゲームの進行ログを簡潔かつ情報密度の高い要約に変換します。

# 要約のルール

## 必ず含める情報
1. **CO情報**: 誰がどの役職をCOしたか（例: 「太郎は占い師CO」）
2. **占い結果**: 誰を占い、結果は何だったか（例: 「太郎→花子=白」）
3. **投票傾向**: 誰が誰への投票を示唆しているか
4. **対立構造**: 誰と誰が対立しているか
5. **重要な発言**: ゲームの勝敗に影響する重要な主張

## 省略してよい情報
- 単なる挨拶や相槌
- 重複する情報
- ゲームに直接関係のない雑談

## 出力形式
- 箇条書きで簡潔に
- 時系列順で整理
- 人名は省略せず明記

# 差分要約について
- 「既存の要約」と「新しいイベント」が与えられます
- 既存の要約を保持しつつ、新しい情報を追加・統合してください
- 矛盾する情報がある場合は最新の情報を優先してください
"""


def _format_events_for_summary(events: list[GameEvent]) -> str:
    """イベントリストを要約用テキストに整形する"""
    lines = []
    for event in events:
        if event.event_type == "speak":
            player = event.payload.get("player", "?")
            text = event.payload.get("text", "")
            lines.append(f"[発言] {player}: {text}")
        elif event.event_type == "gm_comment":
            speaker = event.payload.get("speaker", "?")
            text = event.payload.get("text", "")
            lines.append(f"[GM→{speaker}] {text}")
        elif event.event_type == "divine_result":
            target = event.payload.get("target", "?")
            # payloadには "role" (実体) または "result" (互換性) が入っている
            result_role = event.payload.get("role") or event.payload.get("result", "?")
            # 日本語名に変換（変換できない場合はそのまま）
            result_ja = get_role_name_ja(result_role)
            lines.append(f"[占い結果] {target} = {result_ja}")
        elif event.event_type == "phase_start":
            phase = event.payload.get("phase", "?")
            lines.append(f"[フェーズ開始] {phase}")
        elif event.event_type == "vote":
            voter = event.payload.get("voter", "?")
            target = event.payload.get("target", "?")
            lines.append(f"[投票] {voter} → {target}")
        else:
            lines.append(f"[{event.event_type}] {event.payload}")
    return "\n".join(lines)


class LogSummarizer:
    """
    ゲームログの差分要約を行うクラス。
    
    設計方針:
    - 前回の要約以降に追加されたイベントのみを対象とする
    - 既存の要約に新しい情報を追加する形式
    - Player用とGM用で共通のロジックを使用
    """
    
    def __init__(self, llm: LLMClient[LogSummaryOutput]):
        self.llm = llm
    
    def summarize_incremental(
        self,
        *,
        events: list[GameEvent],
        previous_summary: str,
        last_index: int,
    ) -> tuple[str, int]:
        """
        差分要約を実行する。
        
        Parameters:
            events: 全イベントリスト
            previous_summary: 前回までの要約テキスト
            last_index: 前回要約済みのインデックス（ここ以降が未処理）
        
        Returns:
            tuple[str, int]: (更新された要約, 新しいカーソル位置)
        """
        # 差分イベントを取得
        new_events = events[last_index:]
        
        # 新しいイベントがなければそのまま返す
        if not new_events:
            return previous_summary, last_index
        
        # プロンプトを構築
        new_events_text = _format_events_for_summary(new_events)
        
        prompt = self._build_prompt(
            previous_summary=previous_summary,
            new_events_text=new_events_text,
            new_event_count=len(new_events),
        )
        
        try:
            result: LogSummaryOutput = self.llm.generate(
                system=LOG_SUMMARY_SYSTEM_PROMPT,
                prompt=prompt,
            )
            
            new_cursor = len(events)
            
            print(f"[LogSummarizer] Summarized {len(new_events)} new events")
            print(f"[LogSummarizer] Key events: {result.key_events}")
            
            return result.updated_summary, new_cursor
            
        except Exception as e:
            print(f"[LogSummarizer] Failed to summarize: {e}")
            # 失敗した場合は前回の要約をそのまま返す
            return previous_summary, last_index
    
    def _build_prompt(
        self,
        *,
        previous_summary: str,
        new_events_text: str,
        new_event_count: int,
    ) -> str:
        """要約用のプロンプトを構築する"""
        
        existing_section = ""
        if previous_summary:
            existing_section = f"""
## 既存の要約
{previous_summary}
"""
        else:
            existing_section = """
## 既存の要約
（まだ要約はありません。新しくゲームが始まりました。）
"""
        
        return f"""
以下のゲームログを要約してください。

{existing_section}

## 新しいイベント（{new_event_count}件）
{new_events_text}

上記の情報を統合して、更新された要約を作成してください。
"""


# --- ファクトリ関数 ---
def create_log_summarizer() -> LogSummarizer:
    """LogSummarizerのインスタンスを作成する"""
    from src.config.llm import create_log_summarizer_llm
    return LogSummarizer(llm=create_log_summarizer_llm())


# --- グローバルインスタンス（遅延初期化） ---
_log_summarizer: Optional[LogSummarizer] = None


def get_log_summarizer() -> LogSummarizer:
    """シングルトンのLogSummarizerを取得する"""
    global _log_summarizer
    if _log_summarizer is None:
        _log_summarizer = create_log_summarizer()
    return _log_summarizer
