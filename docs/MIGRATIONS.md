# Database Migration Guide

## Overview

This guide explains how to manage database migrations using Alembic for the Pre-Visit Voice Agent API.

Alembic is a database migration tool that allows you to:
- ✅ Version control your database schema
- ✅ Track schema changes over time
- ✅ Migrate between versions (upgrade/downgrade)
- ✅ Deploy to production safely

---

## Installation

Alembic is already in `requirements.txt`. Install it:

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install alembic>=1.12.1
```

---

## Quick Start

### Initialize Database (First Time)

```bash
# Apply all pending migrations to your database
alembic upgrade head

# Verify tables were created
python -c "from database import init_db; db = init_db(); print('✓ Database initialized')"
```

### Check Migration Status

```bash
# Show current revision
alembic current

# Show history
alembic history --verbose

# Show pending migrations
alembic branches
```

---

## Creating New Migrations

### Scenario: Add a new column to clinical_data

#### Step 1: Modify the Model

Edit `models.py`:

```python
class ClinicalData(Base):
    # ... existing columns ...
    new_field = Column(String(255), nullable=True)  # ← ADD THIS
```

#### Step 2: Auto-Generate Migration

```bash
# Generate migration file based on model changes
alembic revision --autogenerate -m "Add new_field to clinical_data"

# This creates: alembic/versions/002_add_new_field_to_clinical_data.py
```

#### Step 3: Review Migration File

Open the generated file and verify:

```python
def upgrade() -> None:
    op.add_column('clinical_data', 
        sa.Column('new_field', sa.String(255), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('clinical_data', 'new_field')
```

#### Step 4: Apply Migration

```bash
# Apply to development database
alembic upgrade head

# Verify
alembic current
```

#### Step 5: Commit & Deploy

```bash
git add alembic/versions/002_add_new_field_to_clinical_data.py
git commit -m "db: add new_field to clinical_data"
git push origin main

# Render automatically runs: alembic upgrade head
```

---

## Manual Migrations

If auto-generation doesn't work, create manually:

### Create Empty Migration

```bash
alembic revision -m "my_migration_description"

# Creates: alembic/versions/003_my_migration_description.py
```

### Edit and Add SQL Operations

```python
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Add column
    op.add_column('table_name', sa.Column('new_col', sa.String(50)))
    
    # Drop column
    op.drop_column('table_name', 'old_col')
    
    # Create index
    op.create_index('idx_name', 'table_name', ['col_name'])
    
    # Execute raw SQL
    op.execute("UPDATE table_name SET col = 'value'")

def downgrade() -> None:
    # Reverse operations
    op.drop_index('idx_name')
    op.drop_column('table_name', 'new_col')
    op.add_column('table_name', sa.Column('old_col', sa.String(50)))
```

---

## Common Operations

### View All Available Commands

```bash
alembic --help
```

### Upgrade to Specific Revision

```bash
# Upgrade to revision abc123
alembic upgrade abc123

# Downgrade to previous
alembic downgrade -1

# Go back 3 revisions
alembic downgrade -3
```

### View Migration Details

```bash
# Show all migrations
alembic history -v

# Show head revision
alembic heads

# Show base revision
alembic bases
```

### Create Stamp (For Existing Databases)

If you already have a database and want to start using migrations:

```bash
# Tell Alembic the database is at HEAD
alembic stamp head

# Now you can use migrations normally
```

---

## Migration Best Practices

### ✅ DO

- ✅ Always create a migration before modifying models
- ✅ Test migrations locally before deploying
- ✅ Write descriptive migration names
- ✅ Keep migrations small and focused
- ✅ Test both upgrade and downgrade
- ✅ Review auto-generated migrations carefully

### ❌ DON'T

- ❌ Don't modify the database directly (always use migrations)
- ❌ Don't create migrations manually when auto-generate can help
- ❌ Don't deploy untested migrations to production
- ❌ Don't delete old migration files
- ❌ Don't modify applied migrations (already in production)

---

## Troubleshooting

### Issue: "Target database is not current"

```bash
# Check what version you're on
alembic current

# Check what's pending
alembic history

# Apply missing migrations
alembic upgrade head
```

### Issue: "Duplicate column name"

```bash
# Migration tried to add column that already exists
# Either:
# 1. Roll back and fix migration
alembic downgrade -1

# 2. Or stamp database to skip bad migration
alembic stamp HEAD
```

### Issue: "Foreign key constraint fails"

When dropping tables or columns with foreign keys:

```python
# Drop dependent table first
def upgrade():
    op.drop_table('conversation_messages')
    op.drop_table('conversation_sessions')

def downgrade():
    op.create_table('conversation_sessions', ...)
    op.create_table('conversation_messages', ...)
```

### Issue: Migration Conflicts in Team

Multiple developers creating migrations simultaneously:

```bash
# Merge migrations manually
alembic merge heads

# Or recreate migration targeting the latest head
alembic revision -m "reconcile branches"
```

---

## Development Workflow

### Local Development

```bash
# 1. Make model changes in models.py
# 2. Create migration
alembic revision --autogenerate -m "description"

# 3. Test locally
alembic upgrade head
python -m pytest tests/test_api.py -v

# 4. If issues, rollback
alembic downgrade -1

# 5. Fix and re-create migration
alembic revision --autogenerate -m "description fixed"
```

### Production Deployment

```bash
# 1. Test on staging first (if available)
# 2. Commit migration files
git add alembic/versions/

# 3. Push to main
git push origin main

# 4. Render automatically runs in Dockerfile:
# RUN python -m alembic upgrade head

# 5. Verify in Render logs
# Look for: "INFO [alembic.runtime.migration] Context impl SQLiteImpl."
```

---

## Current Migrations

### 001_initial_schema (APPLIED)

Creates 4 tables:
- `conversation_sessions` - Session metadata
- `conversation_messages` - Message history
- `clinical_data` - Extracted clinical info
- `audit_logs` - API access logs

Applied automatically on first run.

---

## Reverting to Previous Schema

```bash
# If you need to rollback production
# WARNING: This will delete data!

# Downgrade one migration
alembic downgrade -1

# Downgrade to specific version
alembic downgrade 001_initial_schema

# Or drop everything
alembic downgrade base

# Then re-apply correct versions
alembic upgrade head
```

---

## Testing Migrations

### Unit Test

```bash
# Create test database
pytest tests/test_migrations.py -v
```

### Integration Test

```bash
# Test with real database
DATABASE_URL=sqlite:///test.db alembic upgrade head
DATABASE_URL=sqlite:///test.db alembic downgrade -1
```

---

## CI/CD Integration

Migrations run automatically in GitHub Actions / Render:

**Dockerfile:**
```dockerfile
RUN python -m alembic upgrade head
```

**GitHub Actions (.github/workflows/deploy.yml):**
```yaml
- name: Run migrations
  run: |
    alembic upgrade head
```

---

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Column Types](https://docs.sqlalchemy.org/en/20/core/types.html)
- [Alembic Operations](https://alembic.sqlalchemy.org/en/latest/ops.html)

---

## Support

For issues:
1. Check migration files: `alembic/versions/`
2. Check current revision: `alembic current`
3. Review error logs: `alembic upgrade head -v`
4. Consult Alembic docs: https://alembic.sqlalchemy.org/
