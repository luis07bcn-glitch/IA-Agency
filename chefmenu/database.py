import sqlite3
import hashlib
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "chefmenu.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Contraseñas ──────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt.hex() + ":" + key.hex()


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, key_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
        return key.hex() == key_hex
    except Exception:
        return False


# ── Init ─────────────────────────────────────────────────────────────────────

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        nombre_restaurante TEXT DEFAULT 'Mi Restaurante',
        plan TEXT DEFAULT 'basico',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS platos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        nombre TEXT NOT NULL,
        categoria TEXT NOT NULL,
        subtipo TEXT DEFAULT '',
        proteina TEXT,
        coste_racion REAL NOT NULL,
        tiempo_prep INTEGER,
        alergenos TEXT DEFAULT '[]',
        dietas TEXT DEFAULT '[]',
        descripcion TEXT,
        activo INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS despensa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        ingrediente TEXT NOT NULL,
        cantidad TEXT,
        unidad TEXT,
        caducidad TEXT,
        nota TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS menus_guardados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        nombre TEXT,
        fecha TEXT,
        precio_menu REAL,
        contenido TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Migraciones para BDs existentes sin user_id
    for sql in [
        "ALTER TABLE platos ADD COLUMN user_id INTEGER DEFAULT 1",
        "ALTER TABLE despensa ADD COLUMN user_id INTEGER DEFAULT 1",
        "ALTER TABLE menus_guardados ADD COLUMN user_id INTEGER DEFAULT 1",
    ]:
        try:
            c.execute(sql)
            conn.commit()
        except Exception:
            pass

    conn.commit()
    conn.close()


# ── Platos demo ──────────────────────────────────────────────────────────────

PLATOS_DEMO = [
    ("Ensalada mixta", "primero", "ensalada", "ninguna", 1.20, 10,
     '["ninguno"]', '["vegano","sin_gluten","sin_lactosa"]', "Lechuga, tomate, cebolla, aceituna"),
    ("Crema de verduras", "primero", "crema", "vegetal", 1.50, 20,
     '["ninguno"]', '["vegano","sin_gluten","vegetariano"]', "Calabaza, zanahoria, puerro"),
    ("Macarrones boloñesa", "primero", "pasta", "ternera", 1.80, 25,
     '["gluten"]', '[]', "Pasta con salsa de carne"),
    ("Gazpacho", "primero", "sopa", "ninguna", 1.10, 15,
     '["ninguno"]', '["vegano","sin_gluten","vegetariano"]', "Tomate, pepino, pimiento"),
    ("Lentejas estofadas", "primero", "legumbres", "cerdo", 1.60, 40,
     '["ninguno"]', '[]', "Lentejas con chorizo y morcilla"),
    ("Pollo al ajillo", "segundo", "plancha", "pollo", 2.80, 30,
     '["ninguno"]', '["sin_gluten"]', "Pollo con ajo y vino blanco"),
    ("Merluza a la plancha", "segundo", "plancha", "pescado", 3.50, 15,
     '["pescado"]', '["sin_gluten","sin_lactosa"]', "Merluza con limon"),
    ("Lomo de cerdo con patatas", "segundo", "plancha", "cerdo", 2.60, 35,
     '["ninguno"]', '["sin_gluten"]', "Lomo a la plancha con patatas asadas"),
    ("Arroz con verduras", "segundo", "arroz", "vegetal", 1.90, 25,
     '["ninguno"]', '["vegano","sin_gluten","vegetariano"]', "Arroz salteado con pisto"),
    ("Ternera guisada", "segundo", "guiso", "ternera", 3.80, 60,
     '["ninguno"]', '["sin_gluten"]', "Ternera estofada con patatas"),
    ("Tortilla de patatas", "segundo", "otro", "huevo", 1.40, 20,
     '["huevo"]', '["vegetariano","sin_gluten"]', "Tortilla española"),
    ("Flan casero", "postre", "postre_frio", "ninguna", 0.60, 5,
     '["huevo","lactosa"]', '["vegetariano"]', "Flan con caramelo"),
    ("Fruta del tiempo", "postre", "fruta", "ninguna", 0.50, 2,
     '["ninguno"]', '["vegano","sin_gluten","vegetariano","sin_lactosa"]', "Fruta de temporada"),
    ("Yogur natural", "postre", "lacteo", "ninguna", 0.45, 1,
     '["lactosa"]', '["vegetariano","sin_gluten"]', "Yogur con miel"),
]


def seed_demo_platos(user_id: int):
    """Inserta platos de ejemplo para un usuario nuevo."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM platos WHERE user_id=?", (user_id,))
    if c.fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO platos (user_id, nombre, categoria, subtipo, proteina, coste_racion, "
            "tiempo_prep, alergenos, dietas, descripcion) VALUES (?,?,?,?,?,?,?,?,?,?)",
            [(user_id,) + p for p in PLATOS_DEMO],
        )
        conn.commit()
    conn.close()


# ── Auth ─────────────────────────────────────────────────────────────────────

def register_user(email: str, password: str, nombre_restaurante: str) -> dict | None:
    """Registra un usuario nuevo. Devuelve el usuario creado o None si el email ya existe."""
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash, nombre_restaurante) VALUES (?,?,?)",
            (email.strip().lower(), _hash_password(password), nombre_restaurante.strip()),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE email=?",
                           (email.strip().lower(),)).fetchone()
        user = dict(row)
        conn.close()
        seed_demo_platos(user["id"])
        return user
    except sqlite3.IntegrityError:
        conn.close()
        return None


def authenticate_user(email: str, password: str) -> dict | None:
    """Devuelve el usuario si las credenciales son correctas, None si no."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE email=?",
                       (email.strip().lower(),)).fetchone()
    conn.close()
    if row and _verify_password(password, row["password_hash"]):
        return dict(row)
    return None


