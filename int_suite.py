import json
import sys
import unittest
import subprocess


# def remove_files(file_names):
#     # rm_list = ['rm', '-r', '-f']
#     try:
#         subprocess.check_output(['rm {files}'.format(files=" ".join(file_names))], shell=True)
#         print "Files removed:"
#         print file_names
#     except subprocess.CalledProcessError:
#         print "No files to delete."


def gco(branch):
    subprocess.call('pushd ../pulp/', shell=True)
    try:
        cmd = 'git checkout {branch}'.format(branch=branch)
        subprocess.call(cmd, shell=True)
    except subprocess.CalledProcessError:
        print 'Failed to check out'
        sys.exit(1)
    subprocess.call('popd', shell=True)


def migrate():
    pyclean()
    subprocess.call(["sudo",  "-u",  "apache",  "/usr/bin/pulp-manage-db"])


def prestart():
    pyclean()
    services = ['pulp_celerybeat', 'pulp_resource_manager', 'pulp_workers', 'httpd']
    for s in services:
        subprocess.call(['sudo', 'systemctl', 'restart', s])


def admin_login():
    subprocess.call('pulp-admin login --username admin --password admin', shell=True)


def drop_db():
    subprocess.call('mongo pulp_database --eval "db.dropDatabase()"', shell=True)


def pyclean():
    subprocess.call('find . -name "*.pyc" -exec rm -rf {} \;', shell=True)


def create_zoo_repo(repo_id):
    feed = "http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/"
    cmd = "pulp-admin rpm repo create --repo-id={repo} --feed={feed} --relative-url={url}".format(
        repo=repo_id, url=repo_id, feed=feed)
    print cmd
    subprocess.call(cmd, shell=True)


def create_empty_repo(repo_id):
    make_http_request('v2/repositories/', 'POST', "id={repo_id}".format(repo_id=repo_id))


def make_http_request(url, req_type, body=""):
    full_url = 'https://localhost/pulp/api/{url}'.format(url=url)
    request = "http --json -a admin:admin -b --verify=no {req_type} {full_url} {body}".format(
        req_type=req_type, full_url=full_url, body=body)
    return subprocess.check_output(request, stderr=subprocess.STDOUT, shell=True)


def get_all_repos_importers():
    return make_http_request('v2/repositories/?importers=True', 'GET')


def get_importers(repo_id):
    return make_http_request('v2/repositories/{repo_id}/importers/'.format(repo_id=repo_id), 'GET')


def get_importer(repo_id, importer_id):
    return make_http_request('v2/repositories/{repo_id}/importers/{imp_id}/'.format(
        repo_id=repo_id, imp_id=importer_id), 'GET')


def create_importer(repo_id, importer_id):
    url = 'v2/repositories/{repo_id}/importers/'.format(repo_id=repo_id)
    body = 'importer_type_id={importer_id}'.format(importer_id=importer_id)
    return make_http_request(url, 'POST', body=body)


def delete_importer(repo_id, importer_id):
    url = 'v2/repositories/{repo_id}/importers/{importer_id}/'.format(repo_id=repo_id,
                                                                      importer_id=importer_id)
    return make_http_request(url, 'DELETE')


def initialize_from_branch(branch):
    gco(branch)
    drop_db()
    migrate()
    prestart()
    admin_login()


