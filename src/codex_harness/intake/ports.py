"""Intake ports: the buckets intake owns (single writer).

Layer: ports
Context: intake
Owns: OWNED_BUCKETS of the intake context (the Portfolio lineage rows; the Portfolio acceptances, investigations and followups; the four `desk_*` front-door buckets; the eight ticket buckets; batch B2: the five ticket buckets of `Tickets` and `GitHubTickets`); OutboxAppend, the consumer-declared shape of coordination's outbox append that FrontDesk.submit joins
Does not own: the Protocols other contexts declare for intake's operations (coordination.ports.PortfolioLineage, coordination.ports.DeskQueue)
Entry points: OWNED_BUCKETS, OutboxAppend
Contracts: INV-CONTINUATION-001
"""

from __future__ import annotations

from typing import Protocol

OWNED_BUCKETS = ("portfolio_bindings", "portfolio_acceptances", "portfolio_investigations",
                 "portfolio_followups",
                 # The sessions, requests, events and receipts only intake.application.frontdesk writes
                 "desk_sessions", "desk_requests", "desk_events", "desk_receipts",
                 # The ticket rows and the lifecycle's decision, closure, reopen and pin rows only
                 # intake.application.ticket_lifecycle writes (the ticket rows' other writers join with `Tickets`)
                 "tickets", "ticket_dispatches", "ticket_closures", "ticket_closure_sequences", "ticket_reopens", "ticket_github",
                 "ticket_lifecycle_events", "ticket_trust_anchors",
                 # Batch B2: `Tickets` writes the revisions and reviews (and, with the lifecycle, `tickets` and
                 # `ticket_dispatches`); `GitHubTickets` writes the remote creations, observations and syncs (and, with the lifecycle, `ticket_github`)
                 "ticket_reviews", "ticket_revisions", "ticket_remote_creations", "ticket_remote_observations", "ticket_syncs")


class OutboxAppend(Protocol):
    """Coordination's `Outbox.append(tx, message)`: the assignment joins the user's turn transaction."""

    def append(self, tx, message: dict) -> None: ...
