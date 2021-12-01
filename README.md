# Botwo

The botwo package provides a boto3 like client with two underlying boto3 clients.

## Features

- Holds two boto clients and routes the requests between them by the bucket/prefix configuration.
- Maps 1:1 with boto client API.

## Installation

Botwo requires Python >= 3.6 to run.

### pip install

If the python package is hosted on a repository, you can install directly using:

```sh
pip install git+https://github.com/treeverse/botwo.git
```
(you may need to run `pip` with root permission: `sudo pip install git+https://github.com/treeverse/botwo.git`)

Then import the package:
```python
import botwo
```

### Setuptools

Install via [Setuptools](http://pypi.python.org/pypi/setuptools).

```sh
python setup.py install --user
```
(or `sudo python setup.py install` to install the package for all users)

Then import the package:
```python
import botwo
```

## Configuration
* client_mapping(dict) - The mapping of the two boto client names for the config. For example, ```{"s3": s3, "minio": minio}```
* config(list of dicts) -  The rules for the client routing. For example:
```python 
config = [
    { 
        "bucket_name": "example-bucket", # required - the bucket name or prefix to route from, supports wildcard matching (example-bucket/prefix/*)
        "mapped_bucket_name": "new-bucket", # optional - the new bucket name to route from bucket name
        "client": "minio", # optinal - the client to call with this bucket name, if not provided will go to default
        "key_prefix": "test/" # optional - add prefix to new files inside the bucket (put_object(Bucket="example-bucket", "Key"="obj.py") --> new-bucket/test/obj.py)
    },   
    {
        "bucket_name": "*", 
        "client": "s3", # default client - required
    }
]
```

## Basic Usage

```python
import boto3
import botwo

# Initializing two boto s3 clients according to boto API
s3_east = boto3.client('s3', region_name='us-east-1', signature_version='v4',)
s3_west = boto3.client('s3', region_name='us-west-1')

# Defining the rules for the routing between the clients
config = [
    {
        "bucket_name": "bucket/a/*",
        "mapped_bucket_name": "new-bucket",
        "client": "s3_west", 
        "key_prefix": "test/"
    },
    {
        "bucket_name": "*",
        "client": "s3_east", # default client
    }
]

# Defining the mapping between the boto clients to the client in the config
client_mapping = {"s3_east": s3_east, "s3_west": s3_west}

# Initializing botwo client
# The client supports all boto client API
client = botwo.client(client_mapping, config)

# Use botwo client as boto client
client.put_object(Bucket="bucket/a/b") # routs to s3_east
```
## Using Botwo with [lakeFS]
When a user with an existing python code that uses boto3 client to access s3 wants to move only part of their buckets/prefixes to lakefs, botwo allows using lakefs and s3 together with minimum code changes.

For example: user can route all requests to s3 with ```bucket-a``` to lakeFs with ```example-repo/main/``` in lakeFS (example-repo = repository name).

Before introducing the new client, the user interacts only with S3:
```python
import boto3

s3 = boto3.client('s3')
s3.get_object(Bucket="test-bucket", Key="test/object.txt")
```
With the new botwo client: change in every place in the code where a boto S3 client is initialized.
```python
import boto3
import botwo

s3 = boto3.client('s3')
lakefs = boto3.client('s3', endpoint_url='https://lakefs.example.com')

    mapping = [
        {
            "bucket_name": "bucket-a",
            "client": "lakefs",
            "key_prefix": "dev/"
        },
        {
            "bucket_name": "example-old-bucket",
            "mapped_bucket_name": "example-repo",
            "client": "lakefs",
            "key_prefix": "main/"
        },
        {
            "bucket_name": "*", # default
            "client": "s3",
        }
    ]

s3 = botwo.client({"s3": s3, "lakefs": lakefs}, mapping)
s3.get_object(Bucket="example-old-bucket", Key="test/object.txt") # routes to example-repo in lakeFS
```

## License

MIT


[lakeFS]: <https://github.com/treeverse/lakeFS>


