# Architecture Documentation

## System Overview

AI Native Books Interaction is a FastAPI-based service that provides AI-powered educational content interaction capabilities including summarization, personalization, and conversational learning.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  (Web App, Mobile App, Learning Management Systems)         │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS/SSE
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway Layer                        │
│                   (FastAPI Application)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ CORS         │  │ Auth         │  │ Logging      │      │
│  │ Middleware   │  │ Middleware   │  │ Middleware   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Router Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Auth      │  │ Summarize   │  │ Personalize │         │
│  │  Endpoints  │  │  Endpoints  │  │  Endpoints  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼─────────────────┼─────────────────┼───────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            OpenAI Agent Service                      │   │
│  │  - Agent configuration & management                  │   │
│  │  - Streaming response generation                     │   │
│  │  - Context management                                │   │
│  └────────────────────┬─────────────────────────────────┘   │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  External Services                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │   Google Gemini 2.0 Flash (via OpenAI SDK)          │   │
│  │   - Content generation                               │   │
│  │   - Streaming responses                              │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. API Gateway Layer

**Technology**: FastAPI 0.115.0+

**Responsibilities**:
- Request routing and validation
- CORS policy enforcement
- Authentication/Authorization
- Request/Response logging
- Error handling and standardization

**Key Features**:
- Automatic OpenAPI documentation
- Request validation via Pydantic
- Async request handling
- Server-Sent Events (SSE) support

### 2. Router Layer

Organized by feature domains:

#### Authentication Router (`/api/v1/auth`)
- `/dummy-login`: Temporary authentication endpoint
- `/verify`: Token validation (placeholder for SSO)
- `/profile-login`: Profile-based authentication

**Future**: Will integrate with SSO provider (OAuth2/OIDC)

#### Summarization Router (`/api/v1`)
- `/summarize`: Streaming content summarization
  - Input: pageId, token, content
  - Output: SSE stream with summary chunks
  - Compression: 20-25% of original (150-500 words)

#### Personalization Router (`/api/v1`)
- `/personalize`: Content personalization
  - Skill level adaptation
  - Background-based examples
  - Progressive difficulty

### 3. Service Layer

#### OpenAI Agent Service

**Purpose**: Manages AI agent lifecycle and streaming responses

**Key Components**:

```python
# Agent Configuration
- Model: Gemini 2.0 Flash (via OpenAI-compatible API)
- Session: SQLite-based conversation tracking
- Tracing: Disabled for production, enabled for debugging

# Core Functions
- generate_summary(): Streaming summarization
- generate_personalized_content(): Adaptive content
- generate_socratic_response(): Question-based learning
```

**Streaming Architecture**:
```
Client Request → Router → Service
                            ↓
                   Create Agent/Runner
                            ↓
                   Stream Responses ←→ Gemini API
                            ↓
                   Format as SSE
                            ↓
                   Yield to Client
```

### 4. Data Models Layer

**Technology**: Pydantic

**Key Schemas**:

```python
# Authentication
- AuthResponse: Login response with token
- UserProfile: User information
- ProfileLoginRequest: Login with profile data

# Summarization
- ErrorResponse: Standardized error format

# Future Models
- ChatMessage: Conversational interactions
- LearningProgress: User progress tracking
- ContentMetadata: Book/chapter information
```

### 5. External Services

#### Google Gemini 2.0 Flash

**Integration Method**: OpenAI-compatible API

```python
AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=GOOGLE_API_KEY
)
```

**Features Used**:
- Streaming chat completions
- Context window: Large (100K+ tokens)
- Response format: JSON-structured
- Rate limiting: Handled by SDK

## Data Flow

### Summarization Flow

