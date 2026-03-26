# SKILL: 4コマ漫画生成（備前焼のヒミツシリーズ）
tags: ig

## 概要
備前焼のヒミツシリーズ（4コマ漫画）を日本語・英語・フランス語の3言語で生成し、ig_schedulerの提案（proposal）に追加するまでを担う。

## トリガー
「4コマ作って」等の依頼が来たとき。

## 手順

### 1. ネタ帳の管理
- `~/workspace/scripts/instagram/4koma_topics.json` にネタをストックしておく
- 備前焼の特徴・歴史・作り方・使い方などをweb検索して新ネタを随時追加する
- `~/workspace/scripts/instagram/4koma_history.json` で使用済みネタを管理する
- **必ず未使用のネタから選ぶ**（重複投稿防止）

### 2. 画像生成（3言語セット）
- 同じ内容で以下の3枚を生成する:
  1. **日本語版** — タイトル「〜備前焼のヒミツ〜」
  2. **英語版** — タイトル「〜The Secret of Bizen Pottery〜」
  3. **フランス語版** — タイトル「〜Le Secret de la Poterie Bizen〜」
- 各タイトルは上部に配置、**通し番号はつけない**
- `workspace/scripts/nanobanana/gen.js` を直接呼び出して生成する
- モデル: `gemini-3-pro-image-preview`（テキスト入り画像に対応）
- アスペクト比: `3:4`
- キャラref: `~/workspace/data/casts/akiko/pure.jpg`（label: A）

```bash
GEMINI_KEY=$(cat ~/workspace/config/google/gemini_api_key)
AKIKO_REF=~/workspace/data/casts/akiko/pure.jpg
OUT=~/workspace/assets/tmp/4koma_<lang>_<timestamp>.png

REFS=$(python3 -c "import json; print(json.dumps([
  {\"path\": \"$AKIKO_REF\", \"label\": \"A\"}
]))")

node ~/workspace/scripts/nanobanana/gen.js \
  "<プロンプト>" \
  "$OUT" "$GEMINI_KEY" "$REFS" \
  "gemini-3-pro-image-preview" "3:4"
```

- プロンプトは以下のフォーマットで指定する:

```
warm beige-toned soft manga style. A 4-panel manga strip, vertical layout with 4 panels stacked top to bottom, each panel separated by a clear border. Each panel has exactly ONE speech bubble with unique text.
Panel 1 (top): <シーン描写>. Speech bubble contains ONLY: 「<セリフ1>」.
Panel 2: <シーン描写>. Speech bubble contains ONLY: 「<セリフ2>」.
Panel 3: <シーン描写>. Speech bubble contains ONLY: 「<セリフ3>」.
Panel 4 (bottom): <シーン描写>. Speech bubble contains ONLY: 「<セリフ4>」.
Do not repeat any text across panels.
Title at the top: 「<タイトル>」
```

- 3言語（日本語・英語・フランス語）それぞれ同じシーン構成で生成する（セリフ・タイトルを各言語に翻訳）

### 3. チェック
- [ ] 各言語のテキスト（セリフ・タイトル）に誤字・文法ミスがないか確認
- [ ] 必要があれば修正して再生成
- [ ] 彰子・テディ・メフィ・りんちゃんなどキャラの顔が変わっていないか確認
- [ ] **アニメ調**にする
- [ ] 彰子の服装: 原則は日本の四季に合わせた着物＋髪はアップ（状況に応じて洋服・髪おろしもOK）

### 4. キャプション作成
- 日本語キャプションに続けて英語キャプションも記載する
- 両言語に不自然な表現がないかチェック・修正する
- ハッシュタグ例: `#備前焼のヒミツ #備前焼 #bizenpottery #4コマ漫画 #BizenyAkiko`

### 5. ig_schedulerに追加
- 1ネタにつき**1エントリ（3枚カルーセル）**をproposalに追加する
- images配列に日本語→英語→フランス語の順で3枚を指定する
- カルーセル1枚目=日本語版、2枚目=英語版、3枚目=フランス語版
- キャプションは日本語→英語→フランス語の順で1つにまとめる
- type: `4koma`
- id例: `4koma_{YYMMDDHHSS}`

### 6. マスターへ確認送信

```
【備前焼のヒミツ 4コマ】完成しました！

内容: <ネタのタイトル>
3言語（日本語・英語・フランス語）をカルーセルで登録済みです。

ig_schedulerでご確認ください😊
https://bizeny.bon-soleil.com/ig_scheduler/
```

送信先: マスター (Telegram: 8579868590)

## 注意事項
- 3言語は同じ内容・同じコマ割りで作成する
- ネタ帳に新しいネタを追加したら `4koma_topics.json` に書き込んでおく
