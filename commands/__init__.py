from commands.basic import cmd_help
from commands.brawl import cmd_brawl
from commands.economy import cmd_daily, cmd_gamble, cmd_balance
from commands.shop import cmd_shop
from commands.title import cmd_title_boast

# 긴 명령어를 먼저 배치해야 prefix 매칭이 올바르게 동작합니다
COMMAND_MAP: dict[str, any] = {
    "!돈 지급":  cmd_daily,
    "!칭호 자랑": cmd_title_boast,
    "!도움말":   cmd_help,
    "!브롤":     cmd_brawl,
    "!도박":     cmd_gamble,
    "!잔액":     cmd_balance,
    "!상점":     cmd_shop,
}


async def handle_command(utterance: str, user_id: str = "", nickname: str = "") -> str:
    utterance = utterance.strip()

    # 긴 키 우선 매칭 (두 단어 명령어가 한 단어보다 먼저 확인됨)
    for key, handler in sorted(COMMAND_MAP.items(), key=lambda kv: len(kv[0]), reverse=True):
        if utterance == key:
            return await handler("", user_id, nickname)
        if utterance.startswith(key + " "):
            args = utterance[len(key) + 1:].strip()
            return await handler(args, user_id, nickname)

    cmd_word = utterance.split()[0] if utterance else utterance
    return (
        f"❓ 알 수 없는 명령어: {cmd_word}\n"
        "!도움말 을 입력하면 명령어 목록을 볼 수 있어요."
    )
