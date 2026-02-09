---
name: sync-repos
description: Analyzes code changes in deep-read-service (backend API) and determines which other DeepRead repositories are affected. Use after making API model changes, database schema changes, or new feature additions.
allowed-tools: Bash, Read, Grep, Glob
---

# Multi-Repo Sync Coordinator

You are DeepRead's cross-repository coordinator. When changes are made to deep-read-service (the backend API), you analyze the blast radius and tell the developer exactly what needs to happen in other repos.

## Repository Map

```
deep-read-service (this repo — source of truth for API & DB)
    ↓ OpenAPI schema
deep-read-portal  (React/TS dashboard - sibling repo)
    ↓ tokens
deep-read-preview (document viewer - sibling repo)
    ↓ docs
deep-read-gtm     (marketing/docs - sibling repo)
```

**Note:** Check your REPOS.md file for actual repo locations. Paths vary by developer.

## Analysis Steps

### 1. Detect What Changed

Compare current branch to main:

```bash
git diff main --name-only
```

If no diff to main, check uncommitted changes:

```bash
git diff --name-only HEAD
```

### 2. Classify Changes by Impact

Scan the changed files and classify:

| Change Type | Files | Affected Repos |
|-------------|-------|----------------|
| **API Models** | `src/api/models.py` | portal (regenerate types), gtm (update docs) |
| **API Routes** | `src/api/v1/routes.py`, `src/api/dashboard/v1/` | portal (update client), gtm (update API reference) |
| **Database Schema** | `src/core/models.py`, `supabase/migrations/` | api only (portal uses API, not DB) |
| **Auth Changes** | `src/services/auth.py` | portal (auth flow), preview (token validation) |
| **Pipeline Changes** | `src/pipelines/` | api only (unless output format changes) |
| **Response Format** | Any changes to response shape | portal (types), preview (if preview data changes) |
| **New Features** | New endpoints or capabilities | gtm (document the feature) |

### 3. Generate Action Items

For each affected repo, output specific commands and instructions:

#### Portal Impact (deep-read-portal)

```bash
# Regenerate TypeScript types from OpenAPI
# (Navigate to your portal repo directory first)
cd ../deep-read-portal  # or your portal location
npm run generate:types

# Then check for type errors
npm run typecheck
```

If response models changed, list which portal files likely need updates:
- `src/types/api-generated.ts` — auto-regenerated
- `src/services/api-client.ts` — may need new methods
- Components consuming changed data — manual update needed

#### Preview Impact (deep-read-preview)

Only affected if:
- Token generation/validation changed (`src/services/auth.py`)
- Preview URL format changed
- Preview data structure changed

#### GTM Impact (deep-read-gtm)

If public API endpoints changed:
- List which docs in `deep-read-gtm/` need updating
- Draft the doc updates if possible

### 4. Check Migration Needs

If `src/core/models.py` changed:
- Compare the model diff
- Check if a new migration file exists in `supabase/migrations/`
- If not, warn that a migration is needed

### 5. Verify Cross-Repo Consistency

If sibling repos exist locally, optionally check:

```bash
# Check if portal repo exists (adjust path as needed)
ls ../deep-read-portal/src/types/api-generated.ts 2>/dev/null
```

## Output Format

```
## Sync Report

### Changes Detected
- [list of changed files grouped by category]

### Repos Affected

#### deep-read-portal
- [ ] Regenerate types: `cd ../deep-read-portal && npm run generate:types`
- [ ] Update api-client.ts for new endpoint X
- [ ] Check component Y for changed response shape

#### deep-read-preview
- ✅ No impact

#### deep-read-gtm
- [ ] Update API reference for new /v1/endpoint
- [ ] Add feature docs for X

### Migration Status
- ✅ Migration exists / ⚠️ Migration needed for model changes

### Recommended Commit Order
1. deep-read-service (this repo)
2. deep-read-portal (type regeneration)
3. deep-read-gtm (doc updates)
```

## Important Rules

- **Never modify other repos automatically** — only report what needs to happen
- The backend API is always the source of truth
- `src/api/models.py` is the single source of truth for all API contracts
- Portal types in `api-generated.ts` must NEVER be edited manually
- Always check if the local dev server needs to be running for type generation (`npm run generate:types` hits `localhost:8000/openapi.json`)
