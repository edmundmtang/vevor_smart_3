"""VEVOR Smart 3: SVG -> HPGL and guarded experimental USB transmission.

Only simple, untransformed SVG geometry is supported. Unsupported drawing
elements fail closed. Live USB writes are EXPERIMENTAL and require confirmation.
"""
from __future__ import annotations
import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SETTINGS_PATH = Path(__file__).resolve().parent / 'settings.txt'
KEYS = ('x_scale', 'y_scale', 'x_offset', 'y_offset')
BOOLEAN_KEYS = ('preserve_origin',)
CHOICE_KEYS = ('finish_mode',)
CUT_KEYS = ('cut_force', 'cut_speed')
MAT_KEYS = ('mat_width_mm', 'mat_height_mm')
DEFAULT_MAT = {'mat_width_mm': 304.8, 'mat_height_mm': 304.8}
DEFAULT_CUT = {'cut_force': 200, 'cut_speed': 100}
ALL_KEYS = KEYS + BOOLEAN_KEYS + CHOICE_KEYS + CUT_KEYS + MAT_KEYS
UNITS_PER_MM = 40.0  # observed in ExactCut square capture; not yet validated for custom sending
NUMBER = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
SUPPORTED = {'svg', 'g', 'rect', 'line', 'polyline', 'polygon', 'circle', 'ellipse', 'path', 'defs', 'metadata', 'title', 'desc', 'namedview'}


def load_settings(path=SETTINGS_PATH):
    if not path.is_file():
        raise ValueError(f'Missing settings file: {path}')
    values = {}
    for line_number, raw in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        if '=' not in line:
            raise ValueError(f'{path}:{line_number}: expected key = value')
        key, value = [part.strip() for part in line.split('=', 1)]
        if key not in ALL_KEYS or key in values:
            raise ValueError(f'{path}:{line_number}: unknown or duplicate setting {key!r}')
        if key in CUT_KEYS:
            try:
                parsed = int(value)
            except ValueError as exc:
                raise ValueError(f'{path}:{line_number}: {key} must be an integer') from exc
            if not 1 <= parsed <= 300:
                raise ValueError(f'{path}:{line_number}: {key} must be between 1 and 300 (conservative software limit)')
            values[key] = parsed
        elif key in CHOICE_KEYS:
            if value.lower() not in ('standard', 'minimal'):
                raise ValueError(f'{path}:{line_number}: {key} must be standard or minimal')
            values[key] = value.lower()
        elif key in BOOLEAN_KEYS:
            if value.lower() not in ('true', 'false'):
                raise ValueError(f'{path}:{line_number}: {key} must be true or false')
            values[key] = value.lower() == 'true'
        else:
            try:
                values[key] = float(value)
            except ValueError as exc:
                raise ValueError(f'{path}:{line_number}: invalid {key}') from exc
    if not set(ALL_KEYS).difference(CUT_KEYS).issubset(values):
        raise ValueError(f'Missing settings: {sorted(set(ALL_KEYS).difference(CUT_KEYS)-set(values))}')
    for key, default in DEFAULT_CUT.items():
        values.setdefault(key, default)
    for key, default in DEFAULT_MAT.items():
        values.setdefault(key, default)
    return values


def length_mm(value):
    match = re.fullmatch(rf'\s*({NUMBER})\s*(mm|cm|in|px|pt|pc|q)?\s*', value or '', re.I)
    if not match:
        raise ValueError(f'Unsupported SVG length {value!r}; use mm, cm, in, px, pt, pc, or q')
    number, unit = float(match[1]), (match[2] or 'px').lower()
    return number * {'mm':1, 'cm':10, 'in':25.4, 'px':25.4/96, 'pt':25.4/72, 'pc':25.4/6, 'q':.25}[unit]


def local(tag):
    return tag.rsplit('}', 1)[-1]


def num(node, key, default='0'):
    raw = node.get(key, default)
    if not re.fullmatch(rf'\s*{NUMBER}\s*', raw):
        raise ValueError(f'Unsupported {key}={raw!r}; convert dimensions to plain numbers')
    return float(raw)


