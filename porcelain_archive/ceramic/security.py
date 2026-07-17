"""HTTP-security middleware: заголовки безопасности и CSRF (double-submit cookie).

CSRF-схема, вынесенная из /admin-роутера прежней Jinja2-версии под JSON API:
non-httponly cookie csrf_token выставляется всем клиентам; фронтенд обязан
прислать её значение обратно в заголовке X-CSRF-Token на любой мутирующий
запрос к /api/ (кроме /api/users/login - там ещё нет установившейся сессии,
вход защищён IP-throttle). Проверка - secrets.compare_digest.
"""
from __future__ import annotations

import secrets

from fastapi import Request

from porcelain_archive.config import config

CSRF_COOKIE_NAME = "csrf_token"
_CERAMIC_API_PREFIX = "/api/ceramic/"
_CSRF_EXEMPT_PATHS = {"/api/ceramic/users/login"}
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


async def security_middleware(request: Request, call_next):
    # Действует только на роуты ceramic (/api/ceramic/) - не должен затрагивать
    # остальные API porcelain_archive (document/task/user).
    if not request.url.path.startswith(_CERAMIC_API_PREFIX):
        return await call_next(request)

    is_dev = config.ceramicsite.app_env != "production"

    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    needs_csrf_cookie = not csrf_cookie

    if (
        request.method not in _SAFE_METHODS
        and request.url.path not in _CSRF_EXEMPT_PATHS
    ):
        sent = request.headers.get("x-csrf-token")
        if not csrf_cookie or not sent or not secrets.compare_digest(sent, csrf_cookie):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "CSRF-токен недействителен"}, status_code=403)

    response = await call_next(request)

    if needs_csrf_cookie:
        response.set_cookie(
            CSRF_COOKIE_NAME,
            secrets.token_urlsafe(32),
            httponly=False,
            samesite="lax",
            secure=not is_dev,
            path="/",
        )

    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "img-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "base-uri 'self'; "
        "frame-ancestors 'self'",
    )
    if not is_dev:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response
