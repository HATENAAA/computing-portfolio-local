#!/usr/bin/env python3
"""Apply a portfolio ZIP to a fixed installation, preserving its runtime state."""
import argparse, hashlib, json, subprocess, os, shlex, shutil, stat, sys, tempfile, time, zipfile
from pathlib import Path, PurePosixPath

PROJECTS = {'vrfitai':'vrfitai', 'firewatch':'firewatch', 'manufacturing-platform':'manufacturing', 'hsi-sr-lab':'hsi', 'signal-lab':'signal','city-explorer':'city','bathymetry-lab':'bathymetry'}
PROTECTED = {'node_modules', '.venv', 'venv', '.tools', '.git', '__pycache__', 'data', '.portfolio', '.pytest_cache'}

def protected(rel):
    return any(p in PROTECTED or p.startswith('.venv.backup-') for p in rel.parts) or rel.name.startswith('~$') or rel.name in {'.env', '.env.local', '.env.production', '.DS_Store'} or rel.as_posix() == 'firewatch/models/config.json' or rel.name.endswith(('.sqlite', '.sqlite-wal', '.sqlite-shm', '.mv.db', '.trace.db', '.pyc'))

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(source):
    for name in ('scripts/manage.py', 'README.md', 'SHA256SUMS.txt'):
        if not (source/name).is_file(): raise ValueError('这不是完整作品集：缺少 '+name)
    entries = {}
    for line in (source/'SHA256SUMS.txt').read_text(encoding='utf8').splitlines():
        if not line.strip(): continue
        value, name = line.split('  ', 1)
        rel = PurePosixPath(name)
        if rel.is_absolute() or '..' in rel.parts or '\\' in name or name in entries: raise ValueError('校验清单路径无效')
        path = source/name
        if len(value)!=64 or not path.is_file() or digest(path)!=value: raise ValueError('压缩包校验失败：'+name)
        entries[name] = value
    for path in source.rglob('*'):
        if path.is_symlink(): raise ValueError('更新包不支持符号链接')
        if path.is_file() and path.name!='SHA256SUMS.txt' and path.relative_to(source).as_posix() not in entries: raise ValueError('文件未列入校验清单：'+str(path.relative_to(source)))
    return entries

def unpack(archive, folder):
    with zipfile.ZipFile(archive) as z:
        entries=z.infolist();seen=set()
        if len(entries)>20000 or sum(x.file_size for x in entries)>1024**3: raise ValueError('更新包超过 20,000 文件或 1 GB 解压限制')
        for entry in entries:
            path=PurePosixPath(entry.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in entry.filename or entry.filename in seen or stat.S_ISLNK(entry.external_attr>>16): raise ValueError('更新包路径无效')
            seen.add(entry.filename)
        z.extractall(folder)
    roots=[folder] if (folder/'scripts/manage.py').is_file() else [p for p in folder.iterdir() if p.is_dir() and (p/'scripts/manage.py').is_file()]
    if len(roots)!=1: raise ValueError('请提供一个完整作品集 ZIP')
    return roots[0]

def apply(source, target, dry_run=False):
    source=source.resolve();target=target.resolve()
    if source==target or source in target.parents or target in source.parents: raise ValueError('更新包与运行目录不能互相包含')
    if not (target/'scripts/manage.py').is_file(): raise ValueError('目标不是现有作品集目录')
    entries=verify(source);changes=[];affected=set()
    for name in sorted(entries):
        rel=Path(name)
        if protected(rel): continue
        destination=target/rel
        if destination.is_symlink() or any(parent.is_symlink() for parent in destination.parents if parent!=target): raise ValueError('目标路径包含符号链接：'+name)
        if destination.is_file() and digest(destination)==entries[name]: continue
        changes.append(rel)
        if rel.name in {'package.json','package-lock.json','requirements.txt','requirements-lock.txt','requirements-eval.txt','pom.xml'} and rel.parts[0] in PROJECTS: affected.add(PROJECTS[rel.parts[0]])
    result={'changed_files':len(changes),'dependency_projects':sorted(affected),'dry_run':dry_run}
    if dry_run or not changes: return result
    backup=target.parent/(target.name+'_更新备份_'+time.strftime('%Y%m%d_%H%M%S')+'_'+str(time.time_ns()%1000000));backup.mkdir()
    (backup/'更新记录.json').write_text(json.dumps({'files':[str(p) for p in changes],'dependency_projects':sorted(affected)},ensure_ascii=False,indent=2),encoding='utf8')
    shutil.copy2(target/'SHA256SUMS.txt',backup/'SHA256SUMS.txt') if (target/'SHA256SUMS.txt').is_file() else None
    try:
        for rel in changes:
            destination=target/rel
            if destination.exists():
                saved=backup/rel;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(destination,saved)
            destination.parent.mkdir(parents=True,exist_ok=True)
            fd,temporary=tempfile.mkstemp(prefix='.portfolio-update-',dir=destination.parent);os.close(fd)
            try:
                shutil.copy2(source/rel,temporary);os.replace(temporary,destination)
            finally:
                if os.path.exists(temporary):os.unlink(temporary)
    except Exception:
        print('更新中断，原文件备份位于：'+str(backup),file=sys.stderr);raise
    result['backup']=str(backup)
    # Preserve the distribution checksum file; it describes the ZIP, not local runtime/private files.
    shutil.copy2(source/'SHA256SUMS.txt', target/'SHA256SUMS.txt')
    receipt=target/'.portfolio';receipt.mkdir(exist_ok=True)
    (receipt/'last-update.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('archive',nargs='?');parser.add_argument('--target',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--dry-run',action='store_true');parser.add_argument('--install-changed',action='store_true');args=parser.parse_args()
    if args.install_changed:
        receipt=args.target/'.portfolio/last-update.json'
        if not receipt.is_file():print('没有待处理的更新记录。');return
        projects=json.loads(receipt.read_text(encoding='utf8'))['dependency_projects']
        if any(name not in PROJECTS.values() for name in projects):raise ValueError('更新记录中的项目无效')
        for name in projects:subprocess.run([sys.executable,str(args.target/'scripts/manage.py'),'install',name],cwd=args.target,check=True)
        print('变化项目的依赖已处理。' if projects else '本次更新没有依赖变化，无需安装。');return
    value=args.archive
    if not value:
        print('先关闭正在运行的作品集及正在编辑的文件。此操作保留依赖、数据库和私有配置。')
        tokens=shlex.split(input('将新作品集 ZIP 拖到此窗口，再按回车：').strip())
        if len(tokens)!=1:raise ValueError('请一次拖入一个 ZIP 文件')
        value=tokens[0]
    with tempfile.TemporaryDirectory(prefix='portfolio-update-') as temp:
        source=unpack(Path(value).expanduser().resolve(),Path(temp));result=apply(source,args.target,args.dry_run)
    print('已检查' if args.dry_run else '更新完成',str(result['changed_files'])+' 个文件。')
    if result.get('backup'):print('原文件备份：'+result['backup'])
    if result['dependency_projects']:
        print('以下项目的依赖清单发生变化，请只安装这些项目：')
        print('、'.join(result['dependency_projects'])+'。在仓库根目录运行 python3 scripts/update_portfolio.py --install-changed 即可，无需安装全部项目。')
    else: print('依赖清单未变；已安装的依赖无需重装，直接运行启动脚本。')
    print('如果此目录尚未安装过依赖，首次仍需运行“Install Dependencies.command”。')

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,zipfile.BadZipFile) as exc:print('更新未完成：'+str(exc),file=sys.stderr);sys.exit(1)
