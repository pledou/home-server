# Git History Cleanup Guide

⚠️ **CRITICAL: READ BEFORE PROCEEDING** ⚠️

This guide helps you remove sensitive data from Git history before making the repository public.

## ⚠️ WARNING

- **This process rewrites Git history** - all commit SHAs will change
- **This is irreversible** - make backups first
- **Collaborators must re-clone** if you've shared the repo
- **Complete this before pushing to GitHub public**

## Prerequisites

```bash
# Install git-filter-repo (recommended method)
pip3 install git-filter-repo

# Verify installation
git-filter-repo --version
```

## Step 1: Backup Your Repository

```bash
# Create a complete backup
cd /home/pledo
cp -r home-server home-server-backup-$(date +%Y%m%d)

# Or create a tarball
tar -czf home-server-backup-$(date +%Y%m%d).tar.gz home-server/
```

## Step 2: Identify Sensitive Files

Files to remove from history:

1. **Primary targets:**
   - `vault-pass.txt`
   - `inventories/inventory.yml`
   - `inventories/group_vars/all.yml`
   - `ansible.cfg` (if contains sensitive paths)
   - `pleduc_opc` (personal file)

2. **Check for accidentally committed secrets:**

```bash
cd /home/pledo/home-server

# Search for potential secrets in history
git log --all --full-history --source --pretty=format:"%h %s" -- \
  vault-pass.txt \
  inventories/inventory.yml \
  inventories/group_vars/all.yml \
  ansible.cfg \
  pleduc_opc

# Check for patterns in all history
git log -p -S "p.leduc@etik.com" --all
git log -p -S "leducd.duckdns.org" --all
git log -p -S "192.168.1.150" --all
git log -p -S "@mailo.com" --all
```

## Step 3: Clean Git History

### Option A: Using git-filter-repo (Recommended)

**Remove specific sensitive files:**

```bash
cd /home/pledo/home-server

# Create a paths file
cat > /tmp/paths-to-remove.txt << 'EOF'
vault-pass.txt
inventories/inventory.yml
inventories/group_vars/all.yml
ansible.cfg
pleduc_opc
EOF

# Remove these files from entire history
git filter-repo --invert-paths --paths-from-file /tmp/paths-to-remove.txt --force

# Clean up
rm /tmp/paths-to-remove.txt
```

**Alternative: Remove by content patterns:**

If you want to remove specific content (like email addresses):

```bash
# This is more aggressive - use with caution
git filter-repo --replace-text <(cat << 'EOF'
p.leduc@etik.com=admin@example.com
leducd@mailo.com=admin@example.com
leducd.duckdns.org=yourdomain.duckdns.org
192.168.1.150=192.168.1.100
EOF
) --force
```

### Option B: Using BFG Repo-Cleaner (Alternative)

```bash
# Download BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# Remove specific files
java -jar bfg-1.14.0.jar --delete-files vault-pass.txt home-server/
java -jar bfg-1.14.0.jar --delete-files inventory.yml home-server/
java -jar bfg-1.14.0.jar --delete-files all.yml home-server/

# Clean up
cd home-server
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## Step 4: Verify Cleanup

```bash
cd /home/pledo/home-server

# Verify files are removed from history
git log --all --full-history -- vault-pass.txt
# Should show: fatal: ambiguous argument 'vault-pass.txt': unknown revision or path

# Search for sensitive content
git log -p -S "p.leduc@etik.com" --all
# Should return no results

# Check for any Ansible vault encrypted content still in history
git log -p -S '$ANSIBLE_VAULT' --all
# Should show only the example files

# Verify current files are correct
ls -la inventories/
# Should show: inventory.example.yml, group_vars/all.example.yml
# Should NOT show: inventory.yml, all.yml (unless you've recreated them)

# Check repository size (should be significantly smaller)
du -sh .git
```

## Step 5: Verify Example Files Exist

```bash
cd /home/pledo/home-server

# Ensure example files are tracked
git add inventories/inventory.example.yml
git add inventories/group_vars/all.example.yml
git add ansible.cfg.example
git add .gitignore

# Commit if needed
git commit -m "Add template files for public release"
```

## Step 6: Final Safety Checks

```bash
# Check what's still in the repository
git ls-files

# Verify sensitive files are NOT in the list
git ls-files | grep -E "vault-pass.txt|inventory.yml|^ansible.cfg$|pleduc_opc"
# Should return nothing

