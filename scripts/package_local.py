"""Build a portable ZIP from tracked files and, on Windows, the verified DLL."""
import argparse
import hashlib
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHERS = {'Install Dependencies', 'Launch Portfolio', 'Launch Project', 'Configure AI Assistant'}


def write_archive(system, output):
    index = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT).decode('utf-8')
    paths = {}
    suffix = '.cmd' if system == 'windows-x64' else '.command'
    for row in index.strip('\0').split('\0'):
        attributes, name = row.split('\t', 1)
        mode, _, stage = attributes.split()
        if stage != '0' or mode not in {'100644', '100755'}:
            raise ValueError(f'Unexpected Git file mode for {name}')
        path = Path(name)
        if name == 'SHA256SUMS.txt' or name.startswith('.github/'):
            continue
        if path.suffix in {'.cmd', '.command'} and path.suffix != suffix:
            continue
        paths[name] = int(mode, 8)

    if {n for n in paths if n.endswith(suffix)} != {n + suffix for n in LAUNCHERS}:
        raise ValueError(f'The {system} launchers are incomplete')
    if system == 'windows-x64':
        source = ROOT / 'firewatch/native/fire_core.cpp'
        digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
        folder = ROOT / 'firewatch/.native'
        dlls = [p for p in folder.glob(f'fire-*-{digest}.dll')
                if re.fullmatch(r'fire-(AMD64|x86_64)-[a-f0-9]{16}\.dll', p.name, re.I)]
        if len(dlls) != 1 or dlls[0].read_bytes()[:2] != b'MZ':
            raise ValueError('Build and test the x64 FireWatch DLL first')
        paths[dlls[0].relative_to(ROOT).as_posix()] = 0o100644
    if not {'index.html', 'README.md', 'scripts/manage.py'} <= paths.keys():
        raise ValueError('The archive is missing the portfolio entry point')

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
        hashes = []
        for name, mode in sorted(paths.items()):
            source = ROOT / name
            if source.is_symlink() or not source.is_file():
                raise ValueError(f'Invalid distribution file: {name}')
            content = source.read_bytes()
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = mode << 16
            archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=3)
            hashes.append(f'{hashlib.sha256(content).hexdigest()}  {name}\n')
        archive.writestr('SHA256SUMS.txt', ''.join(hashes).encode('utf-8'))
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() or set(archive.namelist()) != set(paths) | {'SHA256SUMS.txt'}:
            raise ValueError(f'Invalid archive: {output}')
    print(f'Created {output} with {len(paths)} files and SHA256SUMS.txt')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('platform', choices=['windows-x64', 'macos'])
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    write_archive(args.platform, args.output)
