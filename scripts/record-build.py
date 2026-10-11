#!/usr/bin/env python3
"""Record source revision and toolchain provenance after a successful cross-build."""
import argparse
import datetime
import json
import subprocess
from pathlib import Path
from artifact import ROOT, inspect_arm32, sha256, source_state

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('target', choices=['armhf', 'sp'])
parser.add_argument('sdl_reference', type=Path)
args = parser.parse_args()
binary = ROOT / 'artifacts' / args.target / 'butterscotch'
cache = (binary.parent / 'CMakeCache.txt').read_text().splitlines()
features = {line.split(':', 1)[0]: line.split('=', 1)[1] for line in cache
            if line.startswith(('ENABLE_VM_TRACING:', 'ENABLE_VM_GML_PROFILER:', 'ENABLE_VM_OPCODE_PROFILER:'))}
ipo = any(line.startswith('CMAKE_INTERPROCEDURAL_OPTIMIZATION:') and line.endswith('=ON')
          for line in cache)
record = {'interprocedural_optimization': ipo, 'diagnostic_features': features,
          'schema': 1, 'target': args.target, 'source': source_state(),
          'runtime_sha256': sha256(binary), 'elf': inspect_arm32(binary),
          'sdl_reference_sha256': sha256(args.sdl_reference),
          'sdl_headers_commit': json.loads((ROOT / 'upstreams.lock.json').read_text())['sdl_headers']['commit'],
          'zig_version': subprocess.check_output(['zig', 'version'], text=True).strip(),
          'cmake_version': subprocess.check_output(['cmake', '--version'], text=True).splitlines()[0],
          'built_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
(binary.parent / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
