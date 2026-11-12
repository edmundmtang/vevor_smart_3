"""Conservative, geometric closed-loop seam relocation (physical mm)."""
import math


def relocate(outline, mode='original', min_straight=0.5, max_turn_degrees=5.0):
    """Return (points, info). No added cuts; preserve winding and exact contour.

    Closed paths require first == last (within 1e-7 mm). A straight run is
    contiguous edges separated by turns <= max_turn_degrees. Start at the
    arc-length midpoint of the longest run, splitting an edge if necessary.
    """
    pts = list(outline)
    if mode == 'original':
        return pts, 'original'
    if mode != 'auto-straight':
        raise ValueError('Unknown loop start mode')
    if len(pts) < 4 or math.dist(pts[0], pts[-1]) > 1e-7:
        return pts, 'open/unchanged'
    pts = pts[:-1]
    # Remove adjacent duplicates, including at wraparound.
    cleaned = []
    for p in pts:
        if not cleaned or math.dist(cleaned[-1], p) > 1e-9:
            cleaned.append(p)
    if len(cleaned) > 1 and math.dist(cleaned[0], cleaned[-1]) < 1e-9:
        cleaned.pop()
    n = len(cleaned)
    if n < 3:
        return outline, 'degenerate/unchanged'
    edges = [(cleaned[(i+1)%n][0]-cleaned[i][0], cleaned[(i+1)%n][1]-cleaned[i][1]) for i in range(n)]
    lens = [math.hypot(*e) for e in edges]
    if min(lens) < 1e-9:
        return outline, 'degenerate/unchanged'
    turns = []
    for i in range(n):
        a, b = edges[i-1], edges[i]
        cross = a[0]*b[1]-a[1]*b[0]
        dot = a[0]*b[0]+a[1]*b[1]
        turns.append(abs(math.degrees(math.atan2(cross, dot))))
    boundaries = [i for i, angle in enumerate(turns) if angle > max_turn_degrees]
    if len(boundaries) < 2:
        return outline, 'no distinct straight run/unchanged'
    runs = []
    for j, start in enumerate(boundaries):
        stop = boundaries[(j+1)%len(boundaries)]
        indices = []
        k = start
        while k != stop:
            indices.append(k)
            k = (k+1)%n
        runs.append((sum(lens[k] for k in indices), start, indices))
    # Reject cumulative curvature: every edge must stay close to the first
    # edge direction, not merely turn a small amount relative to its neighbor.
    def truly_straight(indices):
        first = edges[indices[0]]
        first_angle = math.atan2(first[1], first[0])
        for k in indices:
            a = math.atan2(edges[k][1], edges[k][0])
            difference = abs(math.degrees(math.atan2(math.sin(a-first_angle), math.cos(a-first_angle))))
            if difference > max_turn_degrees:
                return False
        return True
    runs = [run for run in runs if truly_straight(run[2])]
    if not runs:
        return outline, 'no globally straight run/unchanged'
    length, start, indices = max(runs, key=lambda r: (r[0], -r[1]))
    if length < min_straight:
        return outline, f'longest straight run {length:.3f} mm below {min_straight:.3f} mm/unchanged'
    remaining = length/2
    for k in indices:
        if remaining <= lens[k]:
            t = remaining/lens[k]
            p = (cleaned[k][0]+t*edges[k][0], cleaned[k][1]+t*edges[k][1])
            # Insert at the seam; never reorder or reverse the original contour.
            new = [p] + [cleaned[(k+1+j)%n] for j in range(n)] + [p]
            # If p coincides with a vertex, remove redundant consecutive points.
            dedup = [new[0]]
            for point in new[1:]:
                if math.dist(point, dedup[-1]) > 1e-9:
                    dedup.append(point)
            if math.dist(dedup[-1], dedup[0]) > 1e-9:
                dedup.append(dedup[0])
            return dedup, f'relocated; straight run {length:.3f} mm'
        remaining -= lens[k]
    raise AssertionError('Straight-run midpoint not found')


def add_same_path_overlap(outline, distance_mm):
    """Append a point along the FIRST existing segment; never leave the contour.

    Reject overlaps longer than the first segment rather than crossing corners.
    A closed path must have at least three distinct vertices. Returns (path, status).
    """
    pts = list(outline)
    if distance_mm == 0:
        return pts, 'disabled'
    if not math.isfinite(distance_mm) or distance_mm < 0:
        raise ValueError('Overlap must be finite and nonnegative')
    if len(pts) < 4 or math.dist(pts[0], pts[-1]) > 1e-7:
        return pts, 'open/unchanged'
    first, second = pts[0], pts[1]
    length = math.dist(first, second)
    if length < 1e-9:
        return pts, 'degenerate/unchanged'
    if distance_mm > length + 1e-8:
        return pts, f'overlap skipped: first segment {length:.3f} mm shorter than {distance_mm:.3f} mm'
    t = min(1.0, distance_mm/length)
    end = (first[0]+t*(second[0]-first[0]), first[1]+t*(second[1]-first[1]))
    return pts + [end], f'overlap {distance_mm:.3f} mm'
