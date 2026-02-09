# Publishing to Skills.sh

This repo is ready to publish! Follow these steps:

## Step 1: Create GitHub Repo

```bash
cd ~/Documents/deepread/deepread-skills

# Create public repo on GitHub
gh repo create deepread-tech/skills \
  --public \
  --source=. \
  --description="AI agent skills for building production-grade codebases with automated quality checks" \
  --push
```

Or manually:
1. Go to https://github.com/organizations/deepread-tech/repositories/new
2. Name: `skills`
3. Description: "AI agent skills for building production-grade codebases with automated quality checks"
4. **Make it PUBLIC** ✅
5. **Don't** initialize with README (we already have one)
6. Click "Create repository"

Then push:
```bash
git remote add origin git@github.com:deepread-tech/skills.git
git branch -M main
git push -u origin main
```

## Step 2: Test Installation

After pushing, anyone can install your skills:

```bash
npx skills add deepread-tech/skills
```

Test it yourself:
```bash
npx skills add deepread-tech/skills
# Try: /prepare "test task"
```

## Step 3: Get Listed on Skills.sh

Skills.sh automatically indexes public GitHub repos with skills in `.claude/skills/` directories.

**Your repo will appear at:**
https://skills.sh/deepread-tech/skills

It may take a few minutes to index after your first push.

## Step 4: Promote

Add to your documentation:
- Update `deep-read-service/README.md` to mention the public skills repo
- Add badge: `[![Skills](https://img.shields.io/badge/Skills-deepread--tech%2Fskills-blue)](https://skills.sh/deepread-tech/skills)`
- Tweet/announce the public skills repo

## Updating Skills

When you update skills in `deep-read-service/.claude/skills/`:

```bash
# Copy changes
cd ~/Documents/deepread/deepread-skills
cp -r ~/Documents/deepread/deep-read-service/.claude/skills/* .claude/

# Commit and push
git add .
git commit -m "Update skills"
git push

# Skills.sh will auto-update within minutes
```

## Keeping in Sync

Consider adding a GitHub Action or script to sync skills automatically from `deep-read-service` to this public repo.
