# SKILL: bizenyakiko note.com 投稿

彰子のnote.comアカウントに記事を投稿するスキル。

## アカウント情報

- **noteユーザー**: bizenyakiko
- **Cookie**: `~/.config/note/cookies`（bizenyakikoのセッション）
- **投稿スクリプト**: `~/workspace/scripts/post_note_draft.mjs`

> ⚠️ Cookieはbizenyakikoアカウントのものであること。
> teddy_on_webのCookieを使わないこと。

---

## STEP 1: 記事を書く

`/tmp/note_<スラッグ>.md` に本文を作成。

### ルール
- **Markdownテーブル（`|`）禁止** → スクリプトが無限ループする。リスト形式（`・`）に変換すること
- コードブロック・引用（`>`）はOK
- 1行目を `# タイトル` にすること（スクリプトがここからタイトルを取得）

### 彰子らしい文体
- 備前焼への愛情・修行の日々・気づきを素直に
- 日仏ハーフらしい視点（パリと岡山の比較等）
- ハッシュタグ: `#備前焼 #陶芸 #備前焼作家 #修行 #bizenpottery #BizenyAkiko`

---

## STEP 2: アイキャッチ画像を生成する

```bash
API_KEY=$(grep LABO_API_KEY ~/labo_portal/.env | cut -d= -f2)
curl -s -X POST http://localhost:8800/labo/image_gen/api/generate \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Warm beige manga-style illustration. [記事のシーンを視覚化]. Wide landscape format for blog header. NOT photorealistic.",
    "cast_refs": "[{\"id\":\"akiko\",\"style\":\"pure\",\"label\":\"A\"}]",
    "gen_model": "gemini-3-pro-image-preview",
    "gen_aspect": "16:9"
  }'
```

生成物は `~/workspace/data/generated/` に保存される。
1280px幅・200KB以下に収まっているか確認（超えたらリサイズ）:

```bash
convert input.jpg -resize 1280x -quality 85 output.jpg
```

---

## STEP 3: 下書きとして投稿する

```bash
node ~/workspace/scripts/post_note_draft.mjs \
  /tmp/note_<スラッグ>.md \
  ~/workspace/data/generated/<アイキャッチ>.jpg
```

成功すると下書きURLが返ってくる。
**マスター（Telegram: 8579868590）に報告して確認してもらうこと。**

---

## STEP 4: 公開はマスターが行う

彰子は下書きまで。公開はマスターがnote管理画面から行う。

---

## トラブルシューティング

**「リソースが見つかりません」エラー → Cookieが切れている**

1. マスターにbizenyakikoのnote.comへのログインを依頼
2. ブラウザのDevTools → Application → Cookies → `note.com`
3. `_note_session_v5` の値を取得
4. `~/.config/note/cookies` を更新:
   ```
   _note_session_v5=<新しい値>
   ```

**アイキャッチのアップロードがタイムアウト → 画像が大きすぎ**

```bash
convert input.jpg -resize 1280x -quality 85 /tmp/eyecatch_resized.jpg
```

**labo-portalが落ちている**

```bash
cd ~/labo_portal && nohup bash start.sh > ~/logs/labo_portal.log 2>&1 &
sleep 8
```
