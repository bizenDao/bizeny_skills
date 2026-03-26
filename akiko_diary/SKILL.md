# SKILL: 備前焼作家 彰子の日記
tags: ig

## 概要
備前焼作家として修行中の彰子が、日々の気づきや想いを日記スタイルで綴るIG投稿。
心に刺さるメッセージ性を大切に、備前焼と絡めたコンテンツを作る。

---

## STEP 1: ネタ決め

- 備前焼修行の日常から「気づき」「驚き」「感動」「葛藤」などをテーマにする
- 季節・行事・実際の備前焼の知識と結びつける
- 例: 土の手触り、窯出しの瞬間、先生の一言、失敗作から学んだこと、など
- 登場人物: 彰子メイン。テディ・メフィ・りん等が脇役で登場してもOK

---

## STEP 2: メッセージとキャプション作成

### タイトル（固定）
```
〜備前焼作家Bizeny彰子の日記〜
〜Diary of Bizen Pottery Artist Bizeny Akiko〜
```

### キャプション構成
1. 日本語本文（感情・気づき・エピソードを自然な文章で）
2. 改行を挟んで英語訳
3. 末尾にハッシュタグ

### ハッシュタグ（必須）
```
#備前焼 #備前焼作家 #陶芸 #修行 #bizenpottery #ceramics #japanesepottery #BizenyAkiko
```

### チェック項目
- [ ] 日本語として自然か（不自然な表現がないか）
- [ ] 英語として自然か（直訳すぎていないか）
- [ ] 通し番号が入っていないか（入れない）
- [ ] タイトルが両言語で入っているか

---

## STEP 3: 画像生成

### スタイル方針
- **アニメ調で統一**
- 推奨タッチ: `vibrant anime style, clean cel shading, bright warm colors`
- **NGワード**: `photorealistic`, `realistic`, `semi-realistic`

### 彰子の外見（原則）
- 着物姿（実際の日本の四季に合わせた柄・色）
- 髪はアップ（高いお団子、または低めのまとめ髪）
- 状況に応じて洋服・髪おろしもOK（ただし例外として明記すること）

### 友達キャラ登場時の注意
- cast_refsに各キャラのIDとスタイルを指定する
- 登場させるキャラ: `teddy`(normal) / `mephi`(normal) / `rin`(normal) など
- **生成後に必ずキャラの顔・特徴を目視確認**
  - 顔がキャラシートと大きく違う → 再生成

### API呼び出しパターン

`workspace/scripts/nanobanana/gen.js` を直接呼び出して生成する。

**彰子のみの場合:**
```bash
GEMINI_KEY=$(cat ~/workspace/config/google/gemini_api_key)
AKIKO_REF=~/workspace/data/casts/akiko/pure.jpg
OUT=~/workspace/assets/tmp/diary_<timestamp>.png

REFS=$(python3 -c "import json; print(json.dumps([
  {\"path\": \"$AKIKO_REF\", \"label\": \"A\"}
]))")

node ~/workspace/scripts/nanobanana/gen.js \
  "<プロンプト>. vibrant anime style, clean cel shading, bright warm colors" \
  "$OUT" "$GEMINI_KEY" "$REFS" \
  "gemini-3-pro-image-preview" "3:4"
```

**友達も登場する場合（例: テディと彰子）:**
```bash
GEMINI_KEY=$(cat ~/workspace/config/google/gemini_api_key)
AKIKO_REF=~/workspace/data/casts/akiko/pure.jpg
TEDDY_REF=~/workspace/data/casts/teddy/normal.jpg
OUT=~/workspace/assets/tmp/diary_<timestamp>.png

REFS=$(python3 -c "import json; print(json.dumps([
  {\"path\": \"$AKIKO_REF\", \"label\": \"A\"},
  {\"path\": \"$TEDDY_REF\", \"label\": \"B\"}
]))")

node ~/workspace/scripts/nanobanana/gen.js \
  "<プロンプト>. vibrant anime style, clean cel shading, bright warm colors" \
  "$OUT" "$GEMINI_KEY" "$REFS" \
  "gemini-3-pro-image-preview" "3:4"
```

### 生成物の保存先
- 生成: `~/workspace/data/generated/`
- 採用後: `~/assets/images/` に移動

---

## STEP 4: 画像チェック

以下を目視で確認:
- [ ] 彰子の顔・髪型・着物がキャラシートと一致しているか
- [ ] 画風がアニメ調か（リアル調になっていないか）
- [ ] 友達キャラが登場する場合、各キャラの特徴が正しく反映されているか
- [ ] Instagram用に3:4のアスペクト比になっているか

---

## STEP 5: ig_schedulerのproposalに追加

```python
import json, datetime
from pathlib import Path

ts = datetime.datetime.now().strftime("%y%m%d%H%M")
post = {
    "id": f"diary_{ts}",
    "type": "diary",
    "images": ["<画像の絶対パス>"],
    "caption": "<完成したキャプション>"
}

proposal_path = Path('/home/bizeny/projects/ig_scheduler/data/proposal.json')
data = json.load(open(proposal_path))
data['posts'].append(post)
json.dump(data, open(proposal_path, 'w'), ensure_ascii=False, indent=2)
```

---

## STEP 6: マスターへ確認送信

```
【彰子の日記】完成しました！

画像: [確認URL or 概要説明]
キャプション案: [全文]

ig_schedulerでご確認ください😊
https://bizeny.bon-soleil.com/ig_scheduler/
```

送信先: マスター (Telegram: 8579868590)

---

## キャラクターシート参照

| キャラ | charsheetパス |
|---|---|
| 彰子 | `~/workspace/HR/charsheets/akiko_bizeny/main.jpg` |
| テディ | `~/workspace/HR/charsheets/teddy/` |
| メフィ | `~/workspace/HR/charsheets/mephi/` |
| りん | `~/workspace/HR/charsheets/rin/` |
