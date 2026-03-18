import subprocess, sys, os, time

ROOT = r"C:\Users\AI-TECH HAVEN INT'L\Desktop\TruthForge"
REMOTE = "origin"
FRONTEND = os.path.join(ROOT, "truthforge_frontend", "truthforge-logistics-verified-main")

def run(args, cwd=None, check=True):
    print(f">>> {' '.join(args) if isinstance(args, list) else args}")
    r = subprocess.run(args, cwd=cwd or ROOT, capture_output=True, text=True, shell=isinstance(args, str))
    if r.stdout.strip(): print(r.stdout[-3000:])
    if r.stderr.strip(): print("STDERR:", r.stderr[-2000:])
    if check and r.returncode != 0:
        print(f"FAILED (code {r.returncode})")
        sys.exit(1)
    return r

# Wait for any running npm to finish
print("=== Checking if packages are installed ===")
hwc = os.path.join(FRONTEND, "node_modules", "@hashgraph", "hedera-wallet-connect")
hiero = os.path.join(FRONTEND, "node_modules", "@hiero-ledger", "sdk")

if not os.path.exists(hwc) or not os.path.exists(hiero):
    print("Packages not found — installing now...")
    run(["cmd", "/c", "npm install @hashgraph/hedera-wallet-connect @hiero-ledger/sdk @walletconnect/modal buffer process stream-browserify events util --legacy-peer-deps"], cwd=FRONTEND)
else:
    print("Packages already installed.")

print("\n=== Git: stage all changes ===")
run(["git", "add", "-A"])

print("\n=== Git: commit ===")
r = run(["git", "commit", "-m",
    "feat: replace hashconnect with DAppConnector (hedera-wallet-connect) for HashPack extension popup; clean up duplicate md files; add vite polyfills"],
    check=False)
if r.returncode != 0 and "nothing to commit" in r.stdout + r.stderr:
    print("Nothing new to commit — already clean.")
else:
    print("\n=== Git: push ===")
    run(["git", "push", REMOTE, "HEAD:main"])

print("\n=== DONE ===")
