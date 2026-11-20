"""Explicit, idempotent local demo data. Never clears existing records."""
import argparse,json,urllib.request,urllib.parse,urllib.error,http.cookiejar
from datetime import datetime,timedelta,timezone

class Session:
 def __init__(self,base):self.base=base.rstrip('/');self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
 def request(self,path,data=None,method='GET',form=False):
  headers={};raw=None
  if method!='GET':
   csrf=self.request('/auth/csrf');headers[csrf['headerName']]=csrf['token'];headers['Content-Type']='application/x-www-form-urlencoded' if form else 'application/json'
   raw=urllib.parse.urlencode(data).encode() if form else json.dumps(data).encode()
  request=urllib.request.Request(self.base+path,data=raw,headers=headers,method=method)
  with self.opener.open(request,timeout=20) as response:
   body=response.read();return json.loads(body) if body else None
 def register(self,account):
  try:self.request('/users/registerUser',account,'POST')
  except urllib.error.HTTPError as e:
   if e.code!=409:raise
 def login(self,name,password):return self.request('/users/login',{'username':name,'password':password},'POST',True)

def seed_inventory(factory, factory_name):
 # Materials are seeded through public business APIs; stable receipt IDs prevent repeated stock increments.
 inventory=factory.request('/inventory');materials={m['sku']:m for m in inventory['materials']}
 for sku,name,quantity in [('AL-6061','6061 铝合金毛坯',1000),('SEAL-08','密封圈 08',1200),('BOLT-M6','M6 紧固件',3000)]:
  if sku not in materials:materials[sku]=factory.request('/inventory/materials',dict(factoryName=factory_name,sku=sku,name=name,unit='件'),'POST')
  material=materials[sku]
  # Preserve existing manually populated stock as-is; only empty materials receive the seed command.
  if material.get('onhand',0)==0 and material.get('reserved',0)==0:factory.request('/inventory/materials/'+str(material['id'])+'/receipts',dict(quantity=quantity,requestId='seed-stock-'+sku+'-v1'),'POST')
 boms={b['productname'] for b in inventory['boms']}
 product='精密轴套 · SH-108'
 if product not in boms:factory.request('/inventory/boms',dict(factoryName=factory_name,productName=product,version=0,lines=[dict(materialId=materials['AL-6061']['id'],units=1),dict(materialId=materials['SEAL-08']['id'],units=2)]),'POST')

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--base',default='http://127.0.0.1:8081/api');parser.add_argument('--inventory-only', action='store_true');args=parser.parse_args()
 if args.inventory_only:
  factory = Session(args.base)
  if not factory.request('/auth/demo').get('enabled'):
   return
  user = factory.login('demo_factory', 'Demo-Factory-2026')
  if user.get('factoryName') != '远川精密制造':
   raise RuntimeError('演示工厂与预期不符')
  seed_inventory(factory, user['factoryName'])
  print('制造演示库存已就绪')
  return
 # Demo credentials are intentional and restricted to the local demonstration.
 primary={'username':'demo_factory','password':'Demo-Factory-2026','role':'factoryAdmin','factoryName':'远川精密制造','factoryDescription':'精密金属加工、数控铣削与小批量装配。此工厂为本机演示数据。','contactEmail':'factory@example.com'}
 secondary={'username':'demo_partner','password':'Demo-Partner-2026','role':'factoryAdmin','factoryName':'锐丰精工','factoryDescription':'提供钣金加工与柔性生产协作。此工厂为本机演示数据。','contactEmail':'partner@example.com'}
 dealer={'username':'demo_dealer','password':'Demo-Dealer-2026','role':'distributor','realName':'演示经销商'}
 setup=Session(args.base)
 for account in (primary,secondary,dealer):setup.register(account)
 factory=Session(args.base);user=factory.login(primary['username'],primary['password']);factory_name=user['factoryName']
 partner=Session(args.base);partner_user=partner.login(secondary['username'],secondary['password'])
 buyer=Session(args.base);buyer.login(dealer['username'],dealer['password'])
 now=datetime.now(timezone(timedelta(hours=8)));today=now.date()
 existing=factory.request('/devices/allDevices');by_name={d['deviceName']:d for d in existing}
 specifications=[('CNC-01 五轴加工中心','CNC 加工','A 车间 · 01 工位','AVAILABLE',1),('CNC-02 数控铣床','数控铣削','A 车间 · 02 工位','AVAILABLE',7),('ASM-01 柔性装配线','装配','B 车间 · 01 线','AVAILABLE',14),('QC-01 三坐标检测仪','质量检测','检测室','MAINTENANCE',-1),('CUT-01 激光切割机','激光切割','C 车间 · 01 工位','OFFLINE',30)]
 for name,category,location,status,days in specifications:
  if name not in by_name:
   by_name[name]=factory.request('/devices',dict(deviceName=name,deviceDescription='本机演示设备，未连接实际硬件。',factoryName=factory_name,status=status,category=category,location=location,dailyCapacityMinutes=480,serviceDueDate=str(today+timedelta(days=days)),maintenanceNote='周期校准，等待恢复' if status=='MAINTENANCE' else '计划停机，等待排班' if status=='OFFLINE' else '',version=0),'POST')
 existing_orders={o['productName']:o for o in buyer.request('/orders')}
 def transition(o,status,note=None):
  payload=dict(status=status,version=o['version'])
  if note:payload['note']=note
  return factory.request('/orders/'+str(o['id'])+'/status',payload,'PATCH')
 products=[('铝合金连接座 · MC-204',240,'URGENT','PRODUCING',0,80,3),('精密轴套 · SH-108',500,'HIGH','ACCEPTED',1,0,0),('传感器安装支架 · BR-026',120,'NORMAL','PENDING',2,0,0),('定位销组件 · PN-012',300,'HIGH','PAUSED',2,96,5),('电机端盖 · EC-402',80,'NORMAL','COMPLETED',0,80,1),('散热壳体 · HS-310',160,'NORMAL','ACCEPTED',0,0,0),('设备护罩 · CV-015',60,'NORMAL','PENDING',1,0,0),('校验样件 · QA-002',20,'NORMAL','CANCELLED',2,0,0)]
 for index,(name,qty,priority,target,machine,good,bad) in sorted(enumerate(products),key=lambda row:row[1][3]!='COMPLETED'):
  if name in existing_orders:continue
  o=buyer.request('/orders',dict(productName=name,quantity=qty,factoryName=factory_name,priority=priority,dueDate=str(today+timedelta(days=index%5+1)),notes='本机演示订单，用于展示排程、报工与追溯，不代表实际生产。'),'POST')
  if target=='PENDING':continue
  if target=='CANCELLED':buyer.request('/orders/'+str(o['id'])+'/status',dict(status='CANCELLED',version=o['version']),'PATCH');continue
  o=transition(o,'ACCEPTED')
  # Different days on the same machine prevent seeded reservation conflicts.
  start=datetime.combine(today+timedelta(days=index),datetime.min.time()).replace(hour=8)
  end=start+timedelta(hours=6)
  result=factory.request('/orders/'+str(o['id'])+'/plan',dict(deviceId=by_name[specifications[machine][0]]['id'],version=o['version'],plannedStart=start.isoformat(),plannedEnd=end.isoformat(),notes='本机演示生产计划'),'PUT');o=result['order']
  if target=='ACCEPTED':continue
  o=transition(o,'PRODUCING')
  if good or bad:o=factory.request('/orders/'+str(o['id'])+'/reports',dict(goodQuantity=good,rejectedQuantity=bad,version=o['version'],notes='首批生产与检验记录（演示）'),'POST')['order']
  if target=='COMPLETED':o=transition(o,'COMPLETED')
  if target=='PAUSED':
   o=transition(o,'PAUSED','等待工装调整与首件复核（演示）')
   factory.request('/orders/'+str(o['id'])+'/issues',dict(type='PROCESS',severity='HIGH',description='定位工装偏差，待复核后恢复生产（演示）',version=o['version']),'POST')
  if index==0:factory.request('/orders/'+str(o['id'])+'/issues',dict(type='QUALITY',severity='MEDIUM',description='首批表面划痕，需复核后续批次（演示）',version=o['version']),'POST')
 seed_inventory(factory, factory_name)
 print('本机演示数据已就绪；已有设备和同名演示订单不会被重置。')
 print('工厂：demo_factory / Demo-Factory-2026；经销商：demo_dealer / Demo-Dealer-2026。')
 print('演示工厂：'+factory_name+'；伙伴工厂：'+partner_user['factoryName'])
if __name__=='__main__':main()
