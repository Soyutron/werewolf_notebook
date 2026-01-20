# src/core/roles/__init__.py
"""
役職管理モジュール

役割:
- 役職の一元管理
- 役職定義の動的登録・取得
- 新規役職追加時の拡張ポイント提供
"""

from .role_registry import (
    RoleConfig,
    RoleRegistry,
    role_registry,
    get_all_role_names,
    get_role_config,
    get_role_advice,
    get_role_display_name,
)

__all__ = [
    "RoleConfig",
    "RoleRegistry",
    "role_registry",
    "get_all_role_names",
    "get_role_config",
    "get_role_advice",
    "get_role_display_name",
]