def parse_svg(path):
    root = ET.parse(path).getroot()
    if local(root.tag) != 'svg':
        raise ValueError('File is not an SVG')
    if root.get('preserveAspectRatio') not in (None, 'xMidYMid meet', 'none'):
        raise ValueError('Unsupported preserveAspectRatio; export as Plain SVG')
    vb = root.get('viewBox')
    if vb:
        coords = [float(x) for x in re.findall(NUMBER, vb)]
        if len(coords) != 4 or coords[2] <= 0 or coords[3] <= 0:
            raise ValueError('Invalid viewBox')
        left, top, vw, vh = coords
        if root.get('width') is None or root.get('height') is None:
            raise ValueError('SVG with viewBox needs physical width and height (e.g. 50.8mm)')
        sx, sy = length_mm(root.get('width')) / vw, length_mm(root.get('height')) / vh
    else:
        left = top = 0.0
        sx = sy = 1.0
        if root.get('width') and root.get('height'):
            sx = length_mm(root.get('width')) / float(re.findall(NUMBER, root.get('width'))[0])
            sy = length_mm(root.get('height')) / float(re.findall(NUMBER, root.get('height'))[0])
    if abs(sx - sy) > 1e-7 and root.get('preserveAspectRatio') != 'none':
        raise ValueError('Unequal SVG viewBox scaling is unsupported; use equal aspect ratio')
    outlines = []

    def point(x, y):
        return ((x-left)*sx, (y-top)*sy)

    def walk(node, inside_defs=False):
        tag = local(node.tag)
        if tag not in SUPPORTED:
            raise ValueError(f'Unsupported SVG element <{tag}>; convert to paths or remove it')
        if node.get('transform'):
            raise ValueError('SVG transforms are not yet supported; flatten transforms in Inkscape')
        if node.get('style') and re.search(r'(?:display\s*:\s*none|visibility\s*:\s*hidden)', node.get('style'), re.I):
            return
        if node.get('display') == 'none' or node.get('visibility') == 'hidden':
            return
        if inside_defs or tag == 'defs':
            return
        if tag in ('svg','g','metadata','title','desc','namedview'):
            for child in node:
                walk(child)
            return
        paths = []
        if tag == 'rect':
            if num(node, 'rx') or num(node, 'ry'):
                raise ValueError('Rounded rectangles not supported; convert to paths')
            x, y, w, h = [num(node, k) for k in ('x','y','width','height')]
            if w > 0 and h > 0:
                paths = [[(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)]]
        elif tag == 'line':
            paths = [[(num(node,'x1'),num(node,'y1')),(num(node,'x2'),num(node,'y2'))]]
        elif tag in ('polygon','polyline'):
            nums = [float(v) for v in re.findall(NUMBER, node.get('points',''))]
            if len(nums)%2 or len(nums)<4:
                raise ValueError('Invalid polygon/polyline points')
            pts = list(zip(nums[::2], nums[1::2]))
            if tag == 'polygon': pts.append(pts[0])
            paths = [pts]
        elif tag in ('circle','ellipse'):
            cx, cy = num(node,'cx'), num(node,'cy')
            rx = num(node, 'r') if tag == 'circle' else num(node, 'rx')
            ry = num(node, 'r') if tag == 'circle' else num(node, 'ry')
            if rx > 0 and ry > 0:
                steps = max(32, math.ceil(2*math.pi*max(rx*sx,ry*sy)/0.3))
                paths = [[(cx+rx*math.cos(2*math.pi*i/steps),cy+ry*math.sin(2*math.pi*i/steps)) for i in range(steps+1)]]
        elif tag == 'path':
            try:
                from svgpathtools import parse_path
            except ImportError as exc:
                raise ValueError('For SVG <path> elements, install: py -m pip install svgpathtools') from exc
            path_obj = parse_path(node.get('d',''))
            for sub in path_obj.continuous_subpaths():
                if not len(sub): continue
                pts = [(sub[0].start.real,sub[0].start.imag)]
                for seg in sub:
                    # Oversample curves to about 0.3mm between points.
                    steps = max(1, math.ceil(seg.length(error=1e-3)*max(sx,sy)/0.3))
                    if steps > 50000:
                        raise ValueError('Path segment too complex')
                    pts.extend((seg.point(i/steps).real,seg.point(i/steps).imag) for i in range(1,steps+1))
                paths.append(pts)
        for p in paths:
            converted = [point(x,y) for x,y in p]
            if len(converted) >= 2:
                outlines.append(converted)

    walk(root)
    if not outlines:
        raise ValueError('No supported cutting geometry found')
    return outlines