# Check .gitignore is comprehensive
cat .gitignore

# Verify no vault passwords in history
git log --all --oneline | wc -l  # Note the commit count
git rev-list --all --objects | \
  git cat-file --batch-check='%(objectname) %(objecttype) %(rest)' | \
  awk '/blob/ {print $3}' | sort -u | \
  grep -E "vault-pass|inventory.yml|all.yml" | \
  grep -v example
# Should return nothing
```

## Step 7: Create Clean Repository for GitHub

### Option 1: Force Push to New Remote

```bash
cd /home/pledo/home-server

# Add your GitHub remote (if not already added)
git remote add origin git@github.com:YOUR_USERNAME/home-server.git

# Force push the cleaned history
git push -u origin main --force

# ⚠️ WARNING: This overwrites remote history!
```

### Option 2: Create Fresh Repository (Safest for Public Release)

```bash
cd /home/pledo

# Create a new directory for the clean repo
mkdir home-server-public
cd home-server-public

# Initialize new Git repo
git init
git branch -M main

# Copy current state (not history) from cleaned repo
cp -r ../home-server/* .
cp ../home-server/.gitignore .

# Verify sensitive files are NOT present
ls -la | grep -E "vault-pass.txt|pleduc_opc"
ls -la inventories/ | grep -v example

# Create initial commit
git add .
git commit -m "Initial public release

- Ansible playbooks for home server infrastructure
- Roles for Docker, Traefik, Nextcloud, Home Assistant, etc.
- Template files for configuration
- Comprehensive documentation

Note: This is a clean git history. Sensitive data has been removed."

# Push to GitHub
git remote add origin git@github.com:YOUR_USERNAME/home-server.git
git push -u origin main
```

## Step 8: Post-Cleanup Verification

After pushing to GitHub:

1. **Review the GitHub repository:**
   - Check files visible on GitHub
   - Verify no sensitive data in any files
   - Review recent commits

2. **Use GitHub Secret Scanning:**
   - GitHub may automatically detect secrets
   - Review any alerts in the Security tab

3. **Manual verification:**
   - Clone the repository to a new location
   - Search for sensitive patterns:

```bash
cd /tmp
git clone git@github.com:YOUR_USERNAME/home-server.git test-clone
cd test-clone

# Search for potential secrets
grep -r "p.leduc@etik.com" .
grep -r "leducd" .
grep -r "192.168.1.150" .
grep -r "@mailo.com" .

# Should only find references in documentation/examples
```

## What If I Find Leaked Secrets?

If you discover secrets in the public repository:

1. **Immediately rotate all exposed credentials**
   - Change all passwords
   - Regenerate all tokens
   - Update API keys

2. **Remove the secrets from GitHub:**
   - Follow this cleanup process again
   - Force push the cleaned history
   - Or delete and recreate the repository

3. **Contact GitHub Support:**
   - Request cache purge
   - GitHub caches repository views

4. **Monitor for abuse:**
   - Check logs for unauthorized access
   - Review Authentik access logs
   - Monitor cloud service access

## Troubleshooting

### "working tree has uncommitted changes"

```bash
# Stash changes
git stash

# Run cleanup
git filter-repo ...

# Reapply changes if needed
git stash pop
```

### "remote already exists"

```bash
# git-filter-repo removes remotes for safety
git remote add origin git@github.com:YOUR_USERNAME/home-server.git
```

### Repository size didn't decrease

```bash
# Force garbage collection
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### "not a git repository" error

```bash
# Ensure you're in the correct directory
cd /home/pledo/home-server
git status
```

## Final Checklist

Before making repository public:

- [ ] Created backup of original repository
- [ ] Removed all sensitive files from history
- [ ] Verified removal with log searches
- [ ] Added .example.yml template files
- [ ] Updated .gitignore comprehensively
- [ ] Created README.md, SETUP.md, SECURITY.md
- [ ] Added LICENSE file
- [ ] Verified no sensitive data in current files
- [ ] Tested cloning and searching for secrets
- [ ] Moved real configuration to private repository
- [ ] Documented setup process for personal use
- [ ] Ready to push to GitHub public

## Resources

- [git-filter-repo](https://github.com/newren/git-filter-repo)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [GitGuardian: Git History](https://blog.gitguardian.com/rewriting-git-history-cheatsheet/)

---

**Remember: Once you push to public, assume all history is permanent. Clean first, push later!**