```
1. Client sends GET /api/v1/summarize
   ├─ Parameters: pageId, token, content
   └─ Headers: Accept: text/event-stream

2. Auth Router validates token
   └─ (Currently dummy implementation)

3. Summarize Router validates request
   ├─ Check pageId format
   ├─ Validate content length (>50 chars)
   └─ Forward to service

4. OpenAI Agent Service
   ├─ Create agent with summarization prompt
   ├─ Initialize streaming runner
   ├─ Configure response format
   └─ Stream to Gemini API

5. Gemini API processes
   ├─ Analyze content structure
   ├─ Generate proportional summary
   └─ Stream tokens back

6. Service formats response
   ├─ Convert to SSE format
   ├─ Add metadata (chunk, done flag)
   └─ Yield events

7. Client receives SSE stream
   ├─ data: {"chunk": "...", "done": false}
   ├─ data: {"chunk": "...", "done": false}
   └─ data: {"chunk": "", "done": true}
```

## Security Architecture

### Current State (Development)

- **Authentication**: Dummy token-based
- **Authorization**: No role-based access control
- **CORS**: Configured for local development
- **API Keys**: Environment variable storage

### Future Production Requirements

```
┌─────────────────────────────────────────────┐
│           Security Layers                    │
├─────────────────────────────────────────────┤
│ 1. API Gateway                              │
│    - Rate limiting                          │
│    - DDoS protection                        │
│    - Request size limits                    │
├─────────────────────────────────────────────┤
│ 2. Authentication                           │
│    - OAuth2/OIDC SSO                       │
│    - JWT token validation                  │
│    - Token refresh mechanism               │
├─────────────────────────────────────────────┤
│ 3. Authorization                            │
│    - Role-Based Access Control (RBAC)      │
│    - Resource-level permissions            │
│    - Multi-tenancy isolation               │
├─────────────────────────────────────────────┤
│ 4. Data Protection                          │
│    - TLS/SSL encryption                    │
│    - API key rotation                      │
│    - Secrets management (Vault)            │
├─────────────────────────────────────────────┤
│ 5. Audit & Monitoring                       │
│    - Request logging                       │
│    - Security event tracking               │
│    - Anomaly detection                     │
└─────────────────────────────────────────────┘
```

## Scalability Considerations

### Current Architecture (Single Instance)

- **Concurrency**: AsyncIO-based
- **Connections**: Limited by server resources
- **State**: In-memory session storage

### Future Horizontal Scaling

```
┌─────────────────────────────────────────────┐
│          Load Balancer                       │
└────────┬────────────────────┬────────────────┘
         │                    │
    ┌────▼─────┐         ┌────▼─────┐
    │ API      │         │ API      │
    │ Instance │         │ Instance │
    │    1     │         │    2     │
    └────┬─────┘         └────┬─────┘
         │                    │
         └────────┬───────────┘
                  │
         ┌────────▼──────────┐
         │  Shared Services  │
         ├───────────────────┤
         │ - Redis (Cache)   │
         │ - PostgreSQL (DB) │
         │ - Session Store   │
         └───────────────────┘
```

### Performance Optimizations

1. **Caching Strategy**
   - Response caching for identical content
   - Agent configuration caching
   - Session state in Redis

2. **Database Optimizations**
   - Connection pooling
   - Read replicas
   - Query optimization

3. **AI Service Optimization**
   - Request batching
   - Streaming chunking
   - Token usage monitoring

## Monitoring & Observability

### Logging Strategy

```python
# Structured logging levels
DEBUG:   Development debugging
INFO:    Request/response tracking
WARNING: Validation failures, rate limits
ERROR:   Service failures, API errors
CRITICAL: System failures
```

### Metrics to Track

1. **API Performance**
   - Request latency (p50, p95, p99)
   - Throughput (requests/second)
   - Error rates by endpoint

2. **AI Service**
   - Token usage per request
   - Streaming latency
   - Model response time

3. **System Health**
   - CPU/Memory usage
   - Active connections
   - Queue depths

### Future Monitoring Stack

```
Application → Structured Logs → ELK Stack
           → Metrics → Prometheus → Grafana
           → Traces → Jaeger/OpenTelemetry
           → Errors → Sentry
```

