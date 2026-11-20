"""Build the atlas basemap and pedestrian graph from overlapping OSM XML extracts."""

import argparse
from collections import defaultdict
import json
from math import hypot
from pathlib import Path
import xml.etree.ElementTree as ET

ROAD = {'primary', 'secondary', 'tertiary', 'residential', 'unclassified',
        'living_street', 'pedestrian', 'footway', 'service', 'trunk',
        'path', 'steps', 'track', 'cycleway', 'primary_link', 'secondary_link',
        'tertiary_link', 'trunk_link', 'motorway', 'motorway_link'}
BLOCKED = {'no', 'private', 'customers', 'permit'}
EXPLICIT_FOOT = {'yes', 'designated', 'permissive'}
ACCESS_ONLY = {'cycleway', 'trunk', 'trunk_link', 'motorway', 'motorway_link'}
METERS_PER_DEGREE = (111195, 95100)


def tags(element):
    return {tag.get('k'): tag.get('v') for tag in element.findall('tag')}


def walkable(way):
    kind = way.get('highway')
    if kind not in ROAD or way.get('area') == 'yes' or way.get('foot') in BLOCKED:
        return False
    if kind in {'motorway', 'motorway_link'} or way.get('motorroad') == 'yes':
        return False
    explicit = way.get('foot') in EXPLICIT_FOOT
    if explicit:
        return True
    if kind in ACCESS_ONLY or way.get('access') in BLOCKED:
        return False
    if way.get('service') in {'driveway', 'drive-through', 'emergency_access'}:
        return False
    return way.get('sidewalk') not in {'no', 'separate'} or kind not in {
        'primary', 'primary_link', 'secondary', 'secondary_link', 'tertiary', 'tertiary_link',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--venues', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('extracts', type=Path, nargs='+')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    data = json.loads(args.venues.read_text())
    nodes, ways, barriers = {}, {}, {}
    for file in args.extracts:
        for item in ET.parse(file).getroot():
            if item.tag not in {'node', 'way'}:
                continue
            key = int(item.get('id'))
            ver = int(item.get('version', '0'))
            attributes = tags(item)
            if item.tag == 'node' and (key not in nodes or ver >= nodes[key][0]):
                nodes[key] = (ver, (float(item.get('lat')), float(item.get('lon'))))
                barriers[key] = (attributes.get('foot') in BLOCKED or
                                 attributes.get('access') in BLOCKED and attributes.get('foot') not in EXPLICIT_FOOT)
            if item.tag == 'way' and (key not in ways or ver >= ways[key][0]):
                ways[key] = (ver, [int(ref.get('ref')) for ref in item.findall('nd')], attributes)
    coords = {key: pos for key, (_, pos) in nodes.items()}

    features, links = [], set()
    for _, refs, fields in ways.values():
        kind = fields.get('highway')
        if len(refs) < 2 or any(n not in coords for n in refs):
            continue
        if refs[0] == refs[-1]:
            if fields.get('leisure') in {'park', 'garden'}:
                kind = 'park'
            elif fields.get('natural') == 'water':
                kind = 'water'
            elif fields.get('building'):
                kind = 'building'
        if kind in ROAD | {'water', 'park', 'building', 'river', 'canal'} or fields.get('waterway') in {'river', 'canal'}:
            if kind not in ROAD | {'water','park','building'}:
                kind = 'shore'
            features.append([kind, fields.get('name:zh', fields.get('name', '')),
                             fields.get('name:en', ''), [[round(v, 5) for v in coords[n]] for n in refs]])
        if walkable(fields):
            for a, b in zip(refs, refs[1:]):
                if a != b and coords[a] != coords[b] and not barriers[a] and not barriers[b]:
                    links.add(tuple(sorted((a, b))))

    graph = defaultdict(set)
    for a, b in links:
        graph[a].add(b)
        graph[b].add(a)
    group = set()
    remaining = set(graph)
    while remaining:
        seed = remaining.pop()
        component = {seed}
        stack = [seed]
        while stack:
            for neighbor in graph[stack.pop()]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        if len(component) > len(group):
            group = component
    links = {(a,b) for a,b in links if a in group}
    # Connect each venue to the nearest segment of the continuous pedestrian network.
    projected = {node: tuple(v * factor for v,factor in zip(pos,METERS_PER_DEGREE))
                 for node,pos in coords.items() if node in group}
    segments = [(a,b,*projected[a],projected[b][0]-projected[a][0],projected[b][1]-projected[a][1])
                for a,b in sorted(links)]
    cuts = defaultdict(list)
    points = sorted(group)
    for i, place in enumerate(data['places'], 1):
        feature, key = place['osm'].split('/')[-2:]
        number = int(key)
        if feature == 'node':
            position = coords[number]
        else:
            refs = list(dict.fromkeys(ways[number][1]))
            position = tuple(sum(values)/len(refs) for values in zip(*(coords[k] for k in refs)))
        place['position'] = [round(v, 6) for v in position]
        x, y = (v * factor for v,factor in zip(position,METERS_PER_DEGREE))
        best = None
        for a,b,px,py,dx,dy in segments:
            if abs(px-x)>160+abs(dx) or abs(py-y)>160+abs(dy):
                continue
            portion = max(0, min(1, ((x-px)*dx+(y-py)*dy)/(dx*dx+dy*dy)))
            point = (px+portion*dx,py+portion*dy)
            length = hypot(point[0]-x,point[1]-y)
            if best is None or length < best[0]:
                best = length,a,b,portion,point
        assert best is not None, place['name']
        length,a,b,portion,point = best
        assert length <= 120, (place['name'], length)
        gate = -i
        coords[gate] = tuple(v / factor for v,factor in zip(point,METERS_PER_DEGREE))
        point_index = len(points)
        points.append(gate)
        cuts[(a,b)].append((portion,gate))
        place['walkNode'] = point_index
        place['walkAccessMeters'] = round(length)
        print(place['name'], place['position'], f'{length:.1f} m')
    for (a,b), inserts in cuts.items():
        sequence = [a, *(gate for _,gate in sorted(inserts)), b]
        links.remove((a,b))
        links.update(zip(sequence,sequence[1:]))
    index = {point:i for i,point in enumerate(points)}
    roads = [[index[a],index[b]] for a,b in sorted(links)]
    meters = [[round(v*1_000_000) for v in coords[n]] for n in points]
    dump = lambda obj: json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    attribution = '/* © OpenStreetMap contributors · Open Database License 1.0 */\n'
    (args.output/'streets.js').write_text(attribution+'const streets = '+dump(features)+';\n')
    (args.output/'walking-data.js').write_text(attribution+'const walkingData = '+dump([meters,roads])+';\n')
    args.venues.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(len(points), 'vertices', len(roads), 'segments', len(features), 'map features')


if __name__ == '__main__':
    main()
