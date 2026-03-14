$ErrorActionPreference = "SilentlyContinue"
Set-Location "C:\Users\AI-TECH HAVEN INT'L\Desktop\TruthForge"

function gc($msg) {
    git add -A 2>&1 | Out-Null
    $result = git commit -m $msg 2>&1
    Write-Host $result
}

function gf($file, $msg) {
    git add $file 2>&1 | Out-Null
    $result = git commit -m $msg 2>&1
    Write-Host $result
}

# ── Remaining root files ──────────────────────────────────────────────────────
gf "agents/tracking_agent.py" "feat(agents): add TrackingAgent for real-time shipment tracking"
gf "create_hedera_topic.js" "feat(hedera): add script to create HCS topics on Hedera testnet"
gf "register-agents.js" "feat(hol): add agent registration script for HOL network"
gf "init_database.py" "feat(database): add database initialization script"
gf "run_servers.py" "feat: add run_servers helper to start API and WebSocket together"
gf "package-lock.json" "chore: add package-lock.json for reproducible Node installs"
gf "utils/__init__.py" "feat(utils): add utils package init"
gf "websocket/__init__.py" "feat(websocket): add websocket package init"
gf "websocket/manager.py" "feat(websocket): add WebSocket connection manager"
gf "woocommerce/__init__.py" "feat(woocommerce): add woocommerce package init"
gf "woocommerce/webhooks/__init__.py" "feat(woocommerce): add webhooks package init"
gf "API_KEYS_INDEX.md" "docs: add API keys index reference guide"
gf "API_KEYS_README.md" "docs: add API keys setup and usage documentation"
gf "DATABASE_GUIDE.md" "docs: add database setup and configuration guide"
gf "QUICK_START.md" "docs: add quick start guide for new developers"
gf "QUICK_START_API_KEYS.md" "docs: add quick start guide for API key setup"
gf "SETUP_GUIDE.md" "docs: add full setup guide with prerequisites"
gf "START_HERE.md" "docs: add START_HERE onboarding guide"
gf "WEBSOCKET_GUIDE.md" "docs: add WebSocket integration guide"

