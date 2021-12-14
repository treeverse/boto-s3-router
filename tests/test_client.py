import unittest
import boto3
import docker
import botos3router
import pytest


def create_client(minio1, minio2):
    profiles = {
        "test_upload": {
            "source_bucket_pattern": "bucket-a",
            "source_key_pattern": "a/*",
            "mapped_bucket_name": "test-upload",
            "mapped_prefix": "main/"
        },
        "test_copy": {
            "source_bucket_pattern": "source",
            "mapped_bucket_name": "test-copy",
            "mapped_prefix": "main/"
        },
        "test_copy2": {
            "source_bucket_pattern": "test-copy",
        },
        "test_delete_objects": {
            "source_bucket_pattern": "delete-objects*",
            "mapped_bucket_name": "test-delete-objects",
            "mapped_prefix": "test/"
        },
        "test_paginator": {
            "source_bucket_pattern": "pagi",
            "mapped_bucket_name": "test-paginator",
            "mapped_prefix": "dev/"
        },
        "test_list_objects": {
            "source_bucket_pattern": "list",
            "mapped_bucket_name": "test-list-objects",
            "mapped_prefix": "dev/"
        }

    }
    client_mapping = {"test_upload": minio1, "test_copy": minio1, "test_copy2": minio1,
                      "test_delete_objects": minio2, "test_paginator": minio2, "test_list_objects": minio2,
                      "default": minio2}

    return botos3router.client(client_mapping, profiles)


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        docker_client = docker.from_env()

        cls.docker1 = docker_client.containers.run(image="minio/minio:RELEASE.2021-06-07T21-40-51Z",
                                                   command=["minio", "server", "/data"],
                                                   environment={"MINIO_ROOT_USER": "minioadmin",
                                                                "MINIO_ROOT_PASSWORD": "minioadmin",
                                                                "MINIO_UPDATE": "off"},
                                                   ports={"9000": None}, detach=True)

        cls.docker2 = docker_client.containers.run(image="minio/minio:RELEASE.2021-06-07T21-40-51Z",
                                                   command=["minio", "server", "/data"],
                                                   environment={"MINIO_ROOT_USER": "minioadmin",
                                                                "MINIO_ROOT_PASSWORD": "minioadmin",
                                                                "MINIO_UPDATE": "off"},
                                                   ports={"9000": None}, detach=True)

        cls.docker1.reload()
        cls.docker2.reload()
        docker1_port = cls.docker1.ports['9000/tcp'][0]['HostPort']
        docker2_port = cls.docker2.ports['9000/tcp'][0]['HostPort']

        cls.minio1 = boto3.client('s3',
                                  endpoint_url=f'http://localhost:{docker1_port}',
                                  aws_access_key_id='minioadmin',
                                  aws_secret_access_key='minioadmin', )

        cls.minio2 = boto3.client('s3',
                                  endpoint_url=f'http://localhost:{docker2_port}',
                                  aws_access_key_id='minioadmin',
                                  aws_secret_access_key='minioadmin')

        cls.botos3router_client = create_client(cls.minio1, cls.minio2)

    def test_upload(self):
        self.minio1.create_bucket(Bucket="test-upload")
        content = "TEST_UPLOAD"
        self.botos3router_client.put_object(Bucket="bucket-a", Key="a/b/1.txt", Body=content)  # route to minio1

        data = self.botos3router_client.get_object(Bucket="bucket-a", Key="a/b/1.txt")
        contents = data['Body'].read().decode('utf-8')
        self.assertEqual(contents, content)

        with pytest.raises(Exception):
            # assert that the call is to minio1
            self.minio2.get_object(Bucket="test-upload", Key="main/a/b/1.txt")

    def test_copy(self):
        self.minio1.create_bucket(Bucket="test-copy")
        content = "TEST_COPY"
        self.botos3router_client.put_object(Bucket="test-copy", Key="main/a/b/1.txt", Body=content)  # route to minio1
        self.botos3router_client.copy_object(Bucket="test-copy", Key="1.txt",
                                      CopySource={"Bucket": "source", "Key": "a/b/1.txt"})

        data = self.botos3router_client.get_object(Bucket="test-copy", Key="1.txt")
        contents = data['Body'].read().decode('utf-8')
        self.assertEqual(contents, content)

        with pytest.raises(Exception):
            # assert that the call is to minio1
            self.minio2.get_object(Bucket="test-copy", Key="1.txt")

    def test_default(self):
        self.minio2.create_bucket(Bucket="test-default")
        content = "TEST_DEFAULT"
        self.botos3router_client.put_object(Bucket="test-default", Key="2.txt", Body=content)  # route to default minio2

        data = self.botos3router_client.get_object(Bucket="test-default", Key="2.txt")
        contents = data['Body'].read().decode('utf-8')
        self.assertEqual(contents, content)

        with pytest.raises(Exception):
            # assert that the call is to minio2
            self.minio1.get_object(Bucket="test_upload", Key="2.txt")

    def test_delete_objects(self):
        self.minio2.create_bucket(Bucket="test-delete-objects")
        content = "TEST_DELETE_OBJECTS"
        self.botos3router_client.put_object(Bucket="test-delete-objects", Key="test/1.txt", Body=content)  # route to minio2
        self.botos3router_client.put_object(Bucket="test-delete-objects", Key="test/2.txt", Body=content)

        res = self.botos3router_client.delete_objects(Bucket="delete-objects1", Delete={
            'Objects': [
                {
                    'Key': '1.txt',
                },
                {
                    'Key': '2.txt',
                },
            ]
        })
        self.assertEqual(res["Deleted"][0]["Key"], "test/1.txt")
        self.assertEqual(res["Deleted"][1]["Key"], "test/2.txt")

    def test_paginator(self):
        self.minio2.create_bucket(Bucket="test-paginator")
        content = "TEST_PAGINATOR"
        self.botos3router_client.put_object(Bucket="test-paginator", Key="dev/test/1.txt", Body=content)  # route to minio2
        self.botos3router_client.put_object(Bucket="test-paginator", Key="dev/test/2.txt", Body=content)
        self.botos3router_client.put_object(Bucket="test-paginator", Key="1.txt", Body=content)
        self.botos3router_client.put_object(Bucket="test-paginator", Key="test/3.txt", Body=content)

        self.assertEqual(self.botos3router_client.can_paginate(operation_name='list_objects'), True)

        # Create a reusable Paginator
        paginator = self.botos3router_client.get_paginator(operation_name='list_objects')

        # Create a PageIterator from the Paginator
        page_iterator = paginator.paginate(Bucket='pagi', Prefix="test")

        # Compare the iterators
        for page in page_iterator:
            self.assertEqual(len(page['Contents']), 2)

    def test_list_objects(self):
        self.minio2.create_bucket(Bucket="test-list-objects")
        content = "TEST_LIST_OBJECTS"

        self.botos3router_client.put_object(Bucket="test-list-objects", Key="dev/test/1.txt", Body=content)  # route to minio2
        self.botos3router_client.put_object(Bucket="test-list-objects", Key="dev/test/2.txt", Body=content)
        self.botos3router_client.put_object(Bucket="test-list-objects", Key="dev/1.txt", Body=content)
        self.botos3router_client.put_object(Bucket="test-list-objects", Key="1.txt", Body=content)
        self.botos3router_client.put_object(Bucket="test-list-objects", Key="test/3.txt", Body=content)

        objects = self.botos3router_client.list_objects_v2(Bucket="list", Prefix="test")
        print(objects)

        self.assertEqual(len(objects['Contents']), 2)
        self.assertEqual(objects["Contents"][0]["Key"], "dev/test/1.txt")
        self.assertEqual(objects["Contents"][1]["Key"], "dev/test/2.txt")

        # test empty prefix
        objects = self.botos3router_client.list_objects_v2(Bucket="list", Prefix="")
        self.assertEqual(len(objects['Contents']), 3)
        self.assertEqual(objects["Contents"][0]["Key"], "dev/1.txt")
        self.assertEqual(objects["Contents"][1]["Key"], "dev/test/1.txt")
        self.assertEqual(objects["Contents"][2]["Key"], "dev/test/2.txt")

    def test_meta(self):
        self.assertEqual(self.botos3router_client.meta, self.minio2.meta)

        self.minio2.create_bucket(Bucket="test-meta")
        event_system = self.botos3router_client.meta.events

        def add_my_bucket(params, **kwargs):
            if 'Bucket' not in params:
                params['Bucket'] = 'test-meta'

        event_system.register('provide-client-params.s3.GetBucketAcl', add_my_bucket)
        self.botos3router_client.get_bucket_acl()

    @classmethod
    def tearDownClass(cls):
        cls.docker1.stop()
        cls.docker2.stop()
