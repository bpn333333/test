"""追跡リスト(watchlist)の読み込みと追記。

CSV(Excel/スプレッドシートからの書き出し)と YAML の両方に対応。
最低限 name と、淘宝側の価格情報(taobao_price_cny または taobao_url)があればよい。

ブラウザで調べた行を貼り付けて追記する経路(pricediff add)もここに置く。
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

# CSV に書き出すときの列順(ヘッダ無しで貼り付けられた場合もこの順とみなす)
CANONICAL_COLUMNS = [
    "key", "name", "taobao_url", "taobao_price_cny", "weight_g",
    "amazon_asin", "amazon_keyword", "rakuten_keyword", "rakuten_genre_id",
    "amazon_price_jpy", "amazon_rank", "rakuten_price_jpy", "rakuten_rank", "note",
]

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


def _looks_like_header(row: list[str]) -> bool:
    """1行目がヘッダかどうか。列名に解釈できるセルが過半数ならヘッダとみなす。"""
    if not row:
        return False
    known = sum(1 for cell in row if _normalize_header(cell) in FIELDS)
    return known >= max(1, len(row) // 2)


def parse_rows(text: str) -> list[WatchItem]:
    """貼り付けられたCSVテキストを WatchItem に変換する。

    1行目がヘッダならそれに従い、無ければ CANONICAL_COLUMNS の順とみなす。
    """
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise WatchlistError("追加する行がありません")

    reader = list(csv.reader(lines))
    header = reader[0]
    if _looks_like_header(header):
        columns = [_normalize_header(cell) for cell in header]
        body = reader[1:]
    else:
        columns = CANONICAL_COLUMNS
        body = reader

    if not body:
        raise WatchlistError("ヘッダ行だけで、追加する行がありません")

    items: list[WatchItem] = []
    for index, row in enumerate(body, start=1):
        if not any(cell.strip() for cell in row):
            continue
        if len(row) > len(columns):
            raise WatchlistError(
                f"{index}行目: 列が多すぎます({len(row)}列 > {len(columns)}列)。"
                "商品名にカンマが入っている場合は \"...\" で囲ってください"
            )
        item = _build_item(dict(zip(columns, row)), index)
        if item is not None:
            items.append(item)

    if not items:
        raise WatchlistError("追加できる行がありませんでした")
    return items


def _format_value(value: Any) -> Any:
    """CSV に書くときの見た目を整える(320.0 -> 320)。"""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _duplicate_key(
    item: WatchItem, by_key: dict[str, WatchItem], explicit_key: bool
) -> Optional[str]:
    """同じ商品が既にあるか。key が明示されていれば key、無ければURL/商品名で見る。"""
    if explicit_key:
        return item.key if item.key in by_key else None
    for key, existing in by_key.items():
        if item.taobao_url and existing.taobao_url == item.taobao_url:
            return key
        if existing.name == item.name:
            return key
    return None


def _merge_items(existing: WatchItem, incoming: WatchItem) -> WatchItem:
    """既存行に、貼り付け行の埋まっている項目だけを反映した新しい行を返す。"""
    merged = WatchItem(**{f: getattr(existing, f) for f in CANONICAL_COLUMNS if f in FIELDS})
    for field in FIELDS:
        value = getattr(incoming, field, None)
        if field != "key" and value not in (None, ""):
            setattr(merged, field, value)
    return merged


def append_items(
    path: str | Path, new_items: list[WatchItem], *, update: bool = False
) -> tuple[list[WatchItem], list[WatchItem]]:
    """追跡リストに行を足す。戻り値は (追加/更新した行, 重複で飛ばした行)。

    同じ商品(key、または淘宝URL/商品名が一致)は既定で飛ばす。
    update=True なら既存の行を新しい内容で置き換える。
    """
    file_path = Path(path).expanduser()
    existing: list[WatchItem] = []
    if file_path.is_file():
        try:
            existing = load_watchlist(file_path)
        except WatchlistError as exc:
            raise WatchlistError(f"既存の追跡リストを読めませんでした: {exc}") from exc

    by_key = {item.key: item for item in existing}
    order = [item.key for item in existing]
    # 自動採番(item001...)が既存と衝突しないよう、最大番号の続きから振る
    auto_index = 0
    for key in by_key:
        if key.startswith("item") and key[4:].isdigit():
            auto_index = max(auto_index, int(key[4:]))

    added: list[WatchItem] = []
    skipped: list[WatchItem] = []
    for item in new_items:
        explicit_key = not (item.key.startswith("item") and item.key[4:].isdigit())
        duplicate = _duplicate_key(item, by_key, explicit_key)

        if duplicate is not None:
            if not update:
                skipped.append(item)
                continue
            # 貼り付けた列だけを既存行に上書きする(空欄の列は既存の値を残す)
            item = _merge_items(by_key[duplicate], item)
        elif not explicit_key:
            auto_index += 1
            item.key = f"item{auto_index:03d}"

        if item.key not in by_key:
            order.append(item.key)
        by_key[item.key] = item
        added.append(item)

    if added:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=CANONICAL_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            for key in order:
                item = by_key[key]
                writer.writerow(
                    {col: _format_value(getattr(item, col, None)) for col in CANONICAL_COLUMNS}
                )
    return added, skipped
