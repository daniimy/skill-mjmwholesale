# skill-mjmwholesale

Coding-agent skill for MJM Battery wholesale sales — sourced from `~/.pi/agent/skills/mjm-battery-wholesale-sale` (Pi).

Posts `Kiriman Luar Kota` (custom grosir) sales to `https://mjmbattery.com/admin/sale_custom_wholesale.php` — browserless, via direct HTTP.

## Setup

```bash
cp .env.example .env
# edit .env in Notepad -> MJM_USERNAME / MJM_PASSWORD
```

Or use env vars / legacy state file — see `SKILL.md` §Credentials.

```bash
# verify login
python3 scripts/post_sale.py login

# post from JSON
cat invoice.json | python3 scripts/post_sale.py post --expense
```

## Source

This repo is a snapshot of the Pi skill at `~/.pi/agent/skills/mjm-battery-wholesale-sale`.
The canonical dev copy lives in `hermes-skills-mjm` — this repo is for sharing as a standalone coding-agent skill.

## Security

`.env` is git-ignored. Do not commit credentials. `.env.example` shows the required keys.
