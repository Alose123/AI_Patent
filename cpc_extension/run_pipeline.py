"""Run offline from bundled government subsets, or refresh from verified bulk inputs."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--refresh-bulk",action="store_true",help="Download ~2.75 GB fixed inputs, re-extract target metadata and re-run")
    args=parser.parse_args()
    stages=["03_technology_analysis.py","04_visualizations.py","05_report.py","06_verify_and_package.py"]
    if args.refresh_bulk:stages=["01_fetch_enrichment.py","02_extract_enrichment.py"]+stages
    for name in stages:
        print(f"Running {name}",flush=True)
        subprocess.run([sys.executable,str(ROOT/"code"/name)],check=True,cwd=ROOT)