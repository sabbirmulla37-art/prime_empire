import os
import re
import json
import time
import random
import sqlite3
import asyncio
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

import discord
from discord.ext import commands, tasks
from discord import app_commands

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from openai import AsyncOpenAI
except Exception:
    AsyncOpenAI = None

PREFIX = "$"
ALT_PREFIX = "!"
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://discord.gg/qn5Tu34TTd")
BOT_NAME = os.getenv("BOT_NAME", "Empire Prime")
FOOTER = os.getenv("BOT_FOOTER", "Empire Prime • Prefix: $ • Made by NotRyxenYT")
LOGO_FILE = os.getenv("LOGO_FILE", "logo.png")
DB_FILE = os.getenv("DB_FILE", "empire_prime.sqlite3")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

# Custom emoji strings from the screenshots. They will fall back to raw text if the emoji is not available.
EM = {
    "antinuke": "<a:antinuke:1483344748990435370>",
    "announcement": "<a:Announcement:1483344095228461056>",
    "clock": "<a:clock:1483340836467900507>",
    "moderation": "<a:Moderation:1483344127071486123>",
    "gift": "<a:Gift:1483344100353642497>",
}

CATEGORY_ORDER = [
    "Index", "Anti-Nuke", "Premium", "Automod", "Security", "Ticket System",
    "Moderation", "Invite Logging", "Giveaways", "Timer", "AFK", "Utility",
    "Logs", "Verification", "Welcome"
]

CATEGORY_ICONS = {
    "Index": "🏠", "Anti-Nuke": EM["antinuke"], "Premium": "⭐", "Automod": "🤖",
    "Security": "🔐", "Ticket System": EM["announcement"], "Moderation": EM["antinuke"],
    "Invite Logging": EM["announcement"], "Giveaways": EM["gift"], "Timer": EM["clock"],
    "AFK": "💤", "Utility": "🔧", "Logs": EM["moderation"], "Verification": EM["antinuke"],
    "Welcome": "👋"
}

CATEGORY_DESC = {
    "Index": "How to use the bot",
    "Anti-Nuke": "Anti-nuke & raid protection",
    "Premium": "All premium commands",
    "Automod": "Auto-moderate messages",
    "Security": "Server security tools",
    "Ticket System": "Ticket commands & setup",
    "Moderation": "Ban, kick, warn, timeout",
    "Invite Logging": "Invite tracking feature",
    "Giveaways": "Giveaway system",
    "Timer": "Timer feature",
    "AFK": "AFK system",
    "Utility": "Useful commands",
    "Logs": "Ticket & bot log setup",
    "Verification": "Member verification system",
    "Welcome": "Join, leave & boost messages",
}

CATEGORY_TEXT = {
    "Index": f"""{EM['moderation']} **Empire Prime — Commands**\n\n**Hey there! My prefix in this server is `$`**\nUse the **dropdown below** to browse all commands.\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{EM['antinuke']} **Anti-Nuke** — Protect from nukers, raiders & ghost pings\n⭐ **Premium** — Giveaways, Levels, Reaction Roles & more\n🚫 **Anti-Spam** — Auto-timeout spammers\n🔐 **Security** — Server security audit tools\n{EM['announcement']} **Ticket System** — Support ticket management\n{EM['antinuke']} **Moderation** — Ban, kick, warn, timeout\n{EM['announcement']} **Invite Logging** — Track who invited who\n{EM['clock']} **Timer** — Set timers\n💤 **AFK** — AFK status system\n🔧 **Utility** — Userinfo, avatar, ping\n{EM['moderation']} **Logs** — Set ticket & bot log channels\n{EM['antinuke']} **Verification** — Member verification system\n👋 **Welcome** — Join, leave & boost messages\n\n{FOOTER}\n\n**Select a category...**""",
    "Anti-Nuke": f"""{EM['antinuke']} **Anti-Nuke & Raid Protection**\n\n**Auto-detect dangerous server actions, ghost pings and raid bursts.**\n\n🔧 **Setup**\n`$antinuke enable` — Turn on Anti-Nuke\n`$antinuke disable` — Turn off Anti-Nuke\n`$antinuke setlog #channel` — Set alert log channel\n`$antinuke setpunish ban/kick/strip` — Punishment mode\n`$antinuke raid on/off` — Toggle raid shield\n`$antinuke test` — Test alerts\n\n👻 **Ghost Ping**\n`$antinuke ghostping` — Show settings\n`$antinuke ghostping timeout` — Timeout repeat offenders\n`$antinuke ghostping kick` — Kick repeat offenders\n`$antinuke ghostping ban` — Ban repeat offenders\n`$antinuke ghostping off` — Log only\n\n👤 **Whitelist**\n`$antinuke whitelist @user`\n`$antinuke unwhitelist @user`\n`$antinuke wlrole @role`\n`$antinuke unwlrole @role`\n`$antinuke wllist`\n\n🔒 **Lockdown**\n`$antinuke lock` — Lock all text channels\n`$antinuke unlock` — Unlock channels\n`$antinuke status` — Security status\n`$antinuke thresholds` — View limits\n\n🚫 **Anti-Spam**\n`$antispam on/off` — Toggle message spam protection\n\n**Empire Prime Anti-Nuke • Made by NotRyxenYT**""",
    "Premium": f"""⭐ **Empire Prime — Premium Commands**\n\n**All premium-style features are unlocked in this build.**\n\n☢️ **Recovery / Backup**\n`$nukerecovery on/off/status`\n`$backup create` — Save a server snapshot\n`$backup info` — View latest snapshot\n\n🎁 **Giveaways**\n`$gstart <dur> <winners> <prize>`\n`$gend <msg_id>`\n`$greroll <msg_id>`\n\n🏆 **Level System**\n`$rank`\n`$leaderboard`\n`$setlevel on/off`\n`$setlevel channel #ch`\n`$setlevel addrole <lvl> @role`\n\n🎭 **Reaction Roles**\n`$rr add <msg_id> <emoji> @role`\n`$rr remove <msg_id> <emoji>`\n`$rr list`\n\n⚡ **Auto React / Word React**\n`$autoreact set #channel 👍`\n`$wordreact add <word> 👍`\n\n🤖 **Auto Role**\n`$autorole add @role`\n`$autorole remove @role`\n`$autorole list`\n\n📊 **Polls / Temp VC / Sticky / Reminder**\n`$poll <dur> Question | Option1 | Option2`\n`$tempvc set #hub`\n`$sticky set <text>`\n`$remind <dur> <what>`\n\n💬 **Auto Responder**\n`$ar add <trigger> <reply>`\n`$ar remove <trigger>`\n`$ar list`\n\n🌟 **Welcome**\n`$setwelcome channel #ch`\n`$setwelcome message <text>`\n`$setwelcome dm <text>`\n`$setwelcome color <#hex>`\n`$setwelcome test`\n\n🔍 **Snipe**\n`$snipe` — Last deleted message\n`$editsnipe` — Last edited message\n\n**Empire Prime • Prefix: $ • Made by NotRyxenYT**""",
    "Automod": f"""🤖 **Automod System**\n\n**Automatically moderate messages in your server.**\n\n⚡ **Quick Setup**\n`$automod enable` — Enable all automod features\n`$automod disable` — Disable all automod features\n`$automod status` — View status\n\n🔧 **Individual Toggles**\n`$automod caps on/off` — Excessive CAPS\n`$automod links on/off` — Block links\n`$automod discordlinks on/off` — Block Discord links\n`$automod invites on/off` — Block invites\n`$automod spam on/off` — Block message spam\n`$automod emoji on/off` — Block emoji spam\n`$automod nsfw on/off` — Block NSFW/adult links\n`$automod extapps on/off` — Block external app links\n`$automod token on/off` — Block token-like strings\n`$automod mention on/off` — Block mass mentions\n`$automod settimeout <feature> <mins>` — Set timeout duration\n\n{EM['moderation']} **Automod Logs**\nActions are logged to the configured bot/mod log channel.\n\n**Empire Prime • Made by NotRyxenYT**""",
    "Security": f"""🔐 **Security Tools**\n\n**Advanced audit & inspection tools for server admins.**\n\n`$security audit` — Recent audit-log actions\n`$security admins` — Members with dangerous permissions\n`$security bots` — List bots in server\n`$security newmembers [days]` — Recent joiners\n`$security checkreps` — Find overpowered roles\n`$security clearblocked` — Clear rate-limited users\n`$security resetpunished` — Reset this session's punished list\n\n**Empire Prime Security • Made by NotRyxenYT**""",
    "Ticket System": f"""{EM['announcement']} **Ticket System**\n\n**Manage support tickets with categories & logging.**\n\n`$ticket panel` — Send ticket panel\n`$ticket setup` — Configure ticket system\n`$ticket close` — Close current ticket\n`$ticket claim` — Claim ticket\n`$ticket add @user` — Add user\n`$ticket remove @user` — Remove user\n`$ticket rename <name>` — Rename ticket\n`$ticket setping @role` — Set staff role\n\n**Categories**\n💰 Buy/Purchase · 🎁 Claim Rewards · 🤝 Partnership · {EM['announcement']} Support Ticket\n\n**Empire Prime Bot • Made by NotRyxenYT**""",
    "Moderation": f"""{EM['antinuke']} **Moderation**\n\n**Moderation commands require the appropriate Discord permissions.**\n\n`$ban @user [reason]` — Ban a member\n`$unban <id>` — Unban by ID\n`$kick @user [reason]` — Kick a member\n`$timeout @user 10m [reason]` — Timeout\n`$untimeout @user` — Remove timeout\n`$warn @user <reason>` — Warn + DM\n`$warnings @user` — View warnings\n`$clearwarns @user` — Clear warnings\n`$purge <1-100>` — Bulk delete messages\n`$lock / $unlock` — Lock/unlock channel\n`$slowmode <sec>` — Set slowmode\n`$note @user [text]` — Staff note\n\n**Empire Prime • Prefix: $ • Made by NotRyxenYT**""",
    "Invite Logging": f"""{EM['announcement']} **Invite Logging**\n\n**Track who invited who to the server.**\n\n`$i [@user]` — Invite stats\n`$invited [@user]` — List invited users\n`$inviteboard` — Invite leaderboard\n`$resetinvites @user` — Reset invite count\n\n**Empire Prime • Prefix: $ • Made by NotRyxenYT**""",
    "Giveaways": f"""{EM['gift']} **Giveaways**\n\n**Run and manage giveaways easily.**\n\n`$gstart <time> <winners> <prize>` — Start a giveaway\nExample: `$gstart 1h 2 Nitro`\n`$gend <msg_id>` — End giveaway early\n`$greroll <msg_id>` — Reroll a winner\n\n**Empire Prime • Prefix: $ • Made by NotRyxenYT**""",
    "Timer": f"""{EM['clock']} **Timer**\n\n**Set timers — the bot pings you when done.**\n\n`$tstart <duration> <label>` — Set a timer\nExample: `$tstart 30m Study Break`\nDurations: `10s` `5m` `2h` `1d`\n\n**Empire Prime • Prefix: $ • Made by NotRyxenYT**""",
    "AFK": f"""💤 **AFK System**\n\n**Set yourself as AFK.**\n\n`$afk [reason]` — Set AFK status\n• Auto-replies when someone pings you\n• Auto-removes when you send a message\n\n**Empire Prime • Prefix: $ • Made by NotRyxenYT**""",
    "Utility": f"""🔧 **Utility**\n\n**Useful commands for everyone.**\n\n`$userinfo [@user]` — Detailed user info\n`$serverinfo` (`$si`) — Server info\n`$mc` — Member count\n`$accage <id/@u>` — Account age\n`$avatar [@user]` — User avatar\n`$ping` — Bot latency\n`$botinfo` — Bot features\n`$ai <question>` — AI chat\n`!ai <question>` — AI chat alias\n`$randomq` — Random question\n\n**Empire Prime • Prefix: $ • Made by NotRyxenYT**""",
    "Logs": f"""{EM['moderation']} **Log Setup**\n\n**Set channels for bot, moderation, tickets, invites and anti-nuke logs.**\n\n`$setuplogs` — Interactive setup\n`$setuplogs all #channel` — Set all logs\n`$setticketlog #channel` — Ticket log\n`$setbotlog #channel` — Bot log\n`$setmodlog #channel` — Mod log\n`$setinvitelog #channel` — Invite log\n`$antinuke setlog #channel` — Anti-Nuke alert log\n\n**Empire Prime • Prefix: $ • Made by NotRyxenYT**""",
    "Verification": f"""{EM['antinuke']} **Verification System**\n\n**Auto-verify members with roles and logs.**\n\n`$verify setup` — Create roles/channels/panel\n`$verify panel` — Send verify panel\n`$verify status` — View config\n`$verify setrole @Verified @Unverified` — Set roles\n`$verify setchannel #channel` — Set verify channel\n`$verify setlog #channel` — Set verify log\n\n**How it works**\n▸ New member joins → gets `Unverified`\n▸ They click **Verify Me** → get `Verified`\n▸ Verification is logged\n\n**Empire Prime • Made by NotRyxenYT**""",
    "Welcome": f"""👋 **Welcome Messages**\n\n**Auto-send rich embeds when members join, leave or boost.**\n\n`$welcome` — Open setup panel\n`$welcome channel #ch` — Set join channel\n`$welcome message <text>` — Set join message\n`$welcome color <#hex>` — Set embed color\n`$welcome joinrole @role` — Auto-assign role\n`$welcome dm <text>` — DM new members\n`$welcome test` — Preview\n`$welcome disable` — Disable\n\n**Variables:** `{mention}` `{user}` `{server}` `{count}` `{id}` `{created_at}` `{boost_count}`\n\n📥 Join · 📤 Leave · 🚀 Boost\n\n**Empire Prime Bot • Use `$welcome` to setup**""",
}

