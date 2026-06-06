import random
from database import ensure_user, update_money, stamp_daily, cooldown_ok, cooldown_remaining, fmt

DAILY_AMOUNT = 10_000


async def cmd_daily(args: str, user_id: str, nickname: str) -> str:
    user = await ensure_user(user_id, nickname)

    if not cooldown_ok(user["last_daily"]):
        h, m = cooldown_remaining(user["last_daily"])
        return f"⏳ 이미 오늘 받았어요!\n{h}시간 {m}분 뒤에 다시 받을 수 있어요."

    new_bal = await update_money(user_id, DAILY_AMOUNT)
    await stamp_daily(user_id)
    return (
        f"💰 {fmt(DAILY_AMOUNT)} 지급!\n"
        f"현재 잔액: {fmt(new_bal)}"
    )


async def cmd_gamble(args: str, user_id: str, nickname: str) -> str:
    user = await ensure_user(user_id, nickname)

    raw = args.strip().replace(",", "").replace("원", "")
    if not raw:
        return "❌ 금액을 입력해주세요.\n예: !도박 5000"
    try:
        amount = int(raw)
    except ValueError:
        return "❌ 올바른 금액을 입력해주세요.\n예: !도박 5000"
    if amount <= 0:
        return "❌ 1원 이상 입력해주세요."
    if user["money"] < amount:
        return f"❌ 잔액이 부족해요.\n현재 잔액: {fmt(user['money'])}"

    if random.random() < 0.5:
        new_bal = await update_money(user_id, amount)
        return (
            f"🎉 당첨! {fmt(amount)} → {fmt(amount * 2)} 획득!\n"
            f"현재 잔액: {fmt(new_bal)}"
        )
    else:
        new_bal = await update_money(user_id, -amount)
        return (
            f"💸 실패... {fmt(amount)} 잃었어요.\n"
            f"현재 잔액: {fmt(new_bal)}"
        )


async def cmd_balance(args: str, user_id: str, nickname: str) -> str:
    user = await ensure_user(user_id, nickname)
    return f"💳 {nickname}의 잔액: {fmt(user['money'])}"
