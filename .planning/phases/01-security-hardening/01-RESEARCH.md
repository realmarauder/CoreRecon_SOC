# Phase 1: Security Hardening - Research

**Researched:** 2026-01-19
**Domain:** API Security, Authentication, Webhook Verification, Rate Limiting
**Confidence:** MEDIUM (some vendor-specific details require validation)

## Summary

This research addresses the six security requirements (SEC-01 through SEC-06) for Phase 1 Security Hardening. The codebase has a working Elastic SIEM webhook with signature verification, but Azure Sentinel and Splunk webhooks lack authentication. The logout endpoint is a no-op, CORS allows all methods/headers, rate limiting is absent, and default credentials can reach production.

**Key findings:**
- Azure Sentinel webhooks from Logic Apps can use SAS query parameters or shared secret headers (API key pattern is recommended)
- Splunk webhook authentication uses `Authorization: Splunk <token>` header format (HEC token pattern)
- JWT revocation with Redis is well-established using JTI claims with TTL matching token expiry
- SlowAPI is the de facto FastAPI rate limiting library with Redis backend support
- CORS should explicitly list methods and headers rather than wildcards
- Startup validation is a simple Pydantic validator or lifespan event check

**Primary recommendation:** Implement all six security controls using the existing Redis infrastructure for token blacklist and rate limiting, following established patterns from the Elastic webhook for signature verification.

---

## SEC-01: Azure Sentinel Webhook Signature Verification

### Background

Azure Sentinel uses Azure Logic Apps for playbook automation. When a Logic App makes outbound HTTP requests (webhooks to external systems like CoreRecon), there is no built-in signature mechanism that Azure adds automatically to outbound requests.

### Authentication Approaches

**Option A: Shared Secret / API Key (RECOMMENDED)**
- Configure Logic App to include a custom header (e.g., `X-Sentinel-Auth-Token`) with a shared secret
- CoreRecon validates the header value against a configured secret
- Simple, effective, and matches the pattern used by Elastic SIEM

**Option B: OAuth 2.0 / Azure AD Token**
- Logic App acquires an Azure AD token for your API
- CoreRecon validates the JWT token using Azure AD public keys
- More complex but provides Azure-native security

**Option C: URL Query Parameter Secret**
- Include secret in webhook URL as query parameter
- Less secure (appears in logs) but simple

### Recommended Implementation

```python
# In app/config.py
sentinel_webhook_secret: Optional[str] = Field(default=None, alias="SENTINEL_WEBHOOK_SECRET")

# In app/api/v1/webhooks.py
@router.post("/sentinel", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def azure_sentinel_webhook(
    request: Request,
    x_sentinel_auth: str = Header(None, alias="X-Sentinel-Auth-Token"),
    db: AsyncSession = Depends(get_db),
):
    # Verify signature/token
    if settings.sentinel_webhook_secret:
        if not x_sentinel_auth or not hmac.compare_digest(
            x_sentinel_auth, settings.sentinel_webhook_secret
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook authentication"
            )
    elif settings.env == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook secret required in production"
        )

    # ... rest of handler
```

### Configuration on Azure Side

1. In Logic App Designer, add an HTTP action
2. Add custom header: `X-Sentinel-Auth-Token: <your-secret>`
3. Store secret in Azure Key Vault and reference it

### Confidence: MEDIUM
- Verified that Logic Apps do not add automatic signatures to outbound requests
- API key pattern is a widely-used approach for webhook authentication
- Specific Azure documentation on outbound webhook security is limited

