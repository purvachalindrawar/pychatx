import time
from collections import defaultdict, deque
from typing import Deque
from fastapi import HTTPException

WINDOW = 10
MAX_HITS = 50

_hits: dict[str, Deque[float]] = defaultdict(deque)

def rate_limit(ip: str):
    now = time.time()
    dq = _hits[ip]
    while dq and now - dq[0] > WINDOW:
        dq.popleft()
    if len(dq) >= MAX_HITS:
        raise HTTPException(status_code=429, detail="Rate limited")
    dq.append(now)
