#!/usr/bin/env python3
"""Prepare cross-build headers and a link-only SDL reference; no device writes."""
import argparse,json,shutil,struct,subprocess,hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('library',type=Path);a=p.parse_args()
with a.library.open('rb') as f:header=f.read(20)
if len(header)<20 or header[:6]!=b'\x7fELF\x01\x01' or struct.unpack_from('<H',header,18)[0]!=40:
    p.error('Expected a little-endian ARM32 ELF SDL library; ARM64/Flip libraries will not work.')
r=Path(__file__).resolve().parents[1];lock=json.loads((r/'upstreams.lock.json').read_text())['sdl_headers'];src=r/'.local/upstream/SDL-1.2'
if not src.exists():
    src.mkdir(parents=True);subprocess.run(['git','init',str(src)],check=True)
    subprocess.run(['git','-C',str(src),'fetch','--depth','1',lock['url'],lock['commit']],check=True)
    subprocess.run(['git','-C',str(src),'checkout','--detach','FETCH_HEAD'],check=True)
if subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()!=lock['commit']:raise SystemExit('SDL source does not match lock')
dest=r/'.local/deps/include/SDL';dest.mkdir(parents=True,exist_ok=True)
for f in (src/'include').glob('*.h'):shutil.copyfile(f,dest/f.name)
features=['STDC_HEADERS','HAVE_SYS_TYPES_H','HAVE_STDIO_H','HAVE_STDLIB_H','HAVE_STDDEF_H','HAVE_STDARG_H','HAVE_STRING_H','HAVE_STRINGS_H','HAVE_STDINT_H','HAVE_INTTYPES_H','HAVE_CTYPE_H']
(dest/'SDL_config.h').write_text('#ifndef _SDL_config_h\n#define _SDL_config_h\n/* ARM Linux/glibc client headers; does not configure the SDL implementation. */\n'+''.join('#define '+x+' 1\n' for x in features)+'#endif\n')
lib=r/'.local/deps/lib/libSDL-1.2.so.0';lib.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a.library,lib)
(r/'.local/deps/provenance.json').write_text(json.dumps({'library_source':str(a.library.resolve()),'sha256':hashlib.sha256(lib.read_bytes()).hexdigest(),'role':'Link-time reference only; not included in package.'},indent=2)+'\n')
