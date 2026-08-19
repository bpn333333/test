"""配信の制御。

やること:
 - 同じシグナルを二度流さない(再起動しても効くようファイルに残す)
 - 投稿間隔と1日の上限を守る(連投でアカウントを飛ばさない)
 - 免責・禁止表現の検査を必ず通す(composer.Post.validate)

X の自動化ポリシー上、同一・類似内容の連投や過剰な投稿は制限対象になりうる。
上限は控えめに設定しておくこと。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .client import Client, DryRunClient, PostResult
from .composer import Post, compose_signal_post


@dataclass
class PublisherConfig:
    min_interval_seconds: int = 300     # 前回投稿からこの秒数は空ける
    max_posts_per_day: int = 12         # 1日の上限
    hashtags: Sequence[str] = ("#FX",)
    show_levels: bool = True            # 損切り・利確を本文に載せるか
    state_file: str = "data/x_publisher_state.json"


@dataclass
class PublisherState:
    posted_ids: Dict[str, str] = field(default_factory=dict)  # signal_id -> 投稿日時
    last_posted_at: Optional[str] = None
    daily_counts: Dict[str, int] = field(default_factory=dict)  # YYYY-MM-DD -> 件数

    @classmethod
    def load(cls, path: Path) -> "PublisherState":
        if not path.exists():
            return cls()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls()
        return cls(
            posted_ids=raw.get("posted_ids", {}),
            last_posted_at=raw.get("last_posted_at"),
            daily_counts=raw.get("daily_counts", {}),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "posted_ids": self.posted_ids,
                    "last_posted_at": self.last_posted_at,
                    "daily_counts": self.daily_counts,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


@dataclass
class PublishOutcome:
    signal_id: str
    posted: bool
    reason: str = ""
    tweet_id: Optional[str] = None


class Publisher:
    def __init__(self, client: Optional[Client] = None,
                 config: Optional[PublisherConfig] = None,
                 now_provider=datetime.now) -> None:
        self.config = config or PublisherConfig()
        self.client = client or DryRunClient()
        self.state_path = Path(self.config.state_file).expanduser()
        self.state = PublisherState.load(self.state_path)
        self._now = now_provider  # テストから時刻を差し替えるため

    def _today_key(self) -> str:
        return self._now().strftime("%Y-%m-%d")

    def _seconds_since_last(self) -> float:
        if not self.state.last_posted_at:
            return float("inf")
        try:
            last = datetime.fromisoformat(self.state.last_posted_at)
        except ValueError:
            return float("inf")
        return (self._now() - last).total_seconds()

    def can_post(self) -> tuple[bool, str]:
        today = self._today_key()
        count = self.state.daily_counts.get(today, 0)
        if count >= self.config.max_posts_per_day:
            return False, f"本日の上限 {self.config.max_posts_per_day} 件に到達"

        elapsed = self._seconds_since_last()
        if elapsed < self.config.min_interval_seconds:
            wait = int(self.config.min_interval_seconds - elapsed)
            return False, f"前回投稿から {wait} 秒待機が必要"
        return True, ""

    def already_posted(self, signal_id: str) -> bool:
        return signal_id in self.state.posted_ids

    def publish_post(self, post: Post) -> PublishOutcome:
        """検査済みの Post を1件流す。"""
        if self.already_posted(post.signal_id):
            return PublishOutcome(post.signal_id, False, "配信済み")

        ok, why = self.can_post()
        if not ok:
            return PublishOutcome(post.signal_id, False, why)

        try:
            post.validate()
        except ValueError as error:
            return PublishOutcome(post.signal_id, False, f"検査で停止: {error}")

        result: PostResult = self.client.post(post.text)
        if not result.ok:
            return PublishOutcome(post.signal_id, False, f"送信失敗: {result.error}")

        now = self._now()
        self.state.posted_ids[post.signal_id] = now.isoformat(timespec="seconds")
        self.state.last_posted_at = now.isoformat(timespec="seconds")
        today = self._today_key()
        self.state.daily_counts[today] = self.state.daily_counts.get(today, 0) + 1
        self._prune()
        self.state.save(self.state_path)

        return PublishOutcome(post.signal_id, True, "", result.tweet_id)

    def publish_signals(self, signals: Sequence) -> List[PublishOutcome]:
        """シグナル配列を順に配信する。上限に当たった分は次回に回る。"""
        outcomes: List[PublishOutcome] = []
        for signal in signals:
            if self.already_posted(signal.signal_id):
                outcomes.append(PublishOutcome(signal.signal_id, False, "配信済み"))
                continue
            try:
                post = compose_signal_post(
                    signal,
                    hashtags=self.config.hashtags,
                    show_levels=self.config.show_levels,
                )
            except ValueError as error:
                outcomes.append(
                    PublishOutcome(signal.signal_id, False, f"本文作成で停止: {error}")
                )
                continue
            outcomes.append(self.publish_post(post))
        return outcomes

    def _prune(self, keep_days: int = 60) -> None:
        """状態ファイルが無限に育たないよう古い記録を落とす。"""
        cutoff = self._now().timestamp() - keep_days * 86400

        self.state.posted_ids = {
            key: value for key, value in self.state.posted_ids.items()
            if _isoformat_timestamp(value) >= cutoff
        }
        self.state.daily_counts = {
            day: count for day, count in self.state.daily_counts.items()
            if _date_timestamp(day) >= cutoff
        }


def _isoformat_timestamp(value: str) -> float:
    try:
        return datetime.fromisoformat(value).timestamp()
    except (ValueError, TypeError):
        return float("inf")  # 読めないものは消さずに残す


def _date_timestamp(value: str) -> float:
    try:
        return datetime.strptime(value, "%Y-%m-%d").timestamp()
    except (ValueError, TypeError):
        return float("inf")
