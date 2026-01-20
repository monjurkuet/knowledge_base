# Knowledge Base UI

A modern, high-performance knowledge base visualization interface built with Bun, SolidJS, and Sigma.js.

## 🚀 Tech Stack

- **Runtime**: Bun 1.1+ - Ultra-fast JavaScript runtime
- **Framework**: SolidJS 1.8+ - Reactive UI framework
- **Graph Visualization**: Sigma.js 2.0+ - WebGL-powered graph rendering
- **Styling**: Tailwind CSS 3.4+ - Utility-first CSS
- **Language**: TypeScript 5.3+ - Type-safe development

## 📦 Installation

```bash
bun install
```

## 🛠️ Development

```bash
bun run dev
```

The application will be available at `http://localhost:3000`.

## 🏗️ Build

```bash
bun run build
```

## 📊 Features

- **Real-time Dashboard**: Live statistics and metrics
- **Graph Visualization**: Interactive knowledge graph with 10,000+ nodes
- **Search**: Full-text search with scoring
- **Domain Schema**: View and manage domain schemas
- **Text Ingestion**: Real-time text ingestion with WebSocket logs
- **WebSocket Integration**: Real-time updates and logs

## 📁 Project Structure

```
src/
├── components/
│   ├── Dashboard/      # Stats and metrics
│   ├── Graph/          # Knowledge graph visualization
│   ├── Search/         # Search functionality
│   ├── Domains/        # Domain schema viewer
│   └── Ingest/         # Text ingestion with WebSocket
├── services/
│   ├── api.ts          # API client
│   └── websocket.ts    # WebSocket service
├── stores/
│   ├── graphStore.ts   # Graph state management
│   └── wsStore.ts      # WebSocket state management
├── App.tsx             # Main application
└── index.tsx           # Entry point
```

## 🔧 Configuration

The application is configured to proxy API requests to the backend:

- API requests: `/api/*` → `http://localhost:8000/api/*`
- WebSocket: `/ws/*` → `ws://localhost:8000/ws/*`

## 🧪 Testing

```bash
bun test
```

## 📝 Type Checking

```bash
bun run check
```