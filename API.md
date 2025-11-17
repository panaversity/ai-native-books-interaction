# API Documentation

Comprehensive API reference for the AI Native Books Interaction service.

## Base URL

**Development**: `http://localhost:8000`  
**Production**: `https://api.yourdomain.com`

## Authentication

Currently using dummy token authentication. Production will use OAuth2/JWT.

### Getting a Token (Dummy)

```http
POST /api/v1/auth/dummy-login
```

**Response**:
```json
{
  "token": "dummy_token_12345",
  "expires": "session",
  "user": {
    "id": "dummy_user",
    "name": "Anonymous User"
  }
}
```

### Token Verification

```http
GET /api/v1/auth/verify?token=YOUR_TOKEN
```

## API Endpoints

### Health Check

Check API health and configuration status.

```http
GET /health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "content-personalization-api",
  "api_configured": true
}
```

---

### Content Summarization

Generate AI-powered summary of content with Server-Sent Events streaming.

```http
GET /api/v1/summarize?pageId=PAGE_ID&token=TOKEN&content=CONTENT
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pageId` | string | Yes | Unique identifier for the content page |
| `token` | string | Yes | Authentication token |
| `content` | string | Yes | Page content to summarize (min 50 chars) |

#### Request Example

```bash
curl -N "http://localhost:8000/api/v1/summarize?pageId=chapter-1&token=dummy_token_12345&content=Your+long+content+here"
```

#### Response

Server-Sent Events stream:

```
data: {"chunk": "This chapter introduces...", "done": false}

data: {"chunk": " the fundamental concepts of", "done": false}

data: {"chunk": " Python programming.", "done": false}

data: {"chunk": "", "done": true}
```

#### Response Format

Each SSE event contains JSON:

```typescript
{
  chunk: string;    // Summary text chunk
  done: boolean;    // true when complete
  error?: string;   // Error message if failed
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | Success - streaming response |
| 400 | Bad Request - invalid parameters |
| 401 | Unauthorized - missing/invalid token |
| 500 | Internal Server Error |

#### Example (JavaScript)

```javascript
const eventSource = new EventSource(
  `http://localhost:8000/api/v1/summarize?pageId=ch1&token=${token}&content=${encodeURIComponent(content)}`
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.error) {
    console.error('Error:', data.error);
    eventSource.close();
    return;
  }
  
  if (data.done) {
    console.log('Summary complete');
    eventSource.close();
    return;
  }
  
  console.log('Chunk:', data.chunk);
};

eventSource.onerror = (error) => {
  console.error('SSE Error:', error);
  eventSource.close();
};
```

#### Example (Python)

```python
import requests
import json

url = "http://localhost:8000/api/v1/summarize"
params = {
    "pageId": "chapter-1",
    "token": "dummy_token_12345",
    "content": "Your long content here..."
}

response = requests.get(url, params=params, stream=True)

for line in response.iter_lines():
    if line:
        # Remove 'data: ' prefix
        data_str = line.decode('utf-8').replace('data: ', '')
        data = json.loads(data_str)
        
        if data.get('error'):
            print(f"Error: {data['error']}")
            break
        
        if data['done']:
            print("\nSummary complete")
            break
        
        print(data['chunk'], end='', flush=True)
```

---

### Content Personalization

Personalize content based on user profile and learning preferences.

```http
POST /api/v1/personalize
```

#### Request Body

```json
{
  "pageId": "chapter-1",
  "token": "dummy_token_12345",
  "content": "Original content to personalize...",
  "userProfile": {
    "skillLevel": "beginner",
    "learningStyle": "visual",
    "background": "web development",
    "preferences": {
      "exampleDomain": "e-commerce",
      "codeComments": true
    }
  }
}
```

#### Response

Server-Sent Events stream (same format as summarization):

```
data: {"chunk": "For web developers like you...", "done": false}

data: {"chunk": " here's an e-commerce example:", "done": false}

data: {"chunk": "", "done": true}
```

#### Skill Levels

- `beginner`: Simplified explanations, basic examples
- `intermediate`: Standard explanations, practical examples
- `advanced`: Concise explanations, complex examples

#### Learning Styles

- `visual`: Diagrams, charts, visual metaphors
- `hands-on`: Code examples, exercises
- `theoretical`: Concepts, principles, explanations

---

### Profile-Based Login

Login with user profile information.

```http
POST /api/v1/auth/profile-login
```

#### Request Body

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "skillLevel": "intermediate",
  "learningStyle": "hands-on",
  "background": "data science"
}
```

#### Response (200 OK)

