from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple


logger = logging.getLogger(__name__)


BanType = Literal["id", "ip"]


@dataclass
class BanRecord:
    type: BanType
    target: str
    expire_at: Optional[float]  # unix ts
    reason: str = ""
    created_at: float = 0.0

    def is_expired(self, now: Optional[float] = None) -> bool:
        if self.expire_at is None:
            return False
        now = time.time() if now is None else now
        return now >= self.expire_at


class SecurityStore:
    """In-memory security store with optional JSON persistence."""

    def __init__(self, path: str | os.PathLike = "security.json") -> None:
        self.path = Path(path)
        self.bans: List[BanRecord] = []
        self.blacklist_ips: Dict[str, Optional[float]] = {}  # ip -> expire_at
        self.ops: set[str] = set()
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.ops = set(map(str, data.get("ops", [])))
            self.blacklist_ips = {
                str(k): (float(v) if v is not None else None)
                for k, v in (data.get("blacklist_ips", {}) or {}).items()
            }
            self.bans = []
            for b in data.get("bans", []) or []:
                self.bans.append(
                    BanRecord(
                        type=b.get("type", "id"),
                        target=str(b.get("target", "")),
                        expire_at=(float(b["expire_at"]) if b.get("expire_at") is not None else None),
                        reason=str(b.get("reason", "")),
                        created_at=float(b.get("created_at", 0.0) or 0.0),
                    )
                )
        except Exception:
            logger.exception("[SecurityStore] Failed to load %s", self.path)

    def save(self) -> None:
        try:
            payload = {
                "ops": sorted(self.ops),
                "blacklist_ips": self.blacklist_ips,
                "bans": [
                    {
                        "type": b.type,
                        "target": b.target,
                        "expire_at": b.expire_at,
                        "reason": b.reason,
                        "created_at": b.created_at,
                    }
                    for b in self.bans
                    if not b.is_expired()
                ],
            }
            self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            logger.exception("[SecurityStore] Failed to save %s", self.path)

    def cleanup(self) -> None:
        now = time.time()
        self.bans = [b for b in self.bans if not b.is_expired(now)]
        for ip, exp in list(self.blacklist_ips.items()):
            if exp is not None and now >= exp:
                self.blacklist_ips.pop(ip, None)

    # ---- ban ----
    def add_ban(self, ban_type: BanType, target: str, duration_s: Optional[int], reason: str = "") -> None:
        now = time.time()
        expire_at = None
        if duration_s is not None:
            expire_at = now + max(0, int(duration_s))
        # remove existing same
        self.bans = [b for b in self.bans if not (b.type == ban_type and b.target == target)]
        self.bans.append(BanRecord(type=ban_type, target=target, expire_at=expire_at, reason=reason, created_at=now))
        self.save()

    def remove_ban(self, ban_type: BanType, target: str) -> bool:
        before = len(self.bans)
        self.bans = [b for b in self.bans if not (b.type == ban_type and b.target == target)]
        changed = len(self.bans) != before
        if changed:
            self.save()
        return changed

    def list_bans(self) -> List[BanRecord]:
        self.cleanup()
        return list(self.bans)

    def is_banned(self, ban_type: BanType, target: str) -> Optional[BanRecord]:
        self.cleanup()
        for b in self.bans:
            if b.type == ban_type and b.target == target:
                return b
        return None

    # ---- blacklist ip ----
    def add_blacklist_ip(self, ip: str, duration_s: Optional[int]) -> None:
        now = time.time()
        exp = None
        if duration_s is not None:
            exp = now + max(0, int(duration_s))
        self.blacklist_ips[str(ip)] = exp
        self.save()

    def remove_blacklist_ip(self, ip: str) -> bool:
        existed = ip in self.blacklist_ips
        self.blacklist_ips.pop(ip, None)
        if existed:
            self.save()
        return existed

    def list_blacklist_ips(self) -> Dict[str, Optional[float]]:
        self.cleanup()
        return dict(self.blacklist_ips)

    def is_blacklisted_ip(self, ip: str) -> bool:
        self.cleanup()
        return ip in self.blacklist_ips

    # ---- ops ----
    def op(self, pid: str) -> None:
        self.ops.add(str(pid))
        self.save()

    def deop(self, pid: str) -> bool:
        pid = str(pid)
        existed = pid in self.ops
        self.ops.discard(pid)
        if existed:
            self.save()
        return existed
