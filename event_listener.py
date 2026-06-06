"""
카카오톡 오픈채팅 이벤트 리스너 (비공식 API)

프로필 변경 감지 흐름:
  1. 카카오톡 비공식 API로 로그인 → access_token 획득
  2. 오픈채팅방 메시지를 주기적으로 폴링
  3. type == "FEED" + feedType == 9(프로필 변경) 메시지 감지
  4. "닉네임이 프로필을 변경했습니다." 전송

주의: 비공식 API는 카카오 정책에 따라 계정이 제한될 수 있습니다.
      전용 봇 계정 사용을 권장합니다.

환경변수 설정 (.env):
  KAKAO_EMAIL    — 카카오 계정 이메일
  KAKAO_PASSWORD — 카카오 계정 비밀번호
  KAKAO_ROOM_ID  — 오픈채팅방 링크 ID (URL 숫자 부분)
"""

import asyncio
import hashlib
import logging
import uuid
import aiohttp
from database import josa_i_ga
from config import settings

logger = logging.getLogger(__name__)

# 카카오톡 비공식 API 엔드포인트
# 버전/업데이트에 따라 변경될 수 있습니다
_BASE = "https://katalk.kakao.com"
_AUTH_URL = f"{_BASE}/win32/account/login.json"
_CHAT_URL = f"{_BASE}/api/v1/open/chat"       # GET  /{room_id}/messages
_SEND_URL = f"{_BASE}/api/v1/open/chat"       # POST /{room_id}/message

# FEED 메시지 중 프로필 변경을 나타내는 feedType 값
# (카카오톡 내부 값 — 업데이트 시 변경될 수 있음)
_PROFILE_FEED_TYPES: set[int] = {9, 15}

# 로그인 시 순서대로 시도할 버전 목록
_KT_VERSIONS = ["10.6.7", "10.5.5", "10.4.9", "10.4.4"]


class ProfileChangeListener:
    def __init__(self) -> None:
        self._email = settings.KAKAO_EMAIL
        self._password = settings.KAKAO_PASSWORD
        self._room_id = settings.KAKAO_ROOM_ID
        self._device_uuid = str(uuid.uuid4())
        self._access_token: str | None = None
        self._session: aiohttp.ClientSession | None = None
        self._last_log_id: int = 0

    # ── 공개 인터페이스 ─────────────────────────────────────────────────

    async def run(self, poll_interval: float = 3.0) -> None:
        """이벤트 리스너를 시작합니다. 무한 루프로 동작합니다."""
        if not all([self._email, self._password, self._room_id]):
            logger.warning(
                "KAKAO_EMAIL / KAKAO_PASSWORD / KAKAO_ROOM_ID 가 설정되지 않아 "
                "프로필 변경 감지를 건너뜁니다."
            )
            return

        async with aiohttp.ClientSession() as session:
            self._session = session
            if not await self._login():
                logger.error("카카오톡 로그인 실패 — 이메일/비밀번호를 확인하세요.")
                return

            logger.info("오픈채팅 %s 모니터링 시작", self._room_id)
            while True:
                try:
                    await self._poll()
                except Exception as exc:
                    logger.warning("폴링 오류: %s", exc)
                await asyncio.sleep(poll_interval)

    # ── 내부 메서드 ────────────────────────────────────────────────────

    async def _login(self) -> bool:
        pw_hash = hashlib.sha512(self._password.encode()).hexdigest()
        data = {
            "email": self._email,
            "password": pw_hash,
            "device_uuid": self._device_uuid,
            "device_name": "Windows PC",
            "os_version": "10.0",
            "permanent": "1",
        }
        for ver in _KT_VERSIONS:
            headers = {
                "User-Agent": f"KT/{ver} Wd/10.0 ko",
                "A": f"win32/{ver}/ko",
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            async with self._session.post(_AUTH_URL, data=data, headers=headers) as resp:
                body = await resp.json(content_type=None)

            status = body.get("status")
            if status == 0:
                self._access_token = body["access_token"]
                self._headers_base = headers
                logger.info("로그인 성공 (버전 %s)", ver)
                return True

            msg = body.get("message", "")
            logger.warning("버전 %s 로그인 실패: %s", ver, msg)

            # 버전 문제가 아닌 오류면 더 시도하지 않음
            if "버전" not in msg and "update" not in msg.lower():
                break

        logger.error("모든 버전으로 로그인 실패 — 이메일/비밀번호를 확인하세요.")
        return False

    def _headers(self) -> dict:
        base = getattr(self, "_headers_base", {"User-Agent": "KT/10.6.7 Wd/10.0 ko"})
        return {**base, "Authorization": f"Bearer {self._access_token}"}

    async def _poll(self) -> None:
        params: dict = {}
        if self._last_log_id:
            params["since"] = self._last_log_id

        url = f"{_CHAT_URL}/{self._room_id}/messages"
        async with self._session.get(url, headers=self._headers(), params=params) as resp:
            body = await resp.json(content_type=None)

        for msg in body.get("chats", []):
            log_id: int = msg.get("logId", 0)
            if log_id > self._last_log_id:
                self._last_log_id = log_id
            await self._handle(msg)

    async def _handle(self, msg: dict) -> None:
        if msg.get("type") != "FEED":
            return

        feed: dict = msg.get("feed", {})
        feed_type = feed.get("feedType")

        is_profile_change = (
            feed_type in _PROFILE_FEED_TYPES
            or "profile" in str(feed).lower()
        )
        if not is_profile_change:
            return

        nickname: str = (
            msg.get("authorNickname")
            or feed.get("nickName")
            or feed.get("nickname")
            or "알 수 없음"
        )

        postfix = josa_i_ga(nickname)
        await self._send(f"{nickname}{postfix} 프로필을 변경했습니다.")

    async def _send(self, text: str) -> None:
        url = f"{_SEND_URL}/{self._room_id}/message"
        payload = {"message": text, "type": "text"}
        async with self._session.post(
            url, headers=self._headers(), json=payload
        ) as resp:
            if resp.status != 200:
                logger.warning("메시지 전송 실패: %s", resp.status)
