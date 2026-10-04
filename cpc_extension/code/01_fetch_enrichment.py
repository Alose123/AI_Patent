"""Download reproducible USPTO/PatentsView bulk inputs; never alter the source CSV."""
from pathlib import Path
import argparse
import concurrent.futures
import hashlib
import json
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RECORD = "15783125"  # final PatentsView grant release, December 31, 2024; Zenodo v2
FILES = {
    "g_cpc_current.tsv.zip": (485195636, "8211b681c392b2810b5a848e1fcfa308"),
    "g_cpc_at_issue.tsv.zip": (321099326, "6541c50b236d711f4b8f379a854a0c8a"),
    "g_cpc_title.tsv.zip": (6427461, "64e5f5e5decd1a1cac171ec550f5352c"),
    "g_patent.tsv.zip": (223192856, "f74fbde4b2adbf980b8e4ed5394f16d2"),
    "g_patent_abstract.tsv.zip": (1647990737, "bb7ff59781633edb61032429a7d8f6f1"),
    "g_application.tsv.zip": (68669855, "26001068098f4240e0762c63ffbb331e"),
}

def digest(path):
    h = hashlib.md5()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 * 1024**2), b""):
            h.update(b)
    return h.hexdigest()

def fetch(name):
    path = ROOT / "cache" / name
    expected_size, expected_md5 = FILES[name]
    url = f"https://zenodo.org/api/records/{RECORD}/files/{name}/content"
    if path.exists() and path.stat().st_size == expected_size and digest(path) == expected_md5:
        print(f"Verified cached {name}", flush=True)
    else:
        temporary = path.with_suffix(path.suffix + ".part")
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "PatentResearch/1.0 (reproducible academic analysis)"})
                downloaded = 0
                last_print = time.monotonic()
                with urllib.request.urlopen(req, timeout=120) as response, temporary.open("wb") as output:
                    while True:
                        block = response.read(4 * 1024**2)
                        if not block:
                            break
                        output.write(block)
                        downloaded += len(block)
                        if time.monotonic() - last_print > 20:
                            print(f"{name}: {downloaded / 1024**2:.0f}/{expected_size / 1024**2:.0f} MiB", flush=True)
                            last_print = time.monotonic()
                if temporary.stat().st_size != expected_size or digest(temporary) != expected_md5:
                    raise ValueError(f"Size/checksum mismatch: {name}")
                temporary.replace(path)
                print(f"Downloaded and verified {name}", flush=True)
                break
            except Exception as exc:
                print(f"Attempt {attempt + 1} {name}: {type(exc).__name__}: {exc}", flush=True)
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
    return {"file": name, "url": url, "bytes": expected_size, "md5": expected_md5,
            "release_date": "2024-12-31", "zenodo_record": RECORD,
            "source": "USPTO PatentsView", "retrieved_utc": "2026-10-04"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--skip-abstract", action="store_true")
    args = parser.parse_args()
    (ROOT / "cache").mkdir(exist_ok=True)
    names = [n for n in FILES if not (args.skip_abstract and n == "g_patent_abstract.tsv.zip")]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(fetch, names))
    (ROOT / "data" / "source_manifest.json").write_text(json.dumps(results, indent=2) + "\n")