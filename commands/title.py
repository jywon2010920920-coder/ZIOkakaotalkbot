import json
from database import (
    ensure_user, stamp_boast, cooldown_ok, cooldown_remaining,
    TITLE_ORDER, TITLE_EMOJI, josa_eul_reul,
)


async def cmd_title_boast(args: str, user_id: str, nickname: str) -> str:
    user = await ensure_user(user_id, nickname)
    owned: list[str] = json.loads(user["titles"])

    if not owned:
        return "❌ 보유한 칭호가 없어요.\n!상점 에서 칭호를 구매해보세요!"

    if not cooldown_ok(user["last_boast"]):
        h, m = cooldown_remaining(user["last_boast"])
        return f"⏳ 이미 오늘 자랑했어요!\n{h}시간 {m}분 뒤에 다시 자랑할 수 있어요."

    # 가장 높은 등급 칭호를 자랑
    best = next((t for t in reversed(TITLE_ORDER) if t in owned), owned[-1])

    await stamp_boast(user_id)

    emoji = TITLE_EMOJI.get(best, "")
    eul_reul = josa_eul_reul(best)
    return f"✨ {nickname}  {emoji}{best}{eul_reul} 보유중입니다!"
