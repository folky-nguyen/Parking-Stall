#!/usr/bin/env python3
import json
import os
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "pc_catalog.db"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "4173"))


def init_db() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pcs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                cpu TEXT NOT NULL,
                ram INTEGER NOT NULL,
                storage INTEGER NOT NULL,
                purpose TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/pcs":
            return self.handle_get_pcs()

        return self.serve_static(path)

    def do_POST(self):
        if self.path != "/api/pcs":
            return self.send_json({"message": "Not found"}, 404)

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            data = json.loads(body.decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            return self.send_json({"message": "Dữ liệu không hợp lệ."}, 400)

        name = str(data.get("name", "")).strip()
        cpu = str(data.get("cpu", "")).strip()
        purpose = str(data.get("purpose", "")).strip()
        note = str(data.get("note", "")).strip()
        item_id = str(data.get("id", "")).strip()

        ram = parse_positive_int(data.get("ram"))
        storage = parse_positive_int(data.get("storage"))

        if not item_id or not name or not cpu or not purpose:
            return self.send_json({"message": "Thiếu thông tin bắt buộc."}, 400)

        if not ram or not storage:
            return self.send_json({"message": "RAM và Ổ cứng phải là số nguyên dương."}, 400)

        created_at = datetime.utcnow().isoformat()

        try:
            with db_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO pcs (id, name, cpu, ram, storage, purpose, note, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (item_id, name, cpu, ram, storage, purpose, note, created_at),
                )
                conn.commit()
        except sqlite3.IntegrityError:
            return self.send_json({"message": "ID đã tồn tại, vui lòng thử lại."}, 409)

        return self.send_json(
            {
                "id": item_id,
                "name": name,
                "cpu": cpu,
                "ram": ram,
                "storage": storage,
                "purpose": purpose,
                "note": note,
                "createdAt": created_at,
            },
            201,
        )

    def do_DELETE(self):
        parsed = urlparse(self.path)
        parts = parsed.path.split("/")
        if len(parts) != 4 or parts[1] != "api" or parts[2] != "pcs":
            return self.send_json({"message": "Not found"}, 404)

        item_id = unquote(parts[3]).strip()
        if not item_id:
            return self.send_json({"message": "ID không hợp lệ."}, 400)

        with db_connection() as conn:
            cursor = conn.execute("DELETE FROM pcs WHERE id = ?", (item_id,))
            conn.commit()

        if cursor.rowcount == 0:
            return self.send_json({"message": "Không tìm thấy bản ghi."}, 404)

        return self.send_json({"message": "Đã xóa."}, 200)

    def handle_get_pcs(self):
        with db_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, name, cpu, ram, storage, purpose, note, created_at
                FROM pcs
                ORDER BY datetime(created_at) DESC
                """
            ).fetchall()

        payload = [
            {
                "id": row["id"],
                "name": row["name"],
                "cpu": row["cpu"],
                "ram": row["ram"],
                "storage": row["storage"],
                "purpose": row["purpose"],
                "note": row["note"] or "",
                "createdAt": row["created_at"],
            }
            for row in rows
        ]

        return self.send_json(payload, 200)

    def serve_static(self, path: str):
        if path == "/":
            path = "/index.html"

        safe_path = (ROOT_DIR / path.lstrip("/")).resolve()
        if ROOT_DIR not in safe_path.parents and safe_path != ROOT_DIR:
            return self.send_error(403)

        if not safe_path.exists() or not safe_path.is_file():
            return self.send_error(404)

        content_type = self.guess_type(safe_path.suffix)
        data = safe_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    @staticmethod
    def guess_type(suffix: str) -> str:
        return {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".json": "application/json; charset=utf-8",
        }.get(suffix.lower(), "application/octet-stream")

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        super().log_message(format, *args)


def parse_positive_int(value):
    text = str(value or "").strip()
    if not text.isdigit():
        return 0

    num = int(text)
    return num if num > 0 else 0


if __name__ == "__main__":
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"Server running at http://{HOST}:{PORT}")
    server.serve_forever()
