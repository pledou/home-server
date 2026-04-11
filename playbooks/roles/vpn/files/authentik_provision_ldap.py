#!/usr/bin/env python3
"""Authentik LDAP provisioning — VPN role.

Idempotent: creates objects only when absent.
Outputs a single JSON line on stdout with all PKs needed by Ansible.
Verbose API trace goes to stderr when DEBUG=1 (or Ansible -vv sets it).

Exit codes:
  0  success
  1  API / runtime error
  2  missing required environment variable

Required env vars:
  AUTHENTIK_BASE            authentik_api_base_url
  AUTHENTIK_TOKEN           authentik_api_token
  AUTHENTIK_VERIFY_CERTS    true/false (default true)
  SA_NAME                   vpn_authentik_ldap_service_account_name
  SA_PASSWORD               vpn_authentik_ldap_bind_password
  BIND_FLOW_NAME            vpn_authentik_ldap_bind_flow_name
  BIND_FLOW_TITLE           vpn_authentik_ldap_bind_flow_title
  BIND_FLOW_SLUG            vpn_authentik_ldap_bind_flow_slug
  BIND_ID_STAGE_NAME        vpn_authentik_ldap_bind_identification_stage_name
  BIND_PW_STAGE_NAME        vpn_authentik_ldap_bind_password_stage_name
  BIND_LOGIN_STAGE_NAME     vpn_authentik_ldap_bind_login_stage_name
  PROVIDER_NAME             vpn_authentik_ldap_provider_name
  BASE_DN                   vpn_authentik_ldap_base_dn
  APP_NAME                  vpn_authentik_ldap_application_name
  APP_SLUG                  vpn_authentik_ldap_application_slug
  OUTPOST_NAME              vpn_authentik_ldap_outpost_name
  OUTPOST_TOKEN_SEED        vpn_authentik_ldap_outpost_token
  ACCESS_GROUP              vpn_authentik_access_group
"""

import hashlib
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DEBUG: bool = os.environ.get("DEBUG", "0") == "1"


def dbg(msg: str) -> None:
    if DEBUG:
        print(f"[DEBUG] {msg}", file=sys.stderr)


def info(msg: str) -> None:
    print(f"[INFO]  {msg}", file=sys.stderr)


