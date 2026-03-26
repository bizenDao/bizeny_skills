#!/usr/bin/env python3
"""
WEAR ガーリーコーデ スクレイパー
- SOCKSプロキシ経由（localhost:1080 = teddy経由日本IP）
- 人気順上位からランダムに1件選んでコーデ情報を返す
- 使用済みIDは wear_posted.json に記録して重複回避
"""
import json, re, sys, random, requests
from datetime import datetime, timedelta
from pathlib import Path

PROXIES = {'http': 'socks5h://localhost:1080', 'https': 'socks5h://localhost:1080'}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'Accept-Language': 'ja,en-US;q=0.9',
}

# ガーリー系タグID一覧
TAG_IDS = {
    'girly': '2198',
    'feminine': '2201',
    'casual': '2200',
}

# 使用済みIDの記録ファイル（30日以上前のIDは自動削除）
POSTED_FILE = Path('/home/bizeny/workspace/data/wear_posted.json')
POSTED_KEEP_DAYS = 30


def load_posted() -> dict:
    """使用済みコーデID辞書を読み込む {id: iso_date}"""
    if not POSTED_FILE.exists():
        return {}
    try:
        return json.loads(POSTED_FILE.read_text())
    except Exception:
        return {}


def save_posted(posted: dict):
    """使用済みコーデID辞書を保存（30日以上前のIDを自動削除）"""
    cutoff = datetime.now() - timedelta(days=POSTED_KEEP_DAYS)
    cleaned = {}
    for k, v in posted.items():
        date_str = v['date'] if isinstance(v, dict) else v
        try:
            if datetime.fromisoformat(date_str) > cutoff:
                cleaned[k] = v
        except Exception:
            pass
    POSTED_FILE.parent.mkdir(parents=True, exist_ok=True)
    POSTED_FILE.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2))
    return cleaned


def mark_posted(coord_id: int, user_name: str = ''):
    """コーデIDを使用済みに記録"""
    posted = load_posted()
    posted[str(coord_id)] = {
        'date': datetime.now().isoformat(),
        'user_name': user_name,
    }
    save_posted(posted)


def recent_users(n: int = 10) -> set:
    """直近n件の投稿ユーザー名セットを返す"""
    posted = load_posted()
    items = sorted(
        [(k, v) for k, v in posted.items() if isinstance(v, dict)],
        key=lambda x: x[1]['date'],
        reverse=True
    )
    return {v['user_name'] for _, v in items[:n] if v.get('user_name')}


DEFAULT_SEARCH_URL = 'https://wear.jp/coordinate/?from_age=18&tag_ids=1132&type_id=2&user_type=2'

def fetch_coordinates(tag_id=None, limit=30, search_url=None):
    """WEARからコーデ一覧を取得"""
    url = search_url or DEFAULT_SEARCH_URL
    resp = requests.get(url, headers=HEADERS, proxies=PROXIES, timeout=45)
    html = resp.text

    idx = html.find('__NEXT_DATA__')
    if idx < 0:
        return []
    start = html.index('>', idx) + 1
    end = html.index('</script>', start)
    data = json.loads(html[start:end])

    fallback = data.get('props', {}).get('pageProps', {}).get('fallback', {})
    key = list(fallback.keys())[0]
    tiles = fallback[key].get('content_tiles', [])

    results = []
    seen_users = set()
    for tile in tiles:
        if tile.get('content_tile_type') != 'coordinate_tile':
            continue
        c = tile['coordinate_tile']['coordinate']
        member = c.get('member', {})
        user_name = member.get('user_name', '')
        # 同一ユーザーの重複を除外
        if user_name in seen_users:
            continue
        seen_users.add(user_name)
        results.append({
            'id': c.get('id'),
            'user_name': user_name,
            'nick_name': member.get('nick_name', ''),
            'title': c.get('display_title', ''),
            'img_url': c.get('image', {}).get('url_1000', ''),
            'wear_url': c.get('url', ''),
            'is_wearista': member.get('is_wearista', False),
        })
        if len(results) >= limit:
            break

    return results


def fetch_instagram_id(wear_username):
    """WEARユーザーページからInstagram IDを取得"""
    url = f'https://wear.jp/{wear_username}/'
    try:
        resp = requests.get(url, headers=HEADERS, proxies=PROXIES, timeout=10)
        hits = re.findall(r'instagram\.com/([^/"\'\\]+)', resp.text)
        hits = [h for h in hits if h not in ('wear_official',) and not h.startswith('_')]
        seen = []
        for h in hits:
            if h not in seen:
                seen.append(h)
        return seen[0] if seen else None
    except Exception:
        return None


def fetch_by_url(wear_url: str) -> dict:
    """WEARコーデのURLから直接コーデ情報を取得する"""
    import re
    resp = requests.get(wear_url, headers=HEADERS, proxies=PROXIES, timeout=45)
    idx = resp.text.find('__NEXT_DATA__')
    if idx < 0:
        return None
    start = resp.text.index('>', idx) + 1
    end = resp.text.index('</script>', start)
    data = json.loads(resp.text[start:end])
    props = data.get('props', {}).get('pageProps', {})
    coord = props.get('coordinate', {})
    member = coord.get('member', {})
    ig_id = fetch_instagram_id(member.get('user_name', ''))
    return {
        'id': coord.get('id'),
        'user_name': member.get('user_name', ''),
        'nick_name': member.get('nick_name', ''),
        'title': coord.get('display_title', ''),
        'img_url': coord.get('image', {}).get('url_1000', ''),
        'wear_url': wear_url,
        'is_wearista': member.get('is_wearista', False),
        'instagram_id': ig_id,
    }


def pick_one(tag_id=None, prefer_wearista=True):
    """未使用のコーデを1件選んでIG IDも付与して返す"""
    coords = fetch_coordinates(limit=30)
    if not coords:
        return None

    posted = load_posted()
    recent = recent_users(10)

    # 使用済みIDを除外 & 直近10件のユーザーを除外
    unused = [
        c for c in coords
        if str(c['id']) not in posted and c['user_name'] not in recent
    ]
    if not unused:
        # ユーザー除外だけ緩めて再試行（ID重複は除外したまま）
        unused = [c for c in coords if str(c['id']) not in posted]
    if not unused:
        # 全件使用済みならリセット
        print('⚠️ 全件使用済み。履歴をリセットして再選択します', file=sys.stderr)
        save_posted({})
        unused = coords

    # ウェアリスタ優先
    wearistas = [c for c in unused if c['is_wearista']]
    pool = wearistas if (prefer_wearista and wearistas) else unused
    coord = random.choice(pool[:10])

    # Instagram IDを取得
    ig_id = fetch_instagram_id(coord['user_name'])
    coord['instagram_id'] = ig_id

    return coord


if __name__ == '__main__':
    tag_id = sys.argv[1] if len(sys.argv) > 1 else '2198'
    result = pick_one(tag_id)
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print('{}')
        sys.exit(1)
