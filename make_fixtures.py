"""Generate artificial people/commitments; strictly no real-world care data."""
import copy,json
from pathlib import Path

base={
  'id':'original_covered','title':'Tomorrow 09:30 follow-up - SYNTHETIC',
  'needs':[
    {'id':'OUT','slot':'outbound','seq':0,'start':510,'end':550,'origin':'HOME','destination':'CLINIC','capability':'DRIVE'},
    {'id':'ESC','slot':'escort','seq':1,'start':555,'end':630,'origin':'CLINIC','destination':'CLINIC','capability':'ESCORT'},
    {'id':'RET','slot':'return','seq':2,'start':645,'end':690,'origin':'CLINIC','destination':'HOME','capability':'DRIVE'}
  ],
  'people':[
    {'id':'SOF','name':'Sofia','capabilities':['DRIVE','ESCORT'],'availability':[[480,720]],'busy':[]},
    {'id':'OMA','name':'Omar','capabilities':['DRIVE'],'availability':[[480,600],[630,720]],'busy':[]},
    {'id':'LIN','name':'Lina','capabilities':['ESCORT'],'availability':[[540,650]],'busy':[]},
    {'id':'CEL','name':'Celine','capabilities':['DRIVE'],'availability':[[630,720]],'busy':[]}
  ],
  'offers':[
    {'id':'SOUT','person':'SOF','need':'OUT','state':'confirmed'},
    {'id':'SESC','person':'SOF','need':'ESC','state':'confirmed'},
    {'id':'SRET','person':'SOF','need':'RET','state':'confirmed'},
    {'id':'OOUT','person':'OMA','need':'OUT','state':'proposed'},
    {'id':'LESC','person':'LIN','need':'ESC','state':'proposed'},
    {'id':'CRET','person':'CEL','need':'RET','state':'proposed'}
  ],'expected_covered':True,
  'purpose':'All obligations confirmed by Sofia; no temporal conflicts.'
}

def clone(name):
 f=copy.deepcopy(base);f['id']=name;return f

def sof_withdrawn(f):
 for o in f['offers']:
  if o['person']=='SOF':o['state']='withdrawn'

def confirm(f,ids):
 for o in f['offers']:
  if o['id'] in ids:o['state']='confirmed'

f=[base]
c=clone('cancelled');sof_withdrawn(c);c['expected_covered']=False;c['purpose']='All Sofia commitments withdrawn; offers remain proposed.';f.append(c)
c=clone('partial_trip');sof_withdrawn(c);confirm(c,['OOUT','LESC']);c['expected_covered']=False;c['purpose']='Outbound and escort confirmed; return not confirmed.';f.append(c)
c=clone('rescue_complete');sof_withdrawn(c);confirm(c,['OOUT','LESC','CRET']);c['expected_covered']=True;c['purpose']='Three compatible, independently confirmed replacement commitments.';f.append(c)
c=copy.deepcopy(f[-1]);c['id']='busy_driver';c['expected_covered']=False;c['purpose']='Omar accepted outbound but has an overlapping external commitment.'
for p in c['people']:
 if p['id']=='OMA':p['busy']=[[530,545]]
f.append(c)
c=copy.deepcopy(f[3]);c['id']='capability_missing';c['expected_covered']=False;c['purpose']='Return driver is confirmed but lacks driving capability.'
for p in c['people']:
 if p['id']=='CEL':p['capabilities']=['ESCORT']
f.append(c)
c=copy.deepcopy(f[3]);c['id']='late_handoff';c['expected_covered']=False;c['purpose']='Outbound arrives too late for the confirmed escort start.'
for n in c['needs']:
 if n['id']=='OUT':n['end']=565
f.append(c)
c=copy.deepcopy(f[3]);c['id']='wrong_handoff_location';c['expected_covered']=False;c['purpose']='Outbound finishes at clinic, escort starts somewhere else.'
for n in c['needs']:
 if n['id']=='ESC':n['origin']='STATION'
f.append(c)
c=copy.deepcopy(f[3]);c['id']='helper_cancelled';c['expected_covered']=False;c['purpose']='Lina cancellation invalidates otherwise confirmed escort.'
for p in c['people']:
 if p['id']=='LIN':p['cancelled']=True
f.append(c)
c=copy.deepcopy(f[3]);c['id']='availability_short';c['expected_covered']=False;c['purpose']='Omar availability ends before the outward trip is complete.'
for p in c['people']:
 if p['id']=='OMA':p['availability']=[[480,530]]
f.append(c)
c=copy.deepcopy(f[3]);c['id']='unconfirmed_return';c['expected_covered']=False;c['purpose']='Celine explicitly changed return confirmation to proposed.'
for o in c['offers']:
 if o['id']=='CRET':o['state']='proposed'
f.append(c)
Path(__file__).with_name('data').joinpath('scenarios.json').write_text(json.dumps({'data_kind':'SYNTHETIC_ONLY','scenarios':f},indent=2)+'\n')
print('Generated',len(f),'synthetic scenarios')
