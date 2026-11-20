"""Rebuild the offline photon-profile view from Li's archived points.csv."""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'assets/public-data/reef-points.csv'
SHA256 = '3fa22e153417818e794d88d0507df7e2af1a80a08067764bb8cefa1fb01777cd'


def build():
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SHA256:
        raise ValueError('Source does not match the published portfolio archive')
    beams = defaultdict(list)
    with SOURCE.open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.DictReader(stream):
            beam = row['GT Num']
            if beam:
                beams[beam].append(tuple(float(row[key]) for key in
                                         ('Delta Time (sec)', 'Along-Track (m)', 'Height (m MSL)')))
    profiles = []
    for beam, observations in sorted(beams.items()):
        segments = []
        for point in sorted(observations):
            if not segments or point[0] - segments[-1][-1][0] > 60:
                segments.append([])
            segments[-1].append(point)
        for number, segment in enumerate(segments, start=1):
            ordered = sorted(segment, key=lambda point: point[1])
            heights = [p[2] for p in ordered]
            limit = min(320, len(ordered))
            points = [ordered[round(i * (len(ordered)-1)/(limit-1))] for i in range(limit)]
            profiles.append(dict(beam=beam, segment=number, count=len(segment),
                                 median=median(heights), low=min(heights), high=max(heights),
                                 points=[[round(p[1],3), round(p[2],4)] for p in points]))
    data = dict(source_sha256=SHA256, profiles=profiles, count=sum(map(len, beams.values())))
    (ROOT/'web/plot-data.js').write_text('const reefObservations = '+json.dumps(data,separators=(',',':'))+';\n')


if __name__ == '__main__':
    build()
