#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات تلگرام دیده‌بان ۲۴ ساعته کافه‌بازار و مایکت (ویژه GitHub Actions و سرور)
- CafeBazaar API: GetPageV2Request با مسیر list~app~automatic~APP_NEW~<slug>
- Myket API: GET /v1/applications/package/Category_New_<id>?limit=24&offset=0
- ذخیره خودکار برنامه‌های ارسال‌شده در seen_apps.json برای جلوگیری از ارسال تکراری در GitHub Actions
"""

import argparse
import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path
import requests

# ==================== تنظیمات از GitHub Secrets یا مقادیر پیش‌فرض ====================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
MAX_APPS_PER_CATEGORY = int(os.environ.get("MAX_APPS_PER_CATEGORY", "24"))
SCAN_INTERVAL_SECONDS = int(os.environ.get("SCAN_INTERVAL_HOURS", "24")) * 3600
SEEN_APPS_FILE = Path(os.environ.get("SEEN_APPS_FILE", "seen_apps.json"))

# ==================== اندپوینت‌های رسمی کافه‌بازار و مایکت ====================
BAZAAR_PAGE_URL = "https://api.cafebazaar.ir/rest-v1/process/GetPageV2Request"
BAZAAR_DETAIL_URL = "https://api.cafebazaar.ir/rest-v1/process/AppDetailsV2Request"

MYKET_SERVERS = [
    "https://apiserver2172.myket.ir",
    "https://apiserver8262.myket.ir",
    "https://apiserver221.myket.ir",
    "https://apiserver210.myket.ir",
    "https://apiserver.myket.ir",
]
MYKET_SALT = "NZe*x:38_Jh@#LM6)!9&wb5:32D"
MYKET_VERSION = "1017"

CATEGORIES = [
    {
        "slug": "tools",
        "bazaar_list_path": "list~app~automatic~APP_NEW~tools",
        "myket_new_package_key": "Category_New_14",
        "title_fa": "ابزارها"
    },
    {
        "slug": "social",
        "bazaar_list_path": "list~app~automatic~APP_NEW~social",
        "myket_new_package_key": "Category_New_32",
        "title_fa": "شبکه‌های اجتماعی"
    },
    {
        "slug": "finance",
        "bazaar_list_path": "list~app~automatic~APP_NEW~finance",
        "myket_new_package_key": "Category_New_20",
        "title_fa": "امور مالی"
    },
    {
        "slug": "education",
        "bazaar_list_path": "list~app~automatic~APP_NEW~education",
        "myket_new_package_key": "Category_New_24",
        "title_fa": "آموزش"
    },
    {
        "slug": "entertainment",
        "bazaar_list_path": "list~app~automatic~APP_NEW~entertainment",
        "myket_new_package_key": "Category_New_11",
        "title_fa": "سرگرمی"
    },
    {
        "slug": "shopping",
        "bazaar_list_path": "list~app~automatic~APP_NEW~shopping",
        "myket_new_package_key": "Category_New_15",
        "title_fa": "خرید"
    },
    {
        "slug": "photography",
        "bazaar_list_path": "list~app~automatic~APP_NEW~photography",
        "myket_new_package_key": "Category_New_4",
        "title_fa": "عکاسی و ویدیو"
    },
    {
        "slug": "medical",
        "bazaar_list_path": "list~app~automatic~APP_NEW~medical",
        "myket_new_package_key": "Category_New_33",
        "title_fa": "پزشکی"
    },
    {
        "slug": "action",
        "bazaar_list_path": "list~app~automatic~APP_NEW~action",
        "myket_new_package_key": "Category_New_26",
        "title_fa": "بازی اکشن"
    },
    {
        "slug": "strategy",
        "bazaar_list_path": "list~app~automatic~APP_NEW~strategy",
        "myket_new_package_key": "Category_New_124",
        "title_fa": "بازی استراتژی"
    }
]


def load_seen_apps() -> set:
    if SEEN_APPS_FILE.exists():
        try:
            data = json.loads(SEEN_APPS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return set(data)
        except Exception:
            pass
    return set()


def save_seen_apps(seen: set):
    SEEN_APPS_FILE.write_text(
        json.dumps(sorted(list(seen)), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clean_html(raw_html: str) -> str:
    if not raw_html:
        return "توضیحاتی برای این برنامه ثبت نشده است."
    text = re.sub(r"<\s*br\s*/?>", "\n", raw_html, flags=re.IGNORECASE)
    text = re.sub(r"</\s*(p|div|li)\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[\u200b\u200e\u200f\u202a-\u202e]", "", text)
    text = re.sub(r"\n\s*\n+", "\n", text).strip()
    return text[:450] + ("…" if len(text) > 450 else "")


def fetch_bazaar_automatic_new_list(bazaar_list_path: str, title_fa: str):
    payload = {
        "properties": {
            "clientID": "xosfmx0w3h4imuraeuzo6drbadccuqsh",
            "clientVersion": "web",
            "deviceID": "xosfmx0w3h4imuraeuzo6drbadccuqsh",
            "language": 2
        },
        "singleRequest": {
            "getPageV2Request": {"path": bazaar_list_path}
        }
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.post(BAZAAR_PAGE_URL, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    rows = (
        resp.json()
        .get("singleReply", {})
        .get("getPageV2Reply", {})
        .get("page", {})
        .get("pageBodyInfo", {})
        .get("pageBody", {})
        .get("rows", [])
    )

    apps = []
    for row in rows:
        item = row.get("simpleAppItem", {})
        if not item or item.get("isAd"):
            continue
        info = item.get("info", {})
        pkg = info.get("packageName")
        if not pkg:
            continue

        detail_payload = {"singleRequest": {"appDetailsV2Request": {"packageName": pkg}}}
        detail_headers = {
            "Content-Type": "application/json",
            "x-device-info": "PHONE/arm64-v8a|GMS",
            "User-Agent": "Bazaar/2600200 (Android 35; Xiaomi 2311DRK48G)"
        }
        desc = info.get("shortDescription", "")
        icon_url = info.get("image", "")
        author = info.get("authorName", "توسعه‌دهنده کافه‌بازار")
        version = "نسخه جدید"
        try:
            d_resp = requests.post(BAZAAR_DETAIL_URL, json=detail_payload, headers=detail_headers, timeout=10)
            reply = d_resp.json().get("singleReply", {}).get("appDetailsV2Reply", {})
            meta = reply.get("meta", {})
            media = reply.get("media", {})
            pkg_meta = reply.get("package", {})
            desc = meta.get("description") or meta.get("shortDescription") or desc
            icon_url = icon_url or media.get("iconUrl", "")
            author = meta.get("author", {}).get("name") or author
            version = pkg_meta.get("versionName") or version
        except Exception:
            pass

        apps.append({
            "market": "کافه‌بازار",
            "category": title_fa,
            "package": pkg,
            "name": (info.get("name") or pkg).strip(),
            "author": author,
            "version": version,
            "icon": icon_url,
            "description": clean_html(desc),
            "url": f"https://cafebazaar.ir/app/{pkg}"
        })
        if len(apps) >= MAX_APPS_PER_CATEGORY:
            break
    return apps


def authorize_myket():
    for server_url in MYKET_SERVERS:
        try:
            u = str(uuid.uuid4())
            hsh_input = f"{MYKET_SALT}-{u}---".encode("utf-8")
            hsh = hashlib.sha1(hsh_input).hexdigest()
            body = {
                "acId": "",
                "acKey": "",
                "api": "35",
                "adId": str(uuid.uuid4()),
                "andId": os.urandom(8).hex(),
                "hsh": hsh,
                "supportedAbis": ["arm64-v8a"],
                "uuid": u,
            }
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "myket-version": MYKET_VERSION,
                "User-Agent": f"Myket/{MYKET_VERSION} (Android 35; Xiaomi 2311DRK48G)"
            }
            resp = requests.post(f"{server_url}/v1/devices/authorize", json=body, headers=headers, timeout=10)
            if resp.status_code == 200 and "token" in resp.json():
                return server_url, resp.json()["token"]
        except Exception:
            continue
    raise RuntimeError("عدم دریافت توکن از سرورهای مایکت")


def fetch_myket_category_newest(server_url: str, token: str, package_key: str, title_fa: str):
    headers = {
        "Authorization": token,
        "myket-version": MYKET_VERSION,
        "Accept-Language": "fa",
        "Accept": "application/json",
        "User-Agent": f"Myket/{MYKET_VERSION} (Android 35; Xiaomi 2311DRK48G)"
    }
    params = {"limit": MAX_APPS_PER_CATEGORY, "offset": 0}
    resp = requests.get(
        f"{server_url}/v1/applications/package/{package_key}",
        params=params,
        headers=headers,
        timeout=15
    )
    resp.raise_for_status()
    items = resp.json().get("appPlusMetaDataList", [])

    apps = []
    for app in items:
        if not app or app.get("adInfo"):
            continue
        pkg = app.get("packageName")
        if not pkg:
            continue

        desc = app.get("tagline", "")
        icon_url = app.get("iconPath", "")
        author = app.get("developerName", "توسعه‌دهنده مایکت")
        version = app.get("version", "۱.۰")
        try:
            d_resp = requests.get(f"{server_url}/v2/applications/{pkg}", headers=headers, timeout=10)
            if d_resp.status_code == 200:
                d_json = d_resp.json()
                desc = d_json.get("description", {}).get("text") or desc
                icon_url = d_json.get("icon", {}).get("url") or icon_url
                author = d_json.get("developer", {}).get("name") or author
                version = d_json.get("version", {}).get("name") or version
        except Exception:
            pass

        apps.append({
            "market": "مایکت",
            "category": title_fa,
            "package": pkg,
            "name": re.sub(r"[\u200b\u200e\u200f]", "", (app.get("farsiTitle") or app.get("title") or pkg)).strip(),
            "author": author,
            "version": version,
            "icon": icon_url,
            "description": clean_html(desc),
            "url": f"https://myket.ir/app/{pkg}"
        })
        if len(apps) >= MAX_APPS_PER_CATEGORY:
            break
    return apps


def send_to_telegram(app_data: dict) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[DRY-RUN] {app_data['market']} | {app_data['category']} -> {app_data['name']} ({app_data['package']})")
        return True

    caption = (
        f"🔔 جدیدترین برنامه در {app_data['market']}\n"
        f"--------------------\n"
        f"📱 نام برنامه: {app_data['name']}\n"
        f"📂 دسته‌بندی: {app_data['category']} ({app_data['market']})\n"
        f"👤 توسعه‌دهنده: {app_data['author']} · نسخه: {app_data['version']}\n"
        f"🖼 آیکون برنامه: {app_data['icon']}\n\n"
        f"📝 توضیحات برنامه:\n{app_data['description']}\n\n"
        f"🔗 مشاهده و دانلود از {app_data['market']}:\n{app_data['url']}"
    )
    try:
        if app_data["icon"]:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            r = requests.post(
                url,
                json={"chat_id": TELEGRAM_CHAT_ID, "photo": app_data["icon"], "caption": caption},
                timeout=15,
            )
            if r.ok and r.json().get("ok"):
                return True
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        r = requests.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": caption},
            timeout=15,
        )
        return bool(r.ok and r.json().get("ok"))
    except Exception as e:
        print(f"خطا در ارسال به تلگرام ({app_data['package']}): {e}")
        return False


def run_single_scan():
    seen_apps = load_seen_apps()
    print(f"شروع اسکن جدیدترین‌های کافه‌بازار و مایکت (برنامه‌های قبلی در حافظه: {len(seen_apps)})...")

    myket_session = None
    try:
        myket_session = authorize_myket()
    except Exception as e:
        print(f"خطا در اتصال به مایکت: {e}")

    new_sent = 0
    for cat in CATEGORIES:
        try:
            bazaar_apps = fetch_bazaar_automatic_new_list(cat["bazaar_list_path"], cat["title_fa"])
            for app in bazaar_apps:
                key = f"bazaar:{app['package']}"
                if key not in seen_apps:
                    if send_to_telegram(app):
                        seen_apps.add(key)
                        new_sent += 1
                        time.sleep(1.1)
        except Exception as e:
            print(f"خطا در کافه‌بازار ({cat['title_fa']}): {e}")

        if myket_session:
            server_url, myket_token = myket_session
            try:
                myket_apps = fetch_myket_category_newest(
                    server_url, myket_token, cat["myket_new_package_key"], cat["title_fa"]
                )
                for app in myket_apps:
                    key = f"myket:{app['package']}"
                    if key not in seen_apps:
                        if send_to_telegram(app):
                            seen_apps.add(key)
                            new_sent += 1
                            time.sleep(1.1)
            except Exception as e:
                print(f"خطا در مایکت ({cat['title_fa']}): {e}")

    save_seen_apps(seen_apps)
    print(f"اسکن کامل شد. {new_sent} برنامه جدید ارسال و در {SEEN_APPS_FILE} ذخیره شد.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bazar & Myket 24h Telegram Radar Bot")
    parser.add_argument("--loop", action="store_true", help="اجرای دائمی ۲۴ ساعته روی سرور")
    args = parser.parse_args()

    if args.loop:
        while True:
            run_single_scan()
            time.sleep(SCAN_INTERVAL_SECONDS)
    else:
        run_single_scan()
