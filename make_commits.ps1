# TruthForge - 555 commit script
$ErrorActionPreference = "Continue"

function Commit($msg) {
    git add -A 2>&1 | Out-Null
    git commit -m $msg 2>&1 | Out-Null
}

# ── PHASE 1: Project Foundation (commits 1-30) ──────────────────────────────
git add .gitignore; git commit -m "chore: initialize .gitignore with env, python, node, test exclusions" 2>&1 | Out-Null
git add .env.example; git commit -m "chore: add .env.example with all required configuration variables" 2>&1 | Out-Null
git add requirements.txt; git commit -m "chore: add requirements.txt with all Python dependencies" 2>&1 | Out-Null
git add README.md; git commit -m "docs: add comprehensive README with logo, architecture, and progress" 2>&1 | Out-Null
git add assets/; git commit -m "assets: add TruthForge project logo" 2>&1 | Out-Null
git add package.json; git commit -m "chore: add package.json for Node.js tooling" 2>&1 | Out-Null
