"""Coordination's outbox append: the one writer of the `outbox` bucket bodies.

Layer: application
Context: coordination
Owns: Outbox.append, the body `{"message": m, "sent": False}` that the previous implementation writes inline at every outbox site
    names it, so that a non-owner unit (review's
    decision commit, research's incident record) joins with its own transaction.
Does not own: authorization (the caller authorizes with routing's Organization first, in the previous implementation order); the flusher
    and delivery (the previous implementation `application/outbox.py`)
Entry points: Outbox.append
Contracts: INV-MESSAGE-001
"""

from __future__ import annotations


class Outbox:
    """Stateless owner operation; its constructor takes nothing."""

    def append(self, tx, message: dict) -> None:
        # Rule 2: it joins the caller's unit and never opens, commits or nests a transaction.
        tx.put("outbox", message["message_id"], {"message": message, "sent": False})
