import discord
from discord.ext import commands
import asyncio
import time
import json
import os

# ─────────────── الإعدادات ───────────────
TOKEN = "MTM1ODkwNTk0MDUwOTcyMDY2OA.G43eTY.3gZ5V3D8miCW93WTI6AdsuINjSj4dIcmyB0HDs"
PREFIX = "!"
# ─────────────────────────────────────────

os.makedirs("cherry_data", exist_ok=True)

SAVE_FILE  = "cherry_data/webhooks.json"
LINKS_FILE = "cherry_data/message_links.json"

client = commands.Bot(command_prefix=PREFIX, self_bot=True)

webhook_bank = {}
message_links = {}
fire_task = None


# ═════════════════════════════════════════
# 🔧 دوال مساعدة
# ═════════════════════════════════════════
def parse_time(value: str) -> float:
    value = value.strip().lower()
    try:
        return float(value)
    except ValueError:
        pass
    units = {
        's': 1, 'sec': 1, 'second': 1, 'ث': 1, 'ثانية': 1, 'ثواني': 1,
        'm': 60, 'min': 60, 'minute': 60, 'د': 60, 'دقيقة': 60, 'دقائق': 60,
        'h': 3600, 'hr': 3600, 'hour': 3600, 'س': 3600, 'ساعة': 3600, 'ساعات': 3600,
    }
    for unit, multiplier in units.items():
        if value.endswith(unit):
            try:
                num = float(value[:-len(unit)].strip())
                return num * multiplier
            except ValueError:
                continue
    raise ValueError(f"❌ صيغة وقت غير صحيحة: {value}")


def human_time(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds:.2f} ثانية"
    elif seconds < 60:
        return f"{seconds:.1f} ثانية"
    elif seconds < 3600:
        return f"{seconds/60:.1f} دقيقة"
    else:
        return f"{seconds/3600:.2f} ساعة"


