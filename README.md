uv run ruff check src
uv run ruff format src

🧠 プレイヤー側（主観・認知）

PlayerMemory

PlayerInput

PlayerOutput

PlayerState

🌍 ゲーム全体（客観・世界）

GameDefinition

Phase

役職定義・配役ルール

Phase 0: 仕様を「これ以上増やさない」と決める
Phase 1: GMなし・Player単体で動かす
Phase 2: GM最小実装（if文GM）
Phase 3: イベント駆動ループ完成
Phase 4: LangGraph化（PlayerGraph）
Phase 5: GMGraph化
Phase 6: 戦略・推論を賢くする
Phase 7: UI / 人間参加 / 評価

game/
 ├─ one_night.py          # ⭐ 起動点（main）
 ├─ setup/
 │   ├─ __init__.py
 │   ├─ players.py        # プレイヤー一覧生成
 │   ├─ roles.py          # 役職配布ロジック
 │   ├─ memory.py         # PlayerMemory 初期化 ← 今の関数
 │   └─ state.py          # PlayerState 初期化
 ├─ gm/
 │   └─ __init__.py       # （将来 GMGraph が入る）
 └─ player/
     └─ graph.py