def die(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def require(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        print(f"[ERROR] Required env var {name} is not set", file=sys.stderr)
        sys.exit(2)
    return val


def bool_env(name: str, default: bool = True) -> bool:
    return os.environ.get(name, "true" if default else "false").lower() not in ("false", "0", "no")


_noverify_ctx: Optional[ssl.SSLContext] = None


def ssl_ctx(verify: bool) -> Optional[ssl.SSLContext]:
    global _noverify_ctx
    if verify:
        return None
    if _noverify_ctx is None:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        _noverify_ctx = ctx
    return _noverify_ctx


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

class API:
    def __init__(self, base: str, token: str, verify: bool) -> None:
        self.base = base.rstrip("/")
        self.token = token
        self.verify = verify
        self.changed = False

    def _call(self, method: str, path: str,
              body: Optional[Dict] = None,
              ok: Tuple[int, ...] = (200,)) -> Tuple[Any, int]:
        url = f"{self.base}{path}"
        data = json.dumps(body).encode() if body is not None else None
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }
        if data:
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        dbg(f"{method} {url}" + (f"  ← {json.dumps(body)[:300]}" if body else ""))

        try:
            resp = urllib.request.urlopen(req, context=ssl_ctx(self.verify))
            text = resp.read().decode()
            parsed: Any = json.loads(text) if text.strip() else {}
            dbg(f"  → {resp.status}  {text[:300]}")
            if resp.status not in ok:
                die(f"Unexpected HTTP {resp.status} for {method} {url}")
            return parsed, resp.status

        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode()
            die(f"HTTP {exc.code} for {method} {url}: {body_text}")
            return {}, exc.code  # never reached, silences type checker

    def get(self, path: str) -> Dict:
        data, _ = self._call("GET", path)
        return data

    def post(self, path: str, body: Dict,
             ok: Tuple[int, ...] = (200, 201)) -> Tuple[Dict, int]:
        data, status = self._call("POST", path, body, ok=ok)
        return data, status

    def patch(self, path: str, body: Dict) -> Dict:
        data, _ = self._call("PATCH", path, body, ok=(200,))
        return data

    def find(self, list_path: str, field: str, value: Any) -> Optional[Dict]:
        """Return the first result where result[field] == value, or None."""
        data = self.get(list_path)
        for r in data.get("results", []):
            if str(r.get(field)) == str(value):
                return r
        return None

    def ensure(self, list_path: str, match_field: str, match_value: Any,
               create_path: str, create_body: Dict,
               ok: Tuple[int, ...] = (200, 201)) -> Dict:
        """Get-or-create: find by match_field==match_value, create if absent."""
        existing = self.find(list_path, match_field, match_value)
        if existing:
            dbg(f"  [exists] {match_value}")
            return existing
        info(f"Creating: {match_value}")
        self.post(create_path, create_body, ok=ok)
        self.changed = True
        found = self.find(list_path, match_field, match_value)
        if not found:
            die(f"Object not found after creation: {match_value} in {list_path}")
        return found


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    base     = require("AUTHENTIK_BASE")
    token    = require("AUTHENTIK_TOKEN")
    verify   = bool_env("AUTHENTIK_VERIFY_CERTS", default=True)

    sa_name  = require("SA_NAME")
    sa_pass  = require("SA_PASSWORD")

    bf_name  = require("BIND_FLOW_NAME")
    bf_title = require("BIND_FLOW_TITLE")
    bf_slug  = require("BIND_FLOW_SLUG")
    id_stage = require("BIND_ID_STAGE_NAME")
    pw_stage = require("BIND_PW_STAGE_NAME")
    ln_stage = require("BIND_LOGIN_STAGE_NAME")

    prov_name = require("PROVIDER_NAME")
    base_dn   = require("BASE_DN")

    app_name  = require("APP_NAME")
    app_slug  = require("APP_SLUG")

    out_name  = require("OUTPOST_NAME")
    out_seed  = require("OUTPOST_TOKEN_SEED")

    grp_name  = require("ACCESS_GROUP")

    ak = API(base, token, verify)

    # ------------------------------------------------------------------
    # Wait for API
    # ------------------------------------------------------------------
    info("Waiting for Authentik API…")
    for attempt in range(10):
        try:
            ak.get("/api/v3/admin/version/")
            break
        except SystemExit:
            if attempt == 9:
                die("Authentik API not reachable after 10 attempts")
            dbg(f"  retry {attempt + 1}/10 in 30 s")
            time.sleep(30)

    # ------------------------------------------------------------------
    # 1. Service account + password
    # ------------------------------------------------------------------
    info(f"Service account: {sa_name}")
    sa = ak.ensure(
        f"/api/v3/core/users/?username={urllib.parse.quote(sa_name)}",
        "username", sa_name,
        "/api/v3/core/users/service_account/",
        {"name": sa_name, "create_group": False, "expiring": False},
        ok=(200, 201),
    )
    sa_pk = sa["pk"]
    ak._call("POST", f"/api/v3/core/users/{sa_pk}/set_password/",
             {"password": sa_pass}, ok=(200, 204))

    # ------------------------------------------------------------------
    # 2. Default system flows
    # ------------------------------------------------------------------
    info("Looking up system flows…")
    auth_flow = ak.find(
        "/api/v3/flows/instances/?slug=default-provider-authorization-implicit-consent",
        "slug", "default-provider-authorization-implicit-consent",
    )
    if not auth_flow:
        die("Default authorization flow 'default-provider-authorization-implicit-consent' not found")
    auth_flow_pk = auth_flow["pk"]

    inv_flow = ak.find(
        "/api/v3/flows/instances/?slug=default-provider-invalidation-flow",
        "slug", "default-provider-invalidation-flow",
    )
    if not inv_flow:
        die("Default invalidation flow 'default-provider-invalidation-flow' not found")
    inv_flow_pk = inv_flow["pk"]

    # ------------------------------------------------------------------
    # 3. Dedicated LDAP bind flow
    # ------------------------------------------------------------------
    info(f"Bind flow: {bf_slug}")
    bind_flow = ak.ensure(
        f"/api/v3/flows/instances/?slug={urllib.parse.quote(bf_slug)}",
        "slug", bf_slug,
        "/api/v3/flows/instances/",
        {"name": bf_name, "title": bf_title, "slug": bf_slug,
         "designation": "authentication", "layout": "stacked",
         "compatibility_mode": False, "denied_action": "message",
         "authentication": "none"},
    )
    bind_flow_pk = bind_flow["pk"]

    # Stages
    info(f"Identification stage: {id_stage}")
    id_st = ak.ensure(
        f"/api/v3/stages/identification/?name={urllib.parse.quote(id_stage)}",
        "name", id_stage,
        "/api/v3/stages/identification/",
        {"name": id_stage, "user_fields": ["username"],
         "case_insensitive_matching": True, "show_matched_user": False,
         "pretend_user_exists": False, "enable_remember_me": False},
    )
    id_st_pk = id_st["pk"]

    info(f"Password stage: {pw_stage}")
    pw_st = ak.ensure(
        f"/api/v3/stages/password/?name={urllib.parse.quote(pw_stage)}",
        "name", pw_stage,
        "/api/v3/stages/password/",
        {"name": pw_stage, "backends": ["authentik.core.auth.InbuiltBackend"],
         "failed_attempts_before_cancel": 5, "allow_show_password": False},
    )
    pw_st_pk = pw_st["pk"]

    info(f"User-login stage: {ln_stage}")
    ln_st = ak.ensure(
        f"/api/v3/stages/user_login/?name={urllib.parse.quote(ln_stage)}",
        "name", ln_stage,
        "/api/v3/stages/user_login/",
        {"name": ln_stage},
    )
    ln_st_pk = ln_st["pk"]

    # Stage → flow bindings
    info("Binding stages to flow…")
    existing_bindings = ak.get(f"/api/v3/flows/bindings/?target={bind_flow_pk}")
    bound: Set[str] = {str(b["stage"]) for b in existing_bindings.get("results", [])}
    for st_pk, order in [(id_st_pk, 10), (pw_st_pk, 20), (ln_st_pk, 30)]:
        if str(st_pk) not in bound:
            ak.post("/api/v3/flows/bindings/",
                    {"target": bind_flow_pk, "stage": st_pk, "order": order,
                     "evaluate_on_plan": False, "re_evaluate_policies": True,
                     "invalid_response_action": "retry"})
            ak.changed = True

    # ------------------------------------------------------------------
    # 4. LDAP provider
    # ------------------------------------------------------------------
    info(f"LDAP provider: {prov_name}")
    provider = ak.ensure(
        f"/api/v3/providers/ldap/?name={urllib.parse.quote(prov_name)}",
        "name", prov_name,
        "/api/v3/providers/ldap/",
        {"name": prov_name, "authentication_flow": bind_flow_pk,
         "authorization_flow": bind_flow_pk, "invalidation_flow": inv_flow_pk,
         "base_dn": base_dn, "bind_mode": "direct", "search_mode": "direct",
         "mfa_support": False},
    )

    # LDAP outpost resolves bind flow from authorization_flow.
    # Reconcile existing providers created with older values.
    provider_patch: Dict[str, Any] = {}
    if str(provider.get("authorization_flow")) != str(bind_flow_pk):
        provider_patch["authorization_flow"] = bind_flow_pk
    if str(provider.get("authentication_flow")) != str(bind_flow_pk):
        provider_patch["authentication_flow"] = bind_flow_pk
    if provider_patch:
        info("Updating LDAP provider flow bindings…")
        ak.patch(f"/api/v3/providers/ldap/{provider['pk']}/", provider_patch)
        ak.changed = True
        provider = ak.get(f"/api/v3/providers/ldap/{provider['pk']}/")
    prov_pk = provider["pk"]

    # ------------------------------------------------------------------
    # 5. LDAP application
    # ------------------------------------------------------------------
    info(f"LDAP application: {app_slug}")
    app = ak.ensure(
        f"/api/v3/core/applications/?slug={urllib.parse.quote(app_slug)}",
        "slug", app_slug,
        "/api/v3/core/applications/",
        {"name": app_name, "slug": app_slug, "provider": int(prov_pk),
         "policy_engine_mode": "any"},
    )
    app_pk = app["pk"]

    prov_check = ak.find(
        f"/api/v3/providers/ldap/?name={urllib.parse.quote(prov_name)}",
        "name", prov_name,
    )
    if not (prov_check or {}).get("assigned_application_slug"):
        die("LDAP provider has no assigned application after app creation")

    # ------------------------------------------------------------------
    # 6. LDAP outpost
    # ------------------------------------------------------------------
    info(f"LDAP outpost: {out_name}")
    out_defaults = ak.get("/api/v3/outposts/instances/default_settings/")
    outpost = ak.ensure(
        f"/api/v3/outposts/instances/?name__iexact={urllib.parse.quote(out_name)}",
        "name", out_name,
        "/api/v3/outposts/instances/",
        {"name": out_name, "type": "ldap", "providers": [int(prov_pk)],
         "service_connection": None, "config": out_defaults.get("config", {})},
    )
    outpost_pk = outpost["pk"]
    outpost_uuid_hex = outpost_pk.replace("-", "")

    # Ensure provider is attached (idempotent)
    current_providers: List[int] = [int(p) for p in outpost.get("providers", [])]
    if int(prov_pk) not in current_providers:
        ak.patch(f"/api/v3/outposts/instances/{outpost_pk}/",
                 {"providers": list(set(current_providers) | {int(prov_pk)})})
        ak.changed = True

    # Token
    runtime_token = hashlib.sha256(f"{out_seed}:{outpost_pk}".encode()).hexdigest()
    token_identifier: str = outpost.get("token_identifier", "")

    info(f"Waiting for outpost token '{token_identifier}'…")
    tok_data: Dict = {}
    for attempt in range(10):
        tok_data = ak.get(f"/api/v3/core/tokens/?identifier={urllib.parse.quote(token_identifier)}")
        if tok_data.get("results"):
            break
        dbg(f"  retry {attempt + 1}/10 in 2 s")
        time.sleep(2)
    else:
        die(f"Outpost token '{token_identifier}' not auto-generated after wait")

    ak._call("POST",
             f"/api/v3/core/tokens/{urllib.parse.quote(token_identifier)}/set_key/",
             {"key": runtime_token}, ok=(200, 204))

    # ------------------------------------------------------------------
    # 7. Access group + policy bindings
    # ------------------------------------------------------------------
    info(f"Access group: {grp_name}")
    group = ak.ensure(
        f"/api/v3/core/groups/?name={urllib.parse.quote(grp_name)}",
        "name", grp_name,
        "/api/v3/core/groups/",
        {"name": grp_name, "is_superuser": False},
    )
    grp_pk = group["pk"]

    info("Policy bindings…")
    if not ak.find(f"/api/v3/policies/bindings/?target={app_pk}&group={grp_pk}",
                   "group", grp_pk):
        ak.post("/api/v3/policies/bindings/",
                {"target": app_pk, "group": grp_pk, "enabled": True, "order": 0})
        ak.changed = True

    if not ak.find(f"/api/v3/policies/bindings/?target={app_pk}&user={sa_pk}",
                   "user", sa_pk):
        ak.post("/api/v3/policies/bindings/",
                {"target": app_pk, "user": sa_pk, "enabled": True, "order": 0})
        ak.changed = True

    # ------------------------------------------------------------------
    # Output facts for Ansible
    # ------------------------------------------------------------------
    print(json.dumps({
        "changed": ak.changed,
        "service_account_pk": sa_pk,
        "bind_flow_pk": bind_flow_pk,
        "provider_pk": prov_pk,
        "app_pk": app_pk,
        "outpost_pk": outpost_pk,
        "outpost_uuid_hex": outpost_uuid_hex,
        "outpost_token_identifier": token_identifier,
        "runtime_token": runtime_token,
    }))


if __name__ == "__main__":
    main()
