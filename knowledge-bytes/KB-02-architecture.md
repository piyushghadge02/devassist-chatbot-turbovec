# KB-02 — Intended Architecture

## Main components
- **Frontend:** Vue.js 3 + Tailwind CSS.
- **Backend:** asynchronous FastAPI.
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions.
- **Vector store after upgrade:** TurboVec `IdMapIndex`, configured with `bit_width=4`.
- **LLM:** Groq Cloud API.
- **Chat transport:** WebSocket streaming.
- **Storage lifecycle:** in-memory/transient according to the upgrade guide.

## Document upload flow
1. Receive an uploaded `.txt`, `.md`, or `.pdf` file.
2. Validate the file and preserve the 5 MB upload limit.
3. Extract text using the project's existing extraction code.
4. Split text into 500-character chunks with 50-character overlap.
5. Generate normalized embeddings with the existing embedding model.
6. Add vectors and matching chunk metadata to TurboVec.
7. Return a response compatible with the current frontend.

## Chat flow
1. Receive the user message over the existing WebSocket.
2. Embed the query using the same embedding model.
3. Retrieve the top 3 relevant chunks from TurboVec.
4. Build context with chunk text and source filename.
5. Send the programming-only system prompt, context, and user message to Groq.
6. Stream generated tokens over the existing WebSocket protocol.
7. Preserve rate-limit handling, including HTTP/API 429 cases.

## Architecture audit warning
This is the architecture described in the upgrade guide. Verify it against the actual repository before implementation. Prior notes mention Docling and PostgreSQL/pgvector in an ingestion pipeline; if those exist in the current branch, determine whether they are part of the same vector-store path before changing or removing them.
