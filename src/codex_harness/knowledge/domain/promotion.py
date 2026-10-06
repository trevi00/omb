"""The verified-promotion graph namespace.

Layer: domain
Context: knowledge
Owns: PROMOTED_NAMESPACE, the repository prefix of every promoted `verified:<run>` graph; BUCKET, the name of the
    promotions bucket (research's program reads it from here, one owner)
Does not own: which run may be promoted (research.domain.autonomous)
Entry points: PROMOTED_NAMESPACE, BUCKET
Contracts: INV-AUTONOMOUS-001

Provenance: carried over from the previous implementation.
"""

PROMOTED_NAMESPACE = "verified:"
BUCKET = "promotions"
