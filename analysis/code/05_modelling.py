"""Document the decision to avoid an unjustified predictive machine-learning model."""
from common import *

def main():
    args=setup()
    text='''# Modelling decision\n\nThe annual trend regressions in stage 04 are descriptive statistical models.\nNo additional predictive ML model is fitted. The file has no independent\ninnovation/impact target, no text or citation outcomes, and only 14 comparable\nannual points per company. Predicting an AI flag from its component scores or\nother AI flags would reproduce its deterministic construction and leak the\ntarget. A random patent split would also ignore years and possible patent\nfamilies. Forecasts beyond 2023 would require newer data, stable entity coverage\nand a temporal evaluation design. Clustering the supplied classifier scores\nwould mostly repackage known technology labels without validating invention.\n\nReasonable alternatives: a time-series forecasting study with longer\ncomparable histories, manual-label validation with document/family-separated\nsplits, or impact modelling with forward citations and a fixed citation window.\nNone can be validly evaluated from the present extract alone.\n'''
    (args.output/'modelling_decision.md').write_text(text,encoding='utf-8')
    log(args.output,'05','Research objective is portfolio evolution, with no independent outcome target.',
        'A predictive ML model may not improve substantive inference.',
        'Use interpretable annual trend models only; do not train a classifier or forecast.',
        'AI labels are threshold functions of supplied scores; fitting them would be circular. Future activity/impact outcomes are absent.',
        'No predictive ML model added; decision and reasonable extensions documented.',
        'Cannot assess model calibration, future grant activity, commercial relevance, or innovation quality.')
    print('Predictive modelling omitted with documented justification.')

if __name__=='__main__':main()