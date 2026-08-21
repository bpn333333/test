"""設定の読み込み。

優先順位: CLI引数 > 環境変数 > config.yaml > 既定値
APIキーは config.yaml に直接書かず、環境変数(.env)で渡すことを推奨。
"""

from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

DEFAULTS: dict[str, Any] = {
    "fx": {
        # 1 CNY = ? JPY。source: fixed / frankfurter
        "source": "fixed",
        "cny_jpy": 21.0,
        "buffer_pct": 2.0,  # 為替変動ぶんの安全マージン(%)
    },
    "cost": {
        # item   = 商品代金だけを円換算する(既定)
        # landed = 送料・代行手数料・税まで積み上げる
        "mode": "item",
        # 以下は mode: landed のときだけ使う
        # 中国国内送料(1商品あたり・元)。代行業者に集約する前提の概算
        "china_domestic_cny": 8.0,
        # 代行手数料。率と最低額の大きい方を採用
        "agent_fee_pct": 5.0,
        "agent_fee_min_jpy": 200.0,
        # 国際送料: 重量課金(円/kg) + 1商品あたり固定費
        "intl_shipping_jpy_per_kg": 1000.0,
        "intl_shipping_min_jpy": 150.0,
        "handling_jpy_per_item": 50.0,
        # 容積重量: (縦cm x 横cm x 高さcm) / divisor。実重量と比べて重い方を課金重量とする
        "volumetric_divisor": 6000.0,
        # 輸入時にかかる税(関税+消費税)の概算率。原価(商品+送料)に対して掛ける
        "import_tax_pct": 0.0,
        # 重量が取得できなかった場合に使う既定値(g)
        "default_weight_g": 500.0,
    },
    "rakuten": {
        "application_id": None,
        "affiliate_id": None,
        "hits": 5,
        # ランキングを引く際の集計期間: realtime / daily / weekly / monthly
        "ranking_period": "realtime",
        "ranking_pages": 1,  # 1ページ30件。増やすと深いランクまで拾える
        "enabled": True,
    },
    "amazon": {
        "access_key": None,
        "secret_key": None,
        "partner_tag": None,
        "host": "webservices.amazon.co.jp",
        "region": "us-west-2",
        "marketplace": "www.amazon.co.jp",
        "enabled": True,
    },
    "taobao": {
        "app_key": None,
        "app_secret": None,
        "endpoint": "https://eco.taobao.com/router/rest",
        # API未設定でも watchlist.csv の手入力値で動く
        "enabled": True,
    },
    "cache": {
        "enabled": True,
        "dir": "~/.cache/pricediff",
        "ttl_seconds": 21600,  # 6時間
    },
    "output": {
        "sort": "diff",  # diff / ratio / rank / name
        "min_diff_jpy": None,
        "max_rank": None,
        "top": None,
    },
    "request": {
        "timeout": 20,
        "retries": 3,
        "backoff": 2.0,
        "interval": 1.0,  # 連続リクエストの間隔(秒)。API側のレート制限対策
        "user_agent": "pricediff/1.0 (+https://github.com/bpn333333/test)",
    },
}

# 環境変数 -> 設定パス のマッピング
ENV_MAP = {
    "RAKUTEN_APPLICATION_ID": ("rakuten", "application_id"),
    "RAKUTEN_AFFILIATE_ID": ("rakuten", "affiliate_id"),
    "AMAZON_ACCESS_KEY": ("amazon", "access_key"),
    "AMAZON_SECRET_KEY": ("amazon", "secret_key"),
    "AMAZON_PARTNER_TAG": ("amazon", "partner_tag"),
    "TAOBAO_APP_KEY": ("taobao", "app_key"),
    "TAOBAO_APP_SECRET": ("taobao", "app_secret"),
    "PRICEDIFF_FX_CNY_JPY": ("fx", "cny_jpy"),
}

_NUMERIC_KEYS = {"cny_jpy"}


class Config:
    def __init__(self, data: dict[str, Any]):
        self._data = data

    # --- アクセサ ----------------------------------------------------
    def section(self, name: str) -> dict[str, Any]:
        return self._data.get(name, {})

    def get(self, *path: str, default: Any = None) -> Any:
        node: Any = self._data
        for key in path:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node if node is not None else default

    def set(self, value: Any, *path: str) -> None:
        node = self._data
        for key in path[:-1]:
            node = node.setdefault(key, {})
        node[path[-1]] = value

    def as_dict(self) -> dict[str, Any]:
        return copy.deepcopy(self._data)

    # --- 判定 --------------------------------------------------------
    def has_rakuten_api(self) -> bool:
        return bool(self.get("rakuten", "enabled") and self.get("rakuten", "application_id"))

    def has_amazon_api(self) -> bool:
        return bool(
            self.get("amazon", "enabled")
            and self.get("amazon", "access_key")
            and self.get("amazon", "secret_key")
            and self.get("amazon", "partner_tag")
        )

    def has_taobao_api(self) -> bool:
        return bool(
            self.get("taobao", "enabled")
            and self.get("taobao", "app_key")
            and self.get("taobao", "app_secret")
        )


def _deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        elif value is not None:
            out[key] = value
    return out


def load_dotenv(path: Path) -> None:
    """依存を増やさないための最小限の .env ローダ。既存の環境変数は上書きしない。"""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def load_config(path: Optional[str] = None, *, use_env: bool = True) -> Config:
    data = copy.deepcopy(DEFAULTS)

    cfg_path = Path(path).expanduser() if path else Path("config.yaml")
    if cfg_path.is_file():
        if yaml is None:  # pragma: no cover
            raise RuntimeError("config.yaml を読むには PyYAML が必要です: pip install pyyaml")
        loaded = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        data = _deep_merge(data, loaded)
    elif path:
        raise FileNotFoundError(f"設定ファイルが見つかりません: {cfg_path}")

    if use_env:
        load_dotenv(Path(".env"))
        for env_key, (section, key) in ENV_MAP.items():
            value = os.environ.get(env_key)
            if value:
                data.setdefault(section, {})[key] = (
                    float(value) if key in _NUMERIC_KEYS else value
                )

    return Config(data)
