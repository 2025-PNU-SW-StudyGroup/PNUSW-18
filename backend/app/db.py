from contextlib import contextmanager
from pathlib import Path
import sqlite3, json, datetime as dt

DB_PATH = Path(__file__).parent / "chat.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        cur.executescript("""\
            DROP TABLE IF EXISTS products;
            DROP TABLE IF EXISTS messages;
            DROP TABLE IF EXISTS chats;""")

        # ── 1. 핵심 설정 ─────────────────────────────────────────
        cur.execute("PRAGMA foreign_keys = ON;")  # FK 무결성 보장
        cur.execute("PRAGMA recursive_triggers = ON;")  # 트리거 재귀 실행 허용

        # ── 2. 테이블 생성 ──────────────────────────────────────
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id     TEXT      PRIMARY KEY,
                title       TEXT,
                created_at  TIMESTAMP DEFAULT (datetime('now','localtime')),
                updated_at  TIMESTAMP DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER   PRIMARY KEY AUTOINCREMENT,
                chat_id     TEXT      REFERENCES chats(chat_id) ON DELETE CASCADE,
                role        TEXT,          -- 'user' | 'assistant'
                content     TEXT,          -- JSON 직렬화
                created_at  TIMESTAMP DEFAULT (datetime('now','localtime')),
                updated_at  TIMESTAMP DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS products (
                id          INTEGER   PRIMARY KEY AUTOINCREMENT,
                chat_id     TEXT      REFERENCES chats(chat_id) ON DELETE CASCADE,
                product     TEXT,          -- JSON 직렬
                created_at  TIMESTAMP DEFAULT (datetime('now','localtime')),
                updated_at  TIMESTAMP DEFAULT (datetime('now','localtime'))
            );
            """)

        # ── 3. updated_at 자동 갱신 트리거 ───────────────────────
        cur.executescript("""
            /* 각 테이블에 AFTER UPDATE 트리거 생성
               - 데이터를 수정할 때만 fired
               - 수정 자체가 updated_at만 바꾸는 2차 UPDATE를 또 만들지만
                 PRAGMA recursive_triggers = ON 이므로 한 번만 실행되고 끝남  */
            CREATE TRIGGER IF NOT EXISTS tr_chats_set_updated_at
            AFTER UPDATE ON chats
            FOR EACH ROW
            WHEN NEW.updated_at = OLD.updated_at
            BEGIN
                UPDATE chats
                   SET updated_at = datetime('now','localtime')
                 WHERE chat_id = NEW.chat_id;
            END;

            CREATE TRIGGER IF NOT EXISTS tr_messages_set_updated_at
            AFTER UPDATE ON messages
            FOR EACH ROW
            WHEN NEW.updated_at = OLD.updated_at
            BEGIN
                UPDATE messages
                   SET updated_at = datetime('now','localtime')
                 WHERE id = NEW.id;
            END;

            CREATE TRIGGER IF NOT EXISTS tr_products_set_updated_at
            AFTER UPDATE ON products
            FOR EACH ROW
            WHEN NEW.updated_at = OLD.updated_at
            BEGIN
                UPDATE products
                   SET updated_at = datetime('now','localtime')
                 WHERE id = NEW.id;
            END;
            """)

        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()
