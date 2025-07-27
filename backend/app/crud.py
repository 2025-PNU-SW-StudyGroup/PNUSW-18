from typing import List
import json, uuid
from app.db import get_conn


def update_chat_title(chat_id: str, title: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE chats SET title = ? WHERE chat_id = ?", (title, chat_id))


def upsert_chat(chat_id: str | None, title: str | None) -> str:
    cid = chat_id or str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO chats(chat_id, title) VALUES(?,?)",
                     (cid, title))
    return cid


def save_msg(chat_id: str, role: str, content_obj) -> None:
    with get_conn() as conn:
        conn.execute("INSERT INTO messages(chat_id, role, content) VALUES(?,?,?)",
                     (chat_id, role, json.dumps(content_obj, ensure_ascii=False)))


def list_chats(offset: int, size: int):
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT chat_id, title, created_at, updated_at "
            "FROM chats ORDER BY updated_at DESC LIMIT ? OFFSET ?", (size, offset))
        return [dict(r) for r in cur.fetchall()]


def save_products(chat_id: str, products_json: List[dict]) -> None:
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO products(chat_id, product) VALUES(?,?)",
            [(chat_id, json.dumps(p, ensure_ascii=False)) for p in products_json])


def get_history(chat_id: str, offset: int, size: int):
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT role, content FROM messages "
            "WHERE chat_id = ? ORDER BY updated_at ASC LIMIT ? OFFSET ?",
            (chat_id, size, offset))
        return [dict(r) for r in cur.fetchall()]
