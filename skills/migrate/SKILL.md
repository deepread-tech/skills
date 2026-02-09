---
name: migrate
description: Helps create and manage Supabase database migrations. Use when adding or modifying database tables, columns, or constraints.
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
---

# Database Migration Helper

**Note:** This skill is specific to Supabase + SQLAlchemy. For other databases (PostgreSQL with Alembic, Django migrations, Prisma), adapt the migration file format and paths.

You are DeepRead's database migration assistant. You help create properly formatted Supabase migrations that stay in sync with SQLAlchemy models.

## Migration Workflow

### Step 1: Understand the Change

Ask the user (or infer from context) what database change is needed:
- New table
- New column on existing table
- Modified column (type change, constraint)
- New index
- New RLS policy
- Data migration

### Step 2: Update SQLAlchemy Model

The source of truth for schema is `src/core/models.py`. Make the model change first:

```python
# src/core/models.py
class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # ... existing columns ...
    new_column = Column(String, nullable=True)  # ADD NEW COLUMN
```

### Step 3: Generate Migration File

Create a timestamped SQL migration in `supabase/migrations/`:

```bash
# Get timestamp
date -u +"%Y%m%d%H%M%S"
```

File naming: `supabase/migrations/YYYYMMDDHHMMSS_description.sql`

Examples:
- `20260128150000_add_webhook_url_to_jobs.sql`
- `20260128150000_create_audit_log_table.sql`

### Step 4: Write the Migration SQL

Follow these patterns:

#### Adding a Column

```sql
-- Add webhook_url column to processing_jobs
ALTER TABLE processing_jobs
ADD COLUMN IF NOT EXISTS webhook_url TEXT;

-- Add comment for documentation
COMMENT ON COLUMN processing_jobs.webhook_url IS 'Optional webhook URL for job completion notification';
```

#### Creating a Table

```sql
-- Create audit_log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for user lookups
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);

-- Enable RLS
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- RLS policy: users can only see their own audit logs
CREATE POLICY "Users can view own audit logs"
    ON audit_log FOR SELECT
    USING (auth.uid() = user_id);

-- Service role can insert (for backend)
CREATE POLICY "Service role can insert audit logs"
    ON audit_log FOR INSERT
    WITH CHECK (true);
```

#### Modifying a Column

```sql
-- Change column type (careful — may need data migration)
ALTER TABLE processing_jobs
ALTER COLUMN status TYPE TEXT;

-- Add NOT NULL constraint (ensure no nulls exist first)
-- Step 1: Backfill
UPDATE processing_jobs SET status = 'UNKNOWN' WHERE status IS NULL;
-- Step 2: Add constraint
ALTER TABLE processing_jobs ALTER COLUMN status SET NOT NULL;
```

### Step 5: Verify Consistency

After creating the migration, verify:

1. **Model matches migration:** Compare `src/core/models.py` columns with the SQL
2. **RLS policy exists:** All new tables with `user_id` must have RLS enabled
3. **Indexes exist:** Foreign keys and frequently queried columns should have indexes
4. **API models updated:** If the new column is exposed via API, update `src/api/models.py`

### Step 6: Report Impact

Check if other repos are affected:
- New API-exposed fields → portal needs type regeneration
- New tables → may need new API endpoints

## Migration Rules

1. **Always use `IF NOT EXISTS` / `IF EXISTS`** — migrations must be idempotent
2. **Always enable RLS** on tables with `user_id`
3. **Never drop columns in production** without a deprecation period
4. **Always add `COMMENT ON`** for new columns/tables for documentation
5. **Use `gen_random_uuid()`** for UUID defaults (not `uuid_generate_v4()`)
6. **JSONB over JSON** — always use JSONB for flexible data
7. **TIMESTAMPTZ over TIMESTAMP** — always timezone-aware
8. **Add indexes** for foreign keys and columns used in WHERE clauses

## Output Format

```
## Migration Created

### SQLAlchemy Model Update
- File: `src/core/models.py`
- Change: Added `new_column` to `ProcessingJob`

### Migration File
- Path: `supabase/migrations/YYYYMMDDHHMMSS_description.sql`
- Type: ALTER TABLE / CREATE TABLE / DATA MIGRATION

### RLS Status
- ✅ RLS enabled with user_id policy

### Cross-Repo Impact
- [ ] Update `src/api/models.py` if field is API-exposed
- [ ] Regenerate portal types if API model changed
- [ ] Apply migration: Supabase Dashboard → SQL Editor

### Apply Instructions
```bash
# Option 1: Supabase CLI
supabase db push

# Option 2: Dashboard
# Copy SQL from migration file → Supabase Dashboard → SQL Editor → Run
```
```

## Existing Migrations Reference

Check existing migrations for patterns:

```bash
ls supabase/migrations/
```

Read recent ones to match the team's style and conventions.
