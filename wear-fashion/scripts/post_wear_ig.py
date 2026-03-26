#!/usr/bin/env python3
"""
WEAR コーデ参考 IG 投稿スクリプト（ジャスミンAPI版）
- ジャスミンAPIからコーデURL・画像URL取得（SOCKSプロキシ不要）
- gen.js で彰子バージョン生成 → IG投稿 → Telegram報告
"""
import base64, json, os, random, subprocess, sys, time, shutil
import requests
from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image
import numpy as np

# ── パス定義 ──────────────────────────────────────────────
WS            = Path('/home/bizeny/workspace')
CREDS         = Path('/home/bizeny/.config/instagram/bizenyakiko_credentials.json')
GEMINI_KEY_F  = WS / 'config/google/gemini_api_key'
GEN_JS        = Path('/home/bizeny/workspace/scripts/nanobanana/gen.js')
AKIKO_PURE    = WS / 'data/casts/akiko/pure.jpg'
GEN_DIR       = WS / 'data/generated'
IG_HOSTING    = Path('/home/bizeny/workspace/projects/www/images/ig_hosting')
IG_HOSTING_URL = 'https://bizeny.bon-soleil.com/images/ig_hosting'
IG_USER_ID    = '26416648414607450'
WEAR_REF      = Path('/tmp/wear_ref.jpg')
POSTED_FILE   = WS / 'data/wear_posted.json'

# ── カテゴリローテーション管理 ────────────────────────────
ROTATION_FILE = WS / 'data/wear_rotation.json'

def get_today_category() -> str:
    """日付の奇数偶数でwearista/shop_staffを交互に返す"""
    import datetime
    day = datetime.date.today().toordinal()
    return 'wearista' if day % 2 == 0 else 'shop_staff'

def load_rotation() -> dict:
    """ローテーション状態を読み込む {category: last_user}"""
    if not ROTATION_FILE.exists():
        return {}
    try:
        return json.loads(ROTATION_FILE.read_text())
    except Exception:
        return {}

def save_rotation(state: dict):
    ROTATION_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))

# ── shop_staffブランドマッピング ──────────────────────────
BRAND_MAP = {
    'axes':    ('Axes femme', '#axesfemme #アクシーズファム'),
    'dazzlin': ('Dazzlin', '#dazzlin #ダズリン'),
    'ingni':   ('ingni', '#ingni #イングニ'),
    'olive':   ('Olive des Olive', '#olivedesolive #オリーブデオリーブ'),
}

def get_brand_info(user: str) -> tuple:
    """ユーザー名からブランド名とハッシュタグを返す"""
    u = user.lower()
    for key, (brand, tag) in BRAND_MAP.items():
        if key in u:
            return brand, tag
    return '', ''

# ── ジャスミンAPI ──────────────────────────────────────────
JASMINE_COORDS_URL = 'https://jasmine.bon-soleil.com/services/wear_style_viewer/api/wear_coords.json'
JASMINE_OGP_URL    = 'https://jasmine.bon-soleil.com/services/wear_style_viewer/api/ogp.php'

# ── 背景・アイテム ──────────────────────────────────────────
BACKGROUNDS = [
    'standing outside in the old townscape of Imbe, traditional buildings and stone paths, warm afternoon light',
    'standing in a Japanese garden, stone lantern and moss visible, dappled sunlight',
    'standing outside a traditional Japanese tea house, viewing the engawa and garden from outside',
    'standing on a quiet Japanese street with a wooden veranda visible in the background',
    'sitting at an outdoor table of a stylish Japanese cafe, warm cozy atmosphere',
    'standing in a sunlit park with cherry blossom trees, soft spring light',
    'standing near a traditional Japanese gate or stone wall, quiet neighborhood street',
    'standing outside a Bizen pottery shop, ceramic works visible through the window',
]

BIZEN_ITEMS = [
    'holding a rustic Bizen pottery cup with both hands',
    'holding a square angular Bizen sake cup (kakukaku cup) in one hand',
    'holding a small Bizen pottery tea bowl naturally in one hand',
    'carrying a small Bizen pottery vase',
    'holding a Bizen pottery mug casually',
]

