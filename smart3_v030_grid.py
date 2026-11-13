"""Generate compact uncompensated and v0.30 compensated cases 4 and 6."""
import argparse, math
from pathlib import Path
from smart3_v029_grid import cases, save
from blade_tip_clean import CleanConfig, compensate, component_audit
from smart3_cut import parse_svg

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output-dir',type=Path,default=Path('v030_comparison'))
    ap.add_argument('--tip-history-mm',type=float,default=-.300)
    args=ap.parse_args()
    groups=[cases()[3],cases()[5]]
    cfg=CleanConfig(lateral_history_mm=args.tip_history_mm)
    target=args.output_dir/'v030_original.svg'
    predicted=args.output_dir/'v030_clean_compensated.svg'
    args.output_dir.mkdir(parents=True,exist_ok=True)
    save(target,groups)
    output=[[compensate(path,cfg,closed=(math.dist(path[0],path[-1])<1e-6)) for path in group] for group in groups]
    save(predicted,output)
    for filename in (target,predicted):
        paths=parse_svg(filename)
        if len(paths)!=4 or any(not (0<=x<=124 and 0<=y<=111) for path in paths for x,y in path):
            raise ValueError('Generated SVG outside grid or path count mismatch')
        print(filename, '4 paths; within 124 x 111 mm SVG')
    print('Single-model audit:',component_audit(cfg))
    print('The compensated SVG is a HOLDER path. Do not apply stateful or legacy compensation again.')
if __name__=='__main__':main()