### Sources
- [Microsoft Docs: Secure Logic Apps](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-securing-a-logic-app)
- [Authenticate Playbooks to Sentinel](https://learn.microsoft.com/en-us/azure/sentinel/automation/authenticate-playbooks-to-sentinel)

---

## SEC-02: Splunk HEC Webhook Signature Verification

### Background

Splunk HTTP Event Collector (HEC) uses token-based authentication. When Splunk sends alert webhooks (not HEC ingest), the authentication mechanism depends on how the webhook is configured.

### Authentication Mechanism

**Splunk Alert Webhook Limitation:**
Native Splunk webhook alert actions do NOT support authentication headers by default. Users must use:
- Third-party apps like "Better Webhooks" for HMAC signatures
- Custom alert actions with authentication
- URL-embedded credentials (not recommended)

**Recommended Approach: HEC Token Pattern**
Since CoreRecon is receiving data FROM Splunk (like HEC does), use the same pattern:
- `Authorization: Splunk <token>` header format
- Validate token against configured secret

### Recommended Implementation

```python
# In app/config.py
splunk_webhook_secret: Optional[str] = Field(default=None, alias="SPLUNK_WEBHOOK_SECRET")

# In app/api/v1/webhooks.py
@router.post("/splunk", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def splunk_webhook(
    request: Request,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    # Verify Splunk HEC-style token
    if settings.splunk_webhook_secret:
        expected_auth = f"Splunk {settings.splunk_webhook_secret}"
        if not authorization or not hmac.compare_digest(
            authorization, expected_auth
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Splunk authentication token"
            )
    elif settings.env == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Splunk webhook token required in production"
        )

    # ... rest of handler
```

### Alternative: HMAC Signature (Better Webhooks pattern)

If using Better Webhooks app or custom solution with HMAC:

```python
import hmac
import hashlib

def verify_splunk_hmac(payload: bytes, signature: str, secret: str, timestamp: str) -> bool:
    """Verify HMAC signature from Splunk Better Webhooks."""
    message = timestamp.encode() + payload
    expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)
```

### Confidence: MEDIUM
- Verified HEC token format from Splunk documentation
- Native webhook limitations confirmed via community forums
- HMAC pattern based on Better Webhooks documentation

### Sources
- [Splunk HEC Token Documentation](https://help.splunk.com/en/splunk-cloud-platform/get-started/get-data-in/10.1.2507/get-data-with-http-event-collector/set-up-and-use-http-event-collector-in-splunk-web)
- [Better Webhooks Documentation](https://betterwebhooks.readthedocs.io/en/latest/alert_action.html)
- [Splunk Community on Webhook Authentication](https://community.splunk.com/t5/Alerting/splunk-alert-webhook-authentication/m-p/700501)

---

## SEC-03: Logout Token Invalidation via Redis Blacklist

### Background

Current logout endpoint does nothing (`pass`). JWTs are stateless, so tokens remain valid until expiry. Need to implement token blacklist using existing Redis infrastructure.

### Standard Pattern: JTI Blacklist

**How it works:**
1. Add unique `jti` (JWT ID) claim to each token using `uuid.uuid4()`
2. On logout, add `jti` to Redis with TTL = remaining token lifetime
3. On each authenticated request, check if `jti` is blacklisted

### Implementation

**1. Update token creation (app/core/security.py):**

```python
import uuid

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    jti = str(uuid.uuid4())

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({
        "exp": expire,
        "jti": jti,
        "iat": datetime.utcnow()
    })

    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
```

**2. Create token blacklist service (app/core/token_blacklist.py):**

```python
import redis.asyncio as redis
from typing import Optional
from app.config import settings

class TokenBlacklist:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.prefix = "token_blacklist:"

    async def init(self, redis_url: str):
        """Initialize Redis connection."""
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.aclose()

    async def blacklist_token(self, jti: str, expires_in: int):
        """Add token JTI to blacklist with TTL."""
        if self.redis:
            await self.redis.setex(
                f"{self.prefix}{jti}",
                expires_in,
                "1"
            )

    async def is_blacklisted(self, jti: str) -> bool:
        """Check if token JTI is blacklisted."""
        if not self.redis:
            return False
        result = await self.redis.exists(f"{self.prefix}{jti}")
        return bool(result)

# Global instance
token_blacklist = TokenBlacklist()
```

**3. Update logout endpoint (app/api/v1/auth.py):**

```python
from app.core.token_blacklist import token_blacklist

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Logout current user by blacklisting their token."""
    token_data = decode_token(token)
    if token_data and token_data.jti and token_data.expires:
        # Calculate remaining TTL
        remaining = int((token_data.expires - datetime.utcnow()).total_seconds())
        if remaining > 0:
            await token_blacklist.blacklist_token(token_data.jti, remaining)
```

**4. Update token validation (app/api/v1/auth.py):**

```python
async def get_current_user(...) -> User:
    # ... existing validation ...

    token_data = decode_token(token)
    if token_data is None or token_data.username is None:
        raise credentials_exception

    # Check blacklist
    if token_data.jti and await token_blacklist.is_blacklisted(token_data.jti):
        raise credentials_exception

    # ... rest of function ...
```

### Redis Persistence Requirement

**CRITICAL:** Configure Redis with disk persistence (AOF or RDB) for production. Without persistence, server restart would re-validate all blacklisted tokens.

```bash
# redis.conf
appendonly yes
appendfsync everysec
```

### Performance Considerations

- Redis `EXISTS` is O(1) - negligible overhead per request
- Use connection pooling (redis-py handles this automatically)
- TTL ensures automatic cleanup - no manual expiration needed

### Confidence: HIGH
- Well-documented pattern used by Flask-JWT-Extended and other libraries
- Redis TTL perfectly matches JWT expiration model
- python-jose supports jti claim natively

### Sources
- [SuperTokens: JWT Blacklist](https://supertokens.com/blog/revoking-access-with-a-jwt-blacklist)
- [Flask-JWT-Extended: Blocklist](https://flask-jwt-extended.readthedocs.io/en/stable/blocklist_and_token_revoking.html)
- [Medium: Revoke JWTs with Redis](https://medium.com/@kodiugos/revoke-jwts-secure-your-api-middleware-redis-in-drf-d8501f1d30ba)
- [redis-py Asyncio Examples](https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html)

---

## SEC-04: Rate Limiting on `/auth/login`

### Background

No rate limiting currently exists. Login endpoints are prime targets for brute force attacks.

### Standard Stack: SlowAPI

SlowAPI is the de facto rate limiting library for FastAPI, built on the `limits` library.

### Installation

```bash
pip install slowapi
```

### Implementation

**1. Configure limiter (app/core/rate_limit.py):**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings

def get_limiter() -> Limiter:
    """Create rate limiter with Redis backend for production."""
    storage_uri = settings.redis_url if settings.env != "development" else None

    return Limiter(
        key_func=get_remote_address,
        storage_uri=storage_uri,
        default_limits=["100/minute"]  # Global default
    )

limiter = get_limiter()
```

**2. Register with FastAPI (app/main.py):**

```python
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.rate_limit import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**3. Apply to login endpoint (app/api/v1/auth.py):**

```python
from app.core.rate_limit import limiter

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # 5 attempts per minute per IP
async def login(
    request: Request,  # Required for slowapi
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
):
    # ... existing implementation ...
```

### Rate Limit Syntax

| Format | Meaning |
|--------|---------|
| `"5/minute"` | 5 requests per minute |
| `"100/hour"` | 100 requests per hour |
| `"1/second"` | 1 request per second |
| `"5/minute;100/hour"` | Multiple limits (both apply) |

### Custom Key Function for User-Based Limits

```python
def get_user_or_ip(request: Request) -> str:
    """Rate limit by user ID if authenticated, otherwise by IP."""
    # Check for Authorization header
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        try:
            token = auth.split(" ")[1]
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
            return f"user:{payload.get('sub')}"
        except:
            pass
    return get_remote_address(request)
```

### Production Configuration

```python
# Redis backend for distributed rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379/1",  # Use different DB than blacklist
    strategy="moving-window"  # More accurate than fixed-window
)
```

### Response Headers

SlowAPI automatically adds headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

### Confidence: HIGH
- SlowAPI is widely used and well-documented
- Redis backend verified to work with FastAPI
- Rate limit syntax is standard from `limits` library

### Sources
- [SlowAPI Documentation](https://slowapi.readthedocs.io/en/latest/)
- [SlowAPI GitHub](https://github.com/laurentS/slowapi)
- [FastAPI Rate Limiting Guide](https://python.plainenglish.io/api-rate-limiting-and-abuse-prevention-at-scale-best-practices-with-fastapi-b5d31d690208)

---

## SEC-05: Startup Validation Rejecting Default Credentials

### Background

Config has default values like `"changeme"` that could reach production if environment variables aren't set.

### Implementation Approaches

**Option A: Pydantic Field Validator (RECOMMENDED)**

```python
# In app/config.py
from pydantic import field_validator

class Settings(BaseSettings):
    # ... existing fields ...

    @field_validator("secret_key")
    @classmethod
    def secret_key_not_default(cls, v, info):
        if info.data.get("env") == "production" and "changeme" in v.lower():
            raise ValueError("SECRET_KEY must be changed from default in production")
        return v

    @field_validator("database_url")
    @classmethod
    def database_not_default(cls, v, info):
        if info.data.get("env") == "production" and "changeme" in v:
            raise ValueError("DATABASE_URL password must be changed in production")
        return v

    @field_validator("elasticsearch_password")
    @classmethod
    def es_password_not_default(cls, v, info):
        if info.data.get("env") == "production" and v == "changeme":
            raise ValueError("ELASTICSEARCH_PASSWORD must be changed in production")
        return v
```

**Option B: Startup Event Check**

```python
# In app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation
    if settings.env == "production":
        defaults = ["changeme", "default", "secret"]

        if any(d in settings.secret_key.lower() for d in defaults):
            raise RuntimeError("SECRET_KEY contains default value - cannot start in production")

        if any(d in settings.database_url.lower() for d in defaults):
            raise RuntimeError("DATABASE_URL contains default credentials")

        if settings.elasticsearch_password in defaults:
            raise RuntimeError("ELASTICSEARCH_PASSWORD is a default value")

    # ... rest of startup ...
    yield
    # ... shutdown ...
```

**Option C: Comprehensive Validation Function**

```python
# In app/core/startup.py
def validate_production_config(settings: Settings) -> list[str]:
    """Validate configuration for production deployment."""
    errors = []

    if settings.env != "production":
        return errors

    # Check for default/weak values
    weak_patterns = ["changeme", "default", "secret", "password", "test", "dev"]

    checks = [
        ("SECRET_KEY", settings.secret_key),
        ("DATABASE_URL", settings.database_url),
        ("ELASTICSEARCH_PASSWORD", settings.elasticsearch_password),
    ]

    for name, value in checks:
        if any(pattern in value.lower() for pattern in weak_patterns):
            errors.append(f"{name} contains weak/default value")

    # Check minimum secret key length
    if len(settings.secret_key) < 32:
        errors.append("SECRET_KEY should be at least 32 characters")

    # Check required webhook secrets
    if not settings.elastic_siem_webhook_secret:
        errors.append("ELASTIC_SIEM_WEBHOOK_SECRET not configured")

    return errors

# Usage in lifespan
errors = validate_production_config(settings)
if errors:
    raise RuntimeError(f"Production configuration errors: {'; '.join(errors)}")
```

### Recommended Approach

Use Option C (comprehensive validation function) because:
1. Clear error messages listing all problems
2. Easy to extend with new checks
3. Can be unit tested
4. Runs early in startup before any connections

### Confidence: HIGH
- Standard pattern for production applications
- Pydantic validators are well-documented
- FastAPI lifespan events provide clean startup hook

### Sources
- [FastAPI Settings](https://fastapi.tiangolo.com/advanced/settings/)
- [FastAPI Production Checklist](https://www.compilenrun.com/docs/framework/fastapi/fastapi-best-practices/fastapi-production-checklist/)

---

## SEC-06: Restrict CORS to Explicit Methods and Headers

### Background

Current CORS allows all methods (`["*"]`) and all headers (`["*"]`). This is overly permissive.

### Current Configuration (app/main.py)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],  # Too permissive
    allow_headers=["*"],  # Too permissive
)
```

### Required Methods and Headers for CoreRecon SOC

**Methods needed:**
- `GET` - Read alerts, incidents, dashboard data
- `POST` - Create resources, login, webhooks
- `PUT` - Update resources
- `PATCH` - Partial updates (status changes)
- `DELETE` - Delete resources
- `OPTIONS` - Preflight requests (automatic)

**Headers needed:**
- `Authorization` - JWT Bearer token
- `Content-Type` - Request body type (application/json)
- `Accept` - Response type negotiation
- `X-Requested-With` - AJAX detection (optional)

### Recommended Configuration

```python
# In app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=[
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
    max_age=600,  # Cache preflight for 10 minutes
)
```

### Configuration Settings (app/config.py)

```python
# CORS
cors_origins: list[str] = Field(
    default=["http://localhost:3000"],
    alias="CORS_ORIGINS"
)
cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")
cors_allowed_methods: list[str] = Field(
    default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    alias="CORS_ALLOWED_METHODS"
)
cors_allowed_headers: list[str] = Field(
    default=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    alias="CORS_ALLOWED_HEADERS"
)
```

### Important Notes

1. **Middleware Order:** CORS middleware should be added first so error responses also have CORS headers
2. **Credentials + Origins:** When `allow_credentials=True`, cannot use `allow_origins=["*"]`
3. **Preflight Caching:** `max_age` reduces preflight requests

### Confidence: HIGH
- CORS configuration is well-documented in FastAPI
- Methods and headers based on actual API usage analysis
- Standard security practice

### Sources
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [FastAPI Security Best Practices](https://blog.greeden.me/en/2025/07/29/fastapi-security-best-practices-from-authentication-authorization-to-cors/)

---

## Standard Stack

### Core Libraries

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| `slowapi` | >=0.1.9 | Rate limiting | Add to requirements |
| `redis` | >=5.2.0 | Token blacklist, rate limit storage | Already installed |
| `python-jose` | >=3.3.0 | JWT with jti claim | Already installed |

### No New Dependencies Needed

The security hardening can be implemented with:
- `slowapi` (new - small footprint)
- Existing `redis` async client
- Existing `python-jose` library
- Existing `hmac`/`hashlib` stdlib modules

### Installation

```bash
pip install slowapi>=0.1.9
```

---

## Architecture Patterns

### File Structure for New Code

```
app/
├── core/
│   ├── security.py          # Update: add jti to tokens
│   ├── token_blacklist.py   # New: Redis blacklist service
│   ├── rate_limit.py        # New: SlowAPI configuration
│   └── startup.py           # New: Production validation
├── api/v1/
│   ├── auth.py              # Update: blacklist check, rate limit
│   └── webhooks.py          # Update: Sentinel/Splunk auth
├── config.py                # Update: new settings, validators
└── main.py                  # Update: CORS, middleware, lifespan
```

### Pattern: Service Singleton with Async Init

```python
# Pattern for token_blacklist
class TokenBlacklist:
    def __init__(self):
        self.redis = None

    async def init(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def close(self):
        if self.redis:
            await self.redis.aclose()

token_blacklist = TokenBlacklist()  # Module-level singleton

# Initialize in lifespan
async with lifespan(app):
    await token_blacklist.init(settings.redis_url)
    yield
    await token_blacklist.close()
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Rate limiting | Custom counter middleware | SlowAPI | Handles distributed state, algorithms, headers |
| UUID generation | Custom ID scheme | `uuid.uuid4()` | Cryptographically random, collision-resistant |
| Time-safe comparison | `==` operator | `hmac.compare_digest()` | Prevents timing attacks |
| Token blacklist | Custom DB table | Redis with TTL | Auto-expiration, fast lookups, existing infra |

---

## Common Pitfalls

### Pitfall 1: Timing Attacks on Signature Verification

**What goes wrong:** Using `==` to compare signatures exposes timing information
**Why it happens:** String comparison short-circuits on first difference
**How to avoid:** Always use `hmac.compare_digest(a, b)` for security comparisons
**Warning signs:** Direct string comparison in signature verification code

### Pitfall 2: Missing Redis Persistence for Token Blacklist

**What goes wrong:** Server restart re-validates all blacklisted tokens
**Why it happens:** Redis defaults to in-memory only
**How to avoid:** Enable AOF or RDB persistence in Redis config
**Warning signs:** Security gaps after deployments or restarts

### Pitfall 3: Rate Limiter Without Request Parameter

**What goes wrong:** SlowAPI silently fails or raises cryptic errors
**Why it happens:** SlowAPI needs the `Request` object to extract client IP
**How to avoid:** Always include `request: Request` in rate-limited endpoint parameters
**Warning signs:** Rate limits not being enforced

### Pitfall 4: CORS Middleware Order

**What goes wrong:** Error responses don't have CORS headers
**Why it happens:** Middleware runs in order; if auth fails before CORS, no headers added
**How to avoid:** Add CORS middleware first (before auth middleware)
**Warning signs:** Browser shows CORS error instead of actual API error

### Pitfall 5: Webhook Secret in URL Query Parameters

**What goes wrong:** Secrets appear in logs, browser history, referrer headers
**Why it happens:** Query parameters are not treated as sensitive
**How to avoid:** Use HTTP headers for secrets, never URL parameters
**Warning signs:** Secrets visible in access logs or monitoring tools

---

## Code Examples

### Verified Signature Verification Pattern

```python
# From existing app/api/v1/webhooks.py - Elastic SIEM (correct pattern)
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    if not secret:
        logger.warning("Webhook secret not configured")
        return True

    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)
```

### Redis Async Operations

```python
# Source: redis-py documentation
import redis.asyncio as redis

# Connection
client = redis.from_url("redis://localhost:6379/0", decode_responses=True)

# Set with TTL
await client.setex("key", 3600, "value")  # Expires in 1 hour

# Check existence
exists = await client.exists("key")

# Delete
await client.delete("key")

# Cleanup
await client.aclose()
```

### SlowAPI Rate Limiting

```python
# Source: SlowAPI documentation
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379/1"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    pass
```

---

## Dependencies and Prerequisites

### Required Before Implementation

1. **Redis must be running** - Already deployed per STACK.md
2. **Redis persistence configured** - Verify AOF/RDB is enabled
3. **Environment variables prepared** - New webhook secrets needed

### New Environment Variables

```bash
# Add to .env.example
SENTINEL_WEBHOOK_SECRET=    # Required in production
SPLUNK_WEBHOOK_SECRET=      # Required in production
CORS_ALLOWED_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS
CORS_ALLOWED_HEADERS=Authorization,Content-Type,Accept,Origin,X-Requested-With
```

### Implementation Order

1. **SEC-05** (Startup validation) - Prevents bad deploys, no dependencies
2. **SEC-06** (CORS) - Simple config change, no code dependencies
3. **SEC-03** (Token blacklist) - Requires Redis, needed before auth changes
4. **SEC-04** (Rate limiting) - Requires Redis, can use same connection
5. **SEC-01/02** (Webhooks) - Independent, can be done in parallel

---

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Redis unavailable breaks blacklist | Tokens can't be revoked | Low | Graceful degradation: log warning, allow request |
| Rate limiting locks out legitimate users | Service disruption | Medium | Start conservative (10/min), monitor, adjust |
| Webhook secrets in logs | Credential exposure | Medium | Never log header values, use structured logging |
| Breaking existing integrations | SIEM alerts stop flowing | High | Make auth optional initially, enforce in next release |

### Graceful Degradation Pattern

```python
async def is_blacklisted(self, jti: str) -> bool:
    if not self.redis:
        logger.warning("Token blacklist unavailable - Redis not connected")
        return False  # Fail open
    try:
        return bool(await self.redis.exists(f"{self.prefix}{jti}"))
    except redis.RedisError as e:
        logger.error(f"Token blacklist check failed: {e}")
        return False  # Fail open with logging
```

---

## Open Questions

### 1. Azure Sentinel Exact Payload Format

- **What we know:** General Azure Logic App webhook patterns
- **What's unclear:** Exact JSON structure Sentinel sends
- **Recommendation:** Start implementation, validate with test payload, adjust normalization as needed

### 2. Splunk Webhook Configuration Requirements

- **What we know:** HEC token format, Better Webhooks HMAC pattern
- **What's unclear:** Which Splunk edition/add-on customer uses
- **Recommendation:** Support both simple token and HMAC patterns

### 3. Rate Limit Thresholds

- **What we know:** 5/min is common for login endpoints
- **What's unclear:** Actual traffic patterns for this SOC
- **Recommendation:** Start with 5/min, expose as config, monitor and adjust

---

## Sources

### Primary (HIGH confidence)
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [FastAPI Settings Documentation](https://fastapi.tiangolo.com/advanced/settings/)
- [redis-py Async Examples](https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html)
- [SlowAPI Documentation](https://slowapi.readthedocs.io/en/latest/)
- [Splunk HEC Documentation](https://help.splunk.com/en/splunk-cloud-platform/get-started/get-data-in/10.1.2507/get-data-with-http-event-collector/set-up-and-use-http-event-collector-in-splunk-web)

### Secondary (MEDIUM confidence)
- [Microsoft Logic Apps Security](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-securing-a-logic-app)
- [SuperTokens JWT Blacklist Guide](https://supertokens.com/blog/revoking-access-with-a-jwt-blacklist)
- [Flask-JWT-Extended Blocklist](https://flask-jwt-extended.readthedocs.io/en/stable/blocklist_and_token_revoking.html)

### Tertiary (LOW confidence - validate during implementation)
- Splunk community forums on webhook authentication limitations
- Azure Sentinel outbound webhook specifics (limited official documentation)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - libraries are well-documented and widely used
- Architecture: HIGH - patterns are established FastAPI practices
- Webhook auth (Elastic): HIGH - already implemented in codebase
- Webhook auth (Sentinel/Splunk): MEDIUM - based on vendor docs, needs validation
- Token blacklist: HIGH - well-documented pattern with Redis
- Rate limiting: HIGH - SlowAPI is mature and documented
- CORS: HIGH - FastAPI native feature

**Research date:** 2026-01-19
**Valid until:** 2026-02-19 (30 days - stable domain)
