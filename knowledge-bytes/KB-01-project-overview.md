# KB-01 — Project Overview

## Purpose
DevAssist is a programming-focused chatbot. The upgrade guide describes a RAG (Retrieval-Augmented Generation) pipeline in which uploaded documentation is chunked and embedded, relevant chunks are retrieved for a user question, and the retrieved context is sent to Groq to help generate the response.

## Upgrade objective
Replace the existing FAISS vector-store implementation with TurboVec `IdMapIndex`, while preserving the existing application and its user-facing behavior.

## Scope
- Replace the FAISS vector-store dependency/implementation with TurboVec where applicable.
- Keep document chunking and embeddings compatible with the stated requirements.
- Connect TurboVec retrieval to the existing upload and WebSocket chat flows.
- Add tests for indexing, retrieval, filtering, clearing, and end-to-end behavior.

## Out of scope
- Rebuilding the frontend.
- Replacing FastAPI, Groq, or the embedding model.
- Adding persistent vector storage when the specified design is transient in-memory storage.
- Unrelated UI or feature redesign.

## Success definition
The existing application runs; uploaded documents can be queried; relevant chunks are supplied to the existing Groq chat flow; WebSocket streaming and error handling continue to work; tests pass.