# wearista用：センスの良さを褒めるパターン
COMMENT_PATTERNS_WEARISTA = [
    """このコーデ画像を見て、インスタグラムの投稿キャプション文を日本語で書いてください。

書き手: 彰子（フランス×日本ハーフ、備前で陶芸修行中、ガーリーファッション好き）
褒める相手: この画像を投稿したWEARユーザー（彰子ではない別人）

条件:
- 2〜3文、自然でかわいい口調
- 画像の投稿者のコーデの選び方・組み合わせのセンスを具体的に褒める
- 「センスいい」「すごくかわいくて」などテンプレ表現は使わない
- 絵文字を1〜2個

コメント文だけ出力してください（前置き・ラベル不要）。""",

    """このコーデ画像を見て、インスタグラムの投稿キャプション文を日本語で書いてください。

書き手: 彰子（フランス×日本ハーフ、備前で陶芸修行中、ガーリーファッション好き）
褒める相手: この画像を投稿したWEARユーザー（彰子ではない別人）

条件:
- 2〜3文、彰子らしい自然な口調
- たまにフランス語フレーズを自然に混ぜる（"j'adore" "magnifique" "c'est parfait" など）
- 画像の投稿者のアイテムの選び方・色の合わせ方のセンスを褒める
- 絵文字を1〜2個

コメント文だけ出力してください（前置き・ラベル不要）。""",

    """このコーデ画像を見て、インスタグラムの投稿キャプション文を日本語で書いてください。

書き手: 彰子（フランス×日本ハーフ、備前で陶芸修行中、ガーリーファッション好き）
褒める相手: この画像を投稿したWEARユーザー（彰子ではない別人）

条件:
- 2〜3文、柔らかくかわいい口調
- 備前焼や陶芸の日常と自然に絡めながら、画像の投稿者のセンスを褒める（無理やり感NG）
- コーデの独自性や目の付け所を具体的に指摘する
- 絵文字を1〜2個

コメント文だけ出力してください（前置き・ラベル不要）。""",
]

# shop_staff用：ブランドの魅力を伝えるパターン
COMMENT_PATTERNS_SHOP = [
    """このコーデ画像を見て、インスタグラムの投稿キャプション文を日本語で書いてください。

書き手: 彰子（フランス×日本ハーフ、備前で陶芸修行中、ガーリーファッション好き）
紹介する相手: この画像のショップスタッフ（彰子ではない別人）

条件:
- 2〜3文、自然でかわいい口調
- コーデの具体的なアイテム・色・素材感に言及する
- ブランドのアイテムの魅力が伝わる内容にする
- テンプレっぽい表現は使わない
- 絵文字を1〜2個

コメント文だけ出力してください（前置き・ラベル不要）。""",

    """このコーデ画像を見て、インスタグラムの投稿キャプション文を日本語で書いてください。

書き手: 彰子（フランス×日本ハーフ、備前で陶芸修行中、ガーリーファッション好き）
紹介する相手: この画像のショップスタッフ（彰子ではない別人）

条件:
- 2〜3文、彰子らしい自然な口調
- たまにフランス語フレーズを自然に混ぜる（"j'adore" "magnifique" など）
- このブランドのアイテムを着てみたいという気持ちを自然に表現する
- 絵文字を1〜2個

コメント文だけ出力してください（前置き・ラベル不要）。""",
]

# ── 使用済みID管理 ────────────────────────────────────────
POSTED_KEEP_DAYS = 30

def load_posted() -> dict:
    """使用済みURL辞書を読み込む {wear_url: iso_date_string}
    旧形式（{coord_id: {date:..., user_name:...}}）は無視して空で返す"""
    if not POSTED_FILE.exists():
        return {}
    try:
        data = json.loads(POSTED_FILE.read_text())
        # 旧形式チェック: 値がdictならリセット
        if data and isinstance(next(iter(data.values())), dict):
            print('wear_posted.json: 旧形式を検出。新形式にリセットします。')
            return {}
        return data
    except Exception:
        return {}

def save_posted(posted: dict):
    POSTED_FILE.write_text(json.dumps(posted, ensure_ascii=False, indent=2))

