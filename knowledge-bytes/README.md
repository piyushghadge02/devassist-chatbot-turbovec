# DevAssist Chatbot — Updated Knowledge Bytes

**Purpose:** Documentation pack for the proposed TurboVec upgrade described in `devassist-turbovec-upgrade.pdf`.

These Knowledge Bytes document the intended requirements and verification plan. They do not claim the upgrade has already been implemented.

## Contents
- `KB-01-project-overview.md` — project purpose and upgrade scope
- `KB-02-architecture.md` — intended request/data flow
- `KB-03-requirements.md` — requirements that must remain unchanged and the TurboVec change
- `KB-04-turbovec-migration.md` — implementation guidance and migration risks
- `KB-05-testing-and-acceptance.md` — test plan and definition of done
- `KB-06-open-questions-and-audit.md` — items to verify against the actual repository

## Important compatibility note
The upgrade guide says to replace FAISS with TurboVec and keep the rest of the stack unchanged. Prior project notes mention a document-ingestion path involving Docling and PostgreSQL/pgvector. These may describe a different revision or a different subsystem. Before coding, inspect the actual repository and reconcile this difference. Do not silently remove Docling, PostgreSQL, or pgvector unless the existing code and approved requirements confirm that they are part of the FAISS-based vector-store path being replaced.

## Source
Based on the 11-page `TurboVec Upgrade Guide — DevAssist Chatbot` PDF dated May 22, 2026. Any additional safeguards or audit notes are explicitly implementation guidance, not claims quoted from the PDF.