DB = sqlite3.connect(DB_FILE, check_same_thread=False)
DB.row_factory = sqlite3.Row
DB.execute("PRAGMA journal_mode=WAL")

def db(sql, params=(), fetch=False, many=False):
    cur = DB.cursor()
    if many:
        cur.executemany(sql, params)
    else:
        cur.execute(sql, params)
    DB.commit()
    if fetch:
        return cur.fetchall()
    return cur.lastrowid

DB.executescript("""
CREATE TABLE IF NOT EXISTS guild_config (
 guild_id INTEGER PRIMARY KEY,
 prefix TEXT DEFAULT '$',
 bot_log INTEGER, mod_log INTEGER, ticket_log INTEGER, invite_log INTEGER,
 antinuke_log INTEGER, welcome_channel INTEGER, welcome_message TEXT,
 welcome_dm TEXT, welcome_color TEXT DEFAULT '#5865F2', welcome_role INTEGER,
 verify_channel INTEGER, verify_log INTEGER, verified_role INTEGER, unverified_role INTEGER,
 automod_enabled INTEGER DEFAULT 0, automod_json TEXT DEFAULT '{}', antinuke_enabled INTEGER DEFAULT 0,
 antinuke_json TEXT DEFAULT '{}', anti_spam INTEGER DEFAULT 0, raid_enabled INTEGER DEFAULT 0,
 level_enabled INTEGER DEFAULT 0, level_channel INTEGER, autoroles_json TEXT DEFAULT '[]',
 autoreact_json TEXT DEFAULT '{}', wordreact_json TEXT DEFAULT '{}', autoresponder_json TEXT DEFAULT '{}',
 sticky_json TEXT DEFAULT '{}', afk_json TEXT DEFAULT '{}', reaction_roles_json TEXT DEFAULT '{}',
 tempvc_hub INTEGER, ticket_category INTEGER, ticket_role INTEGER, ticket_types_json TEXT DEFAULT '[]',
 nukerecovery INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS warnings (guild_id INTEGER, user_id INTEGER, moderator_id INTEGER, reason TEXT, created_at INTEGER);
CREATE TABLE IF NOT EXISTS notes (guild_id INTEGER, user_id INTEGER, moderator_id INTEGER, text TEXT, created_at INTEGER);
CREATE TABLE IF NOT EXISTS invites (guild_id INTEGER, inviter_id INTEGER, uses INTEGER DEFAULT 0, leaves INTEGER DEFAULT 0, fake INTEGER DEFAULT 0, rejoins INTEGER DEFAULT 0, PRIMARY KEY(guild_id, inviter_id));
CREATE TABLE IF NOT EXISTS invited_users (guild_id INTEGER, user_id INTEGER, inviter_id INTEGER, joined_at INTEGER, left_at INTEGER);
CREATE TABLE IF NOT EXISTS giveaways (message_id INTEGER PRIMARY KEY, guild_id INTEGER, channel_id INTEGER, host_id INTEGER, prize TEXT, winners INTEGER, end_at INTEGER, ended INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS levels (guild_id INTEGER, user_id INTEGER, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 0, PRIMARY KEY(guild_id,user_id));
CREATE TABLE IF NOT EXISTS timers (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, channel_id INTEGER, user_id INTEGER, end_at INTEGER, label TEXT);
CREATE TABLE IF NOT EXISTS backups (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, created_at INTEGER, data TEXT);
CREATE TABLE IF NOT EXISTS mod_cases (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER, moderator_id INTEGER, action TEXT, reason TEXT, created_at INTEGER);
""")


def cfg(guild_id):
    row = db("SELECT * FROM guild_config WHERE guild_id=?", (guild_id,), True)
    if row:
        return row[0]
    db("INSERT INTO guild_config(guild_id) VALUES(?)", (guild_id,))
    return db("SELECT * FROM guild_config WHERE guild_id=?", (guild_id,), True)[0]


def update_cfg(guild_id, **values):
    cfg(guild_id)
    if not values:
        return
    cols = ", ".join(f"{k}=?" for k in values)
    db(f"UPDATE guild_config SET {cols} WHERE guild_id=?", tuple(values.values()) + (guild_id,))


def parse_duration(s: str):
    m = re.fullmatch(r"\s*(\d+)\s*([smhdw])\s*", s.lower())
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    return n * {"s":1, "m":60, "h":3600, "d":86400, "w":604800}[unit]


def now():
    return int(time.time())


def human_time(seconds):
    seconds = max(0, int(seconds))
    for unit, size in (("d",86400),("h",3600),("m",60),("s",1)):
        if seconds >= size:
            return f"{seconds//size}{unit}"
    return "0s"


def render_vars(text, member, guild):
    return (text or "").replace("{mention}", member.mention).replace("{user}", str(member)).replace("{server}", guild.name).replace("{count}", str(guild.member_count)).replace("{id}", str(member.id)).replace("{created_at}", discord.utils.format_dt(member.created_at, style="R")).replace("{boost_count}", str(guild.premium_subscription_count or 0))

async def send_log(guild, kind, title, description, color=discord.Color.blurple()):
    c = cfg(guild.id)
    channel_id = {"bot":c["bot_log"], "mod":c["mod_log"], "ticket":c["ticket_log"], "invite":c["invite_log"], "antinuke":c["antinuke_log"]}.get(kind)
    if not channel_id:
        return
    channel = guild.get_channel(channel_id)
    if not channel:
        return
    e = discord.Embed(title=title, description=description, color=color, timestamp=datetime.now(timezone.utc))
    e.set_footer(text=FOOTER)
    try:
        await channel.send(embed=e)
    except discord.HTTPException:
        pass

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True
intents.guilds = True
intents.messages = True
intents.reactions = True
intents.invites = True

