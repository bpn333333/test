"""X API v2 への投稿クライアント。

本番投稿には OAuth 1.0a のユーザーコンテキスト(API Key/Secret + Access
Token/Secret)が必要。認証情報は環境変数から読む(コードに書かない)。

  X_API_KEY / X_API_SECRET / X_ACCESS_TOKEN / X_ACCESS_TOKEN_SECRET

料金プランと無料枠の投稿上限は変動が激しい。運用前に必ず最新の開発者ダッシュ
ボードで確認すること。上限に当たった場合は 429 が返るので、publisher 側の
レート制御と合わせて使う。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Protocol

X_TWEETS_ENDPOINT = "https://api.x.com/2/tweets"


@dataclass
class PostResult:
    ok: bool
    tweet_id: Optional[str] = None
    error: str = ""
    dry_run: bool = False


class Client(Protocol):
    def post(self, text: str) -> PostResult:
        ...


class DryRunClient:
    """外部送信せずファイルに書くだけ。既定はこちら。

    ネットワークが使えない環境でも配信パイプライン全体を通しで確認できる。
    本番に切り替えるまでは必ずこれで文面を目視すること。
    """

    def __init__(self, output_path: str | Path = "data/x_dryrun.log") -> None:
        self.output_path = Path(output_path).expanduser()

    def post(self, text: str) -> PostResult:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(f"----- {stamp} -----\n{text}\n\n")
        return PostResult(ok=True, tweet_id=None, dry_run=True)


class XClient:
    """本番投稿。requests と requests-oauthlib が必要。"""

    def __init__(self,
                 api_key: Optional[str] = None,
                 api_secret: Optional[str] = None,
                 access_token: Optional[str] = None,
                 access_token_secret: Optional[str] = None,
                 timeout: int = 15) -> None:
        self.api_key = api_key or os.environ.get("X_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("X_API_SECRET", "")
        self.access_token = access_token or os.environ.get("X_ACCESS_TOKEN", "")
        self.access_token_secret = (
            access_token_secret or os.environ.get("X_ACCESS_TOKEN_SECRET", "")
        )
        self.timeout = timeout

        missing = [
            name for name, value in (
                ("X_API_KEY", self.api_key),
                ("X_API_SECRET", self.api_secret),
                ("X_ACCESS_TOKEN", self.access_token),
                ("X_ACCESS_TOKEN_SECRET", self.access_token_secret),
            ) if not value
        ]
        if missing:
            raise ValueError(f"認証情報が足りません: {', '.join(missing)}")

    def _session(self):
        try:
            import requests  # noqa: F401
            from requests_oauthlib import OAuth1Session
        except ImportError as error:  # pragma: no cover - 依存が無い環境向け
            raise RuntimeError(
                "requests と requests-oauthlib が必要です: "
                "pip install -r distribution/requirements.txt"
            ) from error

        return OAuth1Session(
            self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
        )

    def post(self, text: str) -> PostResult:
        try:
            session = self._session()
            response = session.post(
                X_TWEETS_ENDPOINT, json={"text": text}, timeout=self.timeout
            )
        except Exception as error:  # ネットワーク断で配信ループを落とさない
            return PostResult(ok=False, error=str(error))

        if response.status_code in (200, 201):
            try:
                tweet_id = response.json().get("data", {}).get("id")
            except json.JSONDecodeError:
                tweet_id = None
            return PostResult(ok=True, tweet_id=tweet_id)

        return PostResult(
            ok=False,
            error=f"HTTP {response.status_code}: {response.text[:300]}",
        )


def build_client(dry_run: bool = True, output_path: str | Path = "data/x_dryrun.log") -> Client:
    """既定は DryRun。本番は明示的に dry_run=False を渡したときだけ。"""
    if dry_run:
        return DryRunClient(output_path)
    return XClient()
