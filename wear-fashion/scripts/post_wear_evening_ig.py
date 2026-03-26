"""
wear_evening_ig.py
朝のWEARコーデ画像をrefに、夕方バージョンを生成してIG投稿する。
wear_today.json（朝のジョブが書く）を読んで動く。
"""
import json, os, random, subprocess, sys, time, shutil, requests
from pathlib import Path
from PIL import Image

# ── 設定 ────────────────────────────────────────────────
WORKSPACE     = Path('/home/bizeny/workspace')
META_PATH     = WORKSPACE / 'data/generated/wear_today.json'
CAST_REF      = WORKSPACE / 'data/casts/akiko/pure.jpg'
GEN_JS        = WORKSPACE / 'scripts/nanobanana/gen.js'
GEMINI_KEY    = (WORKSPACE / 'config/google/gemini_api_key').read_text().strip()
IG_HOSTING    = WORKSPACE / 'projects/www/images/ig_hosting'
IG_HOSTING_URL = 'https://bizeny.bon-soleil.com/images/ig_hosting'
IG_USER_ID    = '26416648414607450'
CRED_PATH     = Path('/home/bizeny/.config/instagram/bizenyakiko_credentials.json')

# ── 夕方シーン（朝と異なる場所） ────────────────────────
EVENING_SCENES = [
    "sitting at a cozy Japanese cafe, leaning on the table with both hands around a Bizen-yaki coffee cup, relaxed happy smile, warm wooden interior, soft evening light",
    "sitting on a park bench at sunset, legs crossed, looking up at the sky with a content expression, golden light filtering through the trees",
    "sitting across a table at a Japanese restaurant, laughing with a friend off-screen, Bizen-yaki dishes on the table, warm izakaya atmosphere",
    "sitting on a traditional engawa veranda, legs dangling, holding a Bizen-yaki cup with both hands, looking out at the garden with a peaceful smile, dusk light",
    "leaning against a railing on a quiet riverside path at dusk, looking at the water with a dreamy expression, golden hour light",
    "sitting cross-legged on a cushion in a cozy Japanese room, reading a book, Bizen-yaki tea cup beside her, warm lamp light",
    "sitting at an outdoor terrace cafe, chin resting on one hand, watching the sunset with a soft smile, warm golden light on her face",
]

# ── メタデータ読み込み ───────────────────────────────────
if not META_PATH.exists():
    print('ERROR: wear_today.json が見つかりません。朝のWEARジョブが先に実行されている必要があります。')
    sys.exit(1)

meta = json.loads(META_PATH.read_text())
morning_img = Path(meta['img_path'])
wear_user   = meta['wear_user']
wear_url    = meta['wear_url']
bizen_item  = meta['bizen_item']

if not morning_img.exists():
    print(f'ERROR: 朝の画像が見つかりません: {morning_img}')
    sys.exit(1)

print(f'朝の画像: {morning_img}')
print(f'参考コーデ: {wear_user} / {wear_url}')

# ── 夕方シーン選択 ───────────────────────────────────────
scene = random.choice(EVENING_SCENES)
print(f'夕方シーン: {scene}')

# ── 画像生成 ─────────────────────────────────────────────
print('\n=== 画像生成 ===')
ts = int(time.time())
out_path = WORKSPACE / f'data/generated/wear_evening_{ts}.jpg'

refs = json.dumps([
    {"path": str(CAST_REF), "label": "A"},
    {"path": str(morning_img), "label": "B"},
])

prompt = (
    f"semi-realistic anime style, detailed facial features, soft lighting. "
    f"Akiko wearing the same outfit as character B, {scene}, "
    f"holding {bizen_item}, natural relaxed end-of-day expression, warm evening atmosphere."
)

result = subprocess.run(
    ['node', str(GEN_JS), prompt, str(out_path), GEMINI_KEY, refs, 'gemini-3-pro-image-preview', '3:4'],
    capture_output=True, text=True, timeout=120
)
print(result.stdout)
if result.returncode != 0:
    print('ERROR:', result.stderr)
    sys.exit(1)

# ── 4:5リサイズ ──────────────────────────────────────────
print('\n=== 4:5リサイズ ===')
img = Image.open(out_path).convert('RGB')
w, h = img.size
target_h = int(w * 5 / 4)
if target_h > h:
    pad = (target_h - h) // 2
    from PIL import ImageOps
    img = ImageOps.expand(img, border=(0, pad, 0, target_h - h - pad), fill=(245, 240, 235))
else:
    top = (h - target_h) // 2
    img = img.crop((0, top, w, top + target_h))

dst = IG_HOSTING / f'ig_{ts}_evening.jpg'
IG_HOSTING.mkdir(exist_ok=True)
img.save(dst, 'JPEG', quality=92)
image_url = f'{IG_HOSTING_URL}/ig_{ts}_evening.jpg'
print(f'保存: {dst}')

# ── キャプション生成 ──────────────────────────────────────
caption = (
    f"今日もこのコーデで過ごしました☀️\n\n"
    f"朝から備前の工房で、夕方までこのスタイルで。\n"
    f"動きやすくて、なんだかずっと気分よく過ごせました。\n\n"
    f"@{wear_user} さんのコーデを参考にしました。ありがとうございます✨\n"
    f"詳しくはこちら→ {wear_url}\n\n"
    f"#備前焼 #陶芸 #ファッション #今日のコーデ #WEAR #bizenpottery #BizenyAkiko"
)
print(f'\nキャプション:\n{caption}')

# ── IG投稿 ───────────────────────────────────────────────
print('\n=== IG投稿 ===')
cred  = json.loads(CRED_PATH.read_text())
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

print(f'\nWEAR_USER: {wear_user}')
print(f'WEAR_URL: {wear_url}')
print(f'WEAR_EVENING_IMG: {dst}')
