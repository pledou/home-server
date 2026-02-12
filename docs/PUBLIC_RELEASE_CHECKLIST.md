# Public Release Preparation Checklist

This document provides a complete checklist for preparing your home-server repository for public release on GitHub.

## 📊 Overview

**Status**: Pre-public release preparation  
**Goal**: Safely share Ansible home server infrastructure code while protecting sensitive data  
**Approach**: Template-based configuration with separate private data repository

---

## ✅ Completed Steps

### ✓ Private Data Repository
- [x] Created `/home/pledo/home-server-private-data/` repository
- [x] Moved sensitive files (inventory.yml, all.yml, vault-pass.txt)
- [x] Created setup-links.sh script for easy configuration
- [x] Documented usage in README

**Location**: `/home/pledo/home-server-private-data/`

### ✓ Template Files
- [x] Created `inventories/inventory.example.yml`
- [x] Created `inventories/group_vars/all.example.yml`
- [x] Created `ansible.cfg.example`
- [x] All templates use placeholder values (REPLACE_ME, example.com, etc.)

### ✓ Git Ignore Configuration
- [x] Updated `.gitignore` to exclude:
  - `vault-pass.txt`
  - `ansible.cfg`
  - `inventories/inventory.yml`
  - `inventories/group_vars/all.yml`
  - Local/backup files
  - Python cache files

### ✓ Security Audit
- [x] Scanned templates for hardcoded IPs/domains
- [x] Identified network-specific templates (netplan.yml, dnsmasq.conf, dhcpd.conf)
- [x] Reviewed ansible.cfg for sensitive paths
- [x] Documented findings

**Findings**: 
- Network templates contain example IPs (192.168.21.x) - documented in README
- Docker network ranges (172.16.0.0/12, 10.0.0.0/8) - standard private ranges, safe

### ✓ Documentation
- [x] Created comprehensive [README.md](../README.md)
- [x] Created detailed [SETUP.md](../SETUP.md)
- [x] Created [SECURITY.md](../SECURITY.md) with security policy
- [x] Created [docs/GIT_HISTORY_CLEANUP.md](GIT_HISTORY_CLEANUP.md)
- [x] Added [LICENSE](../LICENSE) (MIT)

### ✓ Repository Structure
- [x] All example files in place
- [x] Documentation complete
- [x] .gitignore configured
- [x] Ready for history cleanup

---

## 🚨 CRITICAL: Next Steps (DO THESE BEFORE PUSHING PUBLIC)

### 1. Backup Everything

```bash
# Create full backup
cd /home/pledo
tar -czf home-server-backup-$(date +%Y%m%d-%H%M%S).tar.gz home-server/

# Verify backup
tar -tzf home-server-backup-*.tar.gz | head -20
```

### 2. Clean Git History

⚠️ **This is the most critical step!**

Follow the guide: [`docs/GIT_HISTORY_CLEANUP.md`](GIT_HISTORY_CLEANUP.md)

**Quick commands:**

```bash
cd /home/pledo/home-server

# Install git-filter-repo
pip3 install git-filter-repo

# Remove sensitive files from history
cat > /tmp/paths-to-remove.txt << 'EOF'
vault-pass.txt
inventories/inventory.yml
inventories/group_vars/all.yml
ansible.cfg
pleduc_opc
EOF

git filter-repo --invert-paths --paths-from-file /tmp/paths-to-remove.txt --force

# Verify cleanup
git log --all --full-history -- vault-pass.txt  # Should error
git log -p -S "p.leduc@etik.com" --all  # Should be empty
git log -p -S "leducd.duckdns.org" --all  # Should be empty
git log -p -S "192.168.1.150" --all  # Should be empty
```

### 3. Verify Current State

```bash
cd /home/pledo/home-server

# Check tracked files
git ls-files | grep -E "vault-pass|inventory.yml|all.yml|pleduc_opc" | grep -v example
# Should return NOTHING

# Check for sensitive patterns in tracked files
git grep -i "p.leduc@etik.com"  # Should be empty or only in docs
git grep -i "leducd.duckdns"  # Should be empty or only in docs
git grep "192.168.1.150"  # Should be empty

# Verify example files exist
ls -la inventories/*.example.yml
ls -la inventories/group_vars/*.example.yml
ls -la ansible.cfg.example
```

### 4. Final Security Scan

```bash
cd /home/pledo/home-server

# Search entire repository for potential secrets
grep -r "p.leduc@etik.com" . 2>/dev/null | grep -v ".git" | grep -v "docs/"
grep -r "@mailo.com" . 2>/dev/null | grep -v ".git" | grep -v "docs/"
grep -r "leducd" . 2>/dev/null | grep -v ".git" | grep -v "docs/"
grep -r "192.168.1.150" . 2>/dev/null | grep -v ".git" | grep -v "docs/"

# All results should only be in documentation/examples
```

### 5. Test Clean Clone

```bash
# Clone to a test location
cd /tmp
git clone /home/pledo/home-server test-home-server
cd test-home-server

# Verify expected structure
ls -la inventories/  # Should have .example.yml files
cat inventories/inventory.example.yml  # Should have REPLACE_ME values

# Search for sensitive data
grep -r "p.leduc" .  # Should be empty or only in docs
grep -r "192.168.1.150" .  # Should be empty
```

