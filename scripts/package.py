#!/usr/bin/env python3
"""Package the game-free ARM runtime and its corresponding source."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile,tempfile,zipfile
root=Path(__file__).resolve().parents[1]
binary=root/'artifacts/armhf/butterscotch'
header=binary.read_bytes()[:20]
if header[:6]!=b'\x7fELF\x01\x01' or int.from_bytes(header[18:20],'little')!=40:
    raise SystemExit('Build the ARM32 runtime first')
out=root/'artifacts/release';out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='ufo50-package-') as tmp:
    stage=Path(tmp);game=stage/'Roms/PORTS/Games/UFO50';(game/'bin').mkdir(parents=True)
    shutil.copy2(binary,game/'bin/butterscotch')
    shutil.copy2(root/'port/script.sh',game/'script.sh');(game/'script.sh').chmod(0o755)
    shortcut=stage/'Roms/PORTS/Shortcuts/Action/UFO50.notfound';shortcut.parent.mkdir(parents=True)
    shutil.copy2(root/'port/UFO50.notfound',shortcut)
    (game/'gamefiles').mkdir();(game/'gamefiles/_required_files.txt').write_text('Copy owned UFO 50 assets imported with scripts/ufo50.py here.\n')
    for name in ['README.md','LICENSE','NOTICE']:shutil.copy2(root/name,game/name)
    source=stage/'source.tar.gz'
    # A distributable package includes the committed source, never local assets or saves.
    subprocess.run(['git','-C',str(root),'archive','--format=tar.gz','--output='+str(source),'HEAD'],check=True)
    digest=hashlib.sha256(binary.read_bytes()).hexdigest()
    (stage/'manifest.json').write_text(json.dumps({'status':'development','runtime_sha256':digest,'gamefiles_included':False},indent=2)+'\n')
    archive=out/'ufo50-miyoo-mini.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(stage.rglob('*')):
            if f.is_file():z.write(f,f.relative_to(stage))
    (out/'SHA256SUMS').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
    print(archive)
