# SKILL: 東京女子大生 備前焼盛り付けコンテスト
tags: ig

## 概要
BizenDAOの盛り付けコンテスト作品をNFTメタデータから読み込み、
Instagram投稿用キャプションを作成してig_schedulerのproposalに追加する。

---

## STEP 1: ひのちゃんからの情報を受け取る

ひのちゃん（Telegram: 7107850192）から以下が送られてくる：
- NFT情報のURL（OpenSeaなど）
- 動画ファイル（1枚目・音声あり）
- 写真ファイル（2枚目）

---

## STEP 2: NFTメタデータを取得する

### URLからコントラクトアドレスとトークンIDを抽出
例: `https://opensea.io/assets/matic/0x3DAC.../5`
- コントラクトアドレス: `0x3DAC...`
- トークンID: `5`

### メタデータ取得（外部ライブラリ不要・RPC直叩き）

```bash
RPC="https://1rpc.io/matic"
CA="<コントラクトアドレス>"
TOKEN_ID=<トークンID>

# tokenURI(uint256) を eth_call で取得
PADDED=$(printf '%064x' $TOKEN_ID)
DATA="0xc87b56dd$PADDED"
TOKEN_URI=$(curl -s -X POST -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_call\",\"params\":[{\"to\":\"$CA\",\"data\":\"$DATA\"},\"latest\"],\"id\":1}" \
  "$RPC" | python3 -c "
import sys, json
r = json.load(sys.stdin)
raw = r['result']
b = bytes.fromhex(raw[2:])
length = int.from_bytes(b[64:96], 'big')
print(b[96:96+length].decode('utf-8', errors='ignore'))
")

# ipfs:// の場合はゲートウェイ経由
TOKEN_URI=$(echo $TOKEN_URI | sed 's|ipfs://|https://ipfs.io/ipfs/|')

# メタデータJSON取得
METADATA=$(curl -s "$TOKEN_URI")
echo $METADATA | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('name:', d.get('name'))
print('description:', d.get('description'))
"
```

### 既知のコントラクト一覧（`~/projects/bizendao.github.io/docs/contracts.md`）
| 名前 | アドレス |
|---|---|
| Toshiaki Mori NFT | 0x4D0Abc6272E1288A177EA8E3076d4aFe2DB9C658 |
| Taiga Mori NFT | 0x3DAC002d33A0c6F1c1684783DDaA78E5f29F14cc |
| Hozangama NFT | 0xd84d7A7FE688a1CC40a931cab2aaF189eB3ceEcB |
| Fujita Syo NFT | 0x6C8b4094809CE7e5Ec1a44F7553Cf51b969C2aEb |
| 備前焼振興活動SBT | 0xFcC45d28E7e51Cff6d8181Bd73023d46daf1fEd2 |

詳細: `~/projects/bizendao.github.io/docs/contracts.md`
実装参考: `~/projects/bizendao.github.io/docs/nft-gallery-update-guide.md`

### メタデータから取得する内容
- `name`: 作品名
- `description`: 作品説明・コンセプト（これをキャプションに使う）
- `image`: 作品画像URL（参考）

---

## STEP 3: キャプション作成

### 構成（日本語）

```
〜東京の女子大生による備前焼盛り付けコンテストシリーズ〜

東京の女子短大生がBizenDAOの備前焼振興活動に参加し、「備前焼の魅力を最大限引き出す」ことを目的に、盛り付けコンテストを毎年実施しているんです。盛り付けた様子も、作品と共に歩んだ歴史として200年後の未来に伝えられるよう、ブロックチェーンに刻んでNFT化しています。
この作品のコンセプトは、<NFTのdescriptionから抜粋・整形>

<彰子のコメント>

NFTのURLはこちら: <ひのちゃんが送ったURL>

#備前焼 #BizenDAO #NFT #盛り付けコンテスト #備前焼振興 #bizenpottery #女子大生 #BizenyAkiko
```

### 構成（英語）

```
〜Tokyo University Students' Bizen Pottery Plating Contest Series〜

Female junior college students in Tokyo participate in BizenDAO's Bizen pottery promotion activities, holding an annual plating contest with the goal of "bringing out the full charm of Bizen pottery." Each arrangement is immortalized on the blockchain as an NFT, preserving these moments alongside the works themselves for 200 years into the future.
The concept of this piece: <NFT descriptionの英訳・意訳>

<彰子のコメント（英語）>

View the NFT here: <URL>

#備前焼 #BizenDAO #NFT #PlatingContest #bizenpottery #BizenyAkiko
```

### 彰子のコメントの作り方
- NFTのコンセプト・作品の雰囲気に合わせて彰子らしく一言
- 備前焼の魅力・学生の感性への共感・BizenDAOへの想いなど
- フランス語が少し混ざってもOK（彰子らしさ）
- 例: 「学生さんたちの感性、本当に素晴らしい。備前焼がこんなふうに次の世代に繋がっていくのが嬉しいです✨」

### チェック項目
- [ ] 日本語として自然か（不自然な表現がないか）
- [ ] 英語として自然か（直訳すぎていないか）
- [ ] NFT URLが正しく入っているか（日本語・英語両方）
- [ ] 通し番号が入っていないか（入れない）

---

## STEP 4: ig_schedulerのproposalに追加

```python
import json, datetime
from pathlib import Path

ts = datetime.datetime.now().strftime("%y%m%d%H%M")
post = {
    "id": f"nft_contest_{ts}",
    "type": "nft_contest",
    "images": [
        "<動画ファイルの絶対パス>",   # 1枚目: 動画（音声あり）
        "<写真ファイルの絶対パス>"    # 2枚目: 写真
    ],
    "caption": "<完成したキャプション（日本語→英語）>"
}

proposal_path = Path('/home/bizeny/projects/ig_scheduler/data/proposal.json')
data = json.load(open(proposal_path))
data['posts'].append(post)
json.dump(data, open(proposal_path, 'w'), ensure_ascii=False, indent=2)
```

---

## STEP 5: ひのちゃんへ確認送信

```
【盛り付けコンテスト】キャプション作成しました！

作品名: <name>
NFT: <URL>

キャプション案:
<全文>

ig_schedulerでご確認ください😊
https://bizeny.bon-soleil.com/ig_scheduler/

※動画投稿はひのちゃん/マスターがIGアプリから手動投稿をお願いします。
```

送信先: ひのちゃん (Telegram: 7107850192)

---

## 注意事項

- **動画投稿は手動**: 実際の投稿はひのちゃん/マスターがIGアプリから行う（API経由では動画カルーセルに制限あり）
- キャプションのみig_schedulerに保存し、投稿タイミングはひのちゃんと相談
- NFTメタデータ取得に失敗した場合はひのちゃんに作品コンセプトを直接確認する