def mark_posted(coord_url: str):
    posted = load_posted()
    cutoff = (datetime.now() - timedelta(days=POSTED_KEEP_DAYS)).isoformat()
    posted = {k: v for k, v in posted.items() if isinstance(v, str) and v >= cutoff}
    posted[coord_url] = datetime.now().isoformat()
    save_posted(posted)

# ── ジャスミンAPIからコーデ取得 ───────────────────────────
def fetch_coords_from_jasmine() -> list:
    """ジャスミンAPIから全コーデURLリストを取得"""
    resp = requests.get(JASMINE_COORDS_URL, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    users = data.get('users', [])
    all_coords = []
    for u in users:
        for url in u.get('recent_coords', []):
            all_coords.append({
                'wear_url': url,
                'user': u.get('user', ''),
                'category': u.get('category', ''),
            })
    return all_coords

def fetch_image_url(wear_url: str) -> str:
    """ジャスミンOGP APIでコーデの画像URLを取得"""
    resp = requests.get(JASMINE_OGP_URL, params={'url': wear_url}, timeout=15)
    resp.raise_for_status()
    return resp.json().get('image', '')

def pick_one_coord(category: str) -> dict:
    """指定カテゴリのコーデをユーザー名アルファベット順でローテーション選択する。
    前回のユーザーより大きいユーザーの中からランダムに1コーデ選ぶ。
    それ以上のユーザーがいなければ最初に戻る。
    """
    all_coords = fetch_coords_from_jasmine()
    filtered = [c for c in all_coords if c.get('category') == category]

    # ユーザーごとにまとめる（アルファベット順ソート）
    users_dict = {}
    for c in filtered:
        u = c['user']
        users_dict.setdefault(u, []).append(c)
    sorted_users = sorted(users_dict.keys())

    # 前回のユーザーを取得
    rotation = load_rotation()
    last_user = rotation.get(category, '')
    print(f'前回のユーザー({category}): {last_user or "(なし)"}')

    # 前回より大きいユーザーを探す
    next_users = [u for u in sorted_users if u > last_user]
    if not next_users:
        print(f'ローテーション一周。{category}は最初のユーザーに戻ります。')
        next_users = sorted_users

    # 次のユーザーを選択（先頭から）
    next_user = next_users[0]
    print(f'今回のユーザー({category}): {next_user}')

    # そのユーザーのコーデから未投稿を選ぶ（なければ全部から）
    posted = load_posted()
    user_coords = users_dict[next_user]
    unposted = [c for c in user_coords if c['wear_url'] not in posted]
    if not unposted:
        print(f'{next_user}の全コーデ投稿済み。全コーデから選びます。')
        unposted = user_coords

    return random.choice(unposted)

# ── コメント生成（Gemini Vision） ─────────────────────────
def generate_comment(wear_ref_path: Path, gemini_key: str, category: str = 'wearista') -> str:
    patterns = COMMENT_PATTERNS_WEARISTA if category == 'wearista' else COMMENT_PATTERNS_SHOP
    pattern = random.choice(patterns)
    img_b64 = base64.b64encode(wear_ref_path.read_bytes()).decode()
    payload = {
        'contents': [{
            'parts': [
                {'inline_data': {'mime_type': 'image/jpeg', 'data': img_b64}},
                {'text': pattern}
            ]
        }]
    }
    resp = requests.post(
        f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}',
        json=payload, timeout=30
    )
    result = resp.json()
    return result['candidates'][0]['content']['parts'][0]['text'].strip()

# ═══════════════════════════════════════════════════════════
# STEP 1: ジャスミンAPIからコーデ取得
# ═══════════════════════════════════════════════════════════
print('=== STEP 1: ジャスミンAPIからコーデ取得 ===')

# 今日のカテゴリを決定（日付の奇偶で交互）
today_category = get_today_category()
print(f'今日のカテゴリ: {today_category}')

# --url オプションでURL指定があれば優先
wear_url_arg = None
for i, arg in enumerate(sys.argv[1:]):
    if arg == '--url' and i + 2 <= len(sys.argv) - 1:
        wear_url_arg = sys.argv[i + 2]
        break
    elif arg.startswith('https://wear.jp/'):
        wear_url_arg = arg
        break

