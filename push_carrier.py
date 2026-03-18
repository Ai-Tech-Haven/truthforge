import subprocess, sys, os

ROOT = r"C:\Users\AI-TECH HAVEN INT'L\Desktop\TruthForge"

def run(args, check=True):
    print(f">>> {' '.join(args)}")
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if r.stdout.strip(): print(r.stdout[-3000:])
    if r.stderr.strip(): print("STDERR:", r.stderr[-2000:])
    if check and r.returncode != 0:
        print(f"FAILED (code {r.returncode})")
        sys.exit(1)
    return r

run(["git", "add", "-A"])
r = run(["git", "commit", "-m",
    "feat: carrier portal — carrier user widget, HashPack wallet, navy upload card, CarrierProcessingTimeline, live backend wiring"],
    check=False)
if r.returncode != 0 and "nothing to commit" in (r.stdout + r.stderr):
    print("Nothing to commit.")
    sys.exit(0)
run(["git", "push", "origin", "HEAD:main"])
print("\n=== DONE ===")
