import time
import decimal
import logging
import psycopg2
from psycopg2.extras import DictCursor
from core.config import DB_CONFIG

logger = logging.getLogger(__name__)

def get_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=DictCursor)

def wait_for_db(retries=20, delay=2):
    """Wait for the database to become available."""
    for i in range(retries):
        try:
            conn = get_connection()
            conn.close()
            logger.info("Postgres is available")
            return
        except Exception as e:
            logger.info(f"Postgres is not available, attempt {i+1}/{retries}: {e}")
            time.sleep(delay)
    raise RuntimeError("Could not connect to Postgres.")

def init_db():
    """Create tables and fill with test stations (if not present)."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        tg_id BIGINT UNIQUE NOT NULL,
        role VARCHAR(20) NOT NULL, -- curator, organizer, admin
        group_id INT,
        station_id INT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id SERIAL PRIMARY KEY,
        group_number VARCHAR(20) UNIQUE NOT NULL,
        score NUMERIC DEFAULT 0
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stations (
        id SERIAL PRIMARY KEY,
        number INT UNIQUE NOT NULL,
        name VARCHAR(200),
        location TEXT,
        is_free BOOLEAN DEFAULT TRUE,
        current_group INT REFERENCES groups(id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS rewards (
        id SERIAL PRIMARY KEY,
        group_id INT REFERENCES groups(id),
        station_id INT REFERENCES stations(id),
        points NUMERIC NOT NULL,
        bonus NUMERIC DEFAULT 0,
        timestamp TIMESTAMP DEFAULT NOW()
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key VARCHAR(100) PRIMARY KEY,
        value TEXT
    );
    """)

    conn.commit()

    # If there are no stations — create sample stations 1..10
    cur.execute("SELECT COUNT(*) FROM stations;")
    cnt = cur.fetchone()[0]

    if cnt == 0:
        logger.info("Creating test stations (1–18)")

        # Sample stations data specially for my university
        stations_data = [
            (1, "Station 1", "329"),
            (2, "Station 2", "above room 101"),
            (3, "Station 3", "near the tennis tables"),
            (4, "Station 4", "253"),
            (5, "Station 5", "above the cafeteria"),
            (6, "Station 6", "hall E"),
            (7, "Station 7", "210D"),
            (8, "Station 8", "235"),
            (9, "Station 9", "hall E"),
            (10, "Station 10", "217"),
            (11, "Station 11", "hall E"),
            (12, "Station 12", "212D"),
            (13, "Station 13", "bank (2nd floor)"),
            (14, "Station 14", "2nd floor above the entrance (windows facing math-mech)"),
            (15, "Station 15", "248"),
            (16, "Station 16", "240"),
            (17, "Station 17", "outside"),
            (18, "Station 18", "outside"),
        ]

        for number, name, location in stations_data:
            cur.execute(
                """
                INSERT INTO stations (number, name, location, is_free)
                VALUES (%s, %s, %s, TRUE)
                ON CONFLICT DO NOTHING;
                """,
                (number, name, location)
            )
        conn.commit()

    # Initialize default settings if not present
    def set_default(key, val):
        cur.execute("INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING;", (key, val))

    set_default("org_registration_open", "false")
    set_default("quest_started", "false")
    set_default("quest_ended", "false")
    conn.commit()

    cur.close()
    conn.close()

