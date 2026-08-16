# Empire Prime Discord Bot

A Python/discord.py multipurpose Discord bot matching the requested Empire Prime style:

- `$help` interactive dropdown with the requested categories, descriptions and support-server button
- `$ai hello` and `!ai hello` AI chat (requires an OpenAI API key)
- Random questions with `$randomq`
- Moderation: warn, warnings, clearwarns, ban, kick, timeout, purge, lock, unlock, slowmode
- Giveaways: `$gstart`, `$gend`, `$greroll` with 🎉 entries
- Announcement and link posting: `$announce #channel <message>`, `$link #channel <url> [text]`
- Tickets with buttons
- Verification panel with button
- Welcome messages and autoroles
- Automod, anti-spam, basic anti-nuke/raid shield, security tools
- Invite stats, logging, levels, reaction roles, auto-react, word-react, auto-responder, reminders, polls, timers, snipe/edit-snipe
- SQLite persistence

## Important

This bot **cannot create unlimited Discord Nitro** or bypass Discord's paid services. You can use `Nitro` as a giveaway prize and manually provide a legitimate gift/subscription.

## Setup

1. Create a Discord application and bot in the Discord Developer Portal.
2. Enable the privileged intents the bot needs, especially **Message Content Intent** and **Server Members Intent**.
3. Invite the bot with the permissions it needs for moderation, channels, messages, roles and reactions.
4. Copy `.env.example` to `.env` and set `DISCORD_TOKEN`.
5. Set `OPENAI_API_KEY` if you want `$ai` / `!ai`.
6. Install dependencies:

```bash
pip install -r requirements.txt
```

7. Start:

```bash
python bot.py
```

The local `logo.png` is included and is used in the help menu. Replace it with your final Empire Prime logo if you want the exact original image.

## First commands

```text
$help
$setalllogs #bot-logs
$ticket setup
$ticket panel
$verify setup
$welcome channel #welcome
$welcome message Welcome {mention} to {server}!
$automod enable
$antinuke enable
$antinuke raid on
$gstart 1h 2 Nitro
$announce #announcements Your announcement here
$link #links https://example.com Open Website
$ai hello
!ai hello
```
