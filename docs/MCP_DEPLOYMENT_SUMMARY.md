# MCP Integration - Deployment Summary (mcpo Architecture)

## ✅ Correct Architecture Chosen: **mcpo (MCP-to-OpenAPI Proxy)**

After reviewing the [official Open WebUI documentation](https://docs.openwebui.com/features/plugin/tools/openapi-servers/mcp/), we're implementing the **recommended stable approach** using `mcpo` instead of direct MCP support.

### Why mcpo is Superior

✅ **Stable & Mature** - OpenAPI is the "preferred integration path" in Open WebUI  
✅ **Better Security** - Standard HTTP auth, HTTPS, API keys, battle-tested  
✅ **Auto-Documentation** - Interactive Swagger/OpenAPI docs at `/docs`  
✅ **Enterprise-Ready** - Works with SSO, API gateways, audit logs, quotas  
✅ **No Protocol Complexity** - Standard REST endpoints instead of stdio/SSE  
✅ **Better Observability** - Standard HTTP tracing, logging, monitoring

### ~~Not Using~~ Direct MCP Support (`ENABLE_MCP_SERVERS`)

Direct MCP support exists but:
- ❌ Only supports "Streamable HTTP" (not stdio)  
- ❌ Still evolving with potential breaking changes  
- ❌ Less mature than OpenAPI integration  
- ❌ Docs explicitly recommend OpenAPI for most deployments

## 📁 What Has Been Implemented

### New Files Created:

1. **`playbooks/roles/ia/templates/mcpo.Dockerfile`**
   - Builds custom image with Python, Node.js, mcpo, and common MCP servers
   - Pre-installs npm MCP packages for faster startup
   - Includes health checks

2. **`playbooks/roles/ia/templates/MCP_MCPO_GUIDE.md`**
   - Comprehensive guide for users
   - Configuration examples for each MCP service
   - Troubleshooting section
   - Security best practices

3. **`playbooks/roles/ia/defaults/main.yml`**
   - `webui_secret_key` - Auto-generated for token encryption (CRITICAL!)
   - `enable_homeassistant_mcp` - Toggle for Home Assistant integration
   - `homeassistant_mcp_token` - Long-lived token storage

### Modified Files:

1. **`playbooks/roles/ia/templates/docker-compose.yml`**
   - ✅ Removed `ENABLE_MCP_SERVERS` (not recommended)
   - ✅ Added `WEBUI_SECRET_KEY` (critical for OAuth/token encryption)
   - ✅ Added mcpo services:
     - `mcpo-memory` - Persistent AI memory
     - `mcpo-filesystem` - Read Open WebUI uploads
     - `mcpo-homeassistant` - Smart home control (optional)
   - ✅ Each service exposes OpenAPI endpoints internally

2. **`playbooks/roles/ia/tasks/main.yml`**
   - ✅ Copies mcpo Dockerfile  
   - ✅ Builds mcpo images
   - ✅ Deploys stack with build step

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────┐
│                  Open WebUI                       │
│            (Admin → External Tools)              │
└──────────────┬───────────────────────────────────┘
               │ OpenAPI REST (http://)
               │
      ┌────────┼─────────────────┬──────────────────┐
      │        │                 │                  │
┌─────▼──────┐ │           ┌─────▼────────┐  ┌─────▼─────────┐
│ mcpo       │ │           │  Nextcloud   │  │ mcpo          │
│ -memory    │ │           │  (per-user)  │  │-homeassistant │
│            │ │           │              │  │               │
│ :8000      │ │           │  :443        │  │ :8000         │
└────┬───────┘ │           └──────┬───────┘  └──────┬────────┘
     │         │                  │                  │
     │   MCP stdio                │ Direct API       │ MCP stdio
     │         │                  │ (Header Auth)   │
 ┌───▼──────┐  │           ┌──────▼─────────┐ ┌─────▼──────────┐
 │ mcp-     │  │           │  Nextcloud     │ │ Home Assistant │
 │ server-  │  │           │  Context Chat  │ │ :8123          │
 │ memory   │  │           │  Backend App   │ │ (host network) │
 └──────────┘  │           └────────────────┘ └────────────────┘
               │
         (All in ia_network)
```

**Key Points:**
- mcpo services expose MCP servers as OpenAPI endpoints
- Nextcloud uses direct API with per-user authentication
- Each user configures their own Nextcloud connection with personal credentials
- No shared secrets for Nextcloud (better security!)

## 🚀 Deployed MCP Services

### 1. Memory MCP (`mcpo-memory`)
- **Purpose**: Persistent AI memory across conversations
- **URL**: `http://mcpo-memory:8000`
- **OpenAPI Schema**: `http://mcpo-memory:8000/openapi.json`
- **Status**: Always enabled

### 2. Nextcloud (Per-User Configuration)
- **Purpose**: Access personal Nextcloud files, calendar, contacts
- **Method**: Per-user mcpo containers (one per user)
- **Authentication**: Handled internally by mcpo container
- **Status**: Deploy per user by adding to `nextcloud_mcp_users` list
- **Benefits**:
  - ✅ Secure (each user has dedicated container with their credentials)
  - ✅ Proper access control (users see only their data)
  - ✅ Works with Open WebUI's auth limitations (None/Bearer/Session/OAuth only)
  - ✅ No custom headers needed

**Why per-user containers?**  
Open WebUI only supports **None**, **Bearer**, **Session**, or **OAuth** authentication - it doesn't support custom headers like `NC-User` or `NC-Password`. Per-user containers handle authentication internally, so Open WebUI just connects with "None".

### 3. Home Assistant MCP (`mcpo-homeassistant`) - Optional
- **Purpose**: Control and query smart home devices
- **URL**: `http://mcpo-homeassistant:8000`
- **OpenAPI Schema**: `http://mcpo-homeassistant:8000/openapi.json`
- **Status**: Deployed only if `enable_homeassistant_mcp: true`

## 🚀 Deployment Steps

### 1. Deploy the Stack

```bash
cd /home/pledo/home-server
ansible-playbook -i inventories/inventory.yml playbooks/install.yml --tags ia
```

This will:
- Build the mcpo Docker image
- Deploy all mcpo services
- Start Open WebUI with proper configuration

### 2. Verify Deployment

```bash
# Check all services are running
docker ps | grep ia-

# Expected output:
# ia-webui-1
# ia-ollama-1  
# ia-speech-1
# ia-mcpo-memory-1
# ia-mcpo-filesystem-1
# ia-mcpo-homeassistant-1  (if enabled)

# Check mcpo service health
docker logs ia-mcpo-memory-1
docker logs ia-mcpo-filesystem-1

# Test OpenAPI endpoints
curl http://localhost:$(docker port ia-mcpo-memory-1 8000 | cut -d: -f2)/docs
```

### 3. Configure in Open WebUI

1. Log into Open WebUI at `https://ia.{{ app_domain_name }}`
2. Go to **⚙️ Admin Settings** → **External Tools**
3. Click **+ (Add Server)**
4. Add each MCP service:

**Memory Service:**
```
Name: AI Memory
Type: OpenAPI
URL: http://mcpo-memory:8000/openapi.json
Authentication: None
```

**Nextcloud Service** (per user with dedicated container):

First, add users to inventory (`inventories/group_vars/all.yml`):
```yaml
nextcloud_mcp_users:
  - username: john
    nextcloud_user: john
    nextcloud_app_password: "xxxxx-xxxxx-xxxxx"
  - username: jane
    nextcloud_user: jane.smith
    nextcloud_app_password: "yyyyy-yyyyy-yyyyy"
```

After deployment, each user configures:
```
Name: My Nextcloud
Type: OpenAPI
URL: http://mcpo-nextcloud-USERNAME:8000/openapi.json
Authentication: None
```

**To get Nextcloud app password:**
1. Nextcloud → Settings → Security → Devices & sessions
2. Create new app password
3. Provide to admin for deployment

**Home Assistant Service** (if enabled):
```
Name: Home Assistant
Type: OpenAPI
URL: http://mcpo-homeassistant:8000/openapi.json
Authentication: None
```

5. Click **Verify Connection** for each
6. Enable the tools you want to use

### 4. Test the Integration

Start a conversation and try:
- **Memory**: "Remember that I prefer detailed explanations"
- **Nextcloud**: "Search my Nextcloud for documents about Ansible"
- **Home Assistant**: "What's the temperature at home?" (if enabled)

## 🔐 Security Configuration

### Critical: WEBUI_SECRET_KEY

The `WEBUI_SECRET_KEY` is **automatically generated** from defaults. This is critical for:
- Encrypting stored API tokens
- OAuth credential persistence
- Multi-restart stability

**Warning**: If this key changes, all encrypted credentials are lost.

### Nextcloud Per-User Credentials

To add Nextcloud users, update your inventory:

```yaml
# inventories/group_vars/all.yml
nextcloud_mcp_users:
  - username: john
    nextcloud_user: john
    nextcloud_app_password: !vault |
      $ANSIBLE_VAULT;1.1;AES256
      ... encrypted password ...
```

**Encrypt with Ansible Vault:**
```bash
ansible-vault encrypt_string 'xxxxx-xxxxx-xxxxx' --name 'nextcloud_app_password'
```

**Add a new user:**
1. User creates Nextcloud app password (Settings → Security)
2. Admin adds to `nextcloud_mcp_users` list
3. Redeploy: `ansible-playbook -i inventories/inventory.yml playbooks/install.yml --tags ia`
4. User configures External Tool in Open WebUI

### Home Assistant Token (Optional)

To enable Home Assistant MCP:

1. **Get token from Home Assistant:**
   - Home Assistant → Your Profile → Security → Long-Lived Access Tokens
   - Create Token → Copy immediately

2. **Store securely in inventory:**
   ```yaml
   # inventories/group_vars/all.yml
   enable_homeassistant_mcp: true
   homeassistant_mcp_token: !vault |
     $ANSIBLE_VAULT;1.1;AES256
     ... encrypted token ...
   ```

3. **Encrypt with Ansible Vault:**
   ```bash
   ansible-vault encrypt_string 'YOUR_HA_TOKEN' --name 'homeassistant_mcp_token'
   ```

4. **Redeploy:**
   ```bash
   ansible-playbook -i inventories/inventory.yml playbooks/install.yml --tags ia
   ```

## 🧪 Testing

### Test mcpo Services

```bash
# Memory service
docker exec ia-webui-1 curl http://mcpo-memory:8000/docs

# Filesystem service
docker exec ia-webui-1 curl http://mcpo-filesystem:8000/docs

# Check OpenAPI schemas
docker exec ia-webui-1 curl http://mcpo-memory:8000/openapi.json | jq '.info'
docker exec ia-webui-1 curl http://mcpo-filesystem:8000/openapi.json | jq '.info'
```

### Test Home Assistant Connectivity (if enabled)

```bash
# From mcpo-homeassistant container
docker exec ia-mcpo-homeassistant-1 curl http://host.docker.internal:8123

# Check token is set
docker exec ia-mcpo-homeassistant-1 env | grep HASS_TOKEN
```

### View Interactive API Docs

```bash
# Get port mappings (if you exposed them)
docker port ia-mcpo-memory-1

# Or access via browser through Open WebUI network
# (These are internal-only by default for security)
```

## 🔧 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker logs ia-mcpo-memory-1
docker logs ia-mcpo-filesystem-1

# Rebuild images
cd ~/home-server/stacks/ia
docker-compose build --no-cache
docker-compose up -d
```

### "Failed to connect" in Open WebUI

1. **Check service is accessible:**
   ```bash
   docker exec ia-webui-1 curl http://mcpo-memory:8000/docs
   ```

2. **Verify OpenAPI schema is valid:**
   ```bash
   docker exec ia-webui-1 curl http://mcpo-memory:8000/openapi.json | jq
   ```

3. **Check External Tool configuration:**
   - Ensure Type is set to **OpenAPI** (not MCP)
   - URL should be internal: `http://mcpo-memory:8000/openapi.json`
   - Authentication should be **None**

### Home Assistant Not Working

1. **Is the service enabled?**
   ```bash
   docker ps | grep mcpo-homeassistant
   ```

2. **Check token:**
   ```bash
   docker exec ia-mcpo-homeassistant-1 env | grep HASS_TOKEN
   ```

3. **Test HA connectivity:**
   ```bash
   docker exec ia-mcpo-homeassistant-1 curl -I http://host.docker.internal:8123
   ```

### Rebuild After Changes

```bash
cd ~/home-server
ansible-playbook -i inventories/inventory.yml playbooks/install.yml --tags ia
```

## 🎯 Next Steps

1. **Deploy** the stack (see step 1 above)
2. **Configure** External Tools in Open WebUI (see step 3 above)
3. **Start simple** - Add Memory tool first
4. **Add more tools** as needed (Filesystem, Home Assistant)
5. **Share guide** with users: `MCP_MCPO_GUIDE.md`

## 🌟 Benefits Summary

| Feature | Direct MCP | mcpo (Our Choice) |
|---------|-----------|-------------------|
| **Stability** | Experimental | Production-ready |
| **Documentation** | Manual | Auto-generated OpenAPI |
| **Security** | Basic | Enterprise (HTTPS, auth, audit) |
| **Integration** | Custom client needed | Standard REST/OpenAPI |
| **Observability** | Limited | Full HTTP tracing |
| **User Experience** | Complex | Familiar REST APIs |
| **Open WebUI Support** | "Still evolving" | "Preferred integration" |

## 📚 References

- **Open WebUI mcpo Guide**: https://docs.openwebui.com/features/plugin/tools/openapi-servers/mcp/
- **Open WebUI MCP Docs**: https://docs.openwebui.com/features/mcp/
- **mcpo GitHub**: https://github.com/open-webui/mcpo
- **MCP Specification**: https://modelcontextprotocol.io/
- **MCP Servers**: https://github.com/modelcontextprotocol/servers

---

**🎉 You're now using the recommended, stable MCP integration approach!**

After deployment, check that MCP servers are installed:

```bash
# Check container logs
docker logs ia-webui-1

# Verify MCP servers are installed
docker exec ia-webui-1 npm list -g | grep modelcontextprotocol

# View quick reference
docker exec ia-webui-1 cat /app/backend/data/mcp-quick-ref.txt

# View available templates
docker exec ia-webui-1 ls -la /app/backend/data/mcp-templates/
```

### 3. Configure MCP Servers (Per User)

Each user can configure their MCP servers:

#### Via Open WebUI Interface:
1. Log into Open WebUI at `https://ia.{{ app_domain_name }}`
2. Go to **Settings** → **Connections** → **Model Context Protocol (MCP)**
3. Click **Add MCP Server**
4. Use templates from `/app/backend/data/mcp-templates/` or create custom configurations

#### For Home Assistant:
```json
{
  "name": "Home Assistant",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-homeassistant"],
  "env": {
    "HASS_URL": "http://host.docker.internal:8123",
    "HASS_TOKEN": "your_long_lived_token"
  }
}
```

**Get Home Assistant token:**
- Home Assistant → Profile → Security → Long-Lived Access Tokens

#### For Nextcloud (Automated):
```bash
# Create app password in Nextcloud first (Settings → Security)
# Then run:
docker exec -it ia-webui-1 /app/backend/data/configure-nextcloud-mcp.sh \
  your_nextcloud_username your_nextcloud_app_password
```

Or manually via UI using the template in `/app/backend/data/mcp-templates/nextcloud.json`

## 📖 Documentation

- **Setup Guide**: Available in container at `/app/backend/data/MCP_SETUP_GUIDE.md`
- **Quick Reference**: Available in container at `/app/backend/data/mcp-quick-ref.txt`
- **Local Copy**: `~/home-server/stacks/ia/MCP_SETUP_GUIDE.md`

## 🔍 Testing MCP Integration

### Test Home Assistant:
```bash
docker exec ia-webui-1 curl http://host.docker.internal:8123
```

### Test Nextcloud:
```bash
docker exec ia-webui-1 curl http://nextcloud-nginx-1:80
```

### Test Network Connectivity:
```bash
# Verify ia_network exists
docker network ls | grep ia_network

# Check which containers are connected
docker network inspect ia_network
```

## 🎯 Usage Examples

Once configured, users can interact naturally:

- **Home Assistant**: "What's the temperature in my living room?"
- **Nextcloud**: "Search my Nextcloud for documents about ansible"
- **Web Fetch**: "Fetch the latest news from example.com"
- **Memory**: "Remember that I prefer Python over JavaScript"
- **Git**: "Show me the recent commits in my repository"

The AI will automatically use the appropriate MCP server to fulfill these requests.

## 🔧 Troubleshooting

### MCP Servers Not Working

1. **Check installation logs:**
   ```bash
   docker logs ia-webui-1 | grep MCP
   ```

2. **Reinstall MCP servers:**
   ```bash
   docker exec ia-webui-1 bash /install-mcp-servers.sh
   ```

3. **Restart container:**
   ```bash
   docker restart ia-webui-1
   ```

### Network Connectivity Issues

```bash
# For Home Assistant
docker exec ia-webui-1 ping host.docker.internal

# For Nextcloud
docker exec ia-webui-1 getent hosts nextcloud-nginx-1
```

## 🎨 Customization

### Add Custom MCP Servers

Users can add any MCP-compatible server:
```json
{
  "name": "Custom Server",
  "command": "/path/to/custom-mcp-server",
  "args": ["--config", "/path/to/config"],
  "env": {
    "CUSTOM_VAR": "value"
  }
}
```

### For Administrators

To add system-wide MCP servers (available to all users by default), modify:
- `install-mcp-servers.sh` to install additional servers
- Add configuration templates in the script

## 📊 Benefits of This Architecture

✅ **User Flexibility** - Each user controls their MCP servers
✅ **No Restarts** - Add/remove MCP servers without redeploying
✅ **Security** - Per-user credentials and access
✅ **Scalable** - Easy to add new MCP servers
✅ **Network Isolated** - Proper network boundaries maintained

## Next Steps

1. Deploy the configuration (see step 1 above)
2. Share the setup guide with users
3. Help users configure their first MCP server (start with Memory or Filesystem)
4. Gradually add more advanced integrations (Home Assistant, Nextcloud)

## Support

For issues or questions, check:
- Container logs: `docker logs ia-webui-1`
- MCP templates: `docker exec ia-webui-1 ls /app/backend/data/mcp-templates/`
- Full guide: `docker exec ia-webui-1 cat /app/backend/data/MCP_SETUP_GUIDE.md`
