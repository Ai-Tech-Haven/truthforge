import subprocess, sys, os

ROOT = r"C:\Users\AI-TECH HAVEN INT'L\Desktop\TruthForge"
REMOTE = "origin"

def run(args, check=True):
    print(f">>> {' '.join(args)}")
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if r.stdout.strip(): print(r.stdout[-3000:])
    if r.stderr.strip(): print("STDERR:", r.stderr[-2000:])
    if check and r.returncode != 0:
        print(f"FAILED (code {r.returncode})")
        sys.exit(1)
    return r

print("=== Staging all changes ===")
run(["git", "add", "-A"])

print("\n=== Committing ===")
r = run(["git", "commit", "-m",
    "feat: replace hashconnect with DAppConnector (hedera-wallet-connect) for HashPack extension popup; clean up duplicate md files; add vite polyfills"],
    check=False)
if r.returncode != 0 and "nothing to commit" in (r.stdout + r.stderr):
    print("Nothing new to commit.")
    sys.exit(0)

print("\n=== Pushing ===")
run(["git", "push", REMOTE, "HEAD:main"])
print("\n=== DONE ===")
