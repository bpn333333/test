"""追跡リスト(watchlist)の読み込み。

CSV(Excel/スプレッドシートからの書き出し)と YAML の両方に対応。
最低限 name と、淘宝側の価格情報(taobao_price_cny または taobao_url)があればよい。
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Optional

from .models import WatchItem

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

FIELDS = {f.name for f in WatchItem.__dataclass_fields__.values()}  # type: ignore[attr-defined]
FLOAT_FIELDS = {"taobao_price_cny", "weight_g", "amazon_price_jpy", "rakuten_price_jpy"}
INT_FIELDS = {"amazon_rank", "rakuten_rank"}

# 日本語ヘッダで書かれていても読めるようにする
HEADER_ALIASES = {
    "商品名": "name",
    "名前": "name",
    "淘宝url": "taobao_url",
    "淘宝リンク": "taobao_url",
    "淘宝価格": "taobao_price_cny",
    "淘宝価格_元": "taobao_price_cny",
    "重さ": "weight_g",
    "重量": "weight_g",
    "重量g": "weight_g",
    "asin": "amazon_asin",
    "amazonキーワード": "amazon_keyword",
    "楽天キーワード": "rakuten_keyword",
    "楽天ジャンルid": "rakuten_genre_id",
    "amazon価格": "amazon_price_jpy",
    "楽天価格": "rakuten_price_jpy",
    "amazonランキング": "amazon_rank",
    "楽天ランキング": "rakuten_rank",
    "備考": "note",
    "メモ": "note",
}


class WatchlistError(ValueError):
    pass


def _normalize_header(header: str) -> str:
    key = (header or "").strip().lower().replace(" ", "").replace("(", "").replace(")", "")
    key = key.replace("（", "").replace("）", "").replace("/", "_").replace("-", "_")
    if key in HEADER_ALIASES:
        return HEADER_ALIASES[key]
    return key


def _coerce(field: str, value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
    if field in FLOAT_FIELDS:
        try:
            return float(re.sub(r"[,¥￥元円\s]", "", str(value)))
        except ValueError as exc:
            raise WatchlistError(f"{field} を数値として読めません: {value!r}") from exc
    if field in INT_FIELDS:
        try:
            return int(float(re.sub(r"[,位#\s]", "", str(value))))
        except ValueError as exc:
            raise WatchlistError(f"{field} を整数として読めません: {value!r}") from exc
    return str(value)


def _build_item(row: dict[str, Any], index: int) -> Optional[WatchItem]:
    data: dict[str, Any] = {}
    for raw_key, raw_value in row.items():
        if raw_key is None:
            continue
        field = _normalize_header(str(raw_key))
        if field in FIELDS:
            data[field] = _coerce(field, raw_value)

    name = data.get("name")
    if not name:
        # 全項目が空の行(CSVの末尾など)は黙って読み飛ばす
        if not any(v for v in data.values()):
            return None
        raise WatchlistError(f"{index}行目: name(商品名)が空です")

    data.setdefault("key", None)
    if not data.get("key"):
        data["key"] = f"item{index:03d}"
    return WatchItem(**{k: v for k, v in data.items() if k in FIELDS})


def load_watchlist(path: str | Path) -> list[WatchItem]:
    file_path = Path(path).expanduser()
    if not file_path.is_file():
        raise WatchlistError(f"追跡リストが見つかりません: {file_path}")

    if file_path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:  # pragma: no cover
            raise WatchlistError("YAML を読むには PyYAML が必要です")
        payload = yaml.safe_load(file_path.read_text(encoding="utf-8")) or []
        rows = payload.get("items", []) if isinstance(payload, dict) else payload
    else:
        # BOM付きUTF-8(Excel書き出し)も読めるように utf-8-sig
        with file_path.open(encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))

    items: list[WatchItem] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise WatchlistError(f"{index}行目の形式が不正です: {row!r}")
        item = _build_item(row, index)
        if item is None:
            continue
        if item.key in seen:
            raise WatchlistError(f"key が重複しています: {item.key}")
        seen.add(item.key)
        items.append(item)

    if not items:
        raise WatchlistError(f"{file_path} に有効な行がありません")
    return items