class TestImporters(unittest.TestCase):

    def assert_same(self, obj_1, obj_2, ignore_values=None, dropped=None):
        if type(obj_1) != type(obj_2):
            print "object 1"
            print obj_1
            print "object 2"
            print obj_2
            raise AssertionError("obj_1 is type {a}, obj_2 is type {b}".format(a=type(obj_1),
                                                                               b=type(obj_2)))

        if type(obj_1) is dict:
            for key, value in obj_1.iteritems():
                if dropped and key in dropped:
                    continue
                if ignore_values and key in ignore_values:
                    continue

                if value is None:
                    try:
                        self.assertTrue(getattr(obj_2, key) is None)
                    except AttributeError:
                        continue
                else:
                    try:
                        self.assert_same(value, obj_2[key], ignore_values, dropped)
                    except AttributeError:
                        continue
        elif type(obj_1) is list:
            for value_1, value_2 in zip(obj_1, obj_2):
                self.assert_same(value_1, value_2, ignore_values, dropped)
        else:
            self.assertEqual(obj_1, obj_2)

    def setUp(self):
        # initialize_from_branch('master')
        # create_zoo_repo('test')
        # create_zoo_repo('othertest')
        self.master_repos_importers = [{u'display_name': None, u'description': None, u'last_unit_added': None, u'notes': {u'_repo-type': u'rpm-repo'}, u'last_unit_removed': None, u'content_unit_counts': {}, u'_ns': u'repos', u'importers': [{u'repo_id': u'test', u'_href': u'/pulp/api/v2/repositories/test/importers/yum_importer/', u'_ns': u'repo_importers', u'importer_type_id': u'yum_importer', u'last_sync': None, u'scheduled_syncs': [], u'_id': {u'$oid': u'55e0b9dae779895e67cabfe2'}, u'config': {u'feed': u'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'}, u'id': u'yum_importer'}], u'_id': {u'$oid': u'55e0b9dae779895e67cabfe1'}, u'id': u'test', u'_href': u'/pulp/api/v2/repositories/test/'}, {u'display_name': None, u'description': None, u'last_unit_added': None, u'notes': {u'_repo-type': u'rpm-repo'}, u'last_unit_removed': None, u'content_unit_counts': {}, u'_ns': u'repos', u'importers': [{u'repo_id': u'othertest', u'_href': u'/pulp/api/v2/repositories/othertest/importers/yum_importer/', u'_ns': u'repo_importers', u'importer_type_id': u'yum_importer', u'last_sync': None, u'scheduled_syncs': [], u'_id': {u'$oid': u'55e0b9dbe779895e6641a443'}, u'config': {u'feed': u'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'}, u'id': u'yum_importer'}], u'_id': {u'$oid': u'55e0b9dbe779895e6641a442'}, u'id': u'othertest', u'_href': u'/pulp/api/v2/repositories/othertest/'}]  # noqa
        self.master_test_importers = [{u'scratchpad': None, u'_href': u'/pulp/api/v2/repositories/test/importers/yum_importer/', u'_ns': u'repo_importers', u'importer_type_id': u'yum_importer', u'last_sync': None, u'scheduled_syncs': [], u'repo_id': u'test', u'_id': {u'$oid': u'55e0b9dae779895e67cabfe2'}, u'config': {u'feed': u'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'}, u'id': u'yum_importer'}]  # noqa
        self.master_test_yum_importer = {u'scratchpad': None, u'_href': u'/pulp/api/v2/repositories/test/importers/yum_importer/', u'_ns': u'repo_importers', u'importer_type_id': u'yum_importer', u'last_sync': None, u'scheduled_syncs': [], u'repo_id': u'test', u'_id': {u'$oid': u'55e0bc65e779897d71226938'}, u'config': {u'feed': u'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'}, u'id': u'yum_importer'}  # noqa
        self.master_test_handmade_yum_importer = [{"_href": u"/pulp/api/v2/repositories/test/importers/yum_importer/", "_id": {"$oid": "55e49e2ce7798926214d6125"}, "_ns": u"repo_importers", "config": {}, "id": u"yum_importer", u"importer_type_id": u"yum_importer", u"last_sync": None, u"repo_id": u"test", u"scratchpad": None}]  # noqa

    def test_upgrade(self):
        initialize_from_branch('master')
        create_zoo_repo('test')
        create_zoo_repo('othertest')
        gco('importers-mongoengine')
        migrate()
        prestart()
        # /repositories/?importers=True
        me_repos_importers = json.loads(get_all_repos_importers())
        # /repositories/test/importers/
        me_test_importers = json.loads(get_importers('test'))
        # /repositories/test/importerss/yum_importer/
        me_test_yum_importer = json.loads(get_importer('test', 'yum_importer'))
        self.assert_same(self.master_repos_importers, me_repos_importers,
                         dropped=['scheduled_syncs'], ignore_values=['$oid'])
        self.assert_same(self.master_test_importers, me_test_importers,
                         dropped=['scheduled_syncs'], ignore_values=['$oid'])
        self.assert_same(self.master_test_yum_importer, me_test_yum_importer,
                         dropped=['scheduled_syncs'], ignore_values=['$oid'])

    def test_new_data(self):
        initialize_from_branch('importers-mongoengine')
        create_zoo_repo('test')
        create_zoo_repo('othertest')
        # /repositories/?importers=True
        new_repos_importers = json.loads(get_all_repos_importers())
        # /repositories/test/importers/
        new_test_importers = json.loads(get_importers('test'))
        # /repositories/test/importers/yum_importer/
        new_test_yum_importer = json.loads(get_importer('test', 'yum_importer'))
        self.assert_same(self.master_repos_importers, new_repos_importers,
                         dropped=['scheduled_syncs'], ignore_values=['$oid'])
        self.assert_same(self.master_test_importers, new_test_importers,
                         dropped=['scheduled_syncs'], ignore_values=['$oid'])
        self.assert_same(self.master_test_yum_importer, new_test_yum_importer,
                         dropped=['scheduled_syncs'], ignore_values=['$oid'])

    def test_create_and_delete(self):
        initialize_from_branch('importers-mongoengine')
        create_empty_repo('test')
        create_empty_repo('othertest')
        self.assertEqual(json.loads(get_importers('test')), [])
        # POST /repositories/test/importers/
        create_importer('test', 'yum_importer')
        self.assert_same(json.loads(get_importers('test')), self.master_test_handmade_yum_importer,
                         ignore_values=['$oid'])
        # DELETE /repositories/test/importers/<importer_id>/
        delete_importer('test', 'yum_importer')
        self.assertEqual(json.loads(get_importers('test')), [])
