# AppWhitelister — Application Whitelisting Tool

Ek dark-mode PyQt5 desktop app jo applications ko whitelist karke unka SHA-256 hash verify karta hai.

---

## Folder Structure

```
AppWhitelister/
├── main.py                  ← Entry point (yahi run karo)
├── requirements.txt
├── whitelister.db           ← Auto-create hoga pehli baar
├── core/
│   ├── __init__.py
│   ├── database.py          ← SQLite DB layer
│   ├── security.py          ← Hashing, validation, process monitor
│   └── exporter.py          ← CSV export
└── ui/
    ├── __init__.py
    ├── main_window.py        ← Main window (tabs)
    ├── dialogs.py            ← Add App, Login, Set Password dialogs
    ├── widgets.py            ← StatCard, BadgeLabel, Toast
    └── styles.py             ← Dark theme QSS
```

---

## Setup & Run Karne Ke Steps

### Step 1 — Python install check
```
python --version
```
Python 3.10+ hona chahiye.

### Step 2 — Dependencies install karo
```
pip install -r requirements.txt
```

### Step 3 — Run karo
```
python main.py
```

---

## Features
- ✅ Application whitelist manage karo (add/remove/toggle)
- 🔐 SHA-256 hash verification har launch pe
- 📊 Dashboard with stats (allowed, blocked, mismatches)
- 🔍 Background process monitor
- 📁 CSV export (logs + whitelist)
- 🔑 Admin password protection
