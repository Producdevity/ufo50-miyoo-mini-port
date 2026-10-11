import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

spec=importlib.util.spec_from_file_location('ufo50',Path(__file__).parents[1]/'scripts/ufo50.py')
ufo=importlib.util.module_from_spec(spec);spec.loader.exec_module(ufo)

def fixture():
    gen=bytearray(100);gen[1]=17
    struct.pack_into('<2I',gen,60,384,216)
    parts=[]
    for name,body in [(b'GEN8',gen),(b'CODE',struct.pack('<I',0)),(b'STRG',struct.pack('<I',0))]:
        parts.append(name+struct.pack('<I',len(body))+body)
    body=b''.join(parts);return b'FORM'+struct.pack('<I',len(body))+body

class Assets(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def archive(self,members):
        p=self.root/'game.zip'
        with zipfile.ZipFile(p,'w') as z:
            for name,content in members:z.writestr(name,content)
        return p
    def test_import_preserves_source_and_excludes_saves_and_binaries(self):
        p=self.archive([('ufo50/data.win',fixture()),('ufo50/ufo50.exe',b'exe'),('ufo50/_Saved Games/save',b'save'),('ufo50/ext/ENGLISH/0.json',b'{}')])
        before=p.read_bytes();out=self.root/'out';ufo.import_zip(p,out)
        self.assertEqual(p.read_bytes(),before)
        self.assertEqual(sorted(str(x.relative_to(out)) for x in out.rglob('*') if x.is_file()),['data.win','ext/ENGLISH/0.json'])
    def test_existing_destination_refused(self):
        p=self.archive([('data.win',fixture())]);out=self.root/'out';out.mkdir();(out/'save').write_text('keep')
        with self.assertRaises(ValueError):ufo.import_zip(p,out)
        self.assertEqual((out/'save').read_text(),'keep')
    def test_path_traversal_refused(self):
        p=self.archive([('data.win',fixture()),('../escape',b'x')])
        with self.assertRaises(ValueError):ufo.import_zip(p,self.root/'out')
        self.assertFalse((self.root/'out').exists())
    def test_zip_symlink_refused(self):
        info=zipfile.ZipInfo('game/link');info.create_system=3;info.external_attr=0o120777<<16
        p=self.archive([('game/data.win',fixture()),(info,b'../../target')])
        with self.assertRaises(ValueError):ufo.import_zip(p,self.root/'out')
    def test_duplicate_case_path_refused(self):
        p=self.archive([('data.win',fixture()),('textures/a.yytex',b''),('textures/A.yytex',b'')])
        with self.assertRaises(ValueError):ufo.import_zip(p,self.root/'out')
    def test_ambiguous_game_root_refused(self):
        p=self.archive([('a/data.win',fixture()),('b/data.win',fixture())])
        with self.assertRaises(ValueError):ufo.import_zip(p,self.root/'out')
    def test_bad_form_does_not_promote_partial_import(self):
        p=self.archive([('data.win',b'FORM'+struct.pack('<I',100))])
        with self.assertRaises(ValueError):ufo.import_zip(p,self.root/'out')
        self.assertFalse((self.root/'out').exists())
        self.assertFalse(list(self.root.glob('.ufo50-import-*')))
    def test_chunk_boundary_rejected(self):
        data=bytearray(fixture());struct.pack_into('<I',data,12,100000)
        with self.assertRaises(ValueError):ufo.chunks(data)

if __name__=='__main__':unittest.main()