# --- Settings ---
def set_setting(key: str, value: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = %s;", (key, value, value))
    conn.commit()
    cur.close()
    conn.close()

def get_setting(key: str) -> str | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=%s;", (key,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["value"] if row else None

# --- User / group helpers ---
def get_user_by_tg(tg_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE tg_id=%s;", (tg_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def get_user_role(tg_id):
    u = get_user_by_tg(tg_id)
    return u["role"] if u else None

def get_group_by_number(group_number):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM groups WHERE group_number=%s;", (group_number,))
    g = cur.fetchone()
    cur.close()
    conn.close()
    return g

def register_curator(tg_id: int, group_number: str):
    conn = get_connection()
    cur = conn.cursor()

    # Find or create group
    cur.execute("SELECT id FROM groups WHERE group_number=%s;", (group_number,))
    row = cur.fetchone()
    if row:
        group_id = row["id"]
    else:
        cur.execute("INSERT INTO groups (group_number) VALUES (%s) RETURNING id;", (group_number,))
        group_id = cur.fetchone()["id"]

    # Check if curator already registered for this group
    cur.execute("SELECT id FROM users WHERE role='curator' AND group_id=%s;", (group_id,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return {"ok": False, "error": "A curator is already registered for this group."}

    # Register user
    cur.execute("""
        INSERT INTO users (tg_id, role, group_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (tg_id) DO UPDATE SET role=EXCLUDED.role, group_id=EXCLUDED.group_id
        RETURNING id;
    """, (tg_id, "curator", group_id))
    uid = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True, "group_id": group_id, "user_id": uid}

def register_organizer(tg_id: int, station_number: int):
    # Check if registration is open
    if get_setting("org_registration_open") != "true":
        return {"ok": False, "error": "Organizer registration is closed."}

    conn = get_connection()
    cur = conn.cursor()

    # Find station
    cur.execute("SELECT id FROM stations WHERE number=%s;", (station_number,))
    st = cur.fetchone()
    if not st:
        cur.close()
        conn.close()
        return {"ok": False, "error": "Station with this number not found."}
    station_id = st["id"]

    # Check if organizer already registered for this station
    cur.execute("SELECT id FROM users WHERE role='organizer' AND station_id=%s;", (station_id,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return {"ok": False, "error": "An organizer is already registered for this station."}

    # Create or update organizer user
    cur.execute("""
        INSERT INTO users (tg_id, role, station_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (tg_id) DO UPDATE SET role=EXCLUDED.role, station_id=EXCLUDED.station_id
        RETURNING id;
    """, (tg_id, "organizer", station_id))
    uid = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True, "user_id": uid, "station_id": station_id}

# --- Stations ---

def get_free_stations_with_location():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT number, location FROM stations WHERE is_free=TRUE ORDER BY number;")
    rows = [(row["number"], row["location"]) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return rows

def get_station_by_number(number):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM stations WHERE number=%s;", (number,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def take_station(group_tg_id: int, station_number: int):
    """Curator takes a station: set is_free=False, current_group=group.id."""
    conn = get_connection()
    cur = conn.cursor()

    # Checks
    cur.execute("SELECT id, group_id FROM users WHERE tg_id=%s AND role='curator';", (group_tg_id,))
    u = cur.fetchone()
    if not u:
        cur.close()
        conn.close()
        return {"ok": False, "error": "You are not registered as a curator."}
    group_id = u["group_id"]

    # Check quest status
    if get_setting("quest_started") != "true":
        cur.close()
        conn.close()
        return {"ok": False, "error": "The quest has not started yet."}
    if get_setting("quest_ended") == "true":
        cur.close()
        conn.close()
        return {"ok": False, "error": "The quest is finished — stations cannot be taken."}

    cur.execute("SELECT id, is_free FROM stations WHERE number=%s;", (station_number,))
    st = cur.fetchone()
    if not st:
        cur.close()
        conn.close()
        return {"ok": False, "error": "Station not found."}
    if not st["is_free"]:
        cur.close()
        conn.close()
        return {"ok": False, "error": "Station is already occupied."}

    # Take the station
    cur.execute("UPDATE stations SET is_free=FALSE, current_group=%s WHERE id=%s;", (group_id, st["id"]))

    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True, "station_id": st["id"]}

def release_station_by_number(station_number: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE stations SET is_free=TRUE, current_group=NULL WHERE number=%s;", (station_number,))
    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True}

# --- Rewards / scoring ---
def reward_current_group_by_organizer(org_tg_id: int, points: float, bonus: float = 0.0):
    conn = get_connection()
    cur = conn.cursor()

    # Find organizer and their station
    cur.execute("SELECT station_id FROM users WHERE tg_id=%s AND role='organizer';", (org_tg_id,))
    u = cur.fetchone()
    if not u:
        cur.close()
        conn.close()
        return {"ok": False, "error": "You are not registered as an organizer."}
    station_id = u["station_id"]
    if station_id is None:
        cur.close()
        conn.close()
        return {"ok": False, "error": "You do not have a station assigned."}

    # Find group at this station
    cur.execute("SELECT current_group FROM stations WHERE id=%s;", (station_id,))
    st = cur.fetchone()
    if not st or not st["current_group"]:
        cur.close()
        conn.close()
        return {"ok": False, "error": "There is no group at your station at the moment."}
    group_id = st["current_group"]

    # Add record to rewards
    cur.execute("INSERT INTO rewards (group_id, station_id, points, bonus) VALUES (%s, %s, %s, %s);",
                (group_id, station_id, decimal.Decimal(points), decimal.Decimal(bonus)))
    # Update group score
    cur.execute("UPDATE groups SET score = score + %s + %s WHERE id=%s;", (decimal.Decimal(points), decimal.Decimal(bonus), group_id))

    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True, "group_id": group_id}

def manual_pay_group(group_number: str, points: float):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM groups WHERE group_number=%s;", (group_number,))
    g = cur.fetchone()
    if not g:
        cur.close()
        conn.close()
        return {"ok": False, "error": "Group not found."}
    group_id = g["id"]
    cur.execute("INSERT INTO rewards (group_id, station_id, points, bonus) VALUES (%s, NULL, %s, %s);",
                (group_id, decimal.Decimal(points), decimal.Decimal(0)))
    cur.execute("UPDATE groups SET score = score + %s WHERE id=%s;", (decimal.Decimal(points), group_id))
    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True, "group_id": group_id}

# --- Queries / stats / history ---
def get_group_score_and_history_by_tg(tg_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT group_id FROM users WHERE tg_id=%s AND role='curator';", (tg_id,))
    u = cur.fetchone()
    if not u:
        cur.close()
        conn.close()
        return None
    group_id = u["group_id"]
    cur.execute("SELECT group_number, score FROM groups WHERE id=%s;", (group_id,))
    g = cur.fetchone()
    cur.execute("""
        SELECT r.points, r.bonus, s.number as station_number, r.timestamp
        FROM rewards r
        LEFT JOIN stations s ON r.station_id = s.id
        WHERE r.group_id = %s
        ORDER BY r.timestamp DESC;
    """, (group_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"group": g, "history": rows}

def get_all_groups_stats():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT group_number, score FROM groups ORDER BY score DESC NULLS LAST;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_all_registered_user_tgids():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT tg_id FROM users;")
    rows = [r["tg_id"] for r in cur.fetchall() if r["tg_id"]]
    cur.close()
    conn.close()
    return rows

def get_curator_tg_by_group_id(group_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT tg_id FROM users WHERE role='curator' AND group_id=%s;", (group_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["tg_id"] if row else None

def get_organizer_station_by_tg(tg_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT station_id FROM users WHERE tg_id=%s AND role='organizer';", (tg_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return None
    station_id = row["station_id"]
    cur.execute("SELECT * FROM stations WHERE id=%s;", (station_id,))
    st = cur.fetchone()
    cur.close()
    conn.close()
    return st
