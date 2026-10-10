# KB-05 — Testing and Acceptance Criteria

## Unit tests
- Store initializes with 384 dimensions and 4-bit configuration.
- Add a document containing several chunks.
- Add a second document and verify the first remains searchable.
- Search returns valid metadata and no more than the requested top-k results.
- Filename filter returns only chunks from the requested filename.
- Unknown filename filter returns no results.
- Empty store search returns an empty result safely.
- Clear removes vectors and metadata.
- Rebuild after subsequent uploads preserves expected indexed content.
- Invalid embedding dimensions and empty inputs are handled safely.

## Upload integration tests
- `.txt`, `.md`, and `.pdf` files are handled.
- Unsupported extensions are rejected.
- The 5 MB limit is enforced.
- Chunking uses 500 characters with 50-character overlap.
- Embeddings are 384-dimensional and normalized as intended.
- Response schema remains compatible with the frontend.

## Chat integration tests
- Relevant uploaded text appears in the RAG context.
- Chat still works when retrieval returns no chunks.
- WebSocket tokens stream using the existing protocol.
- Programming-only guardrail remains present.
- Groq rate-limit/429 behavior remains handled.
- Errors do not leave the WebSocket or store in an inconsistent state.

## End-to-end acceptance
1. Start the backend and frontend using the repository's existing instructions.
2. Upload a known PDF containing a specific fact or code example.
3. Ask a programming question whose answer is present in the PDF.
4. Verify the answer reflects the uploaded content.
5. Upload a second document and verify both remain retrievable.
6. Verify streaming, upload limits, and relevant error behavior.
7. Restart the server and confirm the transient-storage behavior expected by the specification.

## Test quality
Use deterministic embeddings or controlled fixtures for unit tests. Random embeddings can test basic mechanics but do not establish semantic retrieval quality. Report only tests actually executed and their actual results.
