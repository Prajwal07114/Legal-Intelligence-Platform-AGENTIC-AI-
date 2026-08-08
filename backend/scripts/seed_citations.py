"""
Seed script: populates the `citations` table with a small starter
reference corpus (sample statutes, regulations, and standard clause
references) so the Research Agent has something to retrieve against
out of the box.

Run from the backend/ directory:
    python -m scripts.seed_citations
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_session  # noqa: E402
from app.models import Citation  # noqa: E402
from app.rag.embeddings import embed_texts  # noqa: E402

SAMPLE_CITATIONS = [
    {
        "source_name": "Indian Contract Act, 1872 — Section 73",
        "source_type": "statute",
        "content": (
            "Section 73 provides that when a contract has been broken, the party who "
            "suffers by such breach is entitled to receive compensation for any loss "
            "or damage caused to them thereby, which naturally arose in the usual "
            "course of things from such breach, or which the parties knew, when they "
            "made the contract, to be likely to result from the breach of it."
        ),
        "url": "https://www.indiacode.nic.in/",
    },
    {
        "source_name": "Indian Contract Act, 1872 — Section 74 (Liquidated Damages)",
        "source_type": "statute",
        "content": (
            "Section 74 deals with compensation for breach of contract where a penalty "
            "or liquidated damages amount has been stipulated. The party complaining of "
            "breach is entitled to receive reasonable compensation not exceeding the "
            "amount named or the penalty stipulated, regardless of whether actual "
            "damage or loss is proven."
        ),
        "url": "https://www.indiacode.nic.in/",
    },
    {
        "source_name": "Standard Clause Reference — Limitation of Liability",
        "source_type": "clause_reference",
        "content": (
            "A well-drafted limitation of liability clause typically caps aggregate "
            "liability at a defined multiple of fees paid, excludes indirect and "
            "consequential damages, and carves out exceptions for gross negligence, "
            "willful misconduct, confidentiality breaches, and indemnification "
            "obligations. Contracts lacking any liability cap expose a party to "
            "unlimited financial risk."
        ),
        "url": None,
    },
    {
        "source_name": "Standard Clause Reference — Termination for Convenience",
        "source_type": "clause_reference",
        "content": (
            "A termination-for-convenience clause allows either party to end the "
            "agreement without cause, typically subject to a written notice period "
            "(commonly 30-90 days). Contracts that omit any termination mechanism, or "
            "that grant termination rights to only one party, are considered "
            "one-sided and may create lock-in risk for the other party."
        ),
        "url": None,
    },
    {
        "source_name": "Standard Clause Reference — Confidentiality / NDA Provisions",
        "source_type": "clause_reference",
        "content": (
            "Robust confidentiality clauses define confidential information broadly, "
            "specify a survival period after termination (commonly 2-5 years, or "
            "indefinite for trade secrets), list standard exclusions (public "
            "information, independently developed information), and specify remedies "
            "including injunctive relief. Weak confidentiality clauses lack a survival "
            "period or carve-outs, weakening enforceability."
        ),
        "url": None,
    },
    {
        "source_name": "General Data Protection Regulation (GDPR) — Article 28 (Processors)",
        "source_type": "regulation",
        "content": (
            "Article 28 requires that processing by a data processor be governed by a "
            "contract that sets out the subject matter, duration, nature and purpose "
            "of processing, the type of personal data, categories of data subjects, "
            "and the obligations and rights of the controller. Contracts involving "
            "personal data processing without such terms may not be GDPR-compliant."
        ),
        "url": "https://gdpr-info.eu/art-28-gdpr/",
    },
    {
        "source_name": "Standard Clause Reference — Indemnification",
        "source_type": "clause_reference",
        "content": (
            "Indemnification clauses allocate risk for third-party claims arising from "
            "a party's breach, negligence, or IP infringement. Mutual indemnification "
            "is considered balanced; one-sided indemnification obligating only one "
            "party (especially uncapped) is a common red flag in contract review."
        ),
        "url": None,
    },
    {
        "source_name": "Standard Clause Reference — Force Majeure",
        "source_type": "clause_reference",
        "content": (
            "A force majeure clause excuses performance when extraordinary events "
            "beyond a party's control (natural disasters, war, pandemics, government "
            "action) prevent performance. Clauses lacking a force majeure provision "
            "may leave a party liable for breach even in genuinely unforeseeable "
            "circumstances."
        ),
        "url": None,
    },
]


def seed():
    texts = [c["content"] for c in SAMPLE_CITATIONS]
    print(f"Embedding {len(texts)} reference documents...")
    vectors = embed_texts(texts)

    with db_session() as db:
        existing = db.query(Citation).count()
        if existing > 0:
            print(f"citations table already has {existing} rows — skipping seed.")
            return

        for citation, vector in zip(SAMPLE_CITATIONS, vectors):
            db.add(Citation(
                source_name=citation["source_name"],
                source_type=citation["source_type"],
                content=citation["content"],
                url=citation["url"],
                embedding=vector,
            ))
        print(f"Inserted {len(SAMPLE_CITATIONS)} citations.")


if __name__ == "__main__":
    seed()