if wear_url_arg:
    print(f'URL指定モード: {wear_url_arg}')
    coord = {'wear_url': wear_url_arg, 'user': '', 'category': today_category}
else:
    coord = pick_one_coord(today_category)

wear_url = coord['wear_url']
wear_user = coord['user']
wear_category = coord.get('category', today_category)
print(f'選択コーデ: {wear_url} (user: {wear_user}, category: {wear_category})')

# 画像URL取得
print('画像URL取得中...')
img_url = fetch_image_url(wear_url)
if not img_url:
    print('ERROR: 画像URL取得失敗')
    sys.exit(1)
print(f'画像URL: {img_url}')

# ═══════════════════════════════════════════════════════════
# STEP 2: コーデ画像ダウンロード
# ═══════════════════════════════════════════════════════════
print('\n=== STEP 2: コーデ画像ダウンロード ===')
r = requests.get(img_url, timeout=15)
WEAR_REF.write_bytes(r.content)
print(f'downloaded: {WEAR_REF} ({WEAR_REF.stat().st_size} bytes)')

# ═══════════════════════════════════════════════════════════
# STEP 3: 彰子バージョン生成
# ═══════════════════════════════════════════════════════════
print('\n=== STEP 3: 画像生成 ===')

gemini_key = GEMINI_KEY_F.read_text().strip()
GEN_DIR.mkdir(parents=True, exist_ok=True)
out_path = GEN_DIR / f'gen_wear_{int(time.time())}.png'

bg_prompt  = random.choice(BACKGROUNDS)
bizen_item = random.choice(BIZEN_ITEMS)
print(f'背景: {bg_prompt}')
print(f'備前焼アイテム: {bizen_item}')

refs = [
    {'path': str(AKIKO_PURE), 'label': 'A'},
    {'path': str(WEAR_REF),   'label': 'B'},
]
prompt = (
    'vibrant anime style, clean cel shading. '
    'Draw character A exactly as shown — keep her face, hair color, hairstyle, and hair length EXACTLY the same as in image A. Do NOT change the hairstyle. '
    'Replace her outfit completely with the fashion coordinate shown in image B — '
    'reproduce the exact same clothes, colors, and styling from image B. '
    'Anime body proportions: 6.5-head-tall figure, slim but cute and youthful, NOT too tall and NOT too short, balanced anime style. '
    'Do NOT use realistic or model proportions. '
    f'Character A is {bizen_item}. '
    'Character A is smiling and looking at the camera, full-body pose. '
    f'Background: {bg_prompt}, bokeh blur, character in sharp focus. '
    'NOT photorealistic.'
)

result = subprocess.run(
    ['node', str(GEN_JS), prompt, str(out_path), gemini_key,
     json.dumps(refs), 'gemini-3-pro-image-preview', '3:4'],
    capture_output=True, text=True
)
print(result.stdout)
if result.returncode != 0:
    print('ERROR:', result.stderr)
    sys.exit(1)

# ═══════════════════════════════════════════════════════════
# STEP 4: IG投稿準備（4:5リサイズ）
# ═══════════════════════════════════════════════════════════
print('\n=== STEP 4: IG投稿準備 ===')
IG_HOSTING.mkdir(exist_ok=True)

# 前日以前の一時ファイル削除
yesterday_ts = int((datetime.now() - timedelta(days=1)).timestamp())
for f in IG_HOSTING.glob('ig_*'):
    parts = f.stem.split('_')
    if len(parts) >= 2:
        try:
            if int(parts[1]) < yesterday_ts:
                f.unlink()
        except Exception:
            pass

img = Image.open(out_path).convert('RGB')
w, h = img.size
ratio = w / h

if ratio < 0.8:
    target_h = int(w / 0.8)
    if target_h > h:
        arr = np.array(img)
        pad_color = np.concatenate([arr[:, :5, :], arr[:, -5:, :]], axis=1).mean(axis=(0, 1)).astype(np.uint8)
        pad_total = target_h - h
        pad_top   = pad_total // 2
        pad_bot   = pad_total - pad_top
        top = np.full((pad_top, w, 3), pad_color, dtype=np.uint8)
        bot = np.full((pad_bot, w, 3), pad_color, dtype=np.uint8)
        img = Image.fromarray(np.concatenate([top, np.array(img), bot], axis=0))
