# PostgreSQL Upgrade System

This system provides automated PostgreSQL version upgrades for multiple services in the home server infrastructure.

## Supported Services

- **Authentik**: Authentication service
- **Kresus**: Banking application (supports multiple databases: k-db and k-db1)
- **Nextcloud**: File sharing and collaboration platform

## Configuration

### Global Variables

Set these variables in `inventories/group_vars/all.yml`:

```yaml
# PostgreSQL versions for all services
authentik_postgres_version: "15"
kresus_postgres_version: "15"
nextcloud_postgres_version: "15"

# Backup retention (in days)
postgres_backup_retention_days: 7
```

### Per-Service Configuration

Each service can override the global version:

```yaml
# In role defaults or group_vars
authentik_postgres_version: "16"  # Upgrade Authentik to PostgreSQL 16
kresus_postgres_version: "15"     # Keep Kresus on PostgreSQL 15
nextcloud_postgres_version: "16"  # Upgrade Nextcloud to PostgreSQL 16
```

## How It Works

### 1. Version Detection
- Checks if PostgreSQL container exists
- Extracts current version from container image
- Compares with target version

### 2. Upgrade Process (if versions differ)
- Creates backup directory with proper permissions (999:999)
- Dumps existing database using `pg_dump`
- Saves timestamped SQL dump file
- Stops all related services
- Removes old PostgreSQL container and volumes
- Cleans up old database directories

### 3. Deployment
- Creates new docker-compose file with updated PostgreSQL version
- Deploys new services with `docker-compose up`

### 4. Database Restoration
- Waits for new PostgreSQL container to be ready
- Finds latest database dump
- Restores data using `psql`
- Restarts services after successful restoration
- Displays upgrade completion message

### 5. Cleanup
- Removes old backup files based on retention policy
- Keeps only recent backups to save disk space

## File Structure

```
playbooks/
├── tasks/
│   ├── upgrade_postgres_service.yml    # Reusable upgrade logic
│   └── restore_postgres_service.yml    # Reusable restore logic
└── roles/
    ├── authentik/
    │   └── tasks/main.yml              # Calls shared upgrade tasks
    ├── kresus/
    │   └── tasks/main.yml              # Handles multiple databases
    └── nextcloud/
        └── tasks/main.yml              # Integrated with existing logic
```

## Usage Examples

### Upgrade Single Service

To upgrade only Authentik to PostgreSQL 16:

```yaml
# In inventories/group_vars/all.yml
authentik_postgres_version: "16"
```

Then run:
```bash
ansible-playbook -i inventories/inventory.yml playbooks/install.yml --tags authentik
```

### Upgrade All Services

Update all versions in `group_vars/all.yml`:

```yaml
authentik_postgres_version: "16"
kresus_postgres_version: "16"
nextcloud_postgres_version: "16"
```

Then run the full playbook:
```bash
ansible-playbook -i inventories/inventory.yml playbooks/install.yml
```

## Safety Features

- **Automatic backups**: Always creates database dump before upgrade
- **Version checking**: Only runs upgrade if versions actually differ
- **Graceful failure handling**: Uses `failed_when: false` for cleanup tasks
- **Proper permissions**: Ensures backup files have correct ownership
- **Retention policy**: Automatically cleans up old backups
- **Bash pipefail**: Ensures pipeline failures are properly detected

## Backup Locations

Backups are stored in:
- Authentik: `{{ docker_volumes_path }}/authentik-db-backup/`
- Kresus k-db: `{{ docker_volumes_path }}/kresus-k-db-backup/`
- Kresus k-db1: `{{ docker_volumes_path }}/kresus-k-db1-backup/`
- Nextcloud: `{{ docker_volumes_path }}/nextcloud-db-backup/`

## Troubleshooting

### Check Upgrade Status
The system displays detailed information about:
- Whether container exists
- Current and target versions
- Whether upgrade is needed

### Manual Recovery
If automatic restore fails, you can manually restore using:

```bash
# Find latest backup
ls -la {{ docker_volumes_path }}/service-name-db-backup/

# Restore manually
cat /path/to/backup.sql | docker exec -i container-name psql -U username -d database
```

### Version Verification
After upgrade, verify the new version:

```bash
docker exec container-name psql -U username -d database -c "SELECT version();"
```

## Requirements

- `community.docker` collection
- Docker and docker-compose installed on target host
- Proper user permissions for Docker operations
- Sufficient disk space for database dumps
