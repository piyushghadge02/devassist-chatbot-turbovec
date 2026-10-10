# KB-04 — TurboVec Migration Notes

## Recommended sequence
1. Inspect the current repository and identify every FAISS import/use.
2. Confirm the actual installed TurboVec package API and version.
3. Add a vector-store adapter or update the existing module with minimal interface changes.
4. Integrate it with the existing upload route.
5. Integrate retrieval with the existing WebSocket chat route.
6. Run unit, integration, and regression tests.
7. Run a real upload-and-question scenario through the UI.

## Index rebuild/data integrity risk
The sample in the PDF clears pending embeddings after rebuilding the index. If a later upload triggers a new index built only from new pending embeddings, previously indexed vectors could be lost while metadata remains. Do not copy that logic blindly.

Choose and test a coherent strategy:
- retain all embeddings needed to rebuild the full in-memory index, or
- add new vectors to the existing index using the supported TurboVec API.

Confirm actual API semantics before choosing. Ensure IDs remain unique and metadata maps to the right vector.

## Data validation
- Validate file size before reading the entire upload into memory where feasible.
- Keep extension and content validation.
- Check embedding shape `(number_of_chunks, 384)` and compatible dtype.
- Handle empty documents and empty chunk lists safely.
- Ensure clearing the store clears index, pending vectors, IDs, and metadata.
- Do not expose internal exception details to end users unless existing policy intentionally does so.

## Concurrency
Because FastAPI is asynchronous and the store is shared in memory, inspect whether concurrent uploads and searches can overlap with index rebuilds. Add appropriate synchronization if needed; do not add complexity without evidence.

## Persistence
The PDF specifies transient in-memory storage and loss on restart. Do not add disk persistence as part of this change. Confirm the existing code's behavior before changing it.
