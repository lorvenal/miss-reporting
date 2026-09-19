import json
import time
import requests
import threading
from pathlib import Path

DATA_DIR   = Path("cherry_data")
LINKS_FILE = DATA_DIR / "message_links.json"

# ─── توكن المُبلِّغ (مختلف عن توكن البوت) ───
REPORTER_TOKEN = "MTU1MDI2OTgwMjcxMzcxODg5Ng.GAY1pc.rQiEhN1jmETc04Q5aI_S9Kb5xdY-d21YzYpJLA"

REASON_MAP = {
    "1": "illegal",
    "2": "harassment",
    "3": "spam",
    "4": "self_harm",
    "5": "nsfw",
}


def load_targets():
    if not LINKS_FILE.exists():
        return []

    content = LINKS_FILE.read_text(encoding="utf-8").strip()

    if not content or content == "{}":
        return []

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        print("[!] الملف تالف")
        return []

    targets = []
    for wid, entries in data.items():
        for e in entries:
            if all(k in e for k in ("guild_id", "channel_id", "msg_id")):
                if e["guild_id"]:
                    targets.append({
                        "guild_id":   e["guild_id"],
                        "channel_id": e["channel_id"],
                        "message_id": e["msg_id"],
                    })
    return targets


def report_once(guild_id, channel_id, message_id, reason, counter):
    """يرسل ريبورت واحد على v9"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "discord/1.0.9175 Chrome/128.0.6613.186 "
            "Electron/32.2.7 Safari/537.36"
        ),
        "Authorization": REPORTER_TOKEN,
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://discord.com",
        "Referer": f"https://discord.com/channels/{guild_id}/{channel_id}",
        "X-Discord-Locale": "en-US",
        "X-Discord-Timezone": "Asia/Riyadh",
    }

    # ⚠️ في v9، الريبورت يحتاج حقل "message_type" و "report_type"
    payload = {
        "channel_id":    channel_id,
        "guild_id":      guild_id,
        "message_id":    message_id,
        "report_type":   reason,
        "message_type":  "default",
    }

    try:
        r = requests.post(
            "https://discord.com/api/v9/report",
            headers=headers, json=payload, timeout=10,
        )
        if r.status_code in (200, 201, 204):
            counter["ok"] += 1
            print(f"[+] OK {r.status_code}  msg={message_id}  total={counter['ok']}")
        elif r.status_code == 401:
            print("[!] token invalid — stopping")
            counter["stop"] = True
        elif r.status_code == 429:
            counter["fail"] += 1
            print(f"[~] rate-limited — sleeping 10s")
            time.sleep(10)
        elif r.status_code == 404:
            counter["fail"] += 1
            print(f"[x] 404 msg not found: {message_id}")
        elif r.status_code == 400:
            counter["fail"] += 1
            try:
                err = r.json()
                print(f"[x] 400 Bad Request: {err}")
            except:
                print(f"[x] 400 Bad Request")
        else:
            counter["fail"] += 1
            print(f"[x] {r.status_code} msg={message_id}")
    except Exception as e:
        counter["fail"] += 1
        print(f"[!] {type(e).__name__}: {str(e)[:100]}")


def mass_report(targets, reason, threads=5):
    """
    ⚠️ threads=5 بدل 500 — لأن Discord يقطع الاتصال لو أكثر
    """
    counter = {"ok": 0, "fail": 0, "stop": False}

    def worker(t):
        while not counter["stop"]:
            report_once(t["guild_id"], t["channel_id"],
                        t["message_id"], reason, counter)
            # ⏱️ تأخير 3 ثواني بين كل ريبورت — مهم جداً
            time.sleep(3)

    # 5 ثريد بس لكل هدف (بدل 500)
    for t in targets:
        for _ in range(threads):
            threading.Thread(target=worker, args=(t,), daemon=True).start()

    while not counter["stop"]:
        time.sleep(5)
        print(f"── ok={counter['ok']}  fail={counter['fail']} ──")


def main():
    print("═" * 50)
    print("  Cherry Reporter v9")
    print("═" * 50)
    print(" {1} illegal  {2} harassment  {3} spam  {4} self-harm  {5} nsfw")
    reason_key = input(" > اختر السبب: ").strip()
    reason = REASON_MAP.get(reason_key, "spam")

    targets = load_targets()
    if not targets:
        print("[!] ما فيه أهداف. شغّل البوت السيلف وسوي !rooms / !fire أول")
        return

    # إزالة التكرار
    unique = {}
    for t in targets:
        unique[t["message_id"]] = t
    targets = list(unique.values())

    print(f"[*] عدد الأهداف الفريدة: {len(targets)}")
    print(f"[*] السبب: {reason}")
    print(f"[*] Threads per target: 5")
    print(f"[*] Delay: 3s")
    input(" > Enter للبدء...")

    mass_report(targets, reason, threads=5)


if __name__ == "__main__":
    main()