```json
{
  "token": "generated_token_xyz",
  "expires": "2024-12-01T12:00:00Z",
  "user": {
    "id": "user_123",
    "name": "John Doe",
    "email": "john@example.com"
  },
  "profile": {
    "skillLevel": "intermediate",
    "learningStyle": "hands-on",
    "background": "data science"
  }
}
```

---

## Error Responses

All errors follow a standard format:

```json
{
  "detail": "Human-readable error message"
}
```

### Common Errors

#### 400 Bad Request

```json
{
  "detail": "Content too short to summarize"
}
```

**Causes**:
- Invalid parameters
- Content length < 50 characters
- Invalid pageId format

#### 401 Unauthorized

```json
{
  "detail": "Missing or invalid authentication token"
}
```

**Causes**:
- Missing token
- Invalid token format
- Expired token (future)

#### 500 Internal Server Error

```json
{
  "detail": "Failed to generate summary: API error"
}
```

**Causes**:
- AI service unavailable
- API key issues
- Internal processing error

---

## Rate Limiting

**Development**: No rate limiting  
**Production**: 
- 10 requests/second per IP
- Burst: 20 requests
- Response header: `X-RateLimit-Remaining`

---

## CORS

Allowed origins configured in environment variables.

**Headers**:
- `Access-Control-Allow-Origin`
- `Access-Control-Allow-Credentials: true`
- `Access-Control-Allow-Methods: *`
- `Access-Control-Allow-Headers: *`

---

## Versioning

Current version: `v1`

API endpoints are prefixed with version:
- `/api/v1/summarize`
- `/api/v1/personalize`

Future versions will maintain backward compatibility for at least 6 months.

---

## OpenAPI/Swagger

Interactive API documentation available at:

**Swagger UI**: `http://localhost:8000/docs`  
**ReDoc**: `http://localhost:8000/redoc`  
**OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## Best Practices

### Handling SSE Streams

1. **Set proper headers**:
   ```javascript
   Accept: text/event-stream
   Cache-Control: no-cache
   ```

2. **Handle connection errors**:
   - Implement reconnection logic
   - Set timeout limits
   - Close connections when done

3. **Parse JSON safely**:
   ```javascript
   try {
     const data = JSON.parse(event.data);
   } catch (e) {
     console.error('Invalid JSON', e);
   }
   ```

### Content Length

- **Minimum**: 50 characters
- **Recommended**: 500-10,000 characters
- **Maximum**: 100,000 characters (for optimal performance)

### Token Management

- Store tokens securely (httpOnly cookies in production)
- Don't expose tokens in URLs (use headers in production)
- Refresh tokens before expiration (future)

### Error Handling

```javascript
async function callAPI() {
  try {
    const response = await fetch(url);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }
    
    return response;
  } catch (error) {
    console.error('API Error:', error.message);
    // Handle error appropriately
  }
}
```

---

## Examples

### Complete Summarization Flow

```javascript
class SummarizationClient {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }
  
  async summarize(pageId, content) {
    const url = new URL(`${this.baseUrl}/api/v1/summarize`);
    url.searchParams.append('pageId', pageId);
    url.searchParams.append('token', this.token);
    url.searchParams.append('content', content);
    
    return new Promise((resolve, reject) => {
      const eventSource = new EventSource(url.toString());
      let summary = '';
      
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.error) {
          eventSource.close();
          reject(new Error(data.error));
          return;
        }
        
        if (data.done) {
          eventSource.close();
          resolve(summary);
          return;
        }
        
        summary += data.chunk;
      };
      
      eventSource.onerror = (error) => {
        eventSource.close();
        reject(error);
      };
    });
  }
}

// Usage
const client = new SummarizationClient('http://localhost:8000', 'dummy_token_12345');

client.summarize('chapter-1', 'Long content here...')
  .then(summary => console.log('Summary:', summary))
  .catch(error => console.error('Error:', error));
```

### TypeScript Types

```typescript
// Request types
interface SummarizeParams {
  pageId: string;
  token: string;
  content: string;
}

interface PersonalizeRequest {
  pageId: string;
  token: string;
  content: string;
  userProfile: UserProfile;
}

interface UserProfile {
  skillLevel: 'beginner' | 'intermediate' | 'advanced';
  learningStyle: 'visual' | 'hands-on' | 'theoretical';
  background: string;
  preferences?: {
    exampleDomain?: string;
    codeComments?: boolean;
  };
}

// Response types
interface SSEChunk {
  chunk: string;
  done: boolean;
  error?: string;
}

interface AuthResponse {
  token: string;
  expires: string;
  user: {
    id: string;
    name: string;
    email?: string;
  };
  profile?: UserProfile;
}
```

---

## Support

- **Documentation**: Check `/docs` endpoint
- **Issues**: GitHub Issues

---

**API Version**: 1.0.0  
**Last Updated**: November 2025
