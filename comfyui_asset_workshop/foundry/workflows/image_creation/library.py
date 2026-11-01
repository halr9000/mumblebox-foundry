"""Creation-level Gallery index, immutable image revisions and exact-file ownership."""
from contextlib import contextmanager
import copy
import hashlib
import json
import re
import secrets
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from PIL import Image
from ...artifacts import digest, owned_path, remove_exact


def identifier(value):
    if not isinstance(value,str) or not re.fullmatch(r"[a-f0-9]{32}",value):raise ValueError("Invalid image creation identity.")
    return value


class ImageLibrary:
    def __init__(self,state_root,output_root,busy=lambda:False):
        self.state_root=Path(state_root);self.state_root.mkdir(parents=True,exist_ok=True)
        self.output_root=Path(output_root).resolve();self.root=self.output_root/'foundry-images'
        self.root.mkdir(parents=True,exist_ok=True)
        self.database=self.state_root/'images.sqlite3';self.lock=threading.RLock();self.busy=busy
        with self.connect() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS creations(
                id TEXT PRIMARY KEY,name TEXT NOT NULL,category TEXT NOT NULL,paired INTEGER NOT NULL,
                created REAL NOT NULL,updated REAL NOT NULL,saved INTEGER NOT NULL,removed INTEGER NOT NULL,
                version TEXT NOT NULL,data TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS gallery_created ON creations(saved,removed,created,id);
                CREATE INDEX IF NOT EXISTS gallery_category ON creations(saved,removed,category,created,id);
                CREATE TABLE IF NOT EXISTS removals(token TEXT PRIMARY KEY,expires REAL NOT NULL,data TEXT NOT NULL);''')

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.database,timeout=10);db.row_factory=sqlite3.Row
        try:
            with db:yield db
        finally:db.close()

    def directory(self,ident):
        return owned_path(self.root,self.root/identifier(ident))

    def create(self,config):
        now=time.time();ident=uuid.uuid4().hex
        self.directory(ident).mkdir()
        record={'id':ident,'config':copy.deepcopy(config),'created':now,'updated':now,'saved':False,'removed':False,
                'status':'idle','stage':'','error':'','events':[],'accepted':{},'revisions':[],'stages':{},'outputs':{}}
        self.save(record);return record

    def save(self,record):
        identifier(record['id']);record['updated']=time.time()
        payload=json.dumps(record,ensure_ascii=False,allow_nan=False)
        version=hashlib.sha256(payload.encode()).hexdigest();config=record['config']
        with self.lock,self.connect() as db:
            existing=db.execute('SELECT removed FROM creations WHERE id=?',(record['id'],)).fetchone()
            if existing and existing['removed']:raise ValueError('This creation was removed from Gallery.')
            db.execute('INSERT OR REPLACE INTO creations VALUES(?,?,?,?,?,?,?,?,?,?)',
                (record['id'],config['name'],config['category'],int(config['paired']),record['created'],record['updated'],
                 int(record['saved']),int(record['removed']),version,payload))

    def get(self,ident):
        identifier(ident)
        with self.connect() as db:row=db.execute('SELECT data FROM creations WHERE id=? AND removed=0',(ident,)).fetchone()
        if not row:raise ValueError('This image creation is no longer available.')
        return json.loads(row['data'])

    def revision(self,record,revision_id):
        revision=next((r for r in record['revisions'] if r['id']==revision_id),None)
        if revision is None:raise ValueError('This revision does not belong to the creation.')
        return revision

    def file(self,record,revision_id):
        revision=self.revision(record,revision_id)
        path=owned_path(self.directory(record['id']),self.directory(record['id'])/revision['file'])
        if not path.is_file() or digest(path)!=revision['sha256']:raise ValueError('The saved image has changed or is missing.')
        return path

    def add_revision(self,record,side,path,provenance,accepted=False,source=None):
        sides=('front','back') if record['config']['paired'] else ('single',)
        if side not in sides:raise ValueError('This view is not part of the creation.')
        path=owned_path(self.directory(record['id']),path)
        if any(r['file']==path.relative_to(self.directory(record['id'])).as_posix() for r in record['revisions']):
            raise ValueError('An image revision cannot overwrite another revision.')
        with Image.open(path) as image:
            if image.width*image.height>40_000_000:raise ValueError('Image exceeds 40 megapixels.')
            size=list(image.size);image.verify()
        item={'id':uuid.uuid4().hex,'side':side,'file':path.relative_to(self.directory(record['id'])).as_posix(),
              'sha256':digest(path),'bytes':path.stat().st_size,'size':size,'created':time.time(),
              'source':source,'provenance':copy.deepcopy(provenance)}
        record['revisions'].append(item)
        if accepted:record['accepted'][side]=item['id']
        self.save(record);return item

    def track_file(self,record,path):
        """Keep masks, edit intermediates and packages in the exact-file deletion inventory."""
        path=owned_path(self.directory(record['id']),path)
        relative=path.relative_to(self.directory(record['id'])).as_posix()
        checksum=digest(path)
        known=next((item for item in record.get('auxiliary_files',[]) if item['file']==relative),None)
        if known:
            if known['sha256']!=checksum:raise ValueError('An owned image file changed unexpectedly.')
            return
        record.setdefault('auxiliary_files',[]).append({'file':relative,'sha256':checksum,'bytes':path.stat().st_size})
        self.save(record)

    def accept(self,record,revision_id,expected):
        item=self.revision(record,revision_id);side=item['side']
        if record['accepted'].get(side)!=expected:raise ValueError('The current image changed; reopen its latest revision.')
        self.file(record,revision_id)
        record['accepted'][side]=revision_id
        if record['config']['paired']:record['pair_review']='Review both views after this edit; the other view was preserved.'
        self.save(record)

    def publish(self,record):
        sides=('front','back') if record['config']['paired'] else ('single',)
        if any(side not in record['accepted'] for side in sides):raise ValueError('Finish every image in this creation before saving to Gallery.')
        for side in sides:self.file(record,record['accepted'][side])
        record['saved']=True;self.save(record)
        return self.summary(record)

    @staticmethod
    def summary(record):
        return {'id':record['id'],'name':record['config']['name'],'category':record['config']['category'],
                'paired':record['config']['paired'],'created':record['created'],'updated':record['updated'],
                'accepted':record['accepted'],'revision_count':len(record['revisions'])}

    def list(self,search='',category='',kind='all',sort='newest',cursor='',limit=24):
        if type(limit) is not int or not 1<=limit<=24:raise ValueError('Request between 1 and 24 creations.')
        if kind not in ('all','single','pair') or sort not in ('newest','oldest'):raise ValueError('Choose a supported Gallery filter.')
        if not isinstance(search,str) or len(search)>200:raise ValueError('Search with up to 200 characters.')
        where=['saved=1','removed=0'];args=[]
        if search:
            where.append("name LIKE ? ESCAPE '\\'")
            args.append('%'+search.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%')
        if category:where.append('category=?');args.append(category)
        if kind!='all':where.append('paired=?');args.append(int(kind=='pair'))
        order='DESC' if sort=='newest' else 'ASC';comparison='<' if sort=='newest' else '>'
        with self.connect() as db:
            if cursor:
                identifier(cursor);anchor=db.execute('SELECT created FROM creations WHERE id=?',(cursor,)).fetchone()
                if not anchor:raise ValueError('The Gallery page has changed. Refresh the list.')
                where.append(f'(created {comparison} ? OR (created=? AND id {comparison} ?))')
                args.extend((anchor['created'],anchor['created'],cursor))
            rows=db.execute(f'SELECT data FROM creations WHERE {" AND ".join(where)} ORDER BY created {order},id {order} LIMIT ?',(*args,limit+1)).fetchall()
        items=[self.summary(json.loads(row['data'])) for row in rows[:limit]]
        return {'items':items,'next_cursor':items[-1]['id'] if len(rows)>limit else None}

    def preview_removal(self,ids=None,delete_files=False):
        if type(delete_files) is not bool:raise ValueError('Choose whether saved files should also be deleted.')
        with self.lock,self.connect() as db:
            if ids is None:ids=[r['id'] for r in db.execute('SELECT id FROM creations WHERE saved=1 AND removed=0 LIMIT 1001')]
            if not isinstance(ids,list) or not 1<=len(ids)<=1000:raise ValueError('Select between 1 and 1000 creations.')
            ids=list(dict.fromkeys(ids));records=[self.get(i) for i in ids]
            versions={r['id']:db.execute('SELECT version FROM creations WHERE id=?',(r['id'],)).fetchone()['version'] for r in records}
            files=[]
            for record in records:
                for revision in record['revisions']+record.get('auxiliary_files',[]):
                    path=owned_path(self.directory(record['id']),self.directory(record['id'])/revision['file'])
                    if delete_files and path.exists() and (not path.is_file() or digest(path)!=revision['sha256']):
                        raise ValueError('A saved image file has changed. Review it before deleting.')
                    files.append({'path':str(path),'sha256':revision['sha256'],'bytes':revision['bytes']})
            review={'ids':ids,'versions':versions,'delete_files':delete_files,'files':files,
                    'entry_count':len(ids),'image_count':len(files),'bytes':sum(f['bytes'] for f in files)}
            token=secrets.token_urlsafe(32)
            db.execute('DELETE FROM removals WHERE expires<?',(time.time(),))
            db.execute('INSERT INTO removals VALUES(?,?,?)',(token,time.time()+300,json.dumps(review)))
            return {key:review[key] for key in ('delete_files','entry_count','image_count','bytes')}|{'token':token}

    def remove(self,token):
        if self.busy():raise ValueError('Wait for image creation to finish before removing saved images.')
        with self.lock,self.connect() as db:
            row=db.execute('SELECT data FROM removals WHERE token=? AND expires>?',(token,time.time())).fetchone()
            if not row:raise ValueError('Review the selection again before deleting.')
            review=json.loads(row['data'])
            for ident,version in review['versions'].items():
                current=db.execute('SELECT version FROM creations WHERE id=? AND removed=0',(ident,)).fetchone()
                if not current or current['version']!=version:raise ValueError('The creation changed. Review removal again.')
            paths=[]
            if review['delete_files']:
                for item in review['files']:
                    path=owned_path(self.root,item['path'])
                    if not path.exists():continue
                    if not path.is_file() or digest(path)!=item['sha256']:raise ValueError('An image changed; no files were deleted.')
                    paths.append(path)
                _,failures=remove_exact(paths)
                if failures:raise OSError('Some image files could not be deleted; their Gallery entries remain. Retry after closing file locks.')
            db.executemany('UPDATE creations SET removed=1 WHERE id=?',[(i,) for i in review['ids']])
            db.execute('DELETE FROM removals WHERE token=?',(token,))
            return {'removed':review['entry_count'],'deleted_files':len(paths)}