---

## 🚀 Publishing to GitHub

### Option 1: New Repository (Recommended)

```bash
cd /home/pledo/home-server

# Create GitHub repository first (via web interface)
# Then:

git remote add origin git@github.com:YOUR_USERNAME/home-server.git
git branch -M main
git push -u origin main
```

### Option 2: Fresh Start (Extra Safe)

```bash
cd /home/pledo
mkdir home-server-public
cd home-server-public
git init
git branch -M main

# Copy cleaned repository (without .git)
rsync -av --exclude='.git' ../home-server/ .

# Verify and commit
git add .
git commit -m "Initial public release of home server infrastructure"
git remote add origin git@github.com:YOUR_USERNAME/home-server.git
git push -u origin main
```

---

## 📝 Post-Publication Checklist

After pushing to GitHub:

### Immediate Verification

- [ ] Visit GitHub repository
- [ ] Check "Code" tab - verify no sensitive files visible
- [ ] Check "History" - review commits for sensitive data
- [ ] Check "Security" tab - review any automatic secret detection
- [ ] Search repository on GitHub for:
  - Your personal email
  - Your domain name
  - Your IP addresses
  - Any service-specific tokens

### Documentation Updates

- [ ] Update README.md with correct GitHub URLs
- [ ] Update clone commands with actual repository URL
- [ ] Add repository badges (optional):
  - License badge
  - Last commit badge
  - Stars badge

### Repository Settings

- [ ] Set repository description
- [ ] Add topics/tags (ansible, home-automation, docker, self-hosted, etc.)
- [ ] Enable/disable discussions
- [ ] Configure branch protection rules (if desired)
- [ ] Set up GitHub Actions (optional - for testing playbooks)

### Cleanup

- [ ] Delete local test clones (`/tmp/test-home-server`)
- [ ] Secure your backup (`home-server-backup-*.tar.gz`)
- [ ] Update your private data repository
- [ ] Document where your private repo is stored

---

## 🔐 Security Reminders

### Ongoing Maintenance

1. **Never commit sensitive data**:
   - Always use template files
   - Always check before committing
   - Review PRs carefully

2. **Rotate exposed secrets**:
   - If you accidentally commit a secret, assume it's compromised
   - Immediately rotate the credential
   - Force push cleaned history
   - Contact GitHub support to clear caches

3. **Monitor access**:
   - Enable GitHub security alerts
   - Review repository access logs
   - Monitor services for unusual activity

4. **Keep private repo secure**:
   - Ensure private data repo is actually private
   - Limit access to trusted users only
   - Regularly backup vault-pass.txt securely

---

## 📋 Files Created

### New Documentation

| File | Purpose |
|------|---------|
| `README.md` | Main project documentation |
| `SETUP.md` | Detailed setup instructions |
| `SECURITY.md` | Security policy and best practices |
| `LICENSE` | MIT License |
| `docs/GIT_HISTORY_CLEANUP.md` | Git history cleaning guide |
| `docs/PUBLIC_RELEASE_CHECKLIST.md` | This file |

### Template Files

| File | Purpose |
|------|---------|
| `ansible.cfg.example` | Ansible configuration template |
| `inventories/inventory.example.yml` | Server inventory template |
| `inventories/group_vars/all.example.yml` | Variables template |

### Configuration Files

| File | Purpose |
|------|---------|
| `.gitignore` | Updated with sensitive file exclusions |

---

## 🎯 Success Criteria

Your repository is ready for public release when:

- ✅ All sensitive data is in a separate private repository
- ✅ Git history is clean (no sensitive data in any commit)
- ✅ All example/template files are present with placeholder values
- ✅ .gitignore properly excludes all sensitive files
- ✅ Comprehensive documentation is available
- ✅ Security policy is documented
- ✅ License is added
- ✅ Test clone contains no sensitive data
- ✅ Repository is helpful to others without exposing your infrastructure

---

## 🤝 Contributing Guidelines

After making public, consider adding `CONTRIBUTING.md`:

```markdown
# Contributing

Thank you for considering contributing to this project!

## Guidelines

1. Test all changes in a local environment first
2. Never include actual credentials, even in PR descriptions
3. Use the template files as examples
4. Update documentation for significant changes
5. Follow existing code style and structure

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Update documentation if needed
6. Submit pull request with clear description

## Security

Never commit:
- Actual inventory files
- Vault passwords
- Service credentials
- Personal IP addresses or domains
- API keys or tokens
```

---

## 📞 Support

If you need help:

1. Check [`SETUP.md`](../SETUP.md) for detailed instructions
2. Review [`SECURITY.md`](../SECURITY.md) for security questions
3. Search existing GitHub issues
4. Create a new issue (without sensitive data!)

---

## ✨ You're All Set!

Once you've completed all steps in this checklist, your repository is ready to help others build their own home server infrastructure while keeping your personal configuration secure.

**Good luck with your public repository! 🚀**
