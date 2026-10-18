import tempfile
import unittest
from pathlib import Path
from file_ops_safe import FileOperationError, copy_or_move

class FileOpsTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.src=Path(self.t.name)/'in.csv';self.dst=Path(self.t.name)/'out.csv'
        self.src.write_text('original',encoding='utf-8')
    def test_copy(self):
        r=copy_or_move(self.src,self.dst)
        self.assertEqual(self.src.read_text(),self.dst.read_text());self.assertEqual(r['source_sha256'],r['destination_sha256'])
    def test_move(self):
        copy_or_move(self.src,self.dst,move=True)
        self.assertFalse(self.src.exists());self.assertEqual(self.dst.read_text(),'original')
    def test_existing_preserved(self):
        self.dst.write_text('PREVIOUS')
        with self.assertRaisesRegex(FileOperationError,'exists'):copy_or_move(self.src,self.dst)
        self.assertEqual(self.dst.read_text(),'PREVIOUS');self.assertTrue(self.src.exists())
    def test_overwrite_after_success(self):
        self.dst.write_text('PREVIOUS');copy_or_move(self.src,self.dst,overwrite=True)
        self.assertEqual(self.dst.read_text(),'original')
    def test_same_path_blocked(self):
        with self.assertRaisesRegex(FileOperationError,'equals'):copy_or_move(self.src,self.src,overwrite=True)
    def test_source_missing(self):
        self.src.unlink()
        with self.assertRaisesRegex(FileOperationError,'unavailable'):copy_or_move(self.src,self.dst)
    def test_symlink_rejected(self):
        link=Path(self.t.name)/'link.csv'
        link.symlink_to(self.src)
        with self.assertRaisesRegex(FileOperationError,'Symbolic'):copy_or_move(link,self.dst)
    def test_temp_cleanup(self):
        copy_or_move(self.src,self.dst)
        self.assertEqual(sorted(p.name for p in Path(self.t.name).iterdir()),['in.csv','out.csv'])

if __name__=='__main__':unittest.main()