elif ratio > 1.91:
    new_w = int(h * 1.91)
    left  = (w - new_w) // 2
    img   = img.crop((left, 0, left + new_w, h))

ts  = int(time.time())
dst = IG_HOSTING / f'ig_{ts}_0.jpg'
img.save(dst, 'JPEG', quality=92)
image_url = f'{IG_HOSTING_URL}/ig_{ts}_0.jpg'
print(f'image_url: {image_url}')

# ═══════════════════════════════════════════════════════════
# STEP 5: コメント生成 & IG投稿
# ═══════════════════════════════════════════════════════════
print('\n=== STEP 5: コメント生成 ===')
comment_body = generate_comment(WEAR_REF, gemini_key, wear_category)
print(f'生成コメント:\n{comment_body}')

user_mention = f'@{wear_user}' if wear_user else ''

# カテゴリ別キャプション
if wear_category == 'shop_staff':
    brand_name, brand_tags = get_brand_info(wear_user)
    brand_line = f'（{brand_name}）' if brand_name else ''
    caption = f"""今日の「参考にしました」コーデ🎀

{user_mention} さん{brand_line}のコーデ参考にしました✨
{comment_body}

詳しくはこちら→ {wear_url}

#備前焼 #陶芸 #ファッション #ガーリーコーデ #WEAR #bizenpottery #BizenyAkiko #コーデ参考 {brand_tags}"""
else:
    # wearista：センスを褒めるキャプション
    caption = f"""今日の「参考にしました」コーデ🎀

{user_mention} さんのコーデ参考にしました✨
{comment_body}

詳しくはこちら→ {wear_url}

#備前焼 #陶芸 #ファッション #ガーリーコーデ #WEAR #bizenpottery #BizenyAkiko #コーデ参考 #wearista"""

print('\n=== STEP 5b: IG投稿 ===')
cred  = json.loads(CREDS.read_text())
token = cred['access_token']

resp = requests.post(
    f'https://graph.instagram.com/v22.0/{IG_USER_ID}/media',
    data={'image_url': image_url, 'caption': caption, 'access_token': token}
)
print('container:', resp.json())
container_id = resp.json().get('id')
if not container_id:
    print('ERROR: container ID取得失敗')
    sys.exit(1)

for _ in range(12):
    time.sleep(5)
    st = requests.get(
        f'https://graph.instagram.com/v22.0/{container_id}',
        params={'fields': 'status_code', 'access_token': token}
    )
    status = st.json().get('status_code')
    print(f'status: {status}')
    if status == 'FINISHED':
        break

resp2 = requests.post(
    f'https://graph.instagram.com/v22.0/{IG_USER_ID}/media_publish',
    data={'creation_id': container_id, 'access_token': token}
)
print('published:', resp2.json())

# ── 使用済みURLを記録 & ローテーション状態を保存 ──────────
mark_posted(wear_url)
print(f'✅ {wear_url} を使用済みに記録')

rotation = load_rotation()
rotation[wear_category] = wear_user
save_rotation(rotation)
print(f'✅ ローテーション更新: {wear_category} → {wear_user}')

# ── 結果出力 ──────────────────────────────────────────────
print(f'WEAR_USER: {wear_user}')
print(f'WEAR_URL: {wear_url}')
print(f'WEAR_BG: {bg_prompt}')
print(f'WEAR_ITEM: {bizen_item}')
print(f'WEAR_IMG_PATH: {dst}')

# ── 夕方投稿用にメタデータ保存 ────────────────────────────
import json as _json
wear_meta = {
    'img_path': str(dst),
    'wear_user': wear_user,
    'wear_url': wear_url,
    'bg_prompt': bg_prompt,
    'bizen_item': bizen_item,
    'ts': ts
}
meta_path = Path('/home/bizeny/workspace/data/generated/wear_today.json')
meta_path.write_text(_json.dumps(wear_meta, ensure_ascii=False, indent=2))
print(f'✅ 夕方投稿用メタデータ保存: {meta_path}')
