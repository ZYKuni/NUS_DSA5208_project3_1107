#!/usr/bin/env python3
"""Assemble the audited main CPU run and full weak-3D repair without duplication.

This writes a dataset manifest, not a fictional single-job PBS success record.
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(prefix):
    paths = {k: Path(str(prefix)+'_'+k) for k in ['samples.csv', 'summary.csv', 'manifest.json', 'audit.json']}
    meta = json.loads(paths['manifest.json'].read_text())
    audit = json.loads(paths['audit.json'].read_text())
    assert meta['job_id'] == audit['job_id']
    assert sha(paths['samples.csv']) == audit['sample_sha256']
    assert all(audit[k] is True for k in ['source_hashes_match', 'placement_verified', 'serial_comparisons_pass'])
    samples = list(csv.DictReader(paths['samples.csv'].open()))
    summary = list(csv.DictReader(paths['summary.csv'].open()))
    assert len(samples) == audit['samples'] and len(summary) == audit['groups']
    return meta, audit, samples, summary, {k: sha(v) for k,v in paths.items()}


def obsolete(row):
    return (row['dim'] == '3' and row['experiment'] == 'weak' or
            row['dim'] == '3' and row['experiment'] == 'serial' and row['n'] == '202')


def repair_selected(row):
    return row['experiment'] == 'weak' or row['experiment'] == 'serial' and row['n'] == '203'


def combine(main, repair, output):
    m, ma, mr, ms, mh = load(main)
    r, ra, rr, rs, rh = load(repair)
    assert ma['documented_missing_reference_failure'] and ma['groups'] == 92
    assert ra['exit_status'] == 0 and ra['groups'] == 10 and r['suite'] == 'weak3d'
    numerical = {k:v for k,v in m['source_hashes'].items() if k.startswith(('include/', 'src/'))}
    assert all(r['source_hashes'][k] == v for k,v in numerical.items()), 'numerical source changed'
    assert m['binary_hashes'] == r['binary_hashes'], 'CPU binary hashes differ; review before combining'
    samples = [x for x in mr if not obsolete(x)] + [x for x in rr if repair_selected(x)]
    summary = [x for x in ms if not obsolete(x)] + [x for x in rs if repair_selected(x)]
    assert len(summary) == 93 and len(samples) == 279
    groups = collections.Counter((x['job_id'], x['group']) for x in samples)
    assert len(groups) == 93 and set(groups.values()) == {3}
    assert {(int(x['ranks']),int(x['n'])) for x in summary if x['experiment']=='weak' and x['dim']=='3'} == {
        (1,32),(8,64),(64,128),(216,192),(256,203)}
    assert all(x['job_id'] == r['job_id'] for x in summary if x['experiment']=='weak' and x['dim']=='3')
    output.parent.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, rows in [('samples.csv',samples),('summary.csv',summary)]:
        path = Path(str(output)+'_'+name)
        with path.open('w',newline='') as stream:
            writer = csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
            writer.writeheader();writer.writerows(rows)
        hashes[name] = sha(path)
    manifest = dict(status='complete audited CPU matrix assembled from two jobs', groups=93, samples=279,
                    sources=[dict(job_id=m['job_id'],exit_status=ma['exit_status'],sha256=mh),
                             dict(job_id=r['job_id'],exit_status=ra['exit_status'],sha256=rh)],
                    numerical_source_hashes_match=True,binary_hashes_match=True,
                    exclusions=[dict(job_id=m['job_id'],group=x['group'],reason='replaced entire weak curve or unused n=202 reference')
                                for x in ms if obsolete(x)] +
                               [dict(job_id=r['job_id'],group=x['group'],reason='duplicate mesh reference retained in repair export')
                                for x in rs if not repair_selected(x)],
                    weak3d_job_id=r['job_id'], output_sha256=hashes)
    Path(str(output)+'_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--main',type=Path,required=True)
    p.add_argument('--repair',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    combine(a.main,a.repair,a.output)


if __name__ == '__main__':main()
