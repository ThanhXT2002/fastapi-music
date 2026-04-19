"""Script migrate data tu SQLite sang MySQL.

Buoc:
1. Tao database musicdb (neu chua co).
2. Tao tables theo SQLAlchemy models.
3. Copy toan bo data tu SQLite sang MySQL.
"""

import sqlite3
import pymysql
from urllib.parse import quote_plus

# -- Config --
SQLITE_PATH = "./fastapi_music.db"
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASS = "Thanh2002@"
MYSQL_DB = "musicdb"

# -- Step 1: Tao database MySQL --
print("=" * 60)
print("[1/4] Tao database MySQL...")
conn_mysql = pymysql.connect(
    host=MYSQL_HOST, port=MYSQL_PORT,
    user=MYSQL_USER, password=MYSQL_PASS,
    charset="utf8mb4",
)
cursor_mysql = conn_mysql.cursor()
cursor_mysql.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
conn_mysql.commit()
cursor_mysql.close()
conn_mysql.close()
print(f"   OK - Database '{MYSQL_DB}' san sang.")

# -- Step 2: Tao tables bang SQLAlchemy --
print("\n[2/4] Tao tables trong MySQL...")

# Build URL with proper password escaping
escaped_pass = quote_plus(MYSQL_PASS)
mysql_url = f"mysql+pymysql://{MYSQL_USER}:{escaped_pass}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"

from sqlalchemy import create_engine, text
mysql_engine = create_engine(mysql_url, pool_pre_ping=True, echo=False)

# Import tat ca models de register voi Base.metadata
from app.config.database import Base
from app.models.song import Song
from app.models.user import User
from app.models.user_songs import user_songs

Base.metadata.create_all(bind=mysql_engine)
print("   OK - Tat ca tables da duoc tao.")

# Verify tables
with mysql_engine.connect() as conn:
    result = conn.execute(text("SHOW TABLES"))
    tables = [row[0] for row in result]
    print(f"   Tables: {tables}")

# -- Step 3: Doc data tu SQLite --
print(f"\n[3/4] Doc data tu SQLite ({SQLITE_PATH})...")
conn_sqlite = sqlite3.connect(SQLITE_PATH)
conn_sqlite.row_factory = sqlite3.Row

cursor = conn_sqlite.cursor()

# Doc songs
cursor.execute("SELECT * FROM songs")
songs = [dict(row) for row in cursor.fetchall()]
print(f"   Songs: {len(songs)} ban ghi")

# Doc users
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
has_users = cursor.fetchone() is not None
users = []
if has_users:
    cursor.execute("SELECT * FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    print(f"   Users: {len(users)} ban ghi")

# Doc user_songs
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_songs'")
has_user_songs = cursor.fetchone() is not None
user_songs_data = []
if has_user_songs:
    cursor.execute("SELECT * FROM user_songs")
    user_songs_data = [dict(row) for row in cursor.fetchall()]
    print(f"   User-Songs: {len(user_songs_data)} ban ghi")

conn_sqlite.close()

# -- Step 4: Insert data vao MySQL --
print("\n[4/4] Migrate data sang MySQL...")
conn_mysql = pymysql.connect(
    host=MYSQL_HOST, port=MYSQL_PORT,
    user=MYSQL_USER, password=MYSQL_PASS,
    database=MYSQL_DB, charset="utf8mb4",
    autocommit=False,
)
cur = conn_mysql.cursor()

# Insert songs
if songs:
    cols = list(songs[0].keys())
    placeholders = ", ".join(["%s"] * len(cols))
    col_names = ", ".join([f"`{c}`" for c in cols])
    insert_sql = f"INSERT IGNORE INTO `songs` ({col_names}) VALUES ({placeholders})"

    count = 0
    for song in songs:
        values = tuple(song[c] for c in cols)
        try:
            cur.execute(insert_sql, values)
            count += 1
        except Exception as e:
            print(f"   WARN - Skip song {song.get('id', '?')}: {e}")

    conn_mysql.commit()
    print(f"   OK - Songs: {count}/{len(songs)} inserted")

# Insert users
if users:
    cols = list(users[0].keys())
    placeholders = ", ".join(["%s"] * len(cols))
    col_names = ", ".join([f"`{c}`" for c in cols])
    insert_sql = f"INSERT IGNORE INTO `users` ({col_names}) VALUES ({placeholders})"

    count = 0
    for user in users:
        values = tuple(user[c] for c in cols)
        try:
            cur.execute(insert_sql, values)
            count += 1
        except Exception as e:
            print(f"   WARN - Skip user {user.get('id', '?')}: {e}")

    conn_mysql.commit()
    print(f"   OK - Users: {count}/{len(users)} inserted")

# Insert user_songs
if user_songs_data:
    insert_sql = "INSERT IGNORE INTO `user_songs` (`user_id`, `song_id`) VALUES (%s, %s)"
    count = 0
    for us in user_songs_data:
        try:
            cur.execute(insert_sql, (us["user_id"], us["song_id"]))
            count += 1
        except Exception as e:
            print(f"   WARN - Skip user_song: {e}")

    conn_mysql.commit()
    print(f"   OK - User-Songs: {count}/{len(user_songs_data)} inserted")

cur.close()
conn_mysql.close()

# -- Done --
print("\n" + "=" * 60)
print("DONE - Migration hoan thanh!")
print(f"   SQLite: {SQLITE_PATH}")
print(f"   MySQL:  {MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")
print("=" * 60)