def save_bank():
    with open(SAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(webhook_bank, f, indent=2, ensure_ascii=False)


def load_bank():
    global webhook_bank
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                webhook_bank = json.load(f)
        except:
            webhook_bank = {}


def save_links():
    with open(LINKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(message_links, f, indent=2, ensure_ascii=False)


def load_links():
    global message_links
    if os.path.exists(LINKS_FILE):
        try:
            content = open(LINKS_FILE, 'r', encoding='utf-8').read().strip()
            if content and content != "{}":
                message_links = json.loads(content)
        except:
            message_links = {}


def build_link(guild_id, channel_id, msg_id) -> str:
    return f"https://discord.com/channels/{guild_id}/{channel_id}/{msg_id}"


# ═════════════════════════════════════════
# 🚀 on_ready
# ═════════════════════════════════════════
@client.event
async def on_ready():
    load_bank()
    load_links()
    linked = sum(1 for w in webhook_bank.values() if w.get("linked_to"))
    total_links = sum(len(v) for v in message_links.values())
    print(f"✅ تم تسجيل الدخول: {client.user}")
    print(f"🏦 البنك: {len(webhook_bank)} (مربوط: {linked})")
    print(f"📎 روابط محفوظة: {total_links}")
    print("─" * 50)


# ═════════════════════════════════════════
# 📦 إنشاء ويبوكات
# ═════════════════════════════════════════
@client.command()
async def hooks(ctx, count: int = 20, name: str = "webhook"):
    if count < 1 or count > 200:
        return await ctx.send("⚠️ العدد بين 1 و 200")

    try:
        await ctx.message.delete()
    except:
        pass

    guild = ctx.guild
    msg = await ctx.send(f"⚡ **إنشاء {count} ويبوك...**")

    temp_channel = await guild.create_text_channel(name="temp-hooks")

    created = 0
    failed = 0
    batch_size = 3

    for batch_start in range(0, count, batch_size):
        batch_end = min(batch_start + batch_size, count)
        batch_tasks = []

        for i in range(batch_start + 1, batch_end + 1):
            batch_tasks.append(temp_channel.create_webhook(name=f"{name}-{i}"))

        results = await asyncio.gather(*batch_tasks, return_exceptions=True)

        for idx, result in enumerate(results):
            i = batch_start + idx + 1
            if isinstance(result, Exception):
                failed += 1
                print(f"❌ [{i}/{count}] {result}")
            else:
                webhook_bank[str(result.id)] = {
                    "url": result.url,
                    "name": result.name,
                    "token": result.token,
                    "id": str(result.id),
                    "guild_id": str(guild.id),
                    "temp_channel": str(temp_channel.id),
                    "channel_name": None,
                    "linked_to": None,
                }
                created += 1
                print(f"✅ [{i}/{count}] {result.name}")

        try:
            await msg.edit(content=f"⚡ **إنشاء ويبوكات... [{batch_end}/{count}]**")
        except:
            pass

        await asyncio.sleep(0.5)

    save_bank()

    try:
        await temp_channel.delete()
    except:
        pass

    await ctx.send(
        f"✅ **تم**\n"
        f"📊 نجح: `{created}` | فشل: `{failed}`\n"
        f"🏦 البنك: `{len(webhook_bank)}`\n"
        f"💡 التالي: `!rooms {created} room`"
    )


# ═════════════════════════════════════════
# 🔗 إنشاء رومات + ربط + إرسال
# ═════════════════════════════════════════
@client.command()
async def rooms(ctx, count: int = 20, name: str = "room", *, message: str = None):
    unlinked = {wid: info for wid, info in webhook_bank.items() if not info.get("linked_to")}

    if not unlinked:
        return await ctx.send("❌ ما فيه ويبوكات. استخدم `!hooks` أول")

    if count > len(unlinked):
        await ctx.send(f"⚠️ عندك `{len(unlinked)}` ويبوك")
        count = len(unlinked)

    if not message:
        message = "السلام عليكم"

    try:
        await ctx.message.delete()
    except:
        pass

    guild = ctx.guild
    msg = await ctx.send(f"⚡ **إنشاء {count} روم...**")

    failed = 0
    first_links = []
    unlinked_list = list(unlinked.items())
    batch_size = 3
    created_channels = []

    # إنشاء الرومات
    for batch_start in range(0, count, batch_size):
        batch_end = min(batch_start + batch_size, count)
        batch_tasks = []

        for i in range(batch_start + 1, batch_end + 1):
            batch_tasks.append(guild.create_text_channel(name=f"{name}-{i}"))

        results = await asyncio.gather(*batch_tasks, return_exceptions=True)

        for idx, result in enumerate(results):
            i = batch_start + idx + 1
            if isinstance(result, Exception):
                failed += 1
                print(f"❌ روم [{i}]: {result}")
            else:
                wid, info = unlinked_list[i - 1]
                created_channels.append((result, wid, info))
                print(f"✅ روم [{i}] {result.name}")

        try:
            await msg.edit(content=f"⚡ **إنشاء رومات... [{batch_end}/{count}]**")
        except:
            pass

        await asyncio.sleep(0.5)

    # ربط الويبوكات
    try:
        await msg.edit(content=f"⚡ **ربط الويبوكات...**")
    except:
        pass

    linked_data = []

    for batch_start in range(0, len(created_channels), batch_size):
        batch_end = min(batch_start + batch_size, len(created_channels))
        batch_tasks = []

        for j in range(batch_start, batch_end):
            channel, wid, info = created_channels[j]
            batch_tasks.append(channel.create_webhook(name=info["name"]))

        results = await asyncio.gather(*batch_tasks, return_exceptions=True)

        for idx, result in enumerate(results):
            j = batch_start + idx
            channel, wid, info = created_channels[j]
            if isinstance(result, Exception):
                print(f"❌ ربط [{channel.name}]: {result}")
            else:
                linked_data.append((channel, result, wid, info))

                old_channel_id = info.get("temp_channel")
                if old_channel_id:
                    old_ch = guild.get_channel(int(old_channel_id))
                    if old_ch:
                        try:
                            hooks_list = await old_ch.webhooks()
                            for h in hooks_list:
                                if str(h.id) == wid:
                                    await h.delete()
                                    break
                        except:
                            pass

                webhook_bank[wid] = {
                    "url": result.url,
                    "name": result.name,
                    "token": result.token,
                    "id": str(result.id),
                    "guild_id": str(guild.id),
                    "channel_id": str(channel.id),
                    "channel_name": channel.name,
                    "linked_to": str(channel.id),
                }

        await asyncio.sleep(0.5)

    save_bank()

    # إرسال أول رسالة
    try:
        await msg.edit(content=f"⚡ **إرسال رسائل...**")
    except:
        pass

    for batch_start in range(0, len(linked_data), batch_size):
        batch_end = min(batch_start + batch_size, len(linked_data))
        batch_tasks = []
        batch_meta = []

        for j in range(batch_start, batch_end):
            channel, new_wh, wid, info = linked_data[j]
            webhook = discord.Webhook.from_url(new_wh.url)   # ← بدون session
            batch_tasks.append(webhook.send(content=message, username=new_wh.name, wait=True))
            batch_meta.append((channel, new_wh, wid, info))

        results = await asyncio.gather(*batch_tasks, return_exceptions=True)

        for idx, result in enumerate(results):
            channel, new_wh, wid, info = batch_meta[idx]

            if isinstance(result, Exception):
                print(f"❌ إرسال [{channel.name}]: {result}")
            else:
                link = build_link(guild.id, channel.id, result.id)

                if wid not in message_links:
                    message_links[wid] = []

                message_links[wid].append({
                    "url": link,
                    "msg_id": str(result.id),
                    "channel": channel.name,
                    "channel_id": str(channel.id),
                    "guild_id": str(guild.id),
                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "first_message"
                })

                first_links.append(link)
                print(f"✅ إرسال [{channel.name}] → {link}")

        await asyncio.sleep(0.5)

    save_links()

    await ctx.send(
        f"✅ **تم**\n"
        f"📊 رومات: `{len(created_channels)}` | مربوط: `{len(linked_data)}`\n"
        f"📨 رسائل: `{len(first_links)}`\n"
        f"💡 التالي: `!fire 30s مرحبا`"
    )


# ═════════════════════════════════════════
# 🔥 إرسال متكرر
# ═════════════════════════════════════════
@client.command()
async def fire(ctx, interval: str, *, message: str):
    linked = {wid: info for wid, info in webhook_bank.items() if info.get("linked_to")}

    if not linked:
        return await ctx.send("❌ ما فيه ويبوكات مربوطة")

    try:
        delay = parse_time(interval)
    except ValueError as e:
        return await ctx.send(f"❌ {e}")

    if delay <= 0:
        return await ctx.send("❌ الوقت لازم أكبر من 0")

    try:
        await ctx.message.delete()
    except:
        pass

    with open("fire_config.json", 'w', encoding='utf-8') as f:
        json.dump({"interval": delay, "message": message, "enabled": True},
                  f, indent=2, ensure_ascii=False)

    global fire_task
    if fire_task and not fire_task.done():
        fire_task.cancel()

    async def send_to_webhook(wid, info):
        """ترسل رسالة واحدة وترجع الرابط"""
        webhook = discord.Webhook.from_url(info["url"], client=client)  # ← بدون session
        result = await webhook.send(
            content=message,
            username=info["name"],
            wait=True
        )
        return (wid, info, result)

    async def fire_loop():
        cycle = 0
        while True:
            cycle += 1
            cycle_start = time.time()
            total = len(linked)
            success = 0
            failed = 0

            print(f"\n🔥 دورة #{cycle} - {total} ويبوك")

            batch_size = 3
            items_list = list(linked.items())

            for batch_start in range(0, total, batch_size):
                items = items_list[batch_start:batch_start + batch_size]
                batch_tasks = []

                for wid, info in items:
                    batch_tasks.append(send_to_webhook(wid, info))

                results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        failed += 1
                        print(f"❌ {result}")
                    else:
                        wid, info, msg = result
                        success += 1

                        link = build_link(
                            int(info["guild_id"]),
                            int(info["channel_id"]),
                            msg.id
                        )

                        if wid not in message_links:
                            message_links[wid] = []

                        message_links[wid].append({
                            "url": link,
                            "msg_id": str(msg.id),
                            "channel": info.get("channel_name", "?"),
                            "channel_id": info["channel_id"],
                            "guild_id": info["guild_id"],
                            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "cycle": cycle
                        })

                        print(f"✅ {info.get('channel_name')} → {link}")

                await asyncio.sleep(0.5)

            save_links()

            cycle_time = time.time() - cycle_start
            total_links = sum(len(v) for v in message_links.values())

            print(f"🏁 دورة #{cycle}: {success}/{total} بـ {cycle_time:.1f}s | روابط: {total_links}")

            wait_time = max(0, delay - cycle_time)
            await asyncio.sleep(wait_time)

    fire_task = asyncio.create_task(fire_loop())

    await ctx.send(
        f"🔥 **بدأ الإرسال**\n"
        f"📌 الويبوكات: `{len(linked)}`\n"
        f"⏱️ كل: `{human_time(delay)}`\n"
        f"💬 الرسالة: `{message[:60]}{'...' if len(message) > 60 else ''}`\n"
        f"🛑 للإيقاف: `!stop`"
    )


# ═════════════════════════════════════════
# 🛑 إيقاف
# ═════════════════════════════════════════
@client.command()
async def stop(ctx):
    global fire_task
    try:
        await ctx.message.delete()
    except:
        pass

    if fire_task and not fire_task.done():
        fire_task.cancel()
        fire_task = None

    total_links = sum(len(v) for v in message_links.values())
    await ctx.send(f"🛑 تم الإيقاف | 📎 روابط: `{total_links}`", delete_after=5)


# ═════════════════════════════════════════
# 📎 عرض الروابط
# ═════════════════════════════════════════
@client.command()
async def links(ctx, limit: int = 30):
    try:
        await ctx.message.delete()
    except:
        pass

    if not message_links:
        return await ctx.send("❌ ما فيه روابط")

    all_links = []
    for wid, links_list in message_links.items():
        for entry in links_list:
            all_links.append(entry)

    all_links.sort(key=lambda x: x.get("time", ""), reverse=True)

    total = len(all_links)
    show = total if limit == 0 else min(limit, total)

    lines = [f"**📎 روابط ({total} - بيعرض {show}):**\n"]

    for i, entry in enumerate(all_links[:show], 1):
        cycle_txt = f"دورة #{entry.get('cycle', 0)}" if entry.get('cycle', 0) > 0 else "أول رسالة"
        lines.append(f"`{i}.` **{entry['channel']}** ({cycle_txt})\n{entry['url']}")

    text = "\n".join(lines)

    if len(text) > 1900:
        parts = [text[i:i+1900] for i in range(0, len(text), 1900)]
        for part in parts:
            await ctx.send(part)
            await asyncio.sleep(0.3)
    else:
        await ctx.send(text)


# ═════════════════════════════════════════
# 📊 الحالة
# ═════════════════════════════════════════
@client.command()
async def status(ctx):
    try:
        await ctx.message.delete()
    except:
        pass

    linked = sum(1 for w in webhook_bank.values() if w.get("linked_to"))
    total_links = sum(len(v) for v in message_links.values())
    fire_status = "🟢 شغال" if (fire_task and not fire_task.done()) else "🔴 متوقف"

    await ctx.send(
        f"**📊 الحالة:**\n"
        f"🔥 الإرسال: {fire_status}\n"
        f"🏦 البنك: `{len(webhook_bank)}` (مربوط: `{linked}`)\n"
        f"📎 روابط: `{total_links}`"
    )


# ═════════════════════════════════════════
# 🗑️ حذف كل شي
# ═════════════════════════════════════════
@client.command()
async def cleanup(ctx):
    try:
        await ctx.message.delete()
    except:
        pass

    global fire_task
    if fire_task and not fire_task.done():
        fire_task.cancel()

    msg = await ctx.send("🗑️ جاري الحذف...")

    deleted = 0
    for channel in ctx.guild.text_channels:
        if channel.name.startswith("room-") or channel.name.startswith("chat-") or channel.name.startswith("temp-"):
            try:
                await channel.delete()
                deleted += 1
                await asyncio.sleep(1)
            except:
                pass

    webhook_bank.clear()
    message_links.clear()
    save_bank()
    save_links()

    await msg.edit(content=f"✅ تم حذف {deleted} روم + مسح كل شي")


# ═════════════════════════════════════════
# 🧪 اختبار
# ═════════════════════════════════════════
@client.command()
async def test(ctx, *, msg: str = "تجربة"):
    """!test تجربة"""
    linked = {wid: info for wid, info in webhook_bank.items() if info.get("linked_to")}
    if not linked:
        return await ctx.send("❌ ما فيه ويبوكات مربوطة")

    wid, info = list(linked.items())[0]
    await ctx.send(f"🔍 أختبر: `{info['name']}`\nقناة: `{info.get('channel_name')}`")

    try:
        webhook = discord.Webhook.from_url(info["url"])   # ← بدون session
        result = await webhook.send(content=msg, wait=True)
        await ctx.send(f"✅ نجح! msg_id: `{result.id}`")
    except Exception as e:
        await ctx.send(f"❌ فشل:\n```\n{type(e).__name__}: {str(e)[:200]}\n```")


# ═════════════════════════════════════════
# ▶️ تشغيل
# ═════════════════════════════════════════
client.run(TOKEN)