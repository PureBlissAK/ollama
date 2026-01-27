"""Zero-trust helpers and manager.

Provides a small, testable scaffold for Issue #43 - Zero-Trust Security Framework.

This module contains a `ZeroTrustManager` class with clear extension points
for workload identity, policy enforcement, and audit logging.
"""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Dict, Any, Callable, Optional
import base64
import json

# Optional runtime dependency for OIDC verification
try:
    import jwt  # PyJWT
    from jwt import PyJWKClient
except Exception:  # pragma: no cover - optional dependency
    jwt = None
    PyJWKClient = None
from dataclasses import dataclass
from typing import Any, Callable, Dict


@dataclass
class ZeroTrustConfig:
    """Configuration for ZeroTrustManager."""

    policy_source: str = "iam"
    audit_log_enabled: bool = True


class ZeroTrustManager:
    """Minimal Zero-Trust manager scaffold.

    Responsibilities (initial scope):
    - Validate service-to-service identity tokens
    - Enforce simple RBAC policies
    - Emit audit events (stubbed)

    Extend this class to integrate with Workload Identity providers,
    OIDC token validation libraries, and policy engines (e.g., OPA).
    """

    def __init__(self, config: ZeroTrustConfig | None = None) -> None:
        self.config = config or ZeroTrustConfig()

    def validate_identity(self, token: str) -> Dict[str, Any]:
        """Validate an identity token and return identity claims.

        This is a stub for unit testing and local development. Production
        implementation should validate signatures, issuer, audience, and
        token expiry using a secure OIDC library.
        """
        # Minimal placeholder implementation
        if not token:
            raise ValueError("empty token")

        # Try to decode JWT payload without verification to extract claims.
        try:
            claims = self._decode_jwt_payload(token)
        except Exception:
            # Fall back to test stub claims for non-JWT tokens
            return {"sub": "service:example", "roles": ["service"]}

        # Basic validation checks (issuer/audience/exp should be checked in prod)
        if not isinstance(claims, dict) or "sub" not in claims:
            raise ValueError("invalid token claims")

        return claims

    @staticmethod
    def _decode_jwt_payload(token: str) -> Dict[str, Any]:
        """Decode a JWT payload without verifying signature.

        This helper is intentionally lightweight for local testing. Production
        code MUST validate signatures using a trusted library and JWKS.
        """
        parts = token.split(".")
        if len(parts) < 2:
            raise ValueError("not a JWT")
        payload_b64 = parts[1]
        # Add padding if necessary
        padding = '=' * (-len(payload_b64) % 4)
        payload_b64 += padding
        decoded = base64.urlsafe_b64decode(payload_b64.encode())
        return json.loads(decoded)

    def verify_oidc_token(
        self,
        token: str,
        *,
        key: Optional[str] = None,
        jwks_url: Optional[str] = None,
        audience: Optional[str] = None,
        issuer: Optional[str] = None,
        leeway: int = 60,
    ) -> Dict[str, Any]:
        """Verify an OIDC token and return validated claims.

        Supports either a direct `key` (symmetric or public key material) or a
        `jwks_url` (fetch signing keys). This method requires `PyJWT` to be
        installed; if it's unavailable a RuntimeError is raised.
        """
        if jwt is None:
            raise RuntimeError("PyJWT is required for OIDC verification. Install pyjwt")

        if jwks_url:
            if PyJWKClient is None:
                raise RuntimeError("PyJWKClient is required for JWKS support. Upgrade PyJWT")
            jwk_client = PyJWKClient(jwks_url)
            signing_key = jwk_client.get_signing_key_from_jwt(token).key
            key_to_use = signing_key
        elif key:
            key_to_use = key
        else:
            raise ValueError("Either 'key' or 'jwks_url' must be provided for verification")

        options = {"verify_aud": bool(audience)}
        claims = jwt.decode(
            token,
            key_to_use,
            algorithms=["RS256", "HS256"],
            audience=audience,
            issuer=issuer,
            leeway=leeway,
            options=options,
        )
        return claims

    def enforce_policy(self, identity: Dict[str, Any], resource: str, action: str) -> bool:
        """Enforce a simple RBAC-style policy for the given identity.

        Returns True if the action is allowed, False otherwise.
        """
        # Allow injection of a policy hook for production integration.
        policy_hook: Callable[[Dict[str, Any], str, str], bool] | None = getattr(
            self, "policy_hook", None
        )
        if policy_hook:
            return bool(policy_hook(identity, resource, action))

        roles = identity.get("roles", [])
        # Default allow for 'admin' role
        if "admin" in roles:
            return True
        # Example: services with 'service' role can read resources
        if action == "read" and "service" in roles:
            return True
        return False

    def emit_audit(self, event: Dict[str, Any]) -> None:
        """Emit an audit event. Production should forward to structured logging or audit store."""
        if self.config.audit_log_enabled:
            # In tests, keep this side-effect small.
            print("AUDIT:", event)