bot = commands.Bot(command_prefix=(PREFIX, ALT_PREFIX), intents=intents, help_command=None, case_insensitive=True)

ai_client = AsyncOpenAI(api_key=OPENAI_KEY) if (OPENAI_KEY and AsyncOpenAI) else None

AFK_CACHE = {}
DELETED_CACHE = {}
EDITED_CACHE = {}
SPAM_CACHE = {}
JOIN_CACHE = {}
INVITE_CACHE = {}


def is_mod():
    async def predicate(ctx):
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return False
        return ctx.author.guild_permissions.manage_guild or ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.administrator
    return commands.check(predicate)


def is_admin():
    async def predicate(ctx):
        return bool(ctx.guild and isinstance(ctx.author, discord.Member) and ctx.author.guild_permissions.administrator)
    return commands.check(predicate)


def admin_only(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

async def ensure_guild(ctx):
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return False
    cfg(ctx.guild.id)
    return True


class HelpSelect(discord.ui.Select):
    def __init__(self, owner_id=None):
        opts = [discord.SelectOption(label=x, description=CATEGORY_DESC[x][:100], emoji=("🔧" if x == "Utility" else None)) for x in CATEGORY_ORDER]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=opts)
        self.owner_id = owner_id

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        if self.owner_id and interaction.user.id != self.owner_id:
            await interaction.response.send_message("Only the person who opened this help menu can use it.", ephemeral=True)
            return
        embed = discord.Embed(description=CATEGORY_TEXT[category], color=discord.Color.blurple())
        embed.set_author(name=BOT_NAME)
        embed.set_footer(text=FOOTER)
        file = discord.File(LOGO_FILE, filename="logo.png") if os.path.exists(LOGO_FILE) else None
        embed.set_thumbnail(url="attachment://logo.png" if file else bot.user.display_avatar.url)
        await interaction.response.edit_message(embed=embed, view=HelpView(self.owner_id), attachments=[file] if file else [])


class HelpView(discord.ui.View):
    def __init__(self, owner_id=None):
        super().__init__(timeout=180)
        self.add_item(HelpSelect(owner_id))
        b = discord.ui.Button(label="Support Server", emoji="🗨️", style=discord.ButtonStyle.link, url=SUPPORT_URL)
        self.add_item(b)


class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify Me", style=discord.ButtonStyle.success, emoji="✅", custom_id="empire_verify")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild:
            return
        c = cfg(interaction.guild.id)
        role_id = c["verified_role"]
        unverified_id = c["unverified_role"]
        if not role_id:
            await interaction.response.send_message("Verification is not configured yet.", ephemeral=True)
            return
        role = interaction.guild.get_role(role_id)
        unverified = interaction.guild.get_role(unverified_id) if unverified_id else None
        try:
            if role:
                await interaction.user.add_roles(role, reason="Empire Prime verification")
            if unverified:
                await interaction.user.remove_roles(unverified, reason="Empire Prime verification")
            await interaction.response.send_message("✅ You are verified!", ephemeral=True)
            await send_log(interaction.guild, "bot", "Member Verified", f"{interaction.user.mention} verified.")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to manage the verification roles.", ephemeral=True)


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="empire_ticket_open")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if not guild:
            return
        c = cfg(guild.id)
        existing = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.id}")
        if existing:
            await interaction.response.send_message(f"You already have {existing.mention}.", ephemeral=True)
            return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True),
        }
        if c["ticket_role"]:
            role = guild.get_role(c["ticket_role"])
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        category = guild.get_channel(c["ticket_category"]) if c["ticket_category"] else None
        try:
            ch = await guild.create_text_channel(f"ticket-{interaction.user.id}", overwrites=overwrites, category=category, reason="Empire Prime ticket")
            e = discord.Embed(title="🎫 Support Ticket", description=f"Hello {interaction.user.mention}! Staff will help you soon.\nUse `$ticket close` when finished.", color=discord.Color.blurple())
            await ch.send(embed=e)
            await interaction.response.send_message(f"Ticket created: {ch.mention}", ephemeral=True)
            await send_log(guild, "ticket", "Ticket Opened", f"{interaction.user.mention} opened {ch.mention}.")
        except discord.Forbidden:
            await interaction.response.send_message("I need Manage Channels and permission to create ticket channels.", ephemeral=True)


@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(VerifyView())
    try:
        await bot.change_presence(status=discord.Status.online, activity=discord.Game(name=os.getenv("BOT_STATUS", "$help • Empire Prime")))
    except Exception:
        pass
    print(f"Logged in as {bot.user} ({bot.user.id})")
    if not giveaway_loop.is_running(): giveaway_loop.start()
    if not timer_loop.is_running(): timer_loop.start()


@bot.event
async def on_guild_join(guild):
    cfg(guild.id)
    await send_log(guild, "bot", "Empire Prime Added", "Thanks for adding Empire Prime!")


@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild:
        return
    DELETED_CACHE[message.channel.id] = (message.author, message.content, now())


@bot.event
async def on_message_edit(before, after):
    if before.author.bot or not before.guild or before.content == after.content:
        return
    EDITED_CACHE[before.channel.id] = (before.author, before.content, after.content, now())


@bot.event
async def on_member_join(member):
    guild = member.guild
    c = cfg(guild.id)
    # Welcome
    if c["welcome_channel"]:
        ch = guild.get_channel(c["welcome_channel"])
        if ch:
            msg = render_vars(c["welcome_message"] or "Welcome {mention} to **{server}**!", member, guild)
            try:
                await ch.send(embed=discord.Embed(description=msg, color=discord.Color(int((c["welcome_color"] or "#5865F2").lstrip("#"),16))))
            except Exception:
                pass
    if c["welcome_dm"]:
        try:
            await member.send(render_vars(c["welcome_dm"], member, guild))
        except Exception:
            pass
    if c["welcome_role"]:
        role = guild.get_role(c["welcome_role"])
        if role:
            try: await member.add_roles(role, reason="Empire Prime welcome autorole")
            except Exception: pass
    # Verification
    if c["unverified_role"]:
        role = guild.get_role(c["unverified_role"])
        if role:
            try: await member.add_roles(role, reason="Empire Prime verification")
            except Exception: pass
    JOIN_CACHE.setdefault(guild.id, []).append(now())
    JOIN_CACHE[guild.id] = [x for x in JOIN_CACHE[guild.id] if now()-x < 5]
    if c["raid_enabled"] and len(JOIN_CACHE[guild.id]) >= 8:
        await send_log(guild, "antinuke", "🚨 Raid Shield", "8+ joins detected in 5 seconds. Raid shield triggered.", discord.Color.red())


@bot.event
async def on_member_remove(member):
    rows = db("SELECT inviter_id FROM invited_users WHERE guild_id=? AND user_id=? ORDER BY joined_at DESC LIMIT 1", (member.guild.id, member.id), True)
    if rows:
        db("UPDATE invited_users SET left_at=? WHERE guild_id=? AND user_id=? AND left_at IS NULL", (now(), member.guild.id, member.id))
        db("UPDATE invites SET leaves=leaves+1 WHERE guild_id=? AND inviter_id=?", (member.guild.id, rows[0][0]))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have the required Discord permission.", delete_after=5)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument: `{error.param.name}`", delete_after=6)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument. Mention the user/channel/role where required.", delete_after=6)
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You need moderator/admin permissions for this command.", delete_after=6)
    else:
        print("Command error:", repr(error))
        await ctx.send("❌ Something went wrong while running that command.", delete_after=6)


@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(description=CATEGORY_TEXT["Index"], color=discord.Color.blurple())
    embed.set_author(name=BOT_NAME)
    embed.set_footer(text=FOOTER)
    file = discord.File(LOGO_FILE, filename="logo.png") if os.path.exists(LOGO_FILE) else None
    embed.set_thumbnail(url="attachment://logo.png" if file else bot.user.display_avatar.url)
    await ctx.send(embed=embed, view=HelpView(ctx.author.id), file=file if file else discord.utils.MISSING)


@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! `{round(bot.latency*1000)}ms`")


@bot.command(name="botinfo")
async def botinfo(ctx):
    e = discord.Embed(title=f"{BOT_NAME}", description="Feature-rich multipurpose Discord bot.", color=discord.Color.blurple())
    e.add_field(name="Prefix", value="`$` (also `!ai` supported)")
    e.add_field(name="Features", value="Moderation • Automod • Giveaways • Tickets • Verification • Welcome • Logs • AI")
    e.add_field(name="Support", value=f"[Support Server]({SUPPORT_URL})")
    await ctx.send(embed=e)


@bot.command(name="ai")
async def ai(ctx, *, question: str = None):
    if not question:
        await ctx.send("Usage: `$ai <question>` or `!ai <question>`")
        return
    if not ai_client:
        await ctx.send("🤖 AI is not configured. The bot owner must set `OPENAI_API_KEY` in `.env`.")
        return
    try:
        response = await ai_client.responses.create(model=OPENAI_MODEL, input=[
            {"role":"system","content":"You are Empire Prime, a concise, friendly Discord server assistant. Do not claim to have abilities you do not have."},
            {"role":"user","content":question},
        ])
        text = getattr(response, "output_text", "") or "I couldn't generate a reply."
        await ctx.reply(text[:4000], mention_author=False)
    except Exception as ex:
        print("AI error:", ex)
        await ctx.send("🤖 AI is temporarily unavailable. Check the API key/model configuration.")


