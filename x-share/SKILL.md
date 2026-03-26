---
name: x-share
description: Generate an X (Twitter) share link for a URL with a one-line description. Use when asked to create a "share on X" link, "Xのポチッとリンク", or tweet intent URL for any article or page.
---

# X シェアリンク生成スキル

URLとひとこと紹介からX（Twitter）のシェアリンクを生成する。

## やること

1. 対象URLの内容をweb_fetchで取得（タイトル・内容を把握）
2. ひとこと紹介文を作成（日本語・100文字以内・引用1行含めると◎）
3. intent URLを生成してTelegramで送る

## シェアリンクのフォーマット

```
https://twitter.com/intent/tweet?text=<URLエンコードされたテキスト>
```

テキストのフォーマット例：
```
📖 タイトルや一言キャッチ

「記事からの印象的な引用」

ひとこと紹介文。

https://note.com/xxxx
```

## URLエンコード

Pythonで生成する：

```python
import urllib.parse

text = """📖 タイトル

「引用」

ひとこと紹介。

https://example.com/article"""

encoded = urllib.parse.quote(text)
share_url = f"https://twitter.com/intent/tweet?text={encoded}"
print(share_url)
```

## Telegramへの送り方（3点セット）

必ず以下の順番で3つ送る：

**1. ツイートテキスト（コードブロック）**

Telegramでコピーボタンが出るようコードブロックで送る。

**2. intent URL（コードブロック）**

URLそのものもコードブロックで送る（コピーして直接ブラウザに貼れる）。

**3. クリックリンク（ポチッと用）**

Markdownリンク形式で送る（タップしてそのままXが開く）。

例：
```
[👉 ポチッとXに投稿する](https://twitter.com/intent/tweet?text=...)
```

## 注意

- 投稿は禁止。シェアリンクを渡すだけ（マスターが自分で投稿する）
- テキストは280文字以内に収まるよう調整
- ハッシュタグは基本つけない（マスターの判断に任せる）
