"""Assumption-based three-gas screening LCA; incomplete upstream closure disclosed."""
import csv, hashlib, json, sys, zipfile
from pathlib import Path
from collections import defaultdict, deque
import numpy as np
from scipy.sparse import coo_matrix, save_npz
from scipy.sparse.linalg import spsolve
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from kettle_lca.ilcd import Archive
US=ROOT/'data/raw/uslci/uslci_fy25_q2_01_olca2_4_1_elci_lib_json_ld.zip'
manifest=json.loads((ROOT/'data/source_manifest.json').read_text())
assert hashlib.sha256(US.read_bytes()).hexdigest()==next(x['sha256'] for x in manifest['uslci']['archives'] if x['format']=='JSON-LD')
method=json.loads((ROOT/'data/gwp_method_unapproved.json').read_text())
# No invented CFs: select values from the archived climate method.
target_names=['carbon dioxide (fossil)','methane (fossil)','nitrous oxide']
cf=[]; cf_evidence=[]
for name in target_names:
 records=[f for f in method['factors'] if f['name'].lower()==name and f['direction']=='Output' and f['reference_unit']=='kg']
 values={float(f['factor']) for f in records}
 assert len(values)==1, (name,values)
 cf.append(values.pop());cf_evidence.append({'gas':name,'factor':cf[-1],'evidence':records})
with zipfile.ZipFile(US) as z:
 processes={Path(n).stem:json.loads(z.read(n)) for n in z.namelist() if n.startswith('processes/') and n.endswith('.json')}
 hashes={id:hashlib.sha256(z.read('processes/'+id+'.json')).hexdigest() for id in processes}

EL='66280f03-b26f-35c4-bda2-3d4a8652943a' # Coal-electricity scenario, not a national grid average.
PP='2e8facf6-46aa-4ddb-95de-a4e2a00eb2bb'
TG='tg:copper'
selections=[('BOM01','49f5324b-fc33-36e9-b5af-3c80d73492bd','Stainless 304 coil proxy'),('BOM02',TG,'100% cathode copper proxy for brass; no alloy-composition claim'),('BOM03',TG,'Cathode copper; fabrication added as electricity proxy'),('BOM04',PP,'Virgin PP resin'),('BOM05','3dbccdda-2014-4239-ad1f-4e15c034942b','Suspension PVC resin; additives excluded'),('BOM06',PP,'PP proxy for unspecified nylon; low material fidelity'),('BOM07',PP,'PP proxy for POM; low material fidelity'),('BOM08',PP,'PP proxy for PC; low material fidelity'),('BOM09','0e42a306-ee2d-362e-8bc3-580000096459','ABS resin'),('BOM10',PP,'PP placeholder proxy for silicone; chemically unsuitable for definitive conclusions'),('BOM11','6a12cba1-889d-4515-90f8-89feb8d662f2','LDPE resin; film electricity added'),('BOM12','226ed3c2-e020-4c95-b1fc-4559fc2d18ac','Corrugated product proxy for cardboard; conversion included')]
bom=list(csv.DictReader((ROOT/'data/bom.csv').open()))
refs={}
for id,p in processes.items():
 r=[x for x in p.get('exchanges',[]) if x.get('isQuantitativeReference')]
 if len(r)==1 and float(r[0]['amount'])>0:refs[id]=r[0]
providers=defaultdict(list)
for id,r in refs.items():
 if not r.get('isInput'):providers[r['flow']['@id']].append(id)

omissions=[]; links=[]; maps=[]; raw_inventory=[]
unit_groups={'mass':{'kg':1,'g':.001,'t':1000,'lb':.45359237},'energy':{'MJ':1,'kWh':3.6,'kJ':.001},'volume':{'m3':1,'l':.001,'L':.001}}
def conversion(src,dst):
 if src==dst:return 1.
 for group in unit_groups.values():
  if src in group and dst in group:return group[src]/group[dst]
 raise ValueError(f'Unsupported dimensional conversion {src} -> {dst}')

def gas_key(name,category,direction,unit):
 n=name.lower();c=category.lower()
 if direction!='Output' or ('emission/air' not in c and 'emissions to air' not in c and not c.startswith('tg-air')):return None
 if n in ['carbon dioxide','carbon dioxide, fossil','carbon dioxide (fossil)']:key=0
 elif n in ['methane','methane, fossil','methane (fossil)']:key=1
 elif n=='nitrous oxide':key=2
 else:return None
 return key, conversion(unit,'kg')

queue=deque([p for _,p,_ in selections if p!=TG]+[EL]); used={}; Bcols={}
while queue:
 id=queue.popleft()
 if id in used:continue
 if id not in refs:raise ValueError('Missing/invalid selected reference '+id)
 p=processes[id];ref=refs[id];q=float(ref['amount']);used[id]=p;Bcols[id]=np.zeros(3)
 for e in p.get('exchanges',[]):
  if e.get('isQuantitativeReference'):continue
  amount=float(e.get('amount',0))/q
  if amount==0:continue
  flow=e.get('flow',{});typ=flow.get('flowType');unit=e.get('unit',{}).get('name','')
  if typ=='ELEMENTARY_FLOW':
   k=gas_key(flow.get('name',''),flow.get('category',''),'Input' if e.get('isInput') else 'Output',unit)
   if k:
    Bcols[id][k[0]]+=amount*k[1]
    maps.append({'process_id':id,'flow_id':flow.get('@id'),'flow_name':flow.get('name'),'category':flow.get('category'),'unit':unit,'gas':target_names[k[0]],'mapping_status':'assumed name/air crosswalk; unspecified CO2/CH4 treated fossil'})
   else:
    raw_inventory.append({'process_id':id,'flow_id':flow.get('@id'),'flow_name':flow.get('name'),'category':flow.get('category'),'amount_per_reference':amount,'unit':unit,'status':'outside three-gas subtotal; not assigned a zero CF'})
   continue
  if p.get('processType')=='LCI_RESULT':
   omissions.append({'process_id':id,'flow_name':flow.get('name'),'amount':amount,'unit':unit,'reason':'LCI_RESULT treated as cumulative; no upstream relinking'});continue
  if not e.get('isInput') or typ!='PRODUCT_FLOW':
   omissions.append({'process_id':id,'flow_name':flow.get('name'),'amount':amount,'unit':unit,'reason':'non-reference output/waste treatment excluded; no substitution credits'});continue
  provider=e.get('defaultProvider',{}).get('@id');selection='default provider'
  if provider not in refs:
   candidates=providers.get(flow.get('@id'),[])
   if len(candidates)==1:provider=candidates[0];selection='unique exact reference-flow provider assumption'
   elif flow.get('name','').lower().startswith('electricity'):
    provider=EL;selection='coal-electricity proxy for missing electricity provider'
   else:
    omissions.append({'process_id':id,'flow_name':flow.get('name'),'flow_id':flow.get('@id'),'amount':amount,'unit':unit,'reason':'unresolved provider explicitly cut off'});continue
  try:amount*=conversion(unit,refs[provider].get('unit',{}).get('name',''))
  except ValueError as ex:
   omissions.append({'process_id':id,'flow_name':flow.get('name'),'amount':amount,'unit':unit,'reason':str(ex)});continue
  links.append({'consumer':id,'provider':provider,'amount_per_reference':amount,'decision':selection});queue.append(provider)

ar=Archive(ROOT/'data/raw/tiangong/tiangong_lca_data')
tgid='6d390a38-8a3d-410c-8192-60b70b0bd286'
p=ar.process(ar.root/'processes'/(tgid+'.xml'));q=float(p['reference_exchanges'][0]['amount']);used[TG]={'name':p['name'],'version':p['dataset_version'],'source_sha256':p['sha256']};Bcols[TG]=np.zeros(3)
for e in p['exchanges']:
 amount=float(e['amount'])/q
 if amount==0 or e['exchange_id'] in p['reference_exchange_ids']:continue
 if e.get('flow_type')=='Elementary flow' and e['direction']=='Output':
  k=gas_key(e.get('name',''),'tg-air-assumed',e['direction'],e.get('reference_unit','')) if any(e['flow_id']==f['flow_id'] for evidence in cf_evidence for f in evidence['evidence']) else None
  if k:
   Bcols[TG][k[0]]+=amount*k[1];maps.append({'process_id':TG,'flow_id':e['flow_id'],'flow_name':e.get('name'),'gas':target_names[k[0]],'mapping_status':'exact TianGong flow UUID match to selected source factor; reference mass unit kg'})
  else:raw_inventory.append({'process_id':TG,'exchange':e,'status':'outside three-gas subtotal'})
 elif e.get('flow_type')=='Product flow' and e['direction']=='Input':
  if e.get('name')=='Electricity':
   value=amount*conversion(e['reference_unit'],'kWh');links.append({'consumer':TG,'provider':EL,'amount_per_reference':value,'decision':'coal electricity proxy'})
  else:omissions.append({'process_id':TG,'flow_name':e.get('name'),'amount':amount,'unit':e.get('reference_unit'),'reason':'TianGong product-flow provider missing; explicitly cut off'})

