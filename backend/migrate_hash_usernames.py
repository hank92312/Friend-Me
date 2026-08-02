"""一次性遷移：users.name（明文暱稱）→ users.name_hash（不可逆雜湊）。

背景見 player_identity.py。此腳本可重複執行（已遷移過會直接跳出）。

用法（在部署好新版程式、且 PLAYER_NAME_PEPPER 已設定的機器上執行）：
    python migrate_hash_usernames.py

注意：雜湊值取決於 pepper。務必在 pepper 設定完成後才執行，
之後也不可再更換 pepper，否則既有統計會全部對不上。

實作採「重建表」而非 ALTER TABLE ... DROP COLUMN：
SQLite 拒絕刪除 UNIQUE 欄位（`cannot drop UNIQUE column`），而 users.name
正是 unique=True。重建表順帶保證明文欄位完全消失，不留殘影。
"""

import os
import sqlite3
import sys

from player_identity import player_key

DB_PATH = os.getenv("DB_PATH", "./friends_and_me.db")

STATS = ("total_guesses", "correct_guesses", "total_disclosures", "recognized_disclosures")


def main():
    conn = sqlite3.connect(DB_PATH)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(users)")]

    if "name_hash" in cols and "name" not in cols:
        print("[Migrate] 已經是雜湊格式，無需處理。")
        return

    if "name" not in cols:
        print(f"[Migrate] 錯誤：users 表既無 name 也無 name_hash 欄位，實際欄位：{cols}")
        sys.exit(1)

    rows = conn.execute(f"SELECT id, name, {', '.join(STATS)} FROM users").fetchall()
    print(f"[Migrate] 開始遷移 {len(rows)} 筆玩家資料…")

    # 雜湊碰撞檢查：先確認一對一，再動任何資料
    names = {r[1] for r in rows}
    hashes = {player_key(r[1]) for r in rows}
    if len(names) != len(hashes):
        print(f"[Migrate] 中止：雜湊碰撞（{len(names)} 個暱稱 → {len(hashes)} 個雜湊），未做任何變更。")
        sys.exit(1)

    # 重建表：新表只有雜湊欄位，明文自始至終沒被寫進去
    conn.execute("DROP TABLE IF EXISTS users_migrating")
    conn.execute(
        "CREATE TABLE users_migrating ("
        " id INTEGER NOT NULL PRIMARY KEY,"
        " name_hash VARCHAR,"
        + "".join(f" {c} INTEGER," for c in STATS).rstrip(",")
        + ")"
    )
    conn.executemany(
        f"INSERT INTO users_migrating (id, name_hash, {', '.join(STATS)})"
        f" VALUES (?, ?, {', '.join('?' * len(STATS))})",
        [(r[0], player_key(r[1]), *r[2:]) for r in rows],
    )
    conn.execute("DROP TABLE users")
    conn.execute("ALTER TABLE users_migrating RENAME TO users")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_name_hash ON users (name_hash)")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_users_id ON users (id)")
    conn.commit()

    # VACUUM：把舊表殘留的明文從釋放頁面中真正抹掉，而非只標記為可用
    conn.execute("VACUUM")

    cols_after = [r[1] for r in conn.execute("PRAGMA table_info(users)")]
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    print(f"[Migrate] 完成。{count} 筆已雜湊化，欄位：{cols_after}")


if __name__ == "__main__":
    main()