@bot.command(name="randomq")
async def randomq(ctx):
    qs = ["What game could you play for hours?", "What is one skill you'd like to learn?", "If you could visit any country, where would you go?", "What is your favorite movie?", "What would you build if you had unlimited creativity?", "What is your favorite food?", "What is one thing that always makes you laugh?"]
    await ctx.send(f"🎲 **Random Question:** {random.choice(qs)}")


# ---------------- Moderation ----------------
@bot.command()
@is_mod()
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    db("INSERT INTO warnings VALUES(?,?,?,?,?)", (ctx.guild.id, member.id, ctx.author.id, reason, now()))
    db("INSERT INTO mod_cases(guild_id,user_id,moderator_id,action,reason,created_at) VALUES(?,?,?,?,?,?)", (ctx.guild.id, member.id, ctx.author.id, "warn", reason, now()))
    try: await member.send(f"⚠️ You were warned in **{ctx.guild.name}**.\nReason: {reason}")
    except Exception: pass
    await ctx.send(f"⚠️ {member.mention} warned. **Reason:** {reason}")
    await send_log(ctx.guild, "mod", "Member Warned", f"**User:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}", discord.Color.orange())

@bot.command()
@is_mod()
async def warnings(ctx, member: discord.Member):
    rows = db("SELECT reason, moderator_id, created_at FROM warnings WHERE guild_id=? AND user_id=? ORDER BY created_at DESC LIMIT 20", (ctx.guild.id, member.id), True)
    if not rows: return await ctx.send("No warnings found.")
    text = "\n".join(f"• <t:{r['created_at']}:R> — <@{r['moderator_id']}> — {r['reason']}" for r in rows)
    await ctx.send(embed=discord.Embed(title=f"Warnings for {member}", description=text, color=discord.Color.orange()))

