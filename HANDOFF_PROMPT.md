# 新しいセッションの最初のプロンプト

下のコードブロックをそのまま貼ってください。

---

```
AI映像プラットフォーム事業の投資家向け資料を作っています。前のセッションから引き継ぎます。

まず以下の順で読んでから、現状を1〜2段落で要約して、次に何をすべきか提案してください。
勝手に作業を始めないでください。

1. README.md            ← 事業の定義と確定値。ここが唯一の「正」
2. SESSION_HANDOFF.md   ← 残っている宿題・この環境の癖・作業のきまり
3. PLATFORM_PIVOT.md    ← 事業設計の本体（第9〜11章に直近の決定）

そのうえで、以下を守ってください。

【作業のきまり】
- ブランチは claude/china-ai-japan-market-fkwvr8 のみ。他へは push しない
- PR は #12 が open。新規に作らず、そこに積む
- コミットメッセージの末尾に必ず入れる:
  Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
  Claude-Session: <このセッションのURL>
- モデル名はコミット・PR・コード内に書かない

【数字を1つ変えたら、直す先が4つある】
README.md → FINANCIAL_PLAN.md → CAP_TABLE.md / ROADMAP.md → deck/build.js と investor_deck.html
過去にここを取りこぼして、上場年が資料の前半と後半で食い違う事故を起こしています。

【この環境の癖】
- 日本語フォントが入っていない。PDF化する前に deck/README.md の手順を実行すること
  （やらないと中国語フォントで代替描画され字形が崩れる）
- PPTX は deck/ のスクリプトから生成する。生成後に必ず deck/slim.py を通す
- Google ドライブにバイナリを置けない。Googleスライドへの取り込みはユーザーに手動で依頼する
- アーティファクトの監視（wake subscription）は登録できない。「監視しています」と言わない
- スクラッチパッドはセッション終了で消える。残すものは必ずリポジトリへ

【進め方】
- 日本語で。相手は松田徳義さん
- 出所のない数字を置かない。［仮置き］は［仮置き］と明記する
- 事実誤認に気づいたら、遠慮せず指摘して直す。SESSION_HANDOFF.md の 4-2 に、
  一度まちがえて直した内容があります。戻さないでください
```

---

## 補足（貼らなくてよい）

- 公開中のアーティファクト: https://claude.ai/code/artifact/81b95a95-bffe-4eaa-8a24-32a5a4622743
- 引き継ぎ元セッション: https://claude.ai/code/session_017HoWLm426zeXirBWkACG6e
- 最優先の宿題は `SESSION_HANDOFF.md` 3-1（HTML版デッキに5枚の図が入っていない）