def make_hpgl(outlines, settings):
    commands = (['SP1;'] if settings['preserve_origin'] else ['IN;', 'SP1;'])
    bounds = [float('inf'),float('inf'),float('-inf'),float('-inf')]
    for outline in outlines:
        coords = []
        for x,y in outline:
            tx = x*settings['x_scale'] + settings['x_offset']
            ty = y*settings['y_scale'] + settings['y_offset']
            if not math.isfinite(tx) or not math.isfinite(ty):
                raise ValueError('Non-finite corrected coordinate')
            if tx < 0 or ty < 0:
                raise ValueError('Corrected geometry contains negative coordinates; adjust offsets')
            bounds[0],bounds[1] = min(bounds[0],tx),min(bounds[1],ty)
            bounds[2],bounds[3] = max(bounds[2],tx),max(bounds[3],ty)
            xy = (round(tx*UNITS_PER_MM),round(ty*UNITS_PER_MM))
            if not coords or xy != coords[-1]:
                coords.append(xy)
        if len(coords) < 2: continue
        commands.append(f'PU{coords[0][0]},{coords[0][1]};')
        for x,y in coords[1:]:
            commands.append(f'PD{x},{y};')
    # Minimal mode deliberately avoids moving back to (0,0) and avoids SP2/PG.
    # This isolates whether end-of-job commands cause an origin reset.
    if settings['finish_mode'] == 'minimal':
        commands.append('PU;')
    else:
        commands.extend(['PU0,0;', 'SP2;', 'PG;'])
    return '\n'.join(commands)+'\n', bounds



def get_physical_bounds(outlines):
    points = [p for outline in outlines for p in outline]
    if not points or any(not (math.isfinite(x) and math.isfinite(y)) for x, y in points):
        raise ValueError('SVG has no finite geometry coordinates')
    return [min(x for x, y in points), min(y for x, y in points),
            max(x for x, y in points), max(y for x, y in points)]


def check_mat_limits(physical_bounds, corrected_bounds, settings):
    """Check intended SVG positions against mat size, NOT calibrated HPGL values."""
    for axis, low, high, limit in (
        ('X', physical_bounds[0], physical_bounds[2], settings['mat_width_mm']),
        ('Y', physical_bounds[1], physical_bounds[3], settings['mat_height_mm']),
    ):
        if low < -1e-7 or high > limit + 1e-7:
            raise ValueError(f'MAT LIMIT: physical {axis} coordinates {low:.3f}..{high:.3f} mm '
                             f'must fit inside 0..{limit:.3f} mm. No USB data sent.')
    # Warn when the geometry reaches 90% of either configured axis travel.
    # Use absolute position as well as span: a small job near the far edge matters.
    for axis, low, high, limit in (
        ('X', physical_bounds[0], physical_bounds[2], settings['mat_width_mm']),
        ('Y', physical_bounds[1], physical_bounds[3], settings['mat_height_mm']),
    ):
        if high >= 0.9 * limit:
            print(f'WARNING: {axis} reaches {high:.3f} mm '
                  f'({100*high/limit:.1f}% of configured {limit:.3f} mm travel).', flush=True)
    # Independent sanity guard for command coordinates, not a second physical mat size.
    # The calibrated Y axis can legitimately exceed 304.8 command-space mm.
    for axis, low, high, scale, offset, limit in (
        ('X', corrected_bounds[0], corrected_bounds[2], settings['x_scale'], settings['x_offset'], settings['mat_width_mm']),
        ('Y', corrected_bounds[1], corrected_bounds[3], settings['y_scale'], settings['y_offset'], settings['mat_height_mm']),
    ):
        if not (math.isfinite(low) and math.isfinite(high)) or low < 0:
            raise ValueError(f'COMMAND SAFETY: invalid {axis} command coordinates')
        expected_max = limit * scale + offset
        if high > expected_max + 1e-6:
            raise ValueError(f'COMMAND SAFETY: {axis} exceeds calibrated mat limit')
        if round(high * UNITS_PER_MM) > 100000:
            raise ValueError(f'COMMAND SAFETY: {axis} HPGL coordinate exceeds 100000 units')


