"""WSGI-обёртка для FastAPI.

alwaysdata запускает Python-приложения через WSGI, а FastAPI работает по
ASGI. a2wsgi превращает ASGI-приложение в WSGI, поэтому микросервис можно
подключить как обычный сайт типа «Python WSGI» — без отдельного процесса
uvicorn и без переменных IP/PORT.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from a2wsgi import ASGIMiddleware

from main import app

_asgi_app = ASGIMiddleware(app)

PREFIX = '/fastapi'


def application(environ, start_response):
    """Точка входа WSGI для alwaysdata."""
    path = environ.get('PATH_INFO', '')

    # Если alwaysdata не включил Path trim, убираем префикс сами.
    if path == PREFIX:
        environ['PATH_INFO'] = '/'
    elif path.startswith(PREFIX + '/'):
        environ['PATH_INFO'] = path[len(PREFIX):]

    environ['SCRIPT_NAME'] = PREFIX
    return _asgi_app(environ, start_response)
