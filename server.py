"""코딩테스트 복습 도구 (1차 버전).

실행:  python3 server.py   →  http://127.0.0.1:8765

- 문제 링크와 제출 코드를 넣으면 AI가 한 장 오답노트를 만들고 복습 일정에 올린다.
- 문제 지문은 노트를 만들 때만 쓰고 저장하지 않는다. 저장하는 것은 링크, 제목,
  내 코드, 내 메모, AI가 만든 노트뿐이다.
- 연습 문제 전용. 실제 시험 중에는 사용하지 않는다.
"""
import json
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data.db"

SITES = {
    "school.programmers.co.kr": "프로그래머스",
    "programmers.co.kr": "프로그래머스",
    "www.acmicpc.net": "백준",
    "acmicpc.net": "백준",
    "leetcode.com": "LeetCode",
    "swexpertacademy.com": "SWEA",
}


def load_config():
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def today():
    override = load_config().get("debug_today")
    return date.fromisoformat(override) if override else date.today()


def db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                site TEXT NOT NULL,
                code TEXT NOT NULL,
                result TEXT NOT NULL,
                memo TEXT NOT NULL,
                note TEXT NOT NULL,
                model TEXT NOT NULL,
                created_on TEXT NOT NULL,
                stage INTEGER NOT NULL DEFAULT 0,
                due_on TEXT,
                review_count INTEGER NOT NULL DEFAULT 0,
                fail_count INTEGER NOT NULL DEFAULT 0
            )"""
        )


def site_of(url):
    host = (urlparse(url).hostname or "").lower()
    return SITES.get(host, host or "기타")


# ---------- 노트 생성 (모델 호출) ----------

def generate_note(title, problem_text, code, result, memo):
    """Claude Code 명령줄(구독)을 통해 노트를 만든다. 모델은 config.json에서 바꾼다."""
    cfg = load_config()
    claude = shutil.which("claude")
    if not claude:
        raise RuntimeError("claude 명령을 찾을 수 없습니다. Claude Code가 설치되어 있는지 확인하세요.")
    system_prompt = (ROOT / "prompt.md").read_text(encoding="utf-8")
    user_prompt = "\n\n".join([
        "## 문제 제목\n" + title,
        "## 문제 설명\n" + (problem_text.strip() or "(학습자가 문제 설명을 붙여 넣지 않았습니다.)"),
        "## 학습자가 제출한 코드\n```\n" + code.strip() + "\n```",
        "## 제출 결과\n" + (result.strip() or "(적지 않음)"),
        "## 학습자 메모\n" + (memo.strip() or "(없음)"),
    ])
    proc = subprocess.run(
        [claude, "-p", "--model", cfg["model"], "--system-prompt", system_prompt,
         "--strict-mcp-config", "--no-session-persistence"],
        input=user_prompt, capture_output=True, text=True,
        timeout=cfg.get("generation_timeout_seconds", 240),
        cwd=tempfile.gettempdir(),
    )
    note = proc.stdout.strip()
    if proc.returncode != 0 or not note:
        raise RuntimeError("노트 생성에 실패했습니다: " + (proc.stderr.strip() or "빈 응답")[:300])
    return note, cfg["model"]


# ---------- 복습 일정 ----------

def next_due(stage):
    """stage번 연속으로 맞힌 문제의 다음 복습일. 간격을 모두 통과하면 졸업(None)."""
    intervals = load_config()["review_intervals_days"]
    if stage >= len(intervals):
        return None
    return (today() + timedelta(days=intervals[stage])).isoformat()


def row_to_dict(row):
    item = dict(row)
    t = today().isoformat()
    item["is_due"] = bool(item["due_on"]) and item["due_on"] <= t
    item["graduated"] = item["due_on"] is None
    return item


# ---------- HTTP ----------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length).decode("utf-8")) if length else {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            body = (ROOT / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/problems":
            with db() as conn:
                rows = conn.execute(
                    "SELECT * FROM problems ORDER BY due_on IS NULL, due_on, id").fetchall()
            cfg = load_config()
            self.send_json({
                "today": today().isoformat(),
                "model": cfg["model"],
                "intervals": cfg["review_intervals_days"],
                "problems": [row_to_dict(r) for r in rows],
            })
        else:
            self.send_json({"error": "없는 주소입니다."}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            data = self.read_json()
            if path == "/api/problems":
                self.create_problem(data)
            elif path == "/api/review":
                self.review(data)
            elif path == "/api/delete":
                with db() as conn:
                    conn.execute("DELETE FROM problems WHERE id = ?", (int(data["id"]),))
                self.send_json({"ok": True})
            else:
                self.send_json({"error": "없는 주소입니다."}, 404)
        except subprocess.TimeoutExpired:
            self.send_json({"error": "노트 생성이 제한 시간을 넘겼습니다. 다시 시도해 주세요."}, 504)
        except Exception as exc:  # 사용자에게 원인을 그대로 보여 준다
            self.send_json({"error": str(exc)}, 500)

    def create_problem(self, data):
        url = (data.get("url") or "").strip()
        title = (data.get("title") or "").strip()
        code = data.get("code") or ""
        if not url.startswith(("http://", "https://")):
            return self.send_json({"error": "문제 링크는 http로 시작해야 합니다."}, 400)
        if not title or not code.strip():
            return self.send_json({"error": "문제 제목과 제출 코드는 꼭 필요합니다."}, 400)
        result = data.get("result") or ""
        memo = data.get("memo") or ""
        # 문제 지문(problem_text)은 노트 생성에만 쓰고 저장하지 않는다.
        note, model = generate_note(title, data.get("problem_text") or "", code, result, memo)
        with db() as conn:
            cur = conn.execute(
                """INSERT INTO problems (url, title, site, code, result, memo, note, model,
                                         created_on, stage, due_on)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""",
                (url, title, site_of(url), code, result, memo, note, model,
                 today().isoformat(), next_due(0)),
            )
            row = conn.execute("SELECT * FROM problems WHERE id = ?", (cur.lastrowid,)).fetchone()
        self.send_json(row_to_dict(row), 201)

    def review(self, data):
        outcome = data.get("outcome")
        if outcome not in ("solved", "failed"):
            return self.send_json({"error": "outcome은 solved 또는 failed여야 합니다."}, 400)
        with db() as conn:
            row = conn.execute("SELECT * FROM problems WHERE id = ?", (int(data["id"]),)).fetchone()
            if not row:
                return self.send_json({"error": "없는 문제입니다."}, 404)
            # 맞히면 다음 간격으로, 틀리면 처음 간격으로 돌아간다.
            stage = row["stage"] + 1 if outcome == "solved" else 0
            conn.execute(
                """UPDATE problems SET stage = ?, due_on = ?, review_count = review_count + 1,
                          fail_count = fail_count + ? WHERE id = ?""",
                (stage, next_due(stage), 0 if outcome == "solved" else 1, row["id"]),
            )
            row = conn.execute("SELECT * FROM problems WHERE id = ?", (row["id"],)).fetchone()
        self.send_json(row_to_dict(row))


if __name__ == "__main__":
    init_db()
    port = load_config().get("port", 8765)
    print("복습 도구 실행 중: http://127.0.0.1:%d" % port)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