def send_live_job(hpgl, bounds, preserve_origin, finish_mode, cut_force, cut_speed):
    """EXPERIMENTAL: send one job to the existing Windows usbprint device.

    Captured ExactCut commands provide a tentative framing example, NOT a
    verified specification. No USB response/handshake is implemented yet.
    """
    import ctypes
    from ctypes import wintypes
    from smart3_usb_probe import enumerate_usbprint, VID_PID, INVALID_HANDLE_VALUE, GENERIC_WRITE, OPEN_EXISTING

    # Physical mat limits are checked by check_mat_limits before this function.
    paths = [path for path in enumerate_usbprint() if VID_PID in path.lower()]
    if len(paths) != 1:
        raise ValueError(f'Expected exactly one Smart 3 USB interface, found {len(paths)}')

    # ExactCut capture included setmat/JS, IN, SP1/FS/VS, and a final PU/SP2/PG.
    # Do NOT use our generated IN/SP1 header verbatim; supply observed framing.
    lines = hpgl.splitlines()
    expected_header = ['SP1;'] if preserve_origin else ['IN;', 'SP1;']
    trailer = ['PU;'] if finish_mode == 'minimal' else ['PU0,0;', 'SP2;', 'PG;']
    if lines[:len(expected_header)] != expected_header or lines[-len(trailer):] != trailer:
        raise ValueError('Unexpected generated HPGL framing; refusing to transmit')
    # Only the IN; token changes between modes. setmat/JS and job trailer
    # remain as in v0.5. Firmware may still reset the origin independently.
    initialization = '' if preserve_origin else 'IN;'
    finish = 'PU;' if finish_mode == 'minimal' else 'PU0,0;SP2;PU0,0;PG;'
    payload = ('setmat:1;JS12192,12192;' + initialization + f'SP1;FS{cut_force};VS{cut_speed};'
               + ''.join(lines[len(expected_header):-len(trailer)])
               + finish).encode('ascii')
    # Job size is not a motion-safety metric. Windows WriteFile receives the
    # entire payload; a failed or partial write is reported rather than retried
    # (retries could duplicate cutting commands). The device's buffering
    # capacity is not established; start with a small job.
    print(f'USB payload: {len(payload):,} bytes (single WriteFile; no job-size cap)', flush=True)

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                   ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = ctypes.c_void_p
    kernel.WriteFile.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD,
                                 ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
    kernel.WriteFile.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle.restype = wintypes.BOOL
    # No shared write access: avoid another process interleaving our commands.
    handle = kernel.CreateFileW(paths[0], GENERIC_WRITE, 0, None, OPEN_EXISTING, 0, None)
    if handle == INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        count = wintypes.DWORD(0)
        buffer = ctypes.create_string_buffer(payload)
        if not kernel.WriteFile(handle, buffer, len(payload), ctypes.byref(count), None):
            raise ctypes.WinError(ctypes.get_last_error())
        if count.value != len(payload):
            raise OSError(f'Partial USB write: {count.value} of {len(payload)} bytes')
        return count.value
    finally:
        kernel.CloseHandle(handle)


