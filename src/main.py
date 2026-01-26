"""
FastAPI アプリケーション - メインファイル

責務:
- FastAPI アプリケーション初期化
- ルーター登録
- ミドルウェア設定
- サーバー起動
"""

from dotenv import load_dotenv
import os

# .env ファイルから環境変数を読み込む
load_dotenv()

from fastapi import FastAPI

from src.app.controllers import game_router


# =========================================================
# FastAPI アプリケーション初期化
# =========================================================
app = FastAPI(
    title="AI Werewolf Game API",
    description="ワンナイト人狼ゲームセッション実行 API",
    version="1.0.0",
)

# =========================================================
# ルーター登録
# =========================================================
app.include_router(game_router)

# =========================================================
# サーバー起動用（開発用）
# =========================================================
if __name__ == "__main__":
    import uvicorn

    print("Starting FastAPI server...")
    print("Access the API at: http://localhost:8000")
    print("Interactive docs at: http://localhost:8000/docs")

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # コード変更時に自動リロード
        log_level="info",
    )
