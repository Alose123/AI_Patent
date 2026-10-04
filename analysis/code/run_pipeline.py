"""Run from any directory: python run_pipeline.py --input source.csv --output outputs."""
from pathlib import Path
import argparse
import subprocess
import sys
from common import sha256, REFERENCE_SOURCE_SHA256

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();root=Path(__file__).resolve().parent
    if not args.input.is_file():p.error('Input CSV does not exist')
    if sha256(args.input)!=REFERENCE_SOURCE_SHA256:
        p.error('This study/report is specific to the supplied extract. Source hash differs; adapt the report builder before using another dataset.')
    for name in ['01_data_validation.py','02_cleaning.py','03_eda.py','04_statistical_analysis.py','05_modelling.py','06_results.py']:
        print(f'Running {name}',flush=True)
        subprocess.run([sys.executable,str(root/name),'--input',str(args.input.resolve()),
                        '--output',str(args.output.resolve())],check=True)

if __name__=='__main__':main()