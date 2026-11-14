#!/usr/bin/env python3
"""Structure-only check (allowed before the preregistration): item identity across participants and the
trial_type vocabulary. It prints NO response or outcome counts."""
import os, glob, collections
import csv
T=os.environ['TOAM']; items={}; vocab=collections.defaultdict(set); tasks=collections.Counter()
for f in sorted(glob.glob(f'{T}/raw/ds00626[56]/sub-*/ses-*/func/*_events.tsv')):
    ds=f.split('/raw/')[1].split('/')[0]; sub=f.split('/sub-')[1].split('/')[0]
    ses=f.split('/ses-')[1].split('/')[0]; task=f.split('task-')[1].split('_')[0]
    R=list(csv.DictReader(open(f),delimiter='\t')); tasks[(ds,ses,task)]+=1
    if R and 'item' in R[0]: items.setdefault((ds,sub),set()).update(r['item'] for r in R if r['item'] not in ('','n/a'))
    for tt in {r['trial_type'] for r in R if r.get('trial_type') not in (None,'','n/a')}:
        p=tt.split('_'); vocab[(ses,task)].add(p[0]+'_'+'_'.join('X' if x in ('sure','unsure','guess','correct','incorrect') else x for x in p[1:]) if len(p)>1 else p[0])
print('event files per (dataset, session, task):'); [print('  ',k,v) for k,v in sorted(tasks.items())]
sets=list(items.values()); inter=set.intersection(*sets); union=set.union(*sets)
print(f'participants with items: {len(items)} | items per participant min {min(map(len,sets))} max {max(map(len,sets))} | shared by all {len(inter)} | union {len(union)}')
odd=[(k,len(v)) for k,v in items.items() if v!=inter]
print('participants whose item set differs from the shared core:',odd[:6])
print('trial_type patterns (status tokens masked as X):')
for k in sorted(vocab): print('  ',k,sorted(vocab[k]))