def get_user(user_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_nombre_restaurante(user_id: int, nombre: str):
    conn = get_conn()
    conn.execute("UPDATE users SET nombre_restaurante=? WHERE id=?", (nombre, user_id))
    conn.commit()
    conn.close()


# ── Platos ───────────────────────────────────────────────────────────────────

def get_platos(user_id: int, categoria=None, solo_activos=True):
    conn = get_conn()
    query = "SELECT * FROM platos WHERE user_id=?"
    params = [user_id]
    if solo_activos:
        query += " AND activo=1"
    if categoria:
        query += " AND categoria=?"
        params.append(categoria)
    query += " ORDER BY nombre"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_plato(user_id: int, nombre, categoria, proteina, coste_racion,
              tiempo_prep, alergenos, dietas, descripcion, subtipo=""):
    import json
    conn = get_conn()
    conn.execute(
        "INSERT INTO platos (user_id, nombre, categoria, subtipo, proteina, coste_racion, "
        "tiempo_prep, alergenos, dietas, descripcion) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (user_id, nombre, categoria, subtipo, proteina, coste_racion,
         tiempo_prep, json.dumps(alergenos), json.dumps(dietas), descripcion),
    )
    conn.commit()
    conn.close()


def bulk_add_platos(user_id: int, platos: list[dict]):
    import json
    conn = get_conn()
    for p in platos:
        conn.execute(
            "INSERT INTO platos (user_id, nombre, categoria, subtipo, proteina, coste_racion, "
            "tiempo_prep, alergenos, dietas, descripcion) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                user_id,
                p.get("nombre", "Sin nombre"),
                p.get("categoria", "primero"),
                p.get("subtipo", ""),
                p.get("proteina", "ninguna"),
                float(p.get("coste_racion", 0.0)),
                int(p.get("tiempo_prep", 20)),
                json.dumps(p.get("alergenos", ["ninguno"])),
                json.dumps(p.get("dietas", [])),
                p.get("descripcion", ""),
            ),
        )
    conn.commit()
    conn.close()


def update_plato(user_id: int, plato_id, **kwargs):
    import json
    conn = get_conn()
    for key, val in kwargs.items():
        if key in ("alergenos", "dietas"):
            val = json.dumps(val)
        conn.execute(f"UPDATE platos SET {key}=? WHERE id=? AND user_id=?",
                     (val, plato_id, user_id))
    conn.commit()
    conn.close()


def delete_plato(user_id: int, plato_id):
    conn = get_conn()
    conn.execute("UPDATE platos SET activo=0 WHERE id=? AND user_id=?", (plato_id, user_id))
    conn.commit()
    conn.close()


def duplicate_plato(user_id: int, plato_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM platos WHERE id=? AND user_id=?",
                       (plato_id, user_id)).fetchone()
    if row:
        d = dict(row)
        conn.execute(
            "INSERT INTO platos (user_id, nombre, categoria, subtipo, proteina, coste_racion, "
            "tiempo_prep, alergenos, dietas, descripcion) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (user_id, f"{d['nombre']} (copia)", d["categoria"], d.get("subtipo", ""),
             d.get("proteina", "ninguna"), d["coste_racion"], d.get("tiempo_prep", 20),
             d["alergenos"], d["dietas"], d.get("descripcion", "")),
        )
    conn.commit()
    conn.close()


# ── Despensa ─────────────────────────────────────────────────────────────────

def get_despensa(user_id: int):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM despensa WHERE user_id=? ORDER BY caducidad ASC, ingrediente ASC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_despensa(user_id: int, ingrediente, cantidad, unidad, caducidad, nota):
    conn = get_conn()
    conn.execute(
        "INSERT INTO despensa (user_id, ingrediente, cantidad, unidad, caducidad, nota) "
        "VALUES (?,?,?,?,?,?)",
        (user_id, ingrediente, cantidad, unidad, caducidad, nota),
    )
    conn.commit()
    conn.close()


def delete_despensa(user_id: int, item_id):
    conn = get_conn()
    conn.execute("DELETE FROM despensa WHERE id=? AND user_id=?", (item_id, user_id))
    conn.commit()
    conn.close()


# ── Menús guardados ───────────────────────────────────────────────────────────

def save_menu(user_id: int, nombre, fecha, precio_menu, contenido):
    import json
    conn = get_conn()
    conn.execute(
        "INSERT INTO menus_guardados (user_id, nombre, fecha, precio_menu, contenido) "
        "VALUES (?,?,?,?,?)",
        (user_id, nombre, fecha, precio_menu, json.dumps(contenido)),
    )
    conn.commit()
    conn.close()


def get_menus_guardados(user_id: int):
    import json
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM menus_guardados WHERE user_id=? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["contenido"] = json.loads(d["contenido"])
        result.append(d)
    return result