ids=list(used);index={id:i for i,id in enumerate(ids)};n=len(ids)
r=list(range(n));c=list(range(n));v=[1.]*n
for l in links:r.append(index[l['provider']]);c.append(index[l['consumer']]);v.append(-l['amount_per_reference'])
A=coo_matrix((v,(r,c)),shape=(n,n)).tocsc();B=coo_matrix(np.column_stack([Bcols[id] for id in ids])).tocsc();C=np.array([cf])
f=np.zeros(n);demands={}; assumptions=[]
for row,(bid,id,reason) in zip(bom,selections):
 assert row['material_id']==bid
 mass=float(row['mass_g'])/1000
 multiplier=1.034 if row['group']=='product' and bid not in ['BOM01','BOM02','BOM03'] else 1.
 d=np.zeros(n);d[index[id]]=mass*multiplier
 # Material provider units validated as kg for all selected US datasets.
 if id!=TG:assert refs[id]['unit']['name']=='kg'
 demands[bid]=d;f+=d;assumptions.append({'material_id':bid,'material':row['material_name'],'mass_kg':mass,'purchase_multiplier':multiplier,'provider':id,'proxy_rationale':reason})
plastic=sum(float(row['mass_g'])/1000 for row in bom if row['group']=='product' and row['material_id'] not in ['BOM01','BOM02','BOM03'])
metal=sum(float(row['mass_g'])/1000 for row in bom if row['material_id'] in ['BOM01','BOM02','BOM03'])
energy={'plastic_conversion':plastic*(6.444/3.6),'metal_fabrication':metal*.5,'film_conversion':.0063*.5,'assembly':.1}
for name,kwh in energy.items():
 d=np.zeros(n);d[index[EL]]=kwh;demands[name]=d;f+=d
s=spsolve(A,f);g=np.asarray(B@s);h=C@g
assert np.isfinite(s).all() and (s>=-1e-9).all() and np.allclose(A@s,f,rtol=1e-8,atol=1e-10)
parts={name:float((C@(B@spsolve(A,d)))[0]) for name,d in demands.items()}
assert np.isclose(sum(parts.values()),h[0])
OUT=ROOT/'results/assumption-screening';OUT.mkdir(exist_ok=True)
save_npz(OUT/'A.npz',A);save_npz(OUT/'B.npz',B);np.savez_compressed(OUT/'vectors.npz',C=C,f=f,s=s,g=g,h=h,process_ids=np.array(ids))
result={'status':'calculated_assumption_based_incomplete_three_gas_screening','functional_unit':'one manufactured and packaged BC1 1 L kettle','three_gas_gwp100_subtotal_kg_co2_eq':float(h[0]),'not_a_complete_cradle_to_gate_gwp':True,'gas_inventory_kg':dict(zip(target_names,g.tolist())),'characterization_factors':dict(zip(target_names,cf)),'process_count':n,'technosphere_residual_max':float(np.max(np.abs(A@s-f))),'contribution_sum_check':bool(np.isclose(sum(parts.values()),h[0])),'contributions_kg_co2_eq':parts,'foreground_energy_kwh':energy,'material_assumptions':assumptions,'cutoff_record_count':len(omissions),'uncharacterized_record_count':len(raw_inventory),'assumptions':['Missing plastics use virgin PP as a deliberately coarse placeholder; silicone proxy is not chemically representative','Brass uses cathode copper proxy, not assumed measured alloy composition','All missing electricity and foreground electricity use actual USLCI bituminous coal power; no national-grid claim','Plastic conversion 1.79 kWh/kg and purchase factor 1.034 adopted from USLCI PP molding; generalized to other plastic components','Metal fabrication 0.5 kWh/kg; film conversion 0.5 kWh/kg; assembly 0.1 kWh/kettle are user-authorized analyst assumptions','No additional site transport; no consumer use or product end-of-life','Unresolved upstream exchanges and production-waste services explicitly excluded; upstream closure incomplete','Only air-emission fossil CO2, fossil CH4 and N2O characterized; other greenhouse gases omitted from subtotal','Generic air CO2 and CH4 treated fossil; biogenic/resource flows outside subtotal','Use archived TianGong method values as-is despite conflicting source-year labels; do not claim certified IPCC/EF version','As-delivered unit datasets treated as preallocated; no additional coproduct credits; system-model harmonization not established'],'source_commit':manifest['uslci']['commit'],'method_uuid':method['dataset_id'],'method_version':method['dataset_version'],'tian_gong_copper_uuid':tgid,'tian_gong_copper_sha256':p['sha256']}
for filename,data in [('results.json',result),('supplier_links.json',links),('cutoffs.json',omissions),('uncharacterized.json',raw_inventory),('flow_crosswalk.json',maps),('cf_evidence.json',cf_evidence),('process_manifest.json',[{'id':id,'name':used[id].get('name'),'version':used[id].get('version'),'sha256':hashes.get(id,used[id].get('source_sha256'))} for id in ids])]:
 (OUT/filename).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
with (OUT/'contributions.csv').open('w',newline='') as stream:
 w=csv.writer(stream);w.writerow(['group','three_gas_gwp100_subtotal_kg_co2_eq']);w.writerows(parts.items())
print(json.dumps({k:result[k] for k in ['status','three_gas_gwp100_subtotal_kg_co2_eq','gas_inventory_kg','process_count','cutoff_record_count','uncharacterized_record_count','foreground_energy_kwh']},indent=2))
