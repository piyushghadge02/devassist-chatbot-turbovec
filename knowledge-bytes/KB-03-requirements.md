# KB-03 — Functional and Technical Requirements

## Required change
- Replace FAISS with TurboVec `IdMapIndex` for the intended vector-store path.
- Configure `dim=384` and `bit_width=4`.
- Remove `faiss-cpu` only if it is no longer needed elsewhere.
- Add the correct TurboVec package dependency and verify its real API/version.

## Requirements to preserve
| Area | Requirement |
|---|---|
| Frontend | Vue.js 3 + Tailwind CSS |
| Backend | Async FastAPI |
| LLM | Groq Cloud API |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector dimension | 384 |
| Chunk size | 500 characters |
| Chunk overlap | 50 characters |
| Retrieval | Top 3 chunks |
| Upload limit | 5 MB |
| Document types in guide | `.txt`, `.md`, `.pdf` |
| Chat | WebSocket token streaming |
| Vector storage | In-memory/transient |
| Prompt restriction | Programming-related questions only |
| Errors | Preserve rate-limit handling for 429 responses |

## Vector-store capabilities
- Add multiple documents and their chunks.
- Give every chunk a stable unique ID for the current index lifecycle.
- Maintain text, filename, and chunk-index metadata.
- Search by query embedding and return text, filename, score, and chunk index.
- Support filename-filtered search.
- Clear index and metadata consistently.
- Handle repeated uploads without losing previously indexed content unintentionally.

## Compatibility
Preserve current API routes, response shapes, WebSocket message protocol, environment configuration, and frontend behavior unless the repository audit proves a change is necessary.
