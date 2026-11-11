#!/usr/bin/env python3
"""Independently audit a completed step-3 job and export its accepted CSVs."""
import argparse
import collections
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import statistics


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind',choices=['cpu','gpu'])
    p.add_argument('evidence',type=Path)
    p.add_argument('--jobs-json',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source-root',type=Path)
    p.add_argument('--prefix')
    p.add_argument('--allow-missing-weak3d-reference',action='store_true',
                   help='audit only the 92 completed groups of the documented failed first job')
    a=p.parse_args()
    d=a.evidence/'measurements'
    meta=json.loads((d/'manifest.json').read_text())
    job=json.loads(a.jobs_json.read_text())['Jobs'][meta['job_id']]
    log=(a.evidence/'job.log').read_text()
    if a.allow_missing_weak3d_reference:
        assert a.kind=='cpu' and meta['suite']=='full' and job['Exit_status']==1
        assert "KeyError: (3, 203)" in log and "ref = references[key]" in log
        assert (a.evidence/'exit_code.txt').read_text().strip()=='1'
    else:
        assert job['Exit_status']==0 and (a.evidence/'exit_code.txt').read_text().strip()=='0'
        assert f'{a.kind.upper()}_SCALING_VALIDATION=PASS' in log
        assert f'STEP3_{a.kind.upper()}_COMPLETE' in log
    assert '100% tests passed' in log
    root=a.source_root or Path(__file__).resolve().parent.parent
    for f,h in meta['source_hashes'].items():
        assert hashlib.sha256((root/f).read_bytes()).hexdigest()==h,f
    rows=list(csv.DictReader((d/'samples.csv').open()))
    summary=list(csv.DictReader((d/'summary.csv').open()))
    expected=(92 if a.allow_missing_weak3d_reference else
              10 if a.kind=='cpu' and meta['suite']=='weak3d' else
              93 if a.kind=='cpu' else 20)
    assert len(summary)==expected and len(rows)==expected*3
    groups=collections.defaultdict(list)
    refs={}
    for r in rows:
        groups[r['group']].append(r)
        assert 1<int(r['iters'])<20000 and 0<=float(r['rel_res'])<1e-8
        assert all(math.isfinite(float(r[k])) and float(r[k])>=0 for k in
                   ['t_total','t_stencil','t_halo','t_reduce','rel_res','err_l2'])
        assert float(r['t_total'])>0 and r['job_id']==meta['job_id']
        if r['impl']=='serial':refs[int(r['dim']),int(r['n'])]=r
        rid=r['group']+'-r'+r['repeat']
        places=[json.loads(f.read_text()) for f in (d/'placement'/rid).glob('rank-*.json')]
        assert len(places)==int(r['ranks'])
        cores=set()
        for x in places:
            assert len(x['cpus'])==int(r['threads']) and x['affinity']==sorted(x['cpus'])
            for core in x['physical_cores']:
                key=(x['host'],*core);assert key not in cores;cores.add(key)
        if a.kind=='cpu':assert len(cores)==int(r['physical_cores'])==int(r['ranks'])*int(r['threads'])
        assert len({x['host'] for x in places})==int(r['nodes'])
    for r in rows:
        ref=refs[int(r['dim']),int(r['n'])]
        assert abs(int(r['iters'])-int(ref['iters']))<=1
        assert math.isclose(float(r['err_l2']),float(ref['err_l2']),rel_tol=1e-6)
    assert len(groups)==expected
    for s in summary:
        group=groups[s['group']]
        assert 'GROUP_PASS '+s['group']+' ' in log
        assert sorted(int(r['repeat']) for r in group)==[0,1,2]
        best=min(group,key=lambda r:float(r['t_total']))
        for k in ['repeat','iters','t_total','t_stencil','t_halo','t_reduce','rel_res','err_l2']:
            assert s[k]==best[k],(s['group'],k)
        times=[float(r['t_total']) for r in group]
        assert float(s['seconds_min'])==min(times)
        assert float(s['seconds_median'])==statistics.median(times)
        assert float(s['seconds_max'])==max(times)
    if a.kind=='cpu':
        assert all(f'PLACEMENT_PASS {p} {t}' in log for p,t in [(256,1),(288,1),(4,72)])
        for dim in ([3] if meta['suite']=='weak3d' else [2,3]):
            for exp in ['strong','weak']:
                if exp=='strong' and meta['suite']=='weak3d':continue
                if a.allow_missing_weak3d_reference and exp=='weak' and dim==3:continue
                assert any(r['experiment']==exp and int(r['dim'])==dim and int(r['ranks'])==256 for r in rows)
            if meta['suite']!='weak3d':
                assert any(r['experiment']=='strong' and int(r['dim'])==dim and int(r['ranks'])==288 for r in rows)
    else:
        assert 'GPU_ALLOCATION_DEVICE_MPI=PASS' in log
        probe=(d/'gpu-allocation-probe.log').read_text()
        assert 'GPU_SMOKE=PASS' in probe
        assert set(re.findall(r'rank=([01]) visible_gpus=1 .*device_mpi=1',probe))=={'0','1'}
        assert '2D and 3D GPU stencil and dot checks passed' in log
        if 'verify_faces' in (root/'src/hybrid_cuda/checks/kernel_check.cu').read_text():
            assert 'GPU halo face packing and unpacking checks passed' in log
        if 'PCG_CUDA_STOP_TOL' in (root/'scripts/run_gpu_scaling.py').read_text():
            assert meta['cuda_cli_true_tolerance']==1e-8 and meta['cuda_recursive_stop_tolerance']==5e-9
            for r in rows:
                command=json.loads((d/(r['group']+'-r'+r['repeat']+'.command.json')).read_text())
                assert command[command.index('--tol')+1]==('1e-8' if r['impl']=='cuda' else '5e-9')
                assert any(command[i:i+2]==['-x','PCG_CUDA_STOP_TOL'] for i in range(len(command)-1))
        for dim in [2,3]:
            for mode in ['staged','device']:
                assert any(r['experiment']=='strong' and int(r['dim'])==dim and r['transport']==mode
                           and int(r['gpus'])==2 and int(r['nodes'])==2 for r in rows)
    a.output.mkdir(parents=True,exist_ok=True)
    prefix=a.prefix or a.kind
    for f in ['samples.csv','summary.csv','manifest.json']:
        shutil.copy2(d/f,a.output/(prefix+'_'+f))
    audit=dict(job_id=meta['job_id'],exit_status=job['Exit_status'],groups=expected,samples=len(rows),
               scope='completed groups only' if a.allow_missing_weak3d_reference else 'complete suite',
               documented_missing_reference_failure=a.allow_missing_weak3d_reference,
               source_hashes_match=True,placement_verified=True,serial_comparisons_pass=True,
               max_true_rel_res=max(float(r['rel_res']) for r in rows),
               exec_host=job['exec_host'],allocation=job['Resource_List']['select'],
               sample_sha256=hashlib.sha256((d/'samples.csv').read_bytes()).hexdigest())
    (a.output/(prefix+'_audit.json')).write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