def main():
    parser = argparse.ArgumentParser(description='Smart 3 SVG -> HPGL; experimental guarded live USB cutting')
    parser.add_argument('svg', type=Path)
    for key in KEYS:
        parser.add_argument('--'+key.replace('_','-'), type=float, default=None)
    parser.add_argument('--preserve-origin', action=argparse.BooleanOptionalAction, default=None,
                        help='Override settings.txt: omit IN; during initialization (experimental)')
    parser.add_argument('--finish-mode', choices=('standard', 'minimal'), default=None,
                        help='Override settings.txt: standard ends with PU0,0/SP2/PG; minimal ends with PU only')
    for key in MAT_KEYS:
        parser.add_argument('--'+key.replace('_','-'), type=float, default=None,
                            help='Physical mat dimension in mm (default 304.8)')
    for key in CUT_KEYS:
        parser.add_argument('--'+key.replace('_','-'), type=int, default=None,
                            help='Override settings.txt for this job (1..300; device units not verified)')
    parser.add_argument('--force', dest='cut_force', type=int, default=argparse.SUPPRESS,
                        help='Alias for --cut-force')
    parser.add_argument('--speed', dest='cut_speed', type=int, default=argparse.SUPPRESS,
                        help='Alias for --cut-speed')
    parser.add_argument('--loop-start', choices=('original', 'auto-straight'), default='original',
                        help='Relocate closed-loop seams onto long straight runs (opt-in; no overcut)')
    parser.add_argument('--min-loop-straight', type=float, default=0.5,
                        help='Minimum straight-run length in mm for seam relocation')
    parser.add_argument('--loop-turn-tolerance', type=float, default=5.0,
                        help='Maximum turn angle in degrees within a straight run')
    parser.add_argument('--cut-strategy', choices=('no-waste', 'keep-inside', 'keep-outside'), default='no-waste',
                        help='Material preservation intent. All modes currently use on-contour cuts only; off-contour lead-ins are NOT implemented.')
    parser.add_argument('--contour-modes', type=Path,
                        help='Optional JSON map of zero-based path indices to per-contour cut strategy')
    parser.add_argument('--loop-overlap-mm', type=float, default=0.0,
                        help='Retrace the start of the closed contour across multiple segments (mm); default disabled')
    parser.add_argument('--blade-offset-mm', type=float, default=0.0,
                        help='EXPERIMENTAL: drag-knife holder path offset in mm (0..2); 0 disables')
    parser.add_argument('--blade-arc-step-deg', type=float, default=10.0,
                        help='Max angular step for holder pivot arcs (1..45 degrees)')
    parser.add_argument('--lead-in-mm', type=float, default=0.0,
                        help='Reserved: off-contour lead-ins NOT implemented; nonzero is rejected')
    parser.add_argument('--dry-run' , action='store_true', help='Generate HPGL only; no USB data sent')
    parser.add_argument('--output', type=Path, help='HPGL output file (default: beside SVG)')
    parser.add_argument('--usb-check', action='store_true', help='Check USB write-open access; sends no bytes')
    parser.add_argument('--cut', action='store_true', help='EXPERIMENTAL: transmit a live job to the cutter (requires --confirm-live-test)')
    parser.add_argument('--confirm-live-test', default='', metavar='PHRASE', help='For --cut only: type I_ACCEPT_MOVEMENT to acknowledge experimental motion')
    args = parser.parse_args()
    if args.cut and args.dry_run:
        parser.error('--cut and --dry-run cannot be used together')
    try:
        settings = load_settings()
        for key in ALL_KEYS:
            if getattr(args,key) is not None:
                settings[key] = getattr(args,key)
        for key in CUT_KEYS:
            val = settings[key]
            if not 1 <= val <= 300:
                raise ValueError(f'{key} must be between 1 and 300 (conservative software limit)')
        for key in KEYS:
            val = settings[key]
            if not math.isfinite(val) or (key.endswith('scale') and val <= 0):
                raise ValueError(f'Invalid {key}: {val}')
        for key in MAT_KEYS:
            val = settings[key]
            if not math.isfinite(val) or not 0 < val <= 304.8:
                raise ValueError(f'{key} must be > 0 and <= 304.8 mm (12-inch mat)')
        if not args.svg.is_file():
            raise ValueError(f'SVG not found: {args.svg}')
        outlines = parse_svg(args.svg)
        if not math.isfinite(args.min_loop_straight) or args.min_loop_straight <= 0:
            raise ValueError('--min-loop-straight must be positive and finite')
        if not math.isfinite(args.loop_turn_tolerance) or not 0 <= args.loop_turn_tolerance < 90:
            raise ValueError('--loop-turn-tolerance must be in [0, 90) degrees')
        if not math.isfinite(args.loop_overlap_mm) or args.loop_overlap_mm < 0 or args.loop_overlap_mm > 5:
            raise ValueError('--loop-overlap-mm must be finite and between 0 and 5 mm')
        if args.lead_in_mm != 0:
            raise ValueError('Off-contour lead-ins are not implemented. --lead-in-mm must be 0; NO DATA SENT.')
        modes = {}
        if args.contour_modes:
            raw = json.loads(args.contour_modes.read_text(encoding='utf-8'))
            if not isinstance(raw, dict):
                raise ValueError('Contour modes must be a JSON object keyed by zero-based path index')
            for k, mode in raw.items():
                if not isinstance(k, str) or not k.isdecimal() or str(int(k)) != k or int(k) >= len(outlines):
                    raise ValueError(f'Invalid contour index {k!r}; must be 0..{len(outlines)-1}')
                if mode not in ('no-waste', 'keep-inside', 'keep-outside'):
                    raise ValueError(f'Invalid contour strategy {mode!r} at index {k}')
                modes[int(k)] = mode
        from loop_closure import relocate, add_same_path_overlap
        from blade_offset import compensate
        processed, counts = [], {}
        for index, outline in enumerate(outlines):
            mode = modes.get(index, args.cut_strategy)
            new, seam_info = relocate(outline, args.loop_start, args.min_loop_straight,
                                      args.loop_turn_tolerance)
            new, overlap_info = add_same_path_overlap(new, args.loop_overlap_mm)
            new, blade_info = compensate(new, args.blade_offset_mm, args.blade_arc_step_deg)
            processed.append(new)
            key = (mode, seam_info, overlap_info, blade_info)
            counts[key] = counts.get(key, 0) + 1
        outlines = processed
        print('Closure diagnostics (all strategies currently prohibit off-contour lead-ins):')
        for (mode, seam_info, overlap_info, blade_info), count in sorted(counts.items()):
            print(f'  {count} path(s): {mode}; {seam_info}; {overlap_info}; blade: {blade_info}')
        if args.blade_offset_mm > 0:
            print('WARNING: EXPERIMENTAL blade-offset holder compensation; pivot arcs leave the nominal contour. Not strict no-waste; inspect HPGL before live cutting.')
        physical_bounds = get_physical_bounds(outlines)
        hpgl,bounds = make_hpgl(outlines,settings)
        check_mat_limits(physical_bounds, bounds, settings)
        output = args.output or args.svg.with_suffix('.hpgl')
        output.write_text(hpgl, encoding='ascii')
        print(f'SVG: {args.svg.resolve()}')
        print(f'Settings file: {SETTINGS_PATH}')
        for key in ALL_KEYS: print(f'{key}: {str(settings[key]).lower() if key in BOOLEAN_KEYS else settings[key]}')
        print(f'Live USB cutting: SP1;FS{settings["cut_force"]};VS{settings["cut_speed"]};')
        print('Live USB ending: ' + ('PU; only (experimental)' if settings['finish_mode'] == 'minimal' else 'PU0,0;SP2;PU0,0;PG;'))
        print(f'Paths: {len(outlines)}; default strategy: {args.cut_strategy}; loop start: {args.loop_start}; requested overlap: {args.loop_overlap_mm} mm; blade offset: {args.blade_offset_mm} mm')
        print(f'Physical SVG bounds (mm): X {physical_bounds[0]:.3f}..{physical_bounds[2]:.3f}, Y {physical_bounds[1]:.3f}..{physical_bounds[3]:.3f}')
        print(f'Physical mat limits (mm): X 0..{settings["mat_width_mm"]:.3f}, Y 0..{settings["mat_height_mm"]:.3f}')
        print(f'Corrected bounds (mm): X {bounds[0]:.3f}..{bounds[2]:.3f}, Y {bounds[1]:.3f}..{bounds[3]:.3f}')
        print(f'HPGL written: {output.resolve()}')
        if args.usb_check:
            if sys.platform != 'win32':
                raise ValueError('--usb-check requires Windows')
            from smart3_usb_probe import enumerate_usbprint, open_only, VID_PID
            matches = [path for path in enumerate_usbprint() if VID_PID in path.lower()]
            if len(matches) != 1:
                raise ValueError(f'Expected exactly one Smart 3 USB interface; found {len(matches)}')
            open_only(matches[0], write_access=True)
            print('Smart 3 USB write-open: SUCCESS (no bytes transmitted)')
        if args.cut:
            if args.confirm_live_test != 'I_ACCEPT_MOVEMENT':
                raise ValueError('LIVE CUT BLOCKED: add --confirm-live-test I_ACCEPT_MOVEMENT to authorize experimental motion; NO DATA SENT')
            if sys.platform != 'win32':
                raise ValueError('--cut requires Windows')
            print('WARNING: EXPERIMENTAL USB write. Device may move unexpectedly; no response handshake is implemented.', flush=True)
            print('Origin mode: ' + ('preserve (omit IN;)' if settings['preserve_origin'] else 'standard (send IN;)'), flush=True)
            sent = send_live_job(hpgl, bounds, settings['preserve_origin'], settings['finish_mode'],
                                 settings['cut_force'], settings['cut_speed'])
            print(f'USB write completed: {sent} bytes (does NOT prove cutter executed job)')
        else:
            print('NO CUT SENT: offline HPGL generation only.')
    except (ValueError,ET.ParseError,OSError,json.JSONDecodeError) as exc:
        parser.exit(1, f'Error: {exc}\n')

if __name__ == '__main__':
    main()
