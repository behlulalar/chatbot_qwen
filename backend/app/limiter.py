"""
Rate limiter (slowapi) - IP bazlı istek sınırı.
main.py içinde app.state.limiter ve exception handler tanımlanır.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