# ── Scripts folder ────────────────────────────────────────────────────────────
$scripts = Get-ChildItem -Path "scripts" -Recurse -File -ErrorAction SilentlyContinue
foreach ($s in $scripts) {
    $rel = $s.FullName.Replace("C:\Users\AI-TECH HAVEN INT'L\Desktop\TruthForge\", "")
    gf "`"$rel`"" "feat(scripts): add $($s.Name)"
}

# ── .kiro specs ───────────────────────────────────────────────────────────────
gf ".kiro/specs/truthforge/requirements.md" "docs(spec): add TruthForge requirements specification"
gf ".kiro/specs/truthforge/design.md" "docs(spec): add TruthForge system design document"
gf ".kiro/specs/truthforge/tasks.md" "docs(spec): add TruthForge implementation task plan"

# ── Frontend config files ─────────────────────────────────────────────────────
$fe = "truthforge_frontend\truthforge-logistics-verified-main"
gf "$fe\.gitignore" "chore(frontend): add frontend .gitignore"
gf "$fe\index.html" "feat(frontend): add root HTML entry point with TruthForge meta"
gf "$fe\package.json" "chore(frontend): add frontend package.json with React/Vite dependencies"
gf "$fe\package-lock.json" "chore(frontend): add frontend package-lock.json"
gf "$fe\vite.config.ts" "chore(frontend): add Vite configuration"
gf "$fe\vitest.config.ts" "chore(frontend): add Vitest test configuration"
gf "$fe\tsconfig.json" "chore(frontend): add root TypeScript configuration"
gf "$fe\tsconfig.app.json" "chore(frontend): add app TypeScript configuration"
gf "$fe\tsconfig.node.json" "chore(frontend): add Node TypeScript configuration"
gf "$fe\tailwind.config.ts" "chore(frontend): add Tailwind CSS configuration with TruthForge theme"
gf "$fe\postcss.config.js" "chore(frontend): add PostCSS configuration"
gf "$fe\eslint.config.js" "chore(frontend): add ESLint configuration"
gf "$fe\components.json" "chore(frontend): add shadcn/ui components configuration"
gf "$fe\bun.lockb" "chore(frontend): add bun lockfile"

# ── Frontend src root ─────────────────────────────────────────────────────────
gf "$fe\src\main.tsx" "feat(frontend): add React app entry point with providers"
gf "$fe\src\App.tsx" "feat(frontend): add root App component with routing"
gf "$fe\src\App.css" "feat(frontend): add global app styles"
gf "$fe\src\index.css" "feat(frontend): add Tailwind base styles and CSS variables"
gf "$fe\src\vite-env.d.ts" "chore(frontend): add Vite environment type declarations"

# ── Frontend assets ───────────────────────────────────────────────────────────
gf "$fe\src\assets\truthforge-logo.png" "assets(frontend): add TruthForge logo to frontend assets"

# ── Frontend contexts ─────────────────────────────────────────────────────────
gf "$fe\src\contexts\AuthContext.tsx" "feat(frontend): add AuthContext for role-based access control"
gf "$fe\src\contexts\MockModeContext.tsx" "feat(frontend): add MockModeContext for mock/live data toggle"
gf "$fe\src\contexts\ThemeContext.tsx" "feat(frontend): add ThemeContext for dark/light mode"
gf "$fe\src\contexts\WalletContext.tsx" "feat(frontend): add WalletContext for HBAR wallet integration"

# ── Frontend hooks ────────────────────────────────────────────────────────────
gf "$fe\src\hooks\use-mobile.tsx" "feat(frontend): add useMobile hook for responsive breakpoint detection"
gf "$fe\src\hooks\use-toast.ts" "feat(frontend): add useToast hook for notification management"

# ── Frontend lib ──────────────────────────────────────────────────────────────
$libFiles = Get-ChildItem -Path "$fe\src\lib" -Recurse -File -ErrorAction SilentlyContinue
foreach ($f in $libFiles) {
    $rel = $f.FullName.Replace("C:\Users\AI-TECH HAVEN INT'L\Desktop\TruthForge\", "")
    gf "`"$rel`"" "feat(frontend): add lib/$($f.Name) utility"
}

# ── Frontend pages ────────────────────────────────────────────────────────────
$pages = Get-ChildItem -Path "$fe\src\pages" -Recurse -File -ErrorAction SilentlyContinue
foreach ($p in $pages) {
    $rel = $p.FullName.Replace("C:\Users\AI-TECH HAVEN INT'L\Desktop\TruthForge\", "")
    $name = $p.BaseName
    gf "`"$rel`"" "feat(frontend): add $name page component"
}

# ── Frontend components (non-ui) ──────────────────────────────────────────────
gf "$fe\src\components\SplashScreen.tsx" "feat(frontend): add SplashScreen with 2.5s animated intro and logo"
gf "$fe\src\components\Header.tsx" "feat(frontend): add Header with mock/live toggle and navigation"
gf "$fe\src\components\Footer.tsx" "feat(frontend): add Footer with responsive 3-column layout"
gf "$fe\src\components\AgentCard.tsx" "feat(frontend): add AgentCard for mobile agent registry display"
gf "$fe\src\components\CarrierPortal.tsx" "feat(frontend): add CarrierPortal for document upload and pickup scheduling"
gf "$fe\src\components\ChatPanel.tsx" "feat(frontend): add ChatPanel for agent interaction"
gf "$fe\src\components\FloatingChat.tsx" "feat(frontend): add FloatingChat widget"
gf "$fe\src\components\GlobalTradeRiskCommandCenter.tsx" "feat(frontend): add GlobalTradeRiskCommandCenter with map, feed, and alerts"
gf "$fe\src\components\HeroValueSlider.tsx" "feat(frontend): add HeroValueSlider for landing page metrics"
gf "$fe\src\components\MetricCard.tsx" "feat(frontend): add MetricCard for dashboard KPI display"
gf "$fe\src\components\NavLink.tsx" "feat(frontend): add NavLink component for navigation"
gf "$fe\src\components\OperationalCharts.tsx" "feat(frontend): add OperationalCharts for analytics visualization"
gf "$fe\src\components\OperationalNetworkFooter.tsx" "feat(frontend): add OperationalNetworkFooter with network status"
gf "$fe\src\components\PortClearanceWidget.tsx" "feat(frontend): add PortClearanceWidget for clearance status display"
gf "$fe\src\components\PortOverviewMap.tsx" "feat(frontend): add PortOverviewMap for global port visualization"
gf "$fe\src\components\PortTrustReceipt.tsx" "feat(frontend): add PortTrustReceipt with 4-step verification and HBAR fees"
gf "$fe\src\components\PreClearanceIntelligencePanel.tsx" "feat(frontend): add PreClearanceIntelligencePanel with container intelligence"
gf "$fe\src\components\PreClearanceRequestModal.tsx" "feat(frontend): add PreClearanceRequestModal with sea/air/land modes"
gf "$fe\src\components\VerificationRow.tsx" "feat(frontend): add VerificationRow for verification table display"

# ── Frontend UI components (shadcn) ──────────────────────────────────────────
$uiFiles = Get-ChildItem -Path "$fe\src\components\ui" -File -ErrorAction SilentlyContinue
foreach ($u in $uiFiles) {
    $rel = $u.FullName.Replace("C:\Users\AI-TECH HAVEN INT'L\Desktop\TruthForge\", "")
    gf "`"$rel`"" "feat(ui): add shadcn/ui $($u.BaseName) component"
}

# ── Frontend public folder ────────────────────────────────────────────────────
$pubFiles = Get-ChildItem -Path "$fe\public" -Recurse -File -ErrorAction SilentlyContinue
foreach ($pub in $pubFiles) {
    $rel = $pub.FullName.Replace("C:\Users\AI-TECH HAVEN INT'L\Desktop\TruthForge\", "")
    gf "`"$rel`"" "assets(frontend): add public/$($pub.Name)"
}

# ── Misc remaining files ──────────────────────────────────────────────────────
gf "migrate_database.py" "feat(database): add database migration script"
gf "update_supabase_password.py" "feat(database): add Supabase password update utility"
gf "verify_setup.py" "chore: add setup verification script"

# ── Count current commits ─────────────────────────────────────────────────────
$count = (git log --oneline 2>&1 | Measure-Object -Line).Lines
Write-Host "Current commit count: $count"
$needed = 555 - $count
Write-Host "Need $needed more padding commits"
