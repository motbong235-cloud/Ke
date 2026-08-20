# របៀប Deploy Bot ទៅ Render

## ⚠️ អំពីសំណើពណ៌ប៊ូតុង
កូដនេះប្រើ **Reply Keyboard** (ក្តារចុចធម្មតា) 100% ដែល Telegram **មិនអនុញ្ញាតឲ្យដាក់ពណ៌បានទេ** — មានតែ **Inline Keyboard** ប៉ុណ្ណោះទើបដាក់ពណ៌បាន (Bot API 9.4 `style` field)។ អ្នកបានជ្រើសរើសរក្សា Reply Keyboard ដដែល ដូច្នេះកូដមិនត្រូវបានប្តូររចនាសម្ព័ន្ធនោះទេ។ ខ្ញុំបានកែតែផ្នែក Deploy ប៉ុណ្ណោះ។

## អ្វីដែលបានកែ
- `MAIN_BOT_TOKEN` និង `SUPER_ADMIN_ID` ផ្លាស់ទៅអានពី Environment Variables (លែងដាក់ត្រង់ៗក្នុងកូដ — សុវត្ថិភាពជាង)
- `DB_FILE` ដាក់ឲ្យទៅតាម `DATA_DIR` ដើម្បីរក្សាទិន្នន័យកុំឲ្យបាត់ពេល Redeploy (ត្រូវប្រើ Render Persistent Disk)

## ជំហាន Deploy

### ១. ដាក់ឡើង GitHub
```bash
git init
git add bot.py requirements.txt render.yaml .gitignore
git commit -m "Deploy: telegram shop bot"
git remote add origin https://github.com/sovannarinsorn-droid/<ឈ្មោះ-repo>.git
git push -u origin main
```

### ២. បង្កើត Service លើ Render
1. ចូល https://dashboard.render.com → **New** → **Blueprint**
2. ភ្ជាប់ GitHub repo ដែលមាន `render.yaml` (Render នឹងអានឯកសារនេះស្វ័យប្រវត្តិ)
3. ប្រភេទ Service ត្រូវជា **Background Worker** (មិនមែន Web Service ព្រោះ Bot នេះប្រើ Polling មិនចាំបាច់បើក Port)

### ៣. ដាក់ Environment Variables (ក្នុង Render Dashboard → Environment)
| Key | Value |
|---|---|
| `MAIN_BOT_TOKEN` | Token ពិត ដែលយកពី @BotFather |
| `SUPER_ADMIN_ID` | Telegram ID របស់អ្នក (Super Admin) |
| `DATA_DIR` | `/var/data` (Render បង្កើត Disk ស្វ័យប្រវត្តិតាម render.yaml រួចហើយ) |

### ៤. Deploy
ចុច **Apply** — Render នឹង build និង start bot ស្វ័យប្រវត្តិ។ Database (SQLite) នឹងរក្សាទុកជាអចិន្ត្រៃយ៍លើ Persistent Disk ១GB (Plan: Starter, មិនមែនឥតគិតថ្លៃទេ ព្រោះ Disk ត្រូវការ Paid Plan)។

### ចំណាំ
- បើមិនចង់ចំណាយលើ Disk ទេ លុប `disk:` ចេញពី `render.yaml` — ប៉ុន្តែទិន្នន័យ (users, stocks, transactions) នឹងបាត់រាល់ពេល Redeploy ឬ Restart។
- កូន Bot ដែលបន្ថែមតាមម៉ឺនុយ "🤖Abb Bot" នឹងឈប់រត់វិញពេល Server restart លុះត្រាតែមាន Logic ស្តារពី `child_bots` table ពេល boot (កូដបច្ចុប្បន្នមាន Logic នេះរួចហើយក្នុង `boot_entire_system()`)។
