import unittest
import boto3
import docker
import botwo
import pytest


def create_botwo_client(minio1, minio2):
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

    return botwo.client(client_mapping, profiles)


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        docker_client = docker.from_env()

        cls.docker1 = docker_client.containers.run(image="minio/minio:RELEASE.2021-06-07T21-40-51Z",
                                                   command=["minio", "server", "/data"],
                                                   environment={"MINIO_ROOT_USER": "minioadmin",
                                                                "MINIO_ROOT_PASSWORD": "minioadmin",
                                                                "MINIO_UPDATE": "off"},
                                                   ports={"9000": 9000}, detach=True)

        cls.docker2 = docker_client.containers.run(image="minio/minio:RELEASE.2021-06-07T21-40-51Z",
                                                   command=["minio", "server", "/data"],
                                                   environment={"MINIO_ROOT_USER": "minioadmin",
                                                                "MINIO_ROOT_PASSWORD": "minioadmin",
                                                                "MINIO_UPDATE": "off"},
                                                   ports={"9000": 7000}, detach=True)

        cls.minio1 = boto3.client('s3',
                                  endpoint_url='http://localhost:9000',
                                  aws_access_key_id='minioadmin',
                                  aws_secret_access_key='minioadmin', )

        cls.minio2 = boto3.client('s3',
                                  endpoint_url='http://localhost:7000',
                                  aws_access_key_id='minioadmin',
                                  aws_secret_access_key='minioadmin')

        cls.botwo_client = create_botwo_client(cls.minio1, cls.minio2)

    def test_upload(self):
        self.minio1.create_bucket(Bucket="test-upload")
        content = "TEST_UPLOAD"
        self.botwo_client.put_object(Bucket="bucket-a", Key="a/b/1.txt", Body=content)  # route to minio1

        data = self.botwo_client.get_object(Bucket="bucket-a", Key="a/b/1.txt")
        contents = data['Body'].read().decode('utf-8')
        self.assertEqual(contents, content)

        with pytest.raises(Exception):
            # assert that the call is to minio1
            self.minio2.get_object(Bucket="test-upload", Key="main/a/b/1.txt")

    def test_copy(self):
        self.minio1.create_bucket(Bucket="test-copy")
        content = "TEST_COPY"
        self.botwo_client.put_object(Bucket="test-copy", Key="main/a/b/1.txt", Body=content)  # route to minio1
        self.botwo_client.copy_object(Bucket="test-copy", Key="1.txt",
                                      CopySource={"Bucket": "source", "Key": "a/b/1.txt"})

        data = self.botwo_client.get_object(Bucket="test-copy", Key="1.txt")
        contents = data['Body'].read().decode('utf-8')
        self.assertEqual(contents, content)

        with pytest.raises(Exception):
            # assert that the call is to minio1
            self.minio2.get_object(Bucket="test-copy", Key="1.txt")

    def test_default(self):
        self.minio2.create_bucket(Bucket="test-default")
        content = "TEST_DEFAULT"
        self.botwo_client.put_object(Bucket="test-default", Key="2.txt", Body=content)  # route to default minio2

        data = self.botwo_client.get_object(Bucket="test-default", Key="2.txt")
        contents = data['Body'].read().decode('utf-8')
        self.assertEqual(contents, content)

        with pytest.raises(Exception):
            # assert that the call is to minio2
            self.minio1.get_object(Bucket="test_upload", Key="2.txt")

    def test_delete_objects(self):
        self.minio2.create_bucket(Bucket="test-delete-objects")
        content = "TEST_DELETE_OBJECTS"
        self.botwo_client.put_object(Bucket="test-delete-objects", Key="test/1.txt", Body=content)  # route to minio2
        self.botwo_client.put_object(Bucket="test-delete-objects", Key="test/2.txt", Body=content)

        res = self.botwo_client.delete_objects(Bucket="delete-objects1", Delete={
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
        self.botwo_client.put_object(Bucket="test-paginator", Key="dev/test/1.txt", Body=content)  # route to minio2
        self.botwo_client.put_object(Bucket="test-paginator", Key="dev/test/2.txt", Body=content)
        self.botwo_client.put_object(Bucket="test-paginator", Key="1.txt", Body=content)
        self.botwo_client.put_object(Bucket="test-paginator", Key="test/3.txt", Body=content)

        self.assertEqual(self.botwo_client.can_paginate(operation_name='list_objects'), True)

        # Create a reusable Paginator
        paginator = self.botwo_client.get_paginator(operation_name='list_objects')

        # Create a PageIterator from the Paginator
        page_iterator = paginator.paginate(Bucket='pagi', Prefix="test")

        # Compare the iterators
        for page in page_iterator:
            self.assertEqual(len(page['Contents']), 2)

    def test_list_objects(self):
        self.minio2.create_bucket(Bucket="test-list-objects")
        content = "TEST_LIST_OBJECTS"

        self.botwo_client.put_object(Bucket="test-list-objects", Key="dev/test/1.txt", Body=content)  # route to minio2
        self.botwo_client.put_object(Bucket="test-list-objects", Key="dev/test/2.txt", Body=content)
        self.botwo_client.put_object(Bucket="test-list-objects", Key="1.txt", Body=content)
        self.botwo_client.put_object(Bucket="test-list-objects", Key="test/3.txt", Body=content)

        objects = self.botwo_client.list_objects(Bucket="list", Prefix="test")

        self.assertEqual(len(objects['Contents']), 2)

    # def test_meta(self):
    #     self.minio2.create_bucket(Bucket="test-meta")
    #     # event_system = self.botwo_client.meta.events
    #     event_system = self.botwo_client.meta
    #     print("nkakfmla")
    #     # def add_my_bucket(params, **kwargs):
    #     #     params['Bucket'] = 'test-meta'
    #     #
    #     # event_system.register('provide-client-params.s3.*', add_my_bucket)
    #     # self.botwo_client.get_bucket_acl(Bucket="hello")

    @classmethod
    def tearDownClass(cls):
        cls.docker1.kill()
        cls.docker2.kill()
