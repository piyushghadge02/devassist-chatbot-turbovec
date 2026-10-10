# KB-06 — Repository Audit and Open Questions

Complete this checklist before making destructive or broad changes.

## Repository audit
- [ ] Identify the backend entry point and app startup lifecycle.
- [ ] Find all FAISS imports and call sites.
- [ ] Find existing vector-store and RAG modules.
- [ ] Find document extraction and chunking code.
- [ ] Find embedding-model initialization and reuse behavior.
- [ ] Find upload validation and the 5 MB limit.
- [ ] Find WebSocket routes and exact message protocol.
- [ ] Find Groq client setup and 429 handling.
- [ ] Review existing unit, integration, and end-to-end tests.
- [ ] Inspect environment variables and ensure secrets are not printed or overwritten.

## Architecture discrepancy to resolve
The TurboVec upgrade PDF describes replacing FAISS with an in-memory TurboVec store. Prior project notes refer to Docling-based PDF conversion and PostgreSQL/pgvector. Verify whether these notes apply to the current checkout and whether pgvector is a separate subsystem or the actual active vector store. Do not remove or bypass an active subsystem without resolving this.

## Package/API verification
- [ ] Confirm TurboVec can be installed in the project's Python version and operating system.
- [ ] Verify `IdMapIndex` constructor, `add_with_ids`, search return shapes, filtering support, and clear/reset behavior from the actual installed version's documentation/API.
- [ ] Verify score direction and ID sentinel behavior.
- [ ] Confirm any `allowlist` argument's expected dtype and semantics.
- [ ] Pin a compatible dependency version if the project uses dependency pinning.

## Decisions to document
- Which current module owns vector storage?
- Is the active branch's storage FAISS, pgvector, or something else?
- How will the full in-memory index be rebuilt after additional uploads?
- What is the intended behavior for duplicate filenames?
- Should an upload replace a prior document with the same filename or add another version?
- How is the embedding model initialized without blocking or duplicating startup work?

## Completion report
Record changed files, dependency changes, commands run, test outcomes, known limitations, and manual verification steps. Do not claim completion until acceptance criteria pass.