## Deployment Architecture

### Development
```
Local Machine
├── API Server (uvicorn --reload)
├── SQLite (sessions.db)
└── Environment variables (.env)
```

### Production (Recommended)

```
┌─────────────────────────────────────────┐
│           Cloud Infrastructure           │
├─────────────────────────────────────────┤
│ Kubernetes Cluster                      │
│  ├── API Deployment (3+ replicas)      │
│  ├── Ingress Controller                │
│  ├── ConfigMaps/Secrets                │
│  └── HPA (Auto-scaling)                │
├─────────────────────────────────────────┤
│ Managed Services                        │
│  ├── PostgreSQL (RDS/Cloud SQL)        │
│  ├── Redis (ElastiCache/MemoryStore)   │
│  ├── Object Storage (S3/GCS)           │
│  └── Secrets Manager                   │
├─────────────────────────────────────────┤
│ Observability                           │
│  ├── Prometheus/Grafana                │
│  ├── ELK Stack                         │
│  └── Distributed Tracing               │
└─────────────────────────────────────────┘
```

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Framework | FastAPI | ≥0.115.0 | Web framework |
| Server | Uvicorn | 0.24.0 | ASGI server |
| AI SDK | openai-agents | ≥0.1.0 | Agent framework |
| AI Model | Gemini 2.0 Flash | Latest | LLM service |
| Validation | Pydantic | (FastAPI dep) | Data validation |
| HTTP Client | httpx | ≥0.27.1 | Async HTTP |
| Config | python-dotenv | 1.0.0 | Environment vars |
| Testing | pytest | 7.4.3 | Test framework |
| Async Test | pytest-asyncio | 0.21.1 | Async testing |

## Future Architecture Enhancements

### Phase 1: Production Ready
- [ ] SSO integration (OAuth2/OIDC)
- [ ] PostgreSQL database
- [ ] Redis caching
- [ ] Rate limiting
- [ ] API versioning

### Phase 2: Multi-Tenancy
- [ ] Book/tenant isolation
- [ ] User role management
- [ ] Resource quotas
- [ ] Audit logging

### Phase 3: Advanced Features
- [ ] Vector database (RAG)
- [ ] Conversation history
- [ ] Analytics dashboard
- [ ] A/B testing framework

### Phase 4: Scale
- [ ] Kubernetes deployment
- [ ] Auto-scaling
- [ ] CDN integration
- [ ] Global distribution

## Design Decisions

### Why FastAPI?
- Native async support
- Automatic API documentation
- Type safety with Pydantic
- High performance
- SSE support

### Why OpenAI Agents SDK?
- Simplified agent management
- Built-in streaming
- Session handling
- OpenAI-compatible interface
- Extensible architecture

### Why Gemini 2.0 Flash?
- Large context window
- Fast response times
- Cost-effective
- Multimodal capabilities
- OpenAI-compatible API

### Why SSE over WebSockets?
- Simpler client implementation
- Automatic reconnection
- Better for unidirectional streaming
- HTTP/2 compatible
- No special server requirements

## API Versioning Strategy

Current: `/api/v1/...`

Future versions will maintain backward compatibility:
- `/api/v1/...` - Current stable
- `/api/v2/...` - Next major version
- Deprecated endpoints: 6-month sunset period

## Error Handling Strategy

```python
# Standardized error response
{
    "detail": "Human-readable message",
    "code": "ERROR_CODE",
    "timestamp": "ISO-8601",
    "request_id": "uuid"
}
```

HTTP Status Codes:
- `200`: Success
- `400`: Bad Request (validation)
- `401`: Unauthorized (auth)
- `403`: Forbidden (permissions)
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error
- `503`: Service Unavailable

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-sdk)
- [Gemini API](https://ai.google.dev/)
- [Pydantic](https://docs.pydantic.dev/)
