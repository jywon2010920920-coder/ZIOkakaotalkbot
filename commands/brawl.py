import aiohttp
from config import settings

BRAWL_API_BASE = "https://api.brawlstars.com/v1"


async def cmd_brawl(args: str) -> str:
    tag = args.strip()
    if not tag:
        return "❌ 태그를 입력해주세요.\n예: !브롤 #2PP00"

    if not tag.startswith("#"):
        tag = "#" + tag

    if not settings.BRAWL_API_KEY:
        return "⚠️ 브롤스타즈 API 키가 설정되지 않았습니다."

    tag_encoded = tag.replace("#", "%23")
    url = f"{BRAWL_API_BASE}/players/{tag_encoded}"
    headers = {
        "Authorization": f"Bearer {settings.BRAWL_API_KEY}",
        "Accept": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 404:
                    return f"❌ '{tag}' 플레이어를 찾을 수 없어요."
                if resp.status == 403:
                    return "⚠️ API 키가 유효하지 않거나 이 IP에서의 접근이 허용되지 않아요."
                if resp.status != 200:
                    return f"⚠️ 브롤스타즈 API 오류 (상태 코드: {resp.status})"
                data = await resp.json()
                return _format_player(data)
    except aiohttp.ClientConnectorError:
        return "⚠️ 브롤스타즈 서버에 연결할 수 없어요."
    except TimeoutError:
        return "⏱️ 요청 시간이 초과됐어요. 다시 시도해주세요."


def _format_player(p: dict) -> str:
    name = p.get("name", "?")
    tag = p.get("tag", "?")
    trophies = p.get("trophies", 0)
    highest = p.get("highestTrophies", 0)
    exp = p.get("expLevel", 0)
    wins_3v3 = p.get("3vs3Victories", 0)
    wins_solo = p.get("soloVictories", 0)
    wins_duo = p.get("duoVictories", 0)
    brawlers = len(p.get("brawlers", []))
    club = p.get("club", {}).get("name", "없음")

    def fmt(n: int) -> str:
        return f"{n:,}"

    return (
        f"🎮 브롤스타즈 프로필\n"
        f"\n"
        f"👤 {name}  ({tag})\n"
        f"⭐ 레벨: {exp}\n"
        f"🏆 트로피: {fmt(trophies)}  (최고: {fmt(highest)})\n"
        f"🏅 클럽: {club}\n"
        f"\n"
        f"📊 전적\n"
        f"3vs3 승리: {fmt(wins_3v3)}\n"
        f"솔로 승리: {fmt(wins_solo)}\n"
        f"듀오 승리: {fmt(wins_duo)}\n"
        f"\n"
        f"🎯 보유 브롤러: {brawlers}개"
    )
