import json
from database import (
    ensure_user, update_money, add_title,
    TITLES, TITLE_ORDER, TITLE_EMOJI,
    fmt, josa_i_ga, josa_eul_reul,
)


async def cmd_shop(args: str, user_id: str, nickname: str) -> str:
    user = await ensure_user(user_id, nickname)
    owned: set[str] = set(json.loads(user["titles"]))

    target = args.strip()
    if target:
        return await _buy(user, user_id, nickname, target, owned)

    lines = [f"🏪 칭호 상점\n"]
    for title in TITLE_ORDER:
        emoji = TITLE_EMOJI[title]
        status = "✅ 보유" if title in owned else fmt(TITLES[title])
        lines.append(f"{emoji} {title}  —  {status}")

    lines.append(f"\n💳 내 잔액: {fmt(user['money'])}")
    lines.append("구매: !상점 [칭호이름]")
    return "\n".join(lines)


async def _buy(user: dict, user_id: str, nickname: str, title: str, owned: set[str]) -> str:
    if title not in TITLES:
        return f"❌ 없는 칭호예요.\n칭호: {', '.join(TITLE_ORDER)}"
    if title in owned:
        return f"❌ 이미 보유한 칭호예요: {TITLE_EMOJI[title]}{title}"

    price = TITLES[title]
    if user["money"] < price:
        short = price - user["money"]
        return (
            f"❌ 잔액이 부족해요.\n"
            f"필요: {fmt(price)}  |  현재: {fmt(user['money'])}  |  부족: {fmt(short)}"
        )

    new_bal = await update_money(user_id, -price)
    await add_title(user_id, title)

    emoji = TITLE_EMOJI[title]
    postfix = josa_i_ga(nickname)
    eul_reul = josa_eul_reul(title)

    return (
        f"🎊 {nickname}{postfix} {emoji}{title} 칭호{eul_reul} 획득했습니다!\n"
        f"남은 잔액: {fmt(new_bal)}"
    )
