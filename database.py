import aiosqlite
import json
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data/bot.db")

TITLES: dict[str, int] = {
    "희귀":   10_000,
    "초희귀": 50_000,
    "영웅":  100_000,
    "신화":  150_000,
    "전설":  300_000,
}
TITLE_ORDER = ["희귀", "초희귀", "영웅", "신화", "전설"]
TITLE_EMOJI  = {"희귀": "🔵", "초희귀": "🟣", "영웅": "🔴", "신화": "🟡", "전설": "🌟"}


async def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id    TEXT PRIMARY KEY,
                nickname   TEXT NOT NULL,
                money      INTEGER NOT NULL DEFAULT 0,
                titles     TEXT NOT NULL DEFAULT '[]',
                last_daily TEXT,
                last_boast TEXT
            )
        """)
        await db.commit()


async def ensure_user(user_id: str, nickname: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()

        if row:
            user = dict(row)
            if user["nickname"] != nickname:
                await db.execute(
                    "UPDATE users SET nickname = ? WHERE user_id = ?",
                    (nickname, user_id),
                )
                await db.commit()
                user["nickname"] = nickname
            return user

        await db.execute(
            "INSERT INTO users (user_id, nickname) VALUES (?, ?)",
            (user_id, nickname),
        )
        await db.commit()
        return {
            "user_id": user_id, "nickname": nickname,
            "money": 0, "titles": "[]",
            "last_daily": None, "last_boast": None,
        }


async def update_money(user_id: str, delta: int) -> int:
    """잔액을 delta 만큼 변경하고 새 잔액을 반환."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET money = money + ? WHERE user_id = ?",
            (delta, user_id),
        )
        await db.commit()
        async with db.execute(
            "SELECT money FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0]


async def add_title(user_id: str, title: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT titles FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
        titles: list = json.loads(row["titles"])
        if title not in titles:
            titles.append(title)
            await db.execute(
                "UPDATE users SET titles = ? WHERE user_id = ?",
                (json.dumps(titles, ensure_ascii=False), user_id),
            )
            await db.commit()


async def stamp_daily(user_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET last_daily = ? WHERE user_id = ?",
            (_now_iso(), user_id),
        )
        await db.commit()


async def stamp_boast(user_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET last_boast = ? WHERE user_id = ?",
            (_now_iso(), user_id),
        )
        await db.commit()


def cooldown_ok(last_used: str | None) -> bool:
    if not last_used:
        return True
    elapsed = (_now() - datetime.fromisoformat(last_used)).total_seconds()
    return elapsed >= 86400


def cooldown_remaining(last_used: str | None) -> tuple[int, int]:
    """남은 시간을 (시간, 분) 으로 반환."""
    if not last_used:
        return 0, 0
    remaining = 86400 - (_now() - datetime.fromisoformat(last_used)).total_seconds()
    remaining = max(0, int(remaining))
    return divmod(remaining // 60, 60)


def fmt(amount: int) -> str:
    return f"{amount:,}원"


def josa_eul_reul(word: str) -> str:
    """을/를 반환."""
    return "을" if _has_batchim(word) else "를"


def josa_i_ga(word: str) -> str:
    """이/가 반환."""
    return "이" if _has_batchim(word) else "가"


def _has_batchim(word: str) -> bool:
    if not word:
        return False
    code = ord(word[-1]) - 0xAC00
    return 0 <= code <= 11171 and (code % 28) != 0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()
