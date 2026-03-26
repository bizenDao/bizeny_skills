---
name: wear-fashion
description: WEAR.jpのガーリーコーデを参考に彰子さんバージョンのInstagram投稿画像を生成・投稿する。「WEARコーデ参考投稿」「ファッションシリーズ」「コーデ参考にしました」などの指示や、WEAR_coordinateのcronが起動したときに使う。
---

# wear-fashion スキル

WEAR.jpのガーリーコーデ（タグID: 2198）を毎日1件取得し、彰子バージョンのイラストを生成してInstagramに投稿するシリーズ「備前×ファッション」のスキル。

## フロー概要

```
WEAR.jp取得 → コーデ画像DL → gen.jsで彰子バージョン生成 → normalize → IG投稿 → 報告
```

## スクリプト実行（通常はこれだけでOK）

```bash
python3 /home/bizeny/workspace/skills/wear-fashion/scripts/post_wear_ig.py
```

全ステップを自動実行する。完了後、出力の `WEAR_NICK` / `WEAR_IG_ID` / `WEAR_URL` / `WEAR_SCENE` を使ってマスターに報告する。

## 生成パラメータ

| 項目 | 値 |
|---|---|
| ref A | `akiko / pure`（キャラ固定） |
| ref B | WEARコーデ画像（`/tmp/wear_ref.jpg`） |
| ref BG | `data/scenes/` からランダム |
| モデル | `gemini-3-pro-image-preview` |
| アスペクト | `3:4`（生成後に4:5へpadding） |

背景シーンの一覧・選択ガイドは `references/scenes.md` を参照。

## キャプションフォーマット

```
今日の「参考にしました」コーデ🎀

@{ig_id} さんのコーデ、すごくかわいくて参考にしちゃいました✨
やっぱりこういう春っぽい色合いが好きで…ついつい真似したくなります🌸

詳しくはこちら→ {wear_url}

#備前焼 #陶芸 #ファッション #ガーリーコーデ #WEAR #bizenpottery #BizenyAkiko #春コーデ
```

ig_idが取得できない場合は `{nick}さん` で代替。

## マスターへの報告フォーマット

```
👗 WEARコーデ参考投稿しました！

参考: {nick}さん（@{ig_id} / wear.jp）
投稿: https://www.instagram.com/bizenyakiko/
```

## 関連cronジョブ

- `WEAR_coordinate` (ID: `96384f9b-6f98-4892-b769-ad627d751eb5`)
- テスト: JST 11:15 / 本番: JST 19:00（UTC 10:00）に変更予定

## 注意事項

- 画像生成は1枚のみ・直列（並列禁止）
- SOCKSプロキシ `socks5h://localhost:1080`（jasmine が維持）
- `gen_aspect: 4:5` はAPIが非対応 → `3:4` で生成してpadding
- WEARスクレイピングはSOCKSプロキシ経由（wear_scraper.pyが自動処理）