@bot.command()
@is_mod()
async def clearwarns(ctx, member: discord.Member):
    db("DELETE FROM warnings WHERE guild_id=? AND user_id=?", (ctx.guild.id, member.id))
    await ctx.send(f"✅ Cleared warnings for {member.mention}.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 Banned {member} — {reason}")
    await send_log(ctx.guild, "mod", "Member Banned", f"**User:** {member}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}", discord.Color.red())

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"✅ Unbanned {user}.")
    except Exception:
        await ctx.send("❌ Could not unban that ID.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(f"👢 Kicked {member} — {reason}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, duration="10m", *, reason="No reason provided"):
    seconds = parse_duration(duration)
    if not seconds or seconds > 28*86400: return await ctx.send("❌ Use a duration like `10m`, `1h`, `1d` (max 28d).")
    await member.timeout(timedelta(seconds=seconds), reason=reason)
    await ctx.send(f"⏳ Timed out {member.mention} for `{duration}` — {reason}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, member: discord.Member):
    await member.timeout(None, reason=f"Untimeout by {ctx.author}")
    await ctx.send(f"✅ Removed timeout from {member.mention}.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    amount = max(1, min(100, amount))
    deleted = await ctx.channel.purge(limit=amount+1)
    await ctx.send(f"🧹 Deleted `{len(deleted)-1}` messages.", delete_after=5)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Channel locked.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.send("🔓 Channel unlocked.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=max(0, min(21600, seconds)))
    await ctx.send(f"🐢 Slowmode set to `{seconds}s`.")

@bot.command()
@is_mod()
async def note(ctx, member: discord.Member, *, text=""):
    db("INSERT INTO notes VALUES(?,?,?,?,?)", (ctx.guild.id, member.id, ctx.author.id, text, now()))
    await ctx.send("📝 Staff note saved.")

# ---------------- Utility ----------------
@bot.command()
async def userinfo(ctx, member: discord.Member=None):
    member = member or ctx.author
    e=discord.Embed(title=str(member), color=member.color if member.color != discord.Color.default() else discord.Color.blurple())
    e.set_thumbnail(url=member.display_avatar.url)
    e.add_field(name="ID", value=member.id)
    e.add_field(name="Joined", value=discord.utils.format_dt(member.joined_at, "R") if member.joined_at else "Unknown")
    e.add_field(name="Created", value=discord.utils.format_dt(member.created_at, "R"))
    e.add_field(name="Roles", value=str(len(member.roles)-1))
    await ctx.send(embed=e)

@bot.command(aliases=["si"])
async def serverinfo(ctx):
    g=ctx.guild
    e=discord.Embed(title=g.name, color=discord.Color.blurple())
    e.set_thumbnail(url=g.icon.url if g.icon else bot.user.display_avatar.url)
    e.add_field(name="Members", value=g.member_count)
    e.add_field(name="Channels", value=len(g.channels))
    e.add_field(name="Roles", value=len(g.roles))
    e.add_field(name="Owner", value=g.owner.mention if g.owner else g.owner_id)
    await ctx.send(embed=e)

@bot.command()
async def mc(ctx): await ctx.send(f"👥 Member count: `{ctx.guild.member_count}`")

@bot.command()
async def accage(ctx, member: discord.Member=None):
    member = member or ctx.author
    await ctx.send(f"🗓️ {member} created their account {discord.utils.format_dt(member.created_at, 'R')}.")

@bot.command()
async def avatar(ctx, member: discord.Member=None):
    member=member or ctx.author
    await ctx.send(member.display_avatar.url)

@bot.command()
async def snipe(ctx):
    row=DELETED_CACHE.get(ctx.channel.id)
    if not row: return await ctx.send("Nothing to snipe.")
    author, content, ts=row
    await ctx.send(embed=discord.Embed(title="🕵️ Snipe", description=content[:4000] or "*(no text)*", color=discord.Color.orange()).set_author(name=str(author), icon_url=author.display_avatar.url))

@bot.command()
async def editsnipe(ctx):
    row=EDITED_CACHE.get(ctx.channel.id)
    if not row: return await ctx.send("Nothing to editsnipe.")
    author,b,a,ts=row
    e=discord.Embed(title="✏️ Edit Snipe", color=discord.Color.orange())
    e.add_field(name="Before", value=b[:1024] or "*(empty)*", inline=False)
    e.add_field(name="After", value=a[:1024] or "*(empty)*", inline=False)
    e.set_author(name=str(author), icon_url=author.display_avatar.url)
    await ctx.send(embed=e)

# ---------------- AFK ----------------
@bot.command()
async def afk(ctx, *, reason="AFK"):
    AFK_CACHE[ctx.author.id]=(reason, now())
    await ctx.send(f"💤 {ctx.author.mention} is now AFK: **{reason}**")

# ---------------- Announcements / links ----------------
@bot.command(aliases=["announcement"])
@is_mod()
async def announce(ctx, channel: discord.TextChannel, *, message):
    e=discord.Embed(title="📢 Announcement", description=message, color=discord.Color.blurple(), timestamp=datetime.now(timezone.utc))
    e.set_footer(text=FOOTER)
    await channel.send(embed=e)
    await ctx.send(f"✅ Announcement sent to {channel.mention}.")

@bot.command()
@is_mod()
async def link(ctx, channel: discord.TextChannel, url: str, *, text="Open Link"):
    p=urlparse(url)
    if p.scheme not in ("http","https") or not p.netloc:
        return await ctx.send("❌ Please provide a valid http/https link.")
    e=discord.Embed(title="🔗 Link", description=f"[{text}]({url})", color=discord.Color.blurple())
    await channel.send(embed=e)
    await ctx.send(f"✅ Link sent to {channel.mention}.")

# ---------------- Giveaways ----------------
@bot.command()
@is_mod()
async def gstart(ctx, duration: str, winners: int, *, prize: str):
    seconds=parse_duration(duration)
    if not seconds or winners < 1: return await ctx.send("Usage: `$gstart 1h 2 Nitro`.")
    end=now()+seconds
    e=discord.Embed(title=f"{EM['gift']} Giveaway", description=f"**Prize:** {prize}\n**Winners:** {winners}\n**Ends:** <t:{end}:R>\n\nReact with 🎉 to enter!", color=discord.Color.gold())
    e.set_footer(text=f"Hosted by {ctx.author}")
    msg=await ctx.send(embed=e)
    await msg.add_reaction("🎉")
    db("INSERT INTO giveaways(message_id,guild_id,channel_id,host_id,prize,winners,end_at) VALUES(?,?,?,?,?,?,?)", (msg.id,ctx.guild.id,ctx.channel.id,ctx.author.id,prize,winners,end))

async def finish_giveaway(row, reroll=False):
    guild=bot.get_guild(row["guild_id"])
    if not guild: return None
    ch=guild.get_channel(row["channel_id"])
    if not ch: return None
    try: msg=await ch.fetch_message(row["message_id"])
    except Exception: return None
    reaction=discord.utils.get(msg.reactions, emoji="🎉")
    users=[]
    if reaction:
        async for u in reaction.users():
            if not u.bot: users.append(u)
    if not users:
        await ch.send(f"🎉 Giveaway ended for **{row['prize']}**, but there were no valid entries.")
        return []
    chosen=random.sample(users, min(row["winners"],len(users)))
    mentions=", ".join(u.mention for u in chosen)
    await ch.send(f"🎉 Congratulations {mentions}! You won **{row['prize']}**!")
    return chosen

@bot.command()
@is_mod()
async def gend(ctx, message_id: int):
    rows=db("SELECT * FROM giveaways WHERE message_id=?", (message_id,), True)
    if not rows: return await ctx.send("Giveaway not found.")
    row=rows[0]
    if row["ended"]: return await ctx.send("Giveaway already ended.")
    await finish_giveaway(row)
    db("UPDATE giveaways SET ended=1 WHERE message_id=?", (message_id,))
    await ctx.send("✅ Giveaway ended.", delete_after=5)

@bot.command()
@is_mod()
async def greroll(ctx, message_id: int):
    rows=db("SELECT * FROM giveaways WHERE message_id=?", (message_id,), True)
    if not rows: return await ctx.send("Giveaway not found.")
    await finish_giveaway(rows[0], True)

@giveaway_loop if False else (lambda f:f)
def _placeholder(): pass

@tasks.loop(seconds=10)
async def giveaway_loop():
    rows=db("SELECT * FROM giveaways WHERE ended=0 AND end_at<=?", (now(),), True)
    for row in rows:
        try: await finish_giveaway(row)
        except Exception as e: print("Giveaway finish error", e)
        db("UPDATE giveaways SET ended=1 WHERE message_id=?", (row["message_id"],))

# ---------------- Timers ----------------
@bot.command()
async def tstart(ctx, duration: str, *, label):
    seconds=parse_duration(duration)
    if not seconds: return await ctx.send("Usage: `$tstart 30m Study Break`.")
    db("INSERT INTO timers(guild_id,channel_id,user_id,end_at,label) VALUES(?,?,?,?,?)", (ctx.guild.id,ctx.channel.id,ctx.author.id,now()+seconds,label))
    await ctx.send(f"⏱️ Timer set for `{duration}` — **{label}**")

@tasks.loop(seconds=5)
async def timer_loop():
    rows=db("SELECT * FROM timers WHERE end_at<=?", (now(),), True)
    for row in rows:
        ch=bot.get_channel(row["channel_id"])
        if ch:
            try: await ch.send(f"⏰ <@{row['user_id']}> your timer is done: **{row['label']}**")
            except Exception: pass
        db("DELETE FROM timers WHERE id=?", (row["id"],))

# ---------------- Welcome ----------------
@bot.group(invoke_without_command=True)
@is_admin()
async def welcome(ctx):
    await ctx.send(CATEGORY_TEXT["Welcome"])

@welcome.command(name="channel")
@is_admin()
async def welcome_channel(ctx, channel: discord.TextChannel): update_cfg(ctx.guild.id, welcome_channel=channel.id); await ctx.send(f"✅ Welcome channel: {channel.mention}")
@welcome.command(name="message")
@is_admin()
async def welcome_message(ctx, *, text): update_cfg(ctx.guild.id, welcome_message=text); await ctx.send("✅ Welcome message saved.")
@welcome.command(name="dm")
@is_admin()
async def welcome_dm(ctx, *, text): update_cfg(ctx.guild.id, welcome_dm=text); await ctx.send("✅ Welcome DM saved.")
@welcome.command(name="color")
@is_admin()
async def welcome_color(ctx, color):
    try: int(color.lstrip("#"),16)
    except ValueError: return await ctx.send("Use a hex color like `#5865F2`.")
    update_cfg(ctx.guild.id, welcome_color=color); await ctx.send("✅ Welcome color saved.")
@welcome.command(name="joinrole")
@is_admin()
async def welcome_joinrole(ctx, role: discord.Role): update_cfg(ctx.guild.id, welcome_role=role.id); await ctx.send(f"✅ Join role: {role.mention}")
@welcome.command(name="disable")
@is_admin()
async def welcome_disable(ctx): update_cfg(ctx.guild.id, welcome_channel=None, welcome_message=None, welcome_dm=None); await ctx.send("✅ Welcome messages disabled.")
@welcome.command(name="test")
@is_admin()
async def welcome_test(ctx):
    c=cfg(ctx.guild.id)
    msg=render_vars(c["welcome_message"] or "Welcome {mention} to **{server}**!", ctx.author, ctx.guild)
    await ctx.send(embed=discord.Embed(title="👋 Welcome Preview", description=msg, color=discord.Color.blurple()))

# ---------------- Verification ----------------
@bot.group(invoke_without_command=True)
@is_admin()
async def verify(ctx): await ctx.send(CATEGORY_TEXT["Verification"])

@verify.command(name="setup")
@is_admin()
async def verify_setup(ctx):
    g=ctx.guild
    verified=discord.utils.get(g.roles,name="Verified") or await g.create_role(name="Verified", reason="Empire Prime verification")
    unverified=discord.utils.get(g.roles,name="Unverified") or await g.create_role(name="Unverified", reason="Empire Prime verification")
    ch=discord.utils.get(g.text_channels,name="verify-here") or await g.create_text_channel("verify-here")
    update_cfg(g.id, verified_role=verified.id, unverified_role=unverified.id, verify_channel=ch.id, verify_log=ch.id)
    await ch.send(embed=discord.Embed(title="🛡️ Verification", description="Click **Verify Me** to get access.", color=discord.Color.green()), view=VerifyView())
    await ctx.send(f"✅ Verification created: {ch.mention}")

@verify.command(name="panel")
@is_admin()
async def verify_panel(ctx): await ctx.send(embed=discord.Embed(title="🛡️ Verification", description="Click **Verify Me** to get access.", color=discord.Color.green()), view=VerifyView())

@verify.command(name="status")
@is_admin()
async def verify_status(ctx):
    c=cfg(ctx.guild.id); await ctx.send(f"Verified role: <@&{c['verified_role']}>\nUnverified role: <@&{c['unverified_role']}>\nChannel: <#{c['verify_channel']}>")

@verify.command(name="setrole")
@is_admin()
async def verify_setrole(ctx, verified: discord.Role, unverified: discord.Role): update_cfg(ctx.guild.id,verified_role=verified.id,unverified_role=unverified.id); await ctx.send("✅ Verification roles saved.")
@verify.command(name="setchannel")
@is_admin()
async def verify_setchannel(ctx, channel: discord.TextChannel): update_cfg(ctx.guild.id,verify_channel=channel.id); await ctx.send("✅ Verification channel saved.")
@verify.command(name="setlog")
@is_admin()
async def verify_setlog(ctx, channel: discord.TextChannel): update_cfg(ctx.guild.id,verify_log=channel.id); await ctx.send("✅ Verification log saved.")

# ---------------- Ticket ----------------
@bot.group(invoke_without_command=True)
@is_admin()
async def ticket(ctx): await ctx.send(CATEGORY_TEXT["Ticket System"])

@ticket.command(name="panel")
@is_admin()
async def ticket_panel(ctx):
    e=discord.Embed(title="🎫 Support Tickets", description="Click **Open Ticket** to create a private support channel.", color=discord.Color.blurple())
    await ctx.send(embed=e, view=TicketView())

@ticket.command(name="setup")
@is_admin()
async def ticket_setup(ctx):
    g=ctx.guild
    cat=discord.utils.get(g.categories,name="Tickets") or await g.create_category("Tickets")
    update_cfg(g.id,ticket_category=cat.id)
    await ctx.send(f"✅ Ticket category configured: {cat.name}")

@ticket.command(name="close")
@is_mod()
async def ticket_close(ctx):
    if not ctx.channel.name.startswith("ticket-"): return await ctx.send("This is not a ticket channel.")
    await send_log(ctx.guild,"ticket","Ticket Closed",f"{ctx.channel.mention} closed by {ctx.author.mention}")
    await ctx.channel.delete(reason=f"Ticket closed by {ctx.author}")

@ticket.command(name="claim")
@is_mod()
async def ticket_claim(ctx): await ctx.send(f"🎫 Ticket claimed by {ctx.author.mention}.")
@ticket.command(name="add")
@is_mod()
async def ticket_add(ctx, member: discord.Member): await ctx.channel.set_permissions(member,view_channel=True,send_messages=True,read_message_history=True); await ctx.send(f"✅ Added {member.mention}.")
@ticket.command(name="remove")
@is_mod()
async def ticket_remove(ctx, member: discord.Member): await ctx.channel.set_permissions(member,view_channel=False); await ctx.send(f"✅ Removed {member.mention}.")
@ticket.command(name="rename")
@is_mod()
async def ticket_rename(ctx, *, name): await ctx.channel.edit(name=name[:90]); await ctx.send("✅ Ticket renamed.")
@ticket.command(name="setping")
@is_admin()
async def ticket_setping(ctx, role: discord.Role): update_cfg(ctx.guild.id,ticket_role=role.id); await ctx.send(f"✅ Ticket staff role: {role.mention}")

# ---------------- Logs ----------------
@bot.command()
@is_admin()
async def setuplogs(ctx):
    await ctx.send("Use `$setuplogs all #channel` or the individual log commands: `$setbotlog`, `$setmodlog`, `$setticketlog`, `$setinvitelog`.")
@bot.command()
@is_admin()
async def setbotlog(ctx, channel: discord.TextChannel): update_cfg(ctx.guild.id,bot_log=channel.id); await ctx.send(f"✅ Bot log: {channel.mention}")
@bot.command()
@is_admin()
async def setmodlog(ctx, channel: discord.TextChannel): update_cfg(ctx.guild.id,mod_log=channel.id); await ctx.send(f"✅ Mod log: {channel.mention}")
@bot.command()
@is_admin()
async def setticketlog(ctx, channel: discord.TextChannel): update_cfg(ctx.guild.id,ticket_log=channel.id); await ctx.send(f"✅ Ticket log: {channel.mention}")
@bot.command()
@is_admin()
async def setinvitelog(ctx, channel: discord.TextChannel): update_cfg(ctx.guild.id,invite_log=channel.id); await ctx.send(f"✅ Invite log: {channel.mention}")
@bot.command()
@is_admin()
async def setalllogs(ctx, channel: discord.TextChannel): update_cfg(ctx.guild.id,bot_log=channel.id,mod_log=channel.id,ticket_log=channel.id,invite_log=channel.id,antinuke_log=channel.id); await ctx.send(f"✅ All logs set to {channel.mention}")

# ---------------- Automod ----------------
DEFAULT_AUTOMOD={"caps":False,"links":False,"discordlinks":False,"invites":False,"spam":False,"emoji":False,"nsfw":False,"extapps":False,"token":False,"mention":False,"timeout":10}

def get_automod(gid):
    c=cfg(gid); d=DEFAULT_AUTOMOD.copy()
    try: d.update(json.loads(c["automod_json"] or "{}"))
    except Exception: pass
    return d

@bot.group(invoke_without_command=True)
@is_admin()
async def automod(ctx): await ctx.send(CATEGORY_TEXT["Automod"])

@automod.command(name="enable")
@is_admin()
async def automod_enable(ctx):
    d=get_automod(ctx.guild.id); d.update({k:True for k in DEFAULT_AUTOMOD if k!="timeout"}); update_cfg(ctx.guild.id,automod_enabled=1,automod_json=json.dumps(d)); await ctx.send("🤖 Automod enabled.")
@automod.command(name="disable")
@is_admin()
async def automod_disable(ctx): update_cfg(ctx.guild.id,automod_enabled=0); await ctx.send("🤖 Automod disabled.")
@automod.command(name="status")
@is_admin()
async def automod_status(ctx): await ctx.send("```json\n"+json.dumps(get_automod(ctx.guild.id),indent=2)+"\n```")
@automod.command(name="settimeout")
@is_admin()
async def automod_settimeout(ctx, feature: str, mins: int):
    d=get_automod(ctx.guild.id); d["timeout"]=max(1,min(28*24*60,mins)); update_cfg(ctx.guild.id,automod_json=json.dumps(d)); await ctx.send(f"✅ Automod timeout set to `{d['timeout']}m`.")

@automod.command(name="caps")
@is_admin()
async def automod_caps(ctx, state: str): await automod_toggle(ctx,"caps",state)
@automod.command(name="links")
@is_admin()
async def automod_links(ctx, state: str): await automod_toggle(ctx,"links",state)
@automod.command(name="discordlinks")
@is_admin()
async def automod_discordlinks(ctx, state: str): await automod_toggle(ctx,"discordlinks",state)
@automod.command(name="invites")
@is_admin()
async def automod_invites(ctx, state: str): await automod_toggle(ctx,"invites",state)
@automod.command(name="spam")
@is_admin()
async def automod_spam(ctx, state: str): await automod_toggle(ctx,"spam",state)
@automod.command(name="emoji")
@is_admin()
async def automod_emoji(ctx, state: str): await automod_toggle(ctx,"emoji",state)
@automod.command(name="nsfw")
@is_admin()
async def automod_nsfw(ctx, state: str): await automod_toggle(ctx,"nsfw",state)
@automod.command(name="extapps")
@is_admin()
async def automod_extapps(ctx, state: str): await automod_toggle(ctx,"extapps",state)
@automod.command(name="token")
@is_admin()
async def automod_token(ctx, state: str): await automod_toggle(ctx,"token",state)
@automod.command(name="mention")
@is_admin()
async def automod_mention(ctx, state: str): await automod_toggle(ctx,"mention",state)

async def automod_toggle(ctx,key,state):
    if state.lower() not in ("on","off"): return await ctx.send("Use `on` or `off`.")
    d=get_automod(ctx.guild.id); d[key]=state.lower()=="on"; update_cfg(ctx.guild.id,automod_enabled=1,automod_json=json.dumps(d)); await ctx.send(f"✅ `{key}` = `{state.lower()}`")

@bot.event
async def _automod_message(message):
    pass

# Use a single message listener so it can coexist with commands.
@bot.listen("on_message")
async def automod_listener(message):
    if message.author.bot or not message.guild: return
    # AFK handling
    if message.author.id in AFK_CACHE:
        AFK_CACHE.pop(message.author.id,None)
        await message.channel.send(f"👋 Welcome back {message.author.mention}! Your AFK was removed.", delete_after=6)
    for user in message.mentions:
        if user.id in AFK_CACHE:
            reason,_=AFK_CACHE[user.id]
            await message.channel.send(f"💤 {user.mention} is AFK: **{reason}**", delete_after=8)
    # Auto responders
    c=cfg(message.guild.id)
    try: ar=json.loads(c["autoresponder_json"] or "{}")
    except Exception: ar={}
    low=message.content.lower()
    for trigger,reply in ar.items():
        if trigger.lower() in low:
            await message.channel.send(reply[:2000]); break
    # Word react
    try: wr=json.loads(c["wordreact_json"] or "{}")
    except Exception: wr={}
    for word, emojis in wr.items():
        if word.lower() in low:
            for emoji in emojis[:3]:
                try: await message.add_reaction(emoji)
                except Exception: pass
    # Auto react
    try: rr=json.loads(c["autoreact_json"] or "{}")
    except Exception: rr={}
    emojis=rr.get(str(message.channel.id),[])
    for emoji in emojis[:3]:
        try: await message.add_reaction(emoji)
        except Exception: pass
    # Level XP
    if c["level_enabled"]:
        row=db("SELECT xp,level FROM levels WHERE guild_id=? AND user_id=?", (message.guild.id,message.author.id), True)
        xp,level=(row[0]["xp"],row[0]["level"]) if row else (0,0)
        xp += random.randint(5,15)
        need=(level+1)*100
        if xp>=need:
            level+=1; xp-=need
            db("INSERT INTO levels(guild_id,user_id,xp,level) VALUES(?,?,?,?) ON CONFLICT(guild_id,user_id) DO UPDATE SET xp=excluded.xp,level=excluded.level", (message.guild.id,message.author.id,xp,level))
            if c["level_channel"]:
                ch=message.guild.get_channel(c["level_channel"])
                if ch: await ch.send(f"🏆 {message.author.mention} reached **Level {level}**!")
        else:
            db("INSERT INTO levels(guild_id,user_id,xp,level) VALUES(?,?,?,?) ON CONFLICT(guild_id,user_id) DO UPDATE SET xp=excluded.xp,level=excluded.level", (message.guild.id,message.author.id,xp,level))
    # Automod
    if not c["automod_enabled"]: return
    d=get_automod(message.guild.id)
    content=message.content
    reason=None
    urls=re.findall(r"https?://\S+|www\.\S+",content.lower())
    if d.get("links") and urls: reason="Links are not allowed"
    if d.get("discordlinks") and any("discord.gg/" in x or "discord.com/invite/" in x for x in urls): reason="Discord links are not allowed"
    if d.get("invites") and ("discord.gg/" in content.lower() or "discord.com/invite/" in content.lower()): reason="Discord invites are not allowed"
    letters=[x for x in content if x.isalpha()]
    if d.get("caps") and len(letters)>=8 and sum(x.isupper() for x in letters)/len(letters)>=.7: reason="Excessive CAPS"
    if d.get("emoji") and len(re.findall(r"<a?:\w+:\d+>|[\U0001F300-\U0001FAFF]",content))>=10: reason="Emoji spam"
    if d.get("mention") and (len(message.mentions)+len(message.role_mentions))>=5: reason="Mass mentions"
    if d.get("token") and re.search(r"[MN][A-Za-z\d_-]{20,}\.[A-Za-z\d_-]{5,}\.[A-Za-z\d_-]{20,}",content): reason="Token-like content"
    if d.get("spam"):
        arr=SPAM_CACHE.setdefault(message.author.id,[]); arr.append(now()); SPAM_CACHE[message.author.id]=[x for x in arr if now()-x<5]
        if len(arr)>=7: reason="Message spam"
    if reason:
        try: await message.delete()
        except Exception: pass
        try:
            if isinstance(message.author,discord.Member) and message.guild.me.guild_permissions.moderate_members:
                await message.author.timeout(timedelta(minutes=int(d.get("timeout",10))), reason=f"Automod: {reason}")
        except Exception: pass
        await send_log(message.guild,"mod","Automod Action",f"**User:** {message.author.mention}\n**Channel:** {message.channel.mention}\n**Reason:** {reason}",discord.Color.orange())

# ---------------- Security ----------------
@bot.group(invoke_without_command=True)
@is_admin()
async def security(ctx): await ctx.send(CATEGORY_TEXT["Security"])

@security.command(name="admins")
@is_admin()
async def security_admins(ctx):
    users=[m.mention for m in ctx.guild.members if m.guild_permissions.administrator and not m.bot]
    await ctx.send("🔐 **Administrators**\n"+("\n".join(users[:50]) or "None"))
@security.command(name="bots")
@is_admin()
async def security_bots(ctx): await ctx.send("🤖 **Bots**\n"+"\n".join(f"• {m} — {m.id}" for m in ctx.guild.members if m.bot)[:3900])
@security.command(name="newmembers")
@is_admin()
async def security_newmembers(ctx, days: int=7):
    cutoff=datetime.now(timezone.utc)-timedelta(days=max(1,min(30,days)))
    users=[m for m in ctx.guild.members if m.joined_at and m.joined_at>=cutoff]
    await ctx.send(f"👤 `{len(users)}` members joined in the last `{days}d`.\n"+"\n".join(f"• {m.mention} — {discord.utils.format_dt(m.joined_at,'R')}" for m in users[:40]))
@security.command(name="checkreps")
@is_admin()
async def security_checkreps(ctx):
    risky=[r for r in ctx.guild.roles if not r.is_default() and (r.permissions.administrator or r.permissions.manage_guild or r.permissions.manage_roles)]
    await ctx.send("⚠️ **Roles with powerful permissions**\n"+"\n".join(f"• {r.mention}: admin={r.permissions.administrator}, manage_guild={r.permissions.manage_guild}, manage_roles={r.permissions.manage_roles}" for r in risky[:50]) or "None")
@security.command(name="audit")
@is_admin()
async def security_audit(ctx):
    try:
        entries=[e async for e in ctx.guild.audit_logs(limit=20)]
        text="\n".join(f"• `{e.action.name}` — {e.user} — <t:{int(e.created_at.timestamp())}:R>" for e in entries)
    except Exception: text="I cannot read the audit log. Check my View Audit Log permission."
    await ctx.send("🔐 **Recent Audit Log**\n"+text[:3900])

# ---------------- Anti-Nuke / Raid ----------------
@bot.group(invoke_without_command=True)
@is_admin()
async def antinuke(ctx): await ctx.send(CATEGORY_TEXT["Anti-Nuke"])

@antinuke.command(name="enable")
@is_admin()
async def antinuke_enable(ctx): update_cfg(ctx.guild.id,antinuke_enabled=1); await ctx.send("🛡️ Anti-Nuke enabled.")
@antinuke.command(name="disable")
@is_admin()
async def antinuke_disable(ctx): update_cfg(ctx.guild.id,antinuke_enabled=0); await ctx.send("🛡️ Anti-Nuke disabled.")
@antinuke.command(name="setlog")
@is_admin()
async def antinuke_setlog(ctx, channel: discord.TextChannel): update_cfg(ctx.guild.id,antinuke_log=channel.id); await ctx.send(f"✅ Anti-Nuke log: {channel.mention}")
@antinuke.command(name="raid")
@is_admin()
async def antinuke_raid(ctx,state:str):
    if state.lower() not in ("on","off"): return await ctx.send("Use on/off")
    update_cfg(ctx.guild.id,raid_enabled=int(state.lower()=="on")); await ctx.send(f"🚨 Raid shield: `{state.lower()}`")
@antinuke.command(name="lock")
@is_admin()
async def antinuke_lock(ctx):
    for ch in ctx.guild.text_channels:
        try: await ch.set_permissions(ctx.guild.default_role, send_messages=False, reason="Empire Prime lockdown")
        except Exception: pass
    await ctx.send("🔒 Server text channels locked.")
@antinuke.command(name="unlock")
@is_admin()
async def antinuke_unlock(ctx):
    for ch in ctx.guild.text_channels:
        try: await ch.set_permissions(ctx.guild.default_role, send_messages=None, reason="Empire Prime lockdown lifted")
        except Exception: pass
    await ctx.send("🔓 Server text channels unlocked.")
@antinuke.command(name="status")
@is_admin()
async def antinuke_status(ctx):
    c=cfg(ctx.guild.id); await ctx.send(f"Anti-Nuke: `{bool(c['antinuke_enabled'])}`\nRaid shield: `{bool(c['raid_enabled'])}`\nLog: {f'<#{c["antinuke_log"]}>' if c['antinuke_log'] else 'not set'}")
@antinuke.command(name="test")
@is_admin()
async def antinuke_test(ctx): await send_log(ctx.guild,"antinuke","🛡️ Anti-Nuke Test",f"Test triggered by {ctx.author.mention}",discord.Color.green()); await ctx.send("✅ Test sent to the Anti-Nuke log.")
@antinuke.command(name="ghostping")
@is_admin()
async def antinuke_ghostping(ctx, action="show"): await ctx.send("👻 Ghost-ping protection is included in the automod/anti-nuke listener. Use `$automod mention on` for mass mention protection.")
@antinuke.command(name="wllist")
@is_admin()
async def antinuke_wllist(ctx):
    c=cfg(ctx.guild.id); d=json.loads(c["antinuke_json"] or "{}"); await ctx.send("Whitelist users: "+", ".join(f"<@{x}>" for x in d.get("users",[])) + "\nWhitelist roles: "+", ".join(f"<@&{x}>" for x in d.get("roles",[])))
@antinuke.command(name="whitelist")
@is_admin()
async def antinuke_whitelist(ctx, member: discord.Member):
    c=cfg(ctx.guild.id); d=json.loads(c["antinuke_json"] or "{}"); d.setdefault("users",[]); 
    if member.id not in d["users"]: d["users"].append(member.id)
    update_cfg(ctx.guild.id,antinuke_json=json.dumps(d)); await ctx.send(f"✅ Whitelisted {member.mention}.")
@antinuke.command(name="unwhitelist")
@is_admin()
async def antinuke_unwhitelist(ctx, member: discord.Member):
    c=cfg(ctx.guild.id); d=json.loads(c["antinuke_json"] or "{}"); d["users"]=[x for x in d.get("users",[]) if x!=member.id]; update_cfg(ctx.guild.id,antinuke_json=json.dumps(d)); await ctx.send(f"✅ Removed {member.mention} from whitelist.")
@antinuke.command(name="wlrole")
@is_admin()
async def antinuke_wlrole(ctx, role: discord.Role):
    c=cfg(ctx.guild.id); d=json.loads(c["antinuke_json"] or "{}"); d.setdefault("roles",[]); 
    if role.id not in d["roles"]: d["roles"].append(role.id)
    update_cfg(ctx.guild.id,antinuke_json=json.dumps(d)); await ctx.send(f"✅ Whitelisted role {role.mention}.")
@antinuke.command(name="unwlrole")
@is_admin()
async def antinuke_unwlrole(ctx, role: discord.Role):
    c=cfg(ctx.guild.id); d=json.loads(c["antinuke_json"] or "{}"); d["roles"]=[x for x in d.get("roles",[]) if x!=role.id]; update_cfg(ctx.guild.id,antinuke_json=json.dumps(d)); await ctx.send(f"✅ Removed role {role.mention} from whitelist.")
@antinuke.command(name="setpunish")
@is_admin()
async def antinuke_setpunish(ctx, mode):
    if mode not in ("ban","kick","strip"): return await ctx.send("Use ban/kick/strip.")
    c=cfg(ctx.guild.id); d=json.loads(c["antinuke_json"] or "{}"); d["punish"]=mode; update_cfg(ctx.guild.id,antinuke_json=json.dumps(d)); await ctx.send(f"✅ Anti-Nuke punishment: `{mode}`")
@antinuke.command(name="thresholds")
@is_admin()
async def antinuke_thresholds(ctx): await ctx.send("Current safe defaults: raid = 8 joins/5s; automod spam = 7 messages/5s; mass mention = 5 mentions/message.")

# ---------------- Invite logging ----------------
@bot.command(aliases=["i"])
async def invite_stats(ctx, member: discord.Member=None):
    member=member or ctx.author
    row=db("SELECT uses,leaves,fake,rejoins FROM invites WHERE guild_id=? AND inviter_id=?",(ctx.guild.id,member.id),True)
    if not row: return await ctx.send(f"📨 {member.mention} has no invite stats yet.")
    r=row[0]; await ctx.send(f"📨 **{member}** — joins: `{r['uses']}` • leaves: `{r['leaves']}` • fake: `{r['fake']}` • rejoins: `{r['rejoins']}`")

@bot.command()
async def invited(ctx, member: discord.Member=None):
    member=member or ctx.author
    rows=db("SELECT user_id,joined_at,left_at FROM invited_users WHERE guild_id=? AND inviter_id=? ORDER BY joined_at DESC LIMIT 30",(ctx.guild.id,member.id),True)
    await ctx.send("\n".join(f"• <@{r['user_id']}> — <t:{r['joined_at']}:d>" for r in rows) or "No invited users recorded.")

@bot.command()
async def inviteboard(ctx):
    rows=db("SELECT inviter_id,uses,leaves FROM invites WHERE guild_id=? ORDER BY uses DESC LIMIT 15",(ctx.guild.id,),True)
    await ctx.send("🏆 **Invite Leaderboard**\n"+"\n".join(f"{i+1}. <@{r['inviter_id']}> — `{r['uses']}` joins / `{r['leaves']}` leaves" for i,r in enumerate(rows)) or "No data yet.")

@bot.command()
@is_admin()
async def resetinvites(ctx, member: discord.Member):
    db("DELETE FROM invites WHERE guild_id=? AND inviter_id=?",(ctx.guild.id,member.id)); await ctx.send(f"✅ Reset invite stats for {member.mention}.")

# ---------------- Premium misc ----------------
@bot.command()
@is_admin()
async def nukerecovery(ctx, state="status"):
    if state not in ("on","off","status"): return await ctx.send("Use on/off/status.")
    if state=="status": return await ctx.send(f"☢️ Nuke recovery: `{bool(cfg(ctx.guild.id)['nukerecovery'])}`")
    update_cfg(ctx.guild.id,nukerecovery=int(state=="on")); await ctx.send(f"☢️ Nuke recovery: `{state}`")

@bot.command()
@is_admin()
async def backup(ctx, action="info"):
    if action=="info":
        r=db("SELECT id,created_at FROM backups WHERE guild_id=? ORDER BY id DESC LIMIT 1",(ctx.guild.id,),True)
        return await ctx.send(f"💾 Latest backup: `{r[0]['id']}` (<t:{r[0]['created_at']}:R>)" if r else "No backup exists.")
    if action!="create": return await ctx.send("Use `$backup create` or `$backup info`.")
    data={"guild":ctx.guild.id,"name":ctx.guild.name,"roles":[{"name":r.name,"permissions":r.permissions.value,"color":r.color.value} for r in ctx.guild.roles if not r.is_default()],"channels":[{"name":c.name,"type":str(c.type),"category":c.category_id} for c in ctx.guild.channels]}
    bid=db("INSERT INTO backups(guild_id,created_at,data) VALUES(?,?,?)",(ctx.guild.id,now(),json.dumps(data)))
    await ctx.send(f"💾 Backup created. Backup ID: `{bid}`")

@bot.command()
async def rank(ctx, member: discord.Member=None):
    member=member or ctx.author; r=db("SELECT xp,level FROM levels WHERE guild_id=? AND user_id=?",(ctx.guild.id,member.id),True)
    xp,level=(r[0]["xp"],r[0]["level"]) if r else (0,0); await ctx.send(f"🏆 {member.mention} — Level `{level}` • XP `{xp}`")

@bot.command()
async def leaderboard(ctx):
    rows=db("SELECT user_id,level,xp FROM levels WHERE guild_id=? ORDER BY level DESC,xp DESC LIMIT 10",(ctx.guild.id,),True)
    await ctx.send("🏆 **Leaderboard**\n"+"\n".join(f"{i+1}. <@{r['user_id']}> — Lv.{r['level']} ({r['xp']} XP)" for i,r in enumerate(rows)) or "No XP yet.")

@bot.command()
@is_admin()
async def setlevel(ctx, state=None, *args):
    if state in ("on","off"): update_cfg(ctx.guild.id,level_enabled=int(state=="on")); return await ctx.send(f"🏆 Leveling `{state}`")
    if state=="channel" and args:
        ch=ctx.message.channel_mentions[0] if ctx.message.channel_mentions else None
        if ch: update_cfg(ctx.guild.id,level_channel=ch.id); return await ctx.send(f"🏆 Level channel: {ch.mention}")
    await ctx.send("Use `$setlevel on/off` or `$setlevel channel #channel`.")

@bot.command()
@is_admin()
async def autorole(ctx, action, role: discord.Role=None):
    c=cfg(ctx.guild.id); roles=json.loads(c["autoroles_json"] or "[]")
    if action=="add" and role: 
        if role.id not in roles: roles.append(role.id)
    elif action=="remove" and role: roles=[x for x in roles if x!=role.id]
    elif action=="list": return await ctx.send("🤖 Autoroles: "+", ".join(f"<@&{x}>" for x in roles) or "none")
    else: return await ctx.send("Use `$autorole add @role`, `$autorole remove @role`, `$autorole list`.")
    update_cfg(ctx.guild.id,autoroles_json=json.dumps(roles)); await ctx.send("✅ Autoroles updated.")

@bot.command()
@is_admin()
async def autoreact(ctx, action, channel: discord.TextChannel=None, *emojis):
    c=cfg(ctx.guild.id); data=json.loads(c["autoreact_json"] or "{}")
    if action=="set" and channel and emojis: data[str(channel.id)]=list(emojis)
    elif action=="remove" and channel: data.pop(str(channel.id),None)
    elif action=="list": return await ctx.send("⚡ Auto-react: "+"\n".join(f"<#{k}>: {' '.join(v)}" for k,v in data.items()) or "none")
    else: return await ctx.send("Use `$autoreact set #channel 👍 ❤️` or remove/list.")
    update_cfg(ctx.guild.id,autoreact_json=json.dumps(data)); await ctx.send("✅ Auto-react updated.")

@bot.command()
@is_admin()
async def wordreact(ctx, action, word=None, *emojis):
    c=cfg(ctx.guild.id); data=json.loads(c["wordreact_json"] or "{}")
    if action=="add" and word and emojis: data[word]=list(emojis)
    elif action=="remove" and word: data.pop(word,None)
    elif action=="list": return await ctx.send("💬 Word-react: "+"\n".join(f"`{k}` → {' '.join(v)}" for k,v in data.items()) or "none")
    else: return await ctx.send("Use `$wordreact add hello 👋` or remove/list.")
    update_cfg(ctx.guild.id,wordreact_json=json.dumps(data)); await ctx.send("✅ Word-react updated.")

@bot.command(aliases=["wr"])
@is_admin()
async def ar(ctx, action, trigger=None, *, reply=None):
    c=cfg(ctx.guild.id); data=json.loads(c["autoresponder_json"] or "{}")
    if action=="add" and trigger and reply: data[trigger]=reply
    elif action=="remove" and trigger: data.pop(trigger,None)
    elif action=="list": return await ctx.send("💬 Auto responders: "+"\n".join(f"`{k}` → {v}" for k,v in data.items()) or "none")
    else: return await ctx.send("Use `$ar add <trigger> <reply>` or remove/list.")
    update_cfg(ctx.guild.id,autoresponder_json=json.dumps(data)); await ctx.send("✅ Auto responder updated.")

@bot.command()
async def remind(ctx, duration: str, *, what):
    seconds=parse_duration(duration)
    if not seconds: return await ctx.send("Use a duration like `10m`, `1h`, `1d`.")
    db("INSERT INTO timers(guild_id,channel_id,user_id,end_at,label) VALUES(?,?,?,?,?)",(ctx.guild.id,ctx.channel.id,ctx.author.id,now()+seconds,what)); await ctx.send(f"🔔 Reminder set for `{duration}`: **{what}**")

@bot.command()
async def poll(ctx, duration: str, *, content):
    parts=[x.strip() for x in content.split("|")]
    if len(parts)<3: return await ctx.send("Use `$poll 1h Question | Option 1 | Option 2`.")
    question=parts[0]; options=parts[1:11]
    e=discord.Embed(title="📊 Poll",description=f"**{question}**\n\n"+"\n".join(f"{i+1}️⃣ {o}" for i,o in enumerate(options)),color=discord.Color.blurple())
    msg=await ctx.send(embed=e)
    for i in range(len(options)): await msg.add_reaction(f"{i+1}️⃣")

# ---------------- Autorole on join hook extension ----------------
@bot.listen("on_member_join")
async def autorole_listener(member):
    c=cfg(member.guild.id)
    try: roles=json.loads(c["autoroles_json"] or "[]")
    except Exception: roles=[]
    for rid in roles:
        role=member.guild.get_role(rid)
        if role:
            try: await member.add_roles(role,reason="Empire Prime autorole")
            except Exception: pass

# ---------------- Simple reaction-role commands ----------------
@bot.command()
@is_admin()
async def rr(ctx, action, message_id=None, emoji=None, role: discord.Role=None):
    c=cfg(ctx.guild.id); data=json.loads(c["reaction_roles_json"] or "{}")
    if action=="add":
        if not message_id or not emoji or not role: return await ctx.send("Usage: reply to a message and use `$rr add 🎉 @role`, or `$rr add <msg_id> 🎉 @role`.")
        data.setdefault(str(message_id),{})[emoji]=role.id
        try:
            msg=await ctx.channel.fetch_message(int(message_id)); await msg.add_reaction(emoji)
        except Exception: pass
    elif action=="remove":
        if str(message_id) in data: data[str(message_id)].pop(emoji,None)
    elif action=="list": return await ctx.send("🎭 Reaction roles configured: "+json.dumps(data)[:3800])
    else: return await ctx.send("Use add/remove/list.")
    update_cfg(ctx.guild.id,reaction_roles_json=json.dumps(data)); await ctx.send("✅ Reaction role updated.")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id: return
    guild=bot.get_guild(payload.guild_id) if payload.guild_id else None
    if not guild: return
    c=cfg(guild.id); data=json.loads(c["reaction_roles_json"] or "{}"); mapping=data.get(str(payload.message_id),{})
    emoji=str(payload.emoji)
    rid=mapping.get(emoji) or mapping.get(payload.emoji.name or "")
    if rid:
        role=guild.get_role(rid); member=guild.get_member(payload.user_id)
        if role and member:
            try: await member.add_roles(role,reason="Empire Prime reaction role")
            except Exception: pass

# ---------------- Commands that mirror the requested menu ----------------
@bot.command()
@is_admin()
async def antispam(ctx, state):
    if state.lower() not in ("on","off"): return await ctx.send("Use on/off")
    update_cfg(ctx.guild.id,anti_spam=int(state.lower()=="on")); d=get_automod(ctx.guild.id); d["spam"]=state.lower()=="on"; update_cfg(ctx.guild.id,automod_json=json.dumps(d),automod_enabled=1); await ctx.send(f"🚫 Anti-spam: `{state.lower()}`")

@bot.command()
@is_admin()
async def tempvc(ctx, action, channel: discord.VoiceChannel=None):
    if action=="set" and channel: update_cfg(ctx.guild.id,tempvc_hub=channel.id); await ctx.send(f"🔊 Temp VC hub: {channel.mention}")
    elif action=="off": update_cfg(ctx.guild.id,tempvc_hub=None); await ctx.send("🔊 Temp VC disabled.")
    else: await ctx.send("Use `$tempvc set #hub` or `$tempvc off`.")

@bot.command()
@is_admin()
async def sticky(ctx, action, *, text=None):
    c=cfg(ctx.guild.id); data=json.loads(c["sticky_json"] or "{}")
    if action=="set" and text: data[str(ctx.channel.id)]=text; update_cfg(ctx.guild.id,sticky_json=json.dumps(data)); await ctx.send("📌 Sticky message saved.")
    elif action=="remove": data.pop(str(ctx.channel.id),None); update_cfg(ctx.guild.id,sticky_json=json.dumps(data)); await ctx.send("📌 Sticky removed.")
    else: await ctx.send("Use `$sticky set <text>` or `$sticky remove`.")

# Add basic custom help aliases for category browsing.
for _name, _category in [("premium","Premium"),("giveaways","Giveaways"),("timer","Timer"),("utility","Utility")]:
    async def _cat(ctx, _cat=_category):
        await ctx.send(embed=discord.Embed(description=CATEGORY_TEXT[_cat], color=discord.Color.blurple()), view=HelpView(ctx.author.id))
    bot.command(name=_name)(_cat)

# Graceful start
TOKEN=os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("ERROR: DISCORD_TOKEN is not set. Copy .env.example to .env and add your bot token.")
else:
    bot.run(TOKEN)
