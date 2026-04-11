# VPN Role

IKEv2/EAP-RADIUS VPN using **strongSwan** + **FreeRADIUS** + **Authentik LDAP outpost**.

## Architecture

```
iOS / macOS / Windows / Linux client
        │  IKEv2 EAP-RADIUS (UDP 500/4500)
        ▼
   strongSwan ──RADIUS──▶ FreeRADIUS ──LDAP──▶ Authentik LDAP outpost
                                                        │
                                               Authentik user store
```

Authentication flow:
1. Client initiates IKEv2 with EAP credentials (username + password).
2. strongSwan forwards credentials to FreeRADIUS via RADIUS.
3. FreeRADIUS performs an LDAP bind against the Authentik LDAP outpost.
4. Authentik grants or denies the bind based on user credentials **and group membership**.

## Granting a user VPN access

Add the user to the **`vpn-users`** group in Authentik:

**Authentik UI:** Directory → Groups → `vpn-users` → Add member

**Authentik API:**
```bash
# 1. Get user PK
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://auth.example.com/api/v3/core/users/?username=alice" | jq '.results[0].pk'

# 2. Add user to group (replace GROUP_PK and USER_PK)
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"pk": USER_PK}' \
  "https://auth.example.com/api/v3/core/groups/GROUP_PK/add_user/"
```

The group and its policy binding on the `vpn-ldap` Authentik application are
created automatically when the role is deployed (`--tags vpn`).

## Removing VPN access

Remove the user from the `vpn-users` group. Active IKEv2 sessions are not
terminated immediately; they will fail to re-authenticate on rekeying (default
every ~1 h).

## Key variables (`defaults/main.yml`)

| Variable | Default | Description |
|---|---|---|
| `vpn_server_address` | `{{ app_domain_name }}` | Public hostname clients connect to |
| `vpn_client_pool` | `10.8.0.0/24` | Virtual IP pool for clients |
| `vpn_authentik_access_group` | `vpn-users` | Authentik group that grants VPN access |
| `vpn_authentik_ldap_outpost_name` | `vpn-ldap-outpost` | Authentik LDAP outpost name |
| `vpn_use_traefik_cert` | `true` | Reuse Traefik Let's Encrypt cert for IKEv2 |

## Secrets (vault-encrypted in `group_vars`)

| Variable | Description |
|---|---|
| `vpn_radius_secret` | Shared secret between strongSwan and FreeRADIUS (auto-generated) |
| `vpn_authentik_ldap_bind_password` | Password for the Authentik LDAP service account (auto-generated) |
| `vpn_authentik_ldap_outpost_token` | Token key for the Authentik LDAP outpost container (auto-generated) |

## Deployment

```bash
ansible-playbook -i inventories/inventory.yml playbooks/install.yml \
  --tags vpn --ask-vault-pass
```

## Client setup (IKEv2 EAP-MSCHAPv2)

| Field | Value |
|---|---|
| Server | value of `vpn_server_address` |
| VPN type | IKEv2 |
| Authentication | Username + Password (EAP-MSCHAPv2) |
| Certificate | Server cert is the domain's Let's Encrypt cert — trust the CA, no custom cert needed |
