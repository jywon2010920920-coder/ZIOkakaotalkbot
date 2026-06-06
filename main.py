import asyncio
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from commands import handle_command
from database import init_db
from event_listener import ProfileChangeListener
from config import settings

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    listener = ProfileChangeListener()
    task = asyncio.create_task(listener.run())
    yield
    task.cancel()


app = FastAPI(title="KakaoTalk OpenChat Bot", lifespan=lifespan)


@app.get("/")
async def health():
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        logging.info("webhook 수신: %s", data)

        user_request = data.get("userRequest", {})
        utterance: str = (user_request.get("utterance") or "").strip()
        user_info: dict = user_request.get("user", {})
        user_id: str = user_info.get("id", "unknown")
        props: dict = user_info.get("properties", {})
        nickname: str = (
            props.get("nickname")
            or props.get("plusfriendUserKey")
            or user_info.get("id", "익명")
        )

        if utterance.startswith("!"):
            text = await handle_command(utterance, user_id=user_id, nickname=nickname)
        else:
            text = "❓ '!' 로 시작하는 명령어를 입력해주세요.\n!도움말 을 입력하면 목록을 볼 수 있어요."

    except Exception as e:
        logging.error("webhook 오류: %s", e, exc_info=True)
        text = "⚠️ 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    return JSONResponse(
        content={
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": text}}]},
        }
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=False)
