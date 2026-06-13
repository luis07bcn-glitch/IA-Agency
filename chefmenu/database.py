import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "chefmenu.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS platos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        ingrediente TEXT NOT NULL,
        cantidad TEXT,
        unidad TEXT,
        caducidad TEXT,
        nota TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS menus_guardados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        fecha TEXT,
        precio_menu REAL,
        contenido TEXT,  -- JSON
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Platos de ejemplo para arrancar
    c.execute("SELECT COUNT(*) FROM platos")
    if c.fetchone()[0] == 0:
        platos_demo = [
            ("Ensalada mixta", "primero", "ninguna", 1.20, 10, '["ninguno"]', '["vegano","sin_gluten","sin_lactosa"]', "Lechuga, tomate, cebolla, aceituna"),
            ("Crema de verduras", "primero", "vegetal", 1.50, 20, '["ninguno"]', '["vegano","sin_gluten","vegetariano"]', "Calabaza, zanahoria, puerro"),
            ("Macarrones boloñesa", "primero", "ternera", 1.80, 25, '["gluten"]', '[]', "Pasta con salsa de carne"),
            ("Gazpacho", "primero", "ninguna", 1.10, 15, '["ninguno"]', '["vegano","sin_gluten","vegetariano"]', "Tomate, pepino, pimiento"),
            ("Lentejas estofadas", "primero", "cerdo", 1.60, 40, '["ninguno"]', '[]', "Lentejas con chorizo y morcilla"),
            ("Pollo al ajillo", "segundo", "pollo", 2.80, 30, '["ninguno"]', '["sin_gluten"]', "Pollo con ajo y vino blanco"),
            ("Merluza a la plancha", "segundo", "pescado", 3.50, 15, '["pescado"]', '["sin_gluten","sin_lactosa"]', "Merluza con limón"),
            ("Lomo de cerdo con patatas", "segundo", "cerdo", 2.60, 35, '["ninguno"]', '["sin_gluten"]', "Lomo a la plancha con patatas asadas"),
            ("Arroz con verduras", "segundo", "vegetal", 1.90, 25, '["ninguno"]', '["vegano","sin_gluten","vegetariano"]', "Arroz salteado con pisto"),
            ("Ternera guisada", "segundo", "ternera", 3.80, 60, '["ninguno"]', '["sin_gluten"]', "Ternera estofada con patatas"),
            ("Tortilla de patatas", "segundo", "huevo", 1.40, 20, '["huevo"]', '["vegetariano","sin_gluten"]', "Tortilla española"),
            ("Flan casero", "postre", "ninguna", 0.60, 5, '["huevo","lactosa"]', '["vegetariano"]', "Flan con caramelo"),
            ("Fruta del tiempo", "postre", "ninguna", 0.50, 2, '["ninguno"]', '["vegano","sin_gluten","vegetariano","sin_lactosa"]', "Fruta de temporada"),
            ("Yogur natural", "postre", "ninguna", 0.45, 1, '["lactosa"]', '["vegetariano","sin_gluten"]', "Yogur con miel"),
        ]
        c.executemany(
            "INSERT INTO platos (nombre, categoria, proteina, coste_racion, tiempo_prep, alergenos, dietas, descripcion) VALUES (?,?,?,?,?,?,?,?)",
            platos_demo
        )

    # Migración: añadir subtipo si la BD ya existía sin él
    try:
        c.execute("ALTER TABLE platos ADD COLUMN subtipo TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass

    conn.commit()
    conn.close()


def get_platos(categoria=None, solo_activos=True):
    conn = get_conn()
    query = "SELECT * FROM platos WHERE 1=1"
    params = []
    if solo_activos:
        query += " AND activo=1"
    if categoria:
        query += " AND categoria=?"
        params.append(categoria)
    query += " ORDER BY nombre"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_plato(nombre, categoria, proteina, coste_racion, tiempo_prep, alergenos, dietas, descripcion, subtipo=""):
    import json
    conn = get_conn()
    conn.execute(
        "INSERT INTO platos (nombre, categoria, subtipo, proteina, coste_racion, tiempo_prep, alergenos, dietas, descripcion) VALUES (?,?,?,?,?,?,?,?,?)",
        (nombre, categoria, subtipo, proteina, coste_racion, tiempo_prep, json.dumps(alergenos), json.dumps(dietas), descripcion)
    )
    conn.commit()
    conn.close()


def bulk_add_platos(platos: list[dict]):
    """Inserta múltiples platos extraídos de un documento importado."""
    import json
    conn = get_conn()
    for p in platos:
        conn.execute(
            "INSERT INTO platos (nombre, categoria, subtipo, proteina, coste_racion, tiempo_prep, alergenos, dietas, descripcion) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                p.get("nombre", "Sin nombre"),
                p.get("categoria", "primero"),
                p.get("subtipo", ""),
                p.get("proteina", "ninguna"),
                float(p.get("coste_racion", 0.0)),
                int(p.get("tiempo_prep", 20)),
                json.dumps(p.get("alergenos", ["ninguno"])),
                json.dumps(p.get("dietas", [])),
                p.get("descripcion", ""),
            )
        )
    conn.commit()
    conn.close()


def update_plato(plato_id, **kwargs):
    import json
    conn = get_conn()
    for key, val in kwargs.items():
        if key in ("alergenos", "dietas"):
            val = json.dumps(val)
        conn.execute(f"UPDATE platos SET {key}=? WHERE id=?", (val, plato_id))
    conn.commit()
    conn.close()


def delete_plato(plato_id):
    conn = get_conn()
    conn.execute("UPDATE platos SET activo=0 WHERE id=?", (plato_id,))
    conn.commit()
    conn.close()


def get_despensa():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM despensa ORDER BY caducidad ASC, ingrediente ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_despensa(ingrediente, cantidad, unidad, caducidad, nota):
    conn = get_conn()
    conn.execute(
        "INSERT INTO despensa (ingrediente, cantidad, unidad, caducidad, nota) VALUES (?,?,?,?,?)",
        (ingrediente, cantidad, unidad, caducidad, nota)
    )
    conn.commit()
    conn.close()


def delete_despensa(item_id):
    conn = get_conn()
    conn.execute("DELETE FROM despensa WHERE id=?", (item_id,))
    conn.commit()
    conn.close()


def save_menu(nombre, fecha, precio_menu, contenido):
    import json
    conn = get_conn()
    conn.execute(
        "INSERT INTO menus_guardados (nombre, fecha, precio_menu, contenido) VALUES (?,?,?,?)",
        (nombre, fecha, precio_menu, json.dumps(contenido))
    )
    conn.commit()
    conn.close()


def get_menus_guardados():
    import json
    conn = get_conn()
    rows = conn.execute("SELECT * FROM menus_guardados ORDER BY created_at DESC").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["contenido"] = json.loads(d["contenido"])
        result.append(d)
    return result
