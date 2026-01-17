uv run ruff check src
uv run ruff format src

du -sh ~/.config/Antigravity/Cache
du -sh ~/.config/Antigravity/CachedData
du -sh ~/.config/Antigravity/Service\ Worker

rm -rf ~/.config/Antigravity/Service\ Worker
rm -rf ~/.config/Antigravity/Cache
rm -rf ~/.config/Antigravity/CachedData


vllm serve google/gemma-3-12b-it \
  --dtype bfloat16 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9

vllm serve Qwen/Qwen2.5-14B-Instruct \
  --quantization awq \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.95

vllm serve Qwen/Qwen2.5-14B-Instruct \
  --dtype bfloat16 \
  --max-model-len 2048 \
  --gpu-memory-utilization 0.95 \
  --disable-torch-compile \
  --trust-remote-code


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

LLM が「自分なりに考え、迷い、振る舞っているように見える」マルチエージェントゲームを成立させること

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


┌───────────────────┐
│   GameSession      │  ← オーケストレーター（通常の Python）
│  ・進行管理        │
│  ・dispatch        │
│  ・保存 / 待機     │
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│   GMGraph          │  ← LangGraph
│  ・フェーズ判断    │
│  ・次の指示決定    │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ PlayerGraph        │  ← LangGraph
│  ・思考            │
│  ・意思決定        │
└───────────────────┘
GameSession          GMGraph             PlayerGraph
     |                  |                    |
     | invoke(gm_state) |                    |
     |----------------->|                    |
     |                  | 判断               |
     |                  | (誰に何をさせるか) |
     |                  |                    |
     |  GMDecision      |                    |
     |<-----------------|                    |
     |                  |                    |
     | run_player_turn  |                    |
     |-------------------------------------->|
     |                  |                    | 思考
     |                  |                    | (PlayerState更新)
     |                  |                    |
     | PlayerOutput     |                    |
     |<--------------------------------------|
     |                  |                    |
     | public_events更新 |                    |
     |------------------|                    |