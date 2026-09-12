r"""
backend/app/integrations/meta_client.py — Official Meta Graph API v21.0 Client.

Implements official Meta OAuth 2.0 and Instagram Professional Content Publishing:
- OAuth dialog URL generation
- Short-lived token exchange
- Long-lived (60-day) token exchange (fb_exchange_token)
- Instagram Business / Creator account discovery via Facebook Pages
- Reels container creation (POST /{ig_user_id}/media)
- Container status polling (GET /{container_id})
- Container publishing (POST /{ig_user_id}/media_publish)
- Content publishing limits & usage monitoring
- Media insights and metrics extraction
- Automatic credential redaction in all logs and error traces
"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from ..core.config import settings

logger = logging.getLogger("autopilot.meta_client")

# Error classification hierarchy
class InstagramClientError(Exception):
    def __init__(self, message: str, code: Optional[int] = None, subcode: Optional[int] = None,
                 error_type: Optional[str] = None, retryable: bool = False):
        super().__init__(message)
        self.message = message
        self.code = code
        self.subcode = subcode
        self.error_type = error_type
        self.retryable = retryable


class InstagramAuthError(InstagramClientError):
    """Token invalid, expired, or revoked (code 190)."""
    def __init__(self, message: str, code: Optional[int] = 190, subcode: Optional[int] = None):
        super().__init__(message, code=code, subcode=subcode, retryable=False)


class InstagramPermissionError(InstagramClientError):
    """Missing required Meta permission or app review approval (code 200)."""
    def __init__(self, message: str, code: Optional[int] = 200, subcode: Optional[int] = None):
        super().__init__(message, code=code, subcode=subcode, retryable=False)


class InstagramMediaError(InstagramClientError):
    """Video format, codec, aspect ratio or duration rejected."""
    def __init__(self, message: str, code: Optional[int] = None, subcode: Optional[int] = None):
        super().__init__(message, code=code, subcode=subcode, retryable=False)


class InstagramRateLimitError(InstagramClientError):
    """User or App rate limit hit (code 4, 17, 9, 2207042)."""
    def __init__(self, message: str, code: Optional[int] = None, subcode: Optional[int] = None):
        super().__init__(message, code=code, subcode=subcode, retryable=True)


class InstagramTransientError(InstagramClientError):
    """Temporary server upload or network failure; safe to retry."""
    def __init__(self, message: str, code: Optional[int] = None, subcode: Optional[int] = None):
        super().__init__(message, code=code, subcode=subcode, retryable=True)


def redact_secrets(text: str) -> str:
    """Redacts access tokens, app secrets, and auth codes from strings."""
    if not text:
        return ""
    # Redact access_token params or values
    text = re.sub(r"(access_token=)[^& \'\"]+", r"\1[REDACTED]", text, flags=re.IGNORECASE)
    text = re.sub(r"(client_secret=)[^& \'\"]+", r"\1[REDACTED]", text, flags=re.IGNORECASE)
    text = re.sub(r"(code=)[^& \'\"]+", r"\1[REDACTED]", text, flags=re.IGNORECASE)
    text = re.sub(r"(Bearer\s+)[A-Za-z0-9_\-\.]+", r"\1[REDACTED]", text, flags=re.IGNORECASE)
    text = re.sub(r"\"access_token\":\s*\"[^\"]+\"", r'"access_token": "[REDACTED]"', text)
    return text


class MetaApiClient:
    """
    Dedicated client for Meta Graph API v21.0.
    All calls are isolated, auditable, and never leak sensitive tokens.
    """

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        api_version: Optional[str] = None,
        base_url: Optional[str] = None,
        oauth_dialog_url: Optional[str] = None
    ):
        self.app_id = app_id or settings.meta_app_id or ""
        self.app_secret = app_secret or settings.meta_app_secret or ""
        self.redirect_uri = redirect_uri or settings.meta_redirect_uri
        self.api_version = api_version or settings.meta_api_version or "v21.0"
        self.base_url = (base_url or settings.meta_graph_base_url or "https://graph.facebook.com").rstrip("/")
        self.oauth_dialog_url = (oauth_dialog_url or settings.meta_oauth_dialog_url or "https://www.facebook.com").rstrip("/")

    # -------------------------------------------------------------------------
    # OAuth 2.0 Protocol
    # -------------------------------------------------------------------------
    def get_authorization_url(self, state: str, redirect_uri: Optional[str] = None) -> str:
        """
        Builds official Meta OAuth 2.0 authorization dialog URL.
        Requests permissions for Instagram Professional Content Publishing.
        """
        r_uri = redirect_uri or self.redirect_uri
        scopes = [
            "instagram_basic",
            "instagram_content_publish",
            "pages_show_list",
            "pages_read_engagement",
            "business_management"
        ]
        params = {
            "client_id": self.app_id,
            "redirect_uri": r_uri,
            "state": state,
            "scope": ",".join(scopes),
            "response_type": "code"
        }
        return f"{self.oauth_dialog_url}/{self.api_version}/dialog/oauth?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """
        Exchanges short-lived authorization code for a user access token.
        """
        r_uri = redirect_uri or self.redirect_uri
        params = {
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "redirect_uri": r_uri,
            "code": code
        }
        return self._http_request(f"/{self.api_version}/oauth/access_token", params=params, method="GET")

    def exchange_long_lived_token(self, short_lived_token: str) -> Dict[str, Any]:
        """
        Exchanges a short-lived token (~1-2h) for a 60-day long-lived token.
        """
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "fb_exchange_token": short_lived_token
        }
        return self._http_request(f"/{self.api_version}/oauth/access_token", params=params, method="GET")

    def get_instagram_accounts(self, user_access_token: str) -> List[Dict[str, Any]]:
        """
        Discovers Instagram Professional accounts linked via Facebook Pages.
        """
        params = {
            "fields": "id,name,access_token,instagram_business_account{id,username,name,profile_picture_url}",
            "access_token": user_access_token
        }
        data = self._http_request(f"/{self.api_version}/me/accounts", params=params, method="GET")
        pages = data.get("data") or []
        discovered_accounts = []

        for page in pages:
            ig_data = page.get("instagram_business_account")
            if ig_data and ig_data.get("id"):
                discovered_accounts.append({
                    "page_id": page.get("id"),
                    "page_name": page.get("name"),
                    "page_access_token": page.get("access_token"),
                    "external_account_id": str(ig_data.get("id")),
                    "username": ig_data.get("username") or "",
                    "display_name": ig_data.get("name") or page.get("name") or "",
                    "profile_image_url": ig_data.get("profile_picture_url") or "",
                    "account_type": "BUSINESS"
                })

        return discovered_accounts

    # -------------------------------------------------------------------------
    # Instagram Account Status & Publishing Limit
    # -------------------------------------------------------------------------
    def get_account_profile(self, ig_user_id: str, access_token: str) -> Dict[str, Any]:
        """Retrieves profile info and account type."""
        params = {
            "fields": "id,username,name,profile_picture_url,followers_count,media_count,account_type",
            "access_token": access_token
        }
        return self._http_request(f"/{self.api_version}/{ig_user_id}", params=params, method="GET")

    def get_publishing_limit(self, ig_user_id: str, access_token: str) -> Dict[str, Any]:
        """
        Queries Meta's official 24h content publishing quota usage.
        """
        params = {
            "fields": "config,quota_usage",
            "access_token": access_token
        }
        res = self._http_request(f"/{self.api_version}/{ig_user_id}/content_publishing_limit", params=params, method="GET")
        data_items = res.get("data") or [{}]
        first = data_items[0] if data_items else {}
        config = first.get("config") or {}
        return {
            "quota_usage": first.get("quota_usage", 0),
            "quota_total": config.get("quota_total", 100),
            "quota_duration": config.get("quota_duration", 86400)
        }

    # -------------------------------------------------------------------------
    # Reel Container & Publishing Operations
    # -------------------------------------------------------------------------
    def create_reels_container(
        self,
        ig_user_id: str,
        video_url: str,
        caption: str,
        access_token: str,
        share_to_feed: bool = True
    ) -> str:
        """
        Step 1: Creates an Instagram Reel media container.
        Meta fetches the video from the public video_url.
        """
        payload = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption[:2200],
            "share_to_feed": "true" if share_to_feed else "false",
            "access_token": access_token
        }
        res = self._http_request(f"/{self.api_version}/{ig_user_id}/media", data=payload, method="POST")
        container_id = res.get("id")
        if not container_id:
            raise InstagramClientError(f"Container ID missing in Meta response: {res}")
        return str(container_id)

    def check_container_status(self, container_id: str, access_token: str) -> Dict[str, Any]:
        """
        Step 2: Polls status of container until FINISHED.
        Returns: {"status_code": "FINISHED"|"IN_PROGRESS"|"ERROR"|"EXPIRED", "status": "..."}
        """
        params = {
            "fields": "status_code,status",
            "access_token": access_token
        }
        res = self._http_request(f"/{self.api_version}/{container_id}", params=params, method="GET")
        return {
            "status_code": res.get("status_code", "UNKNOWN"),
            "status": res.get("status", "")
        }

    def publish_container(self, ig_user_id: str, container_id: str, access_token: str) -> str:
        """
        Step 3: Commits and publishes the ready media container.
        Returns: external_media_id (Instagram Media ID)
        """
        payload = {
            "creation_id": container_id,
            "access_token": access_token
        }
        res = self._http_request(f"/{self.api_version}/{ig_user_id}/media_publish", data=payload, method="POST")
        media_id = res.get("id")
        if not media_id:
            raise InstagramClientError(f"Media ID missing in publish response: {res}")
        return str(media_id)

    def get_media_permalink(self, media_id: str, access_token: str) -> Optional[str]:
        """Fetches permalink for a published Reel."""
        try:
            params = {"fields": "permalink", "access_token": access_token}
            res = self._http_request(f"/{self.api_version}/{media_id}", params=params, method="GET")
            return res.get("permalink")
        except Exception:
            return None

    def get_media_insights(self, media_id: str, access_token: str) -> Dict[str, Any]:
        """
        Fetches insights/analytics for published media.
        """
        params = {
            "metric": "reach,saved,video_views,likes,comments,shares",
            "access_token": access_token
        }
        try:
            res = self._http_request(f"/{self.api_version}/{media_id}/insights", params=params, method="GET")
            metrics = {}
            for item in res.get("data", []):
                name = item.get("name")
                values = item.get("values", [])
                if values and "value" in values[0]:
                    metrics[name] = values[0]["value"]
            return metrics
        except Exception as e:
            logger.warning(f"Failed to fetch insights for media {media_id}: {redact_secrets(str(e))}")
            return {}

    # -------------------------------------------------------------------------
    # Internal HTTP Request Dispatcher & Error Normalization
    # -------------------------------------------------------------------------
    def _http_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        method: str = "GET"
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        query_str = f"?{urllib.parse.urlencode(params)}" if params else ""
        full_url = f"{url}{query_str}"
        body_bytes = urllib.parse.urlencode(data).encode("utf-8") if data is not None else None

        req = urllib.request.Request(
            full_url,
            data=body_bytes,
            method=method,
            headers={"User-Agent": "AUTOPILOT-SaaS/1.0"}
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8") or "{}")
                # Parse rate limit headers
                app_usage = response.headers.get("X-App-Usage")
                if app_usage:
                    try:
                        usage_dict = json.loads(app_usage)
                        if usage_dict.get("call_count", 0) > 80:
                            logger.warning(f"Meta App Usage high: {usage_dict}")
                    except Exception:
                        pass
                return payload
        except urllib.error.HTTPError as http_err:
            raw_body = http_err.read().decode("utf-8", errors="replace")
            raise self._parse_meta_error(http_err.code, raw_body) from http_err
        except urllib.error.URLError as url_err:
            raise InstagramTransientError(f"Network error communicating with Meta: {redact_secrets(str(url_err))}") from url_err

    def _parse_meta_error(self, http_code: int, raw_body: str) -> InstagramClientError:
        """Parses Meta Graph API error payload and converts to domain exception."""
        code, subcode, msg, err_type = None, None, raw_body, "UnknownError"
        try:
            err_json = json.loads(raw_body).get("error", {})
            code = err_json.get("code")
            subcode = err_json.get("error_subcode")
            msg = err_json.get("message", raw_body)
            err_type = err_json.get("type", "MetaError")
        except Exception:
            pass

        safe_msg = redact_secrets(msg)
        full_detail = f"Meta API {http_code} [{err_type} code={code} subcode={subcode}]: {safe_msg}"

        # 1. Authentication / Token Expiration
        if code == 190 or http_code == 401:
            return InstagramAuthError(full_detail, code=code, subcode=subcode)

        # 2. Permission Denied
        if code == 200 or http_code == 403:
            return InstagramPermissionError(full_detail, code=code, subcode=subcode)

        # 3. Rate Limits
        if code in (4, 17, 9) or subcode == 2207042 or http_code == 429:
            return InstagramRateLimitError(full_detail, code=code, subcode=subcode)

        # 4. Media Invalidation
        if code == 24 or subcode in (2207026, 2207050):
            return InstagramMediaError(full_detail, code=code, subcode=subcode)

        # 5. Ingestion Server or URL Failures (retryable)
        if subcode in (2207001, 2207052) or http_code in (500, 502, 503, 504):
            return InstagramTransientError(full_detail, code=code, subcode=subcode)

        return InstagramClientError(full_detail, code=code, subcode=subcode, error_type=err_type)
