# Security Policy

## Supported Versions

This project is actively maintained. Security updates will be applied to the latest version.

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < Latest| :x:                |

## Reporting a Vulnerability

We take the security of this project seriously. If you discover a security vulnerability, please follow these steps:

### 1. **Do Not** Open a Public Issue

Please **do not** report security vulnerabilities through public GitHub issues, discussions, or pull requests.

### 2. Report Privately

Send a detailed report to: **[Your Email or GitHub Private Security Advisory]**

You can also use GitHub's private security advisory feature:
1. Go to the repository's "Security" tab
2. Click "Report a vulnerability"
3. Fill in the details privately

### 3. Include in Your Report

- **Description**: Clear description of the vulnerability
- **Impact**: What can be compromised (data, access, etc.)
- **Reproduction Steps**: Detailed steps to reproduce the issue
- **Affected Components**: Which roles/playbooks are affected
- **Suggested Fix**: If you have ideas on how to fix it
- **Disclosure Timeline**: Your expectations for disclosure

### Example Report Template

```
**Summary:** Brief description of the vulnerability

**Affected Components:**
- Role: [e.g., traefik, nextcloud]
- Files: [specific files affected]
- Versions: [known affected versions]

**Impact:**
- Confidentiality: [High/Medium/Low]
- Integrity: [High/Medium/Low]
- Availability: [High/Medium/Low]

**Reproduction Steps:**
1. Step one
2. Step two
3. ...

**Suggested Mitigation:**
[Your suggestions if any]

**Additional Context:**
[Any other relevant information]
```

## Response Timeline

- **Initial Response**: Within 48 hours of report
- **Validation**: Within 7 days
- **Fix Development**: Depends on severity (1-30 days)
- **Public Disclosure**: After fix is released and users have time to update

## Security Best Practices

When using this project, we recommend:

### Infrastructure Security

1. **Vault Passwords**
   - Use strong, randomly generated vault passwords
   - Store vault-pass.txt securely (password manager, encrypted backup)
   - Never commit vault-pass.txt to any repository
   - Rotate vault passwords periodically

2. **SSH Access**
   - Use SSH key authentication (disable password auth)
   - Use ED25519 keys for better security: `ssh-keygen -t ed25519`
   - Protect SSH keys with strong passphrases
   - Use ssh-agent to securely manage key passphrases
   - Configure Ansible with `ansible_ssh_private_key_file` in inventory
   - Limit SSH access by IP when possible (via firewall rules)
   - Disable password authentication after confirming key auth works
   - Consider using fail2ban for brute-force protection
   - Regularly audit authorized_keys files

3. **Firewall Configuration**
   - Review UFW rules configured by the playbooks
   - Only expose necessary ports
   - Use Traefik reverse proxy for all web services
   - Consider using a VPN for administrative access

4. **SSL/TLS**
   - Let's Encrypt certificates are automatically renewed
   - Monitor certificate expiration
   - Use TLS 1.2+ only
   - Keep Traefik updated for latest security patches

5. **Container Security**
   - Regularly update Docker images
   - Use DIUN for image update notifications
   - Review container configurations
   - Run containers as non-root when possible

6. **Network Isolation**
   - Services run in isolated Docker networks
   - Review docker-compose network configurations
   - Limit direct container-to-container communication

### Access Control

1. **Authentik SSO**
   - Enable multi-factor authentication (MFA)
   - Use strong passwords
   - Regularly review user access
   - Implement principle of least privilege

2. **Service Accounts**
   - Use unique passwords for each service
   - Store all secrets in Ansible Vault
   - Use Docker secrets for sensitive data in containers (e.g., database passwords, API keys)
   - Never hardcode secrets in docker-compose.yml templates
   - Generate strong random secrets: `openssl rand -hex 32`
   - Store Docker secret files with restrictive permissions (600)
   - Rotate credentials periodically
   - Use token-based authentication when available
   - Document secret file locations without exposing values

3. **Database Security**
   - PostgreSQL containers are not exposed externally
   - Use strong database passwords
   - Regular backups (automated via Restic)
   - Consider encryption at rest for sensitive data

### Monitoring & Auditing

1. **Logging**
   - Centralized logging via Docker logging driver
   - Regular log review
   - Set up alerts for suspicious activity

2. **Monitoring**
   - Use Grafana dashboards to monitor system health
   - Set up alerts for anomalies
   - Monitor failed login attempts

3. **Backup Verification**
   - Regularly test backup restoration
   - Verify backup integrity
   - Store backups in multiple locations
   - Encrypt backup data

### Update Management

1. **Regular Updates**
   - Run `upgrade-packages.yml` monthly
   - Subscribe to security advisories for deployed services
   - Test updates in staging environment first
   - Keep Ansible and control machine updated

2. **Vulnerability Scanning**
   - Use `test-security-scan.sh` to scan images
   - Review security scan results before deployment
   - Address high-priority vulnerabilities promptly

## Known Security Considerations

### Template Files with Network-Specific IPs

The following template files contain example IP addresses that should be customized for your network:

- `playbooks/templates/netplan.yml` - Static IP configuration
- `playbooks/templates/dnsmasq.conf` - DNS forwarder configuration
- `playbooks/templates/dhcpd.conf` - DHCP server configuration

**Action Required**: Review and customize these files for your network topology.

### Sensitive Data Management

This repository uses a **template approach** for sensitive data:

- ✅ **Safe**: `.example.yml` files (public templates)
- ❌ **Sensitive**: Actual `inventory.yml`, `all.yml`, `vault-pass.txt` (git-ignored)

**Before pushing to public repository:**
1. Verify `.gitignore` excludes sensitive files
2. Clean Git history of any accidentally committed secrets
3. Use a separate private repository for actual configuration

### Service-Specific Security

1. **Nextcloud**
   - Review `config.php` security settings post-installation
   - Enable encryption at rest
   - Regular security scan via admin interface

2. **Home Assistant**
   - Restrict API access
   - Use HTTPS only
   - Review integration permissions

3. **Grafana**
   - Change default admin password immediately
   - Use OAuth via Authentik
   - Restrict dashboard access appropriately

4. **GitLab**
   - Configure rate limiting
   - Enable admin notifications
   - Regular security updates

## Security Scanning

This project includes Trivy scanning for Docker images. Run security scans:

```bash
# Run the security scan script
./test-security-scan.sh

# Or manually scan specific images
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image nextcloud:32
```

## Incident Response

If you suspect a security incident:

1. **Isolate**: Disconnect affected systems if necessary
2. **Assess**: Determine scope and impact
3. **Contain**: Stop the attack vector
4. **Eradicate**: Remove malicious access/code
5. **Recover**: Restore from clean backups
6. **Review**: Analyze logs and improve security

## Disclosure Policy

- **Private Disclosure**: Security issues are handled privately until fixed
- **Public Disclosure**: After fix is released and users notified
- **Credit**: Security researchers will be credited (unless they prefer anonymity)
- **CVE Assignment**: For significant vulnerabilities, we may request CVE IDs

## Security Resources

- [Ansible Vault Documentation](https://docs.ansible.com/ansible/latest/user_guide/vault.html)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)

## Contact

For security concerns:
- **GitHub Security Advisories**: [Preferred method]
- **Email**: [Your security contact email]
- **PGP Key**: [Optional: Your PGP public key fingerprint]

---

**Thank you for helping keep this project and its users secure!**
