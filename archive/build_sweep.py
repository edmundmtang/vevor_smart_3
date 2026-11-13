"""Build a single 3x3 per-column HPGL sweep OFFLINE ONLY (no USB imports)."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent

def build(project, output, reach=(0.0,0.10,0.20), support=1.0):
    project = Path(project).resolve()
    sys.path.insert(0,str(project))
    from smart3_cut import parse_svg, load_settings, make_hpgl, check_mat_limits, get_physical_bounds
    from blade_tip_clean import compensate, CleanConfig
    from loop_closure import relocate, add_same_path_overlap
    from corner_reach import apply_corner_reach
    target = ROOT/'corner_sweep_target.svg'
    outlines = parse_svg(target)
    if len(outlines) != 15: raise ValueError('Expected 15 contours across 9 cells')
    settings = load_settings(project/'settings.txt')
    results=[]
    for index, original in enumerate(outlines):
        col=index//5
        base,_=relocate(original,'original')
        base,_=add_same_path_overlap(base,0.0)
        closed=len(base)>2 and base[0]==base[-1]
        holder=compensate(base,CleanConfig(),closed=closed)
        results.append(apply_corner_reach(holder,base,reach[col],support))
    hpgl,bounds=make_hpgl(results,settings)
    check_mat_limits(get_physical_bounds(results),bounds,settings)
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(hpgl,encoding='ascii')
    report={'status':'offline_only_not_physically_validated','baseline':'v0.30',
            'reach_mm_by_column':dict(zip('ABC',reach)),'support_mm':support,
            'contours':len(results),'holder_bounds_mm':get_physical_bounds(results),
            'command_bounds_mm':bounds,'settings':settings,
            'original_svg':target.name,'hpgl':output.name}
    output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',required=True,help='Extracted v0.30 project root')
    p.add_argument('--output',default=str(ROOT/'corner_sweep_v031_EXPERIMENTAL.hpgl'))
    p.add_argument('--reach',type=float,nargs=3,default=[0,.10,.20])
    p.add_argument('--support-mm',type=float,default=1.)
    a=p.parse_args()
    print(json.dumps(build(a.project,a.output,a.reach,a.support_mm),indent=2))
