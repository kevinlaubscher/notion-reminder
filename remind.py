import os, requests
from datetime import date

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["DATABASE_ID"]
PUSHOVER_TOKEN = os.environ["PUSHOVER_TOKEN"]
PUSHOVER_USER = os.environ["PUSHOVER_USER"]
MODE = os.environ.get("MODE", "morning")  # "morning" oder "evening"

today = date.today().isoformat()

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# --- MORGENS: alle To-Dos mit Datum = heute ---
# --- ABENDS:  nur To-Dos mit Datum = heute UND Checkbox = false ---

filter_conditions = [
    {
        "property": "Erledigen bis",  # <-- ggf. exakten Property-Namen anpassen
        "date": {"equals": today}
    }
]

if MODE == "evening":
    filter_conditions.append({
        "property": "Kontrollkästchen",  # <-- ggf. anpassen
        "checkbox": {"equals": False}
    })

res = requests.post(
    f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
    headers=headers,
    json={"filter": {"and": filter_conditions}}
)

todos = res.json().get("results", [])

# --- ABENDS: nur senden wenn wirklich noch was offen ist ---
if MODE == "evening" and not todos:
    print("Alles erledigt – keine Notification nötig.")
    exit()

# Aufgaben-Namen extrahieren
items = []
for page in todos:
    try:
        name = page["properties"]["Name"]["title"][0]["plain_text"]
        items.append(name)
    except (KeyError, IndexError):
        pass

if MODE == "morning":
    if not items:
        print("Keine To-Dos heute – keine Notification.")
        exit()
    title = f"☀️ {len(items)} Aufgabe(n) heute"
    msg   = "\n".join(f"• {i}" for i in items)
    priority = 0
    sound    = "pushover"
else:
    title = f"🌙 Noch {len(items)} nicht erledigt"
    msg   = "\n".join(f"• {i}" for i in items)
    priority = -1   # leise abends
    sound    = "none"

# Pushover senden
r = requests.post(
    "https://api.pushover.net/1/messages.json",
    data={
        "token":    PUSHOVER_TOKEN,
        "user":     PUSHOVER_USER,
        "title":    title,
        "message":  msg,
        "priority": priority,
        "sound":    sound
    }
)
print(f"Pushover Status: {r.status_code} – {r.text}")