import subprocess
from mock import patch

from django.test import TestCase
from django.core.management.base import CommandError
from django.conf import settings
from django.utils import six

from dbbackup.management.commands.dbrestore import Command as DbrestoreCommand
from dbbackup.dbcommands import DBCommands
from dbbackup.tests.utils import FakeStorage, ENCRYPTED_FILE, TEST_DATABASE
from dbbackup.tests.utils import GPG_PRIVATE_PATH, DEV_NULL, COMPRESSED_FILE
from dbbackup.tests.utils import GPG_PUBLIC_PATH, clean_gpg_keys


@patch('dbbackup.management.commands.dbrestore.input', return_value='y')
class DbrestoreCommandRestoreBackupTest(TestCase):
    def setUp(self):
        self.command = DbrestoreCommand()
        self.command.stdout = DEV_NULL
        self.command.uncompress = False
        self.command.decrypt = False
        self.command.backup_extension = 'bak'
        self.command.filepath = 'foofile'
        self.command.database = TEST_DATABASE
        self.command.dbcommands = DBCommands(TEST_DATABASE)
        self.command.passphrase = None
        self.command.storage = FakeStorage()
        cmd = ('gpg --import %s' % GPG_PRIVATE_PATH).split()
        subprocess.call(cmd, stdout=DEV_NULL, stderr=DEV_NULL)

    def tearDown(self):
        clean_gpg_keys()

    def test_no_filepath(self, *args):
        self.command.storage.list_files = ['foo.bak']
        self.command.filepath = None
        self.command.restore_backup()

    def test_no_backup_found(self, *args):
        self.command.filepath = None
        with self.assertRaises(CommandError):
            self.command.restore_backup()

    def test_uncompress(self, *args):
        self.command.storage.file_read = COMPRESSED_FILE
        self.command.filepath = COMPRESSED_FILE
        self.command.uncompress = True
        self.command.restore_backup()

    @patch('dbbackup.utils.getpass', return_value=None)
    def test_decrypt(self, *args):
        self.command.decrypt = True
        self.command.filepath = ENCRYPTED_FILE
        self.command.restore_backup()


class DbrestoreCommandGetDatabaseTest(TestCase):
    def setUp(self):
        self.command = DbrestoreCommand()

    def test_give_db_name(self):
        db = self.command._get_database({'database': 'default'})
        self.assertEqual(db, settings.DATABASES['default'])

    def test_no_given_db(self):
        db = self.command._get_database({})
        self.assertEqual(db, settings.DATABASES['default'])

    @patch('django.conf.settings.DATABASES', {'db1': {}, 'db2': {}})
    def test_no_given_db_multidb(self):
        with self.assertRaises(CommandError):
            self.command._get_database({})


class DbrestoreCommandGetExtensionTest(TestCase):
    def setUp(self):
        self.command = DbrestoreCommand()

    def test_tar(self):
        ext = self.command.get_extension('foo.tar')
        self.assertEqual(ext, '.tar')

    def test_tar_gz(self):
        ext = self.command.get_extension('foo.tar.gz')
        self.assertEqual(ext, '.gz')

    def test_no_extension(self):
        ext = self.command.get_extension('foo')
        self.assertEqual(ext, '')
