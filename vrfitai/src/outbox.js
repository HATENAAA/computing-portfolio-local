// One immutable entry per UUID avoids cross-tab read/modify/write races.
export class Outbox {
 constructor(storage){this.storage=storage;this.prefix='vrfitai.outbox.v1.';}
 put(record){const key=this.prefix+record.id,value=JSON.stringify(record),old=this.storage.getItem(key);if(old&&old!==value)throw Error('离线记录编号冲突，请保留原记录');this.storage.setItem(key,value);}
 remove(id){this.storage.removeItem(this.prefix+id);}
 entries(){const values=[];for(let i=0;i<this.storage.length;i++){const key=this.storage.key(i);if(key?.startsWith(this.prefix)){try{const r=JSON.parse(this.storage.getItem(key));if(r.id&&key===this.prefix+r.id)values.push(r);}catch{/* Keep unreadable entries for manual recovery. */}}}return values;}
}
