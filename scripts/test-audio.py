#!/usr/bin/env python3
"""Generate a synthetic audio group and exercise the native mixer. No game files."""
import argparse,io,math,struct,subprocess,tempfile,wave
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('runner',type=Path);p.add_argument('--fixture-only',type=Path)
a=p.parse_args()
def fixture(root):
    buf=io.BytesIO()
    with wave.open(buf,'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100)
        w.writeframes(b''.join(struct.pack('<hh',int(12000*math.sin(i*2*math.pi*440/44100)),int(8000*math.sin(i*2*math.pi*220/44100))) for i in range(4410)))
    wav=buf.getvalue();audo=struct.pack('<III',1,24,len(wav))+wav
    form=b'AUDO'+struct.pack('<I',len(audo))+audo
    (root/'audiogroup2.dat').write_bytes(b'FORM'+struct.pack('<I',len(form))+form)
if a.fixture_only:
    a.fixture_only.mkdir(parents=True,exist_ok=True);fixture(a.fixture_only)
else:
    with tempfile.TemporaryDirectory(prefix='ufo50-audio-test-') as d:
        fixture(Path(d));subprocess.run([str(a.runner.resolve()),'--audio-selftest',d],check=True,timeout=15)
