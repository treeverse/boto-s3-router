# Boto S3 Router

Interact with S3-compatible services side-by-side with S3, without making any changes to your code. This package provides a boto3-like client that routes requests between S3 clients according to the bucket and the key in the request.

## Installation

Boto S3 Router requires Python >= 3.6 to run.

### pip install

If the python package is hosted on a repository, you can install directly using:

```sh
pip install git+https://github.com/treeverse/botos3router.git
```
(you may need to run `pip` with root permission: `sudo pip install git+https://github.com/treeverse/botos3router.git`)

Then import the package:
```python
import botos3router as s3r
```

### Setuptools

Install via [Setuptools](http://pypi.python.org/pypi/setuptools).

```sh
python setup.py install --user
```
(or `sudo python setup.py install` to install the package for all users)

Then import the package:
```python
import botos3router as s3r
```

## Configuration
* client_mapping(dict) - The mapping between the profiles to the S3 clients. default client is required. For example, ```{"profile1": s3, "profile2": minio, "default": s3}```
* profiles(dict of dicts) -  The rules for the client routing. For example:
```python 
profiles = {
               "profile1": {
                   "source_bucket_pattern": "example-bucket" (required - the bucket name to route from;
                                                              supports wildcard matching (example-bucket*))
                   "source_key_pattern": "a/*", (optional - the prefix to route from; route all bucket if not specified
                                                           ;supports wildcard matching (prefix/a/*))
                   "mapped_bucket_name": "new-bucket", (optional - the new bucket name to use;
                                                       bucket name unchanged if not specified)
                   "mapped_prefix": "test/" (optional - add this to the given key/prefix when routing the request to the
                   mapped bucket. For example,(put_object(Bucket="example-bucket", "Key"="a/obj.py") --> new-bucket/test/a/obj.py))
               },
               "profile2": {
                    "source_bucket_pattern": "bucket"
                    "mapped_bucket_name": "bucket-a"
               }
           }
```

## Basic Usage

```python
import boto3
import botos3router as s3r

# Initialize two boto S3 clients according to boto API
s3_east = boto3.client('s3', region_name='us-east-1', signature_version='v4',)
s3_west = boto3.client('s3', region_name='us-west-1')

# Defining the rules for the routing between the clients
profiles = {
    "s3_west": {
        "source_bucket_pattern": "bucket",
        "mapped_bucket_name": "new-bucket",
        "mapped_prefix": "test/"
    },
    "s3_east": {
        "bucket_name": "bucket*",
        "source_key_pattern": "a/*",
        "mapped_prefix": "test/"
    }
}

# Defining the mapping between the profiles to the boto clients
client_mapping = {"s3_west": s3_west, "s3_east": s3_east, "default":s3_east }

# Initializing the client
# The client supports all boto client API
client = s3r.client(client_mapping, profiles)

# Use botwo client as boto client
client.put_object(Bucket="bucket", Prefix="a/b/obj") # routs to s3_west, the object will be "new-bucket/test/a/b/obj
```
## Usage with [lakeFS]
When a user uses boto3 client to access S3 wants to move only a subset of their data to lakeFS, Boto S3 Router allows using lakeFS and S3 side-by-side with minimum code changes.

For example: a user can route all requests to S3 with ```bucket-a``` to lakeFS with ```example-repo/main/``` in lakeFS (example-repo = repository name).

Before introducing the new client, the user interacts only with S3:
```python
import boto3

s3 = boto3.client('s3')
s3.get_object(Bucket="test-bucket", Key="test/object.txt")
```
With the new client: change in every place in the code where a boto S3 client is initialized.
```python
import boto3
import botos3router as s3r

s3 = boto3.client('s3')
lakefs = boto3.client('s3', endpoint_url='https://lakefs.example.com')

profiles = {
   "lakefs":{
        "source_bucket_pattern": "bucket-a",
        "mapped_prefix": "dev/"
    },
    "lakefs-test":{
        "source_bucket_pattern": "example-old-bucket",
        "mapped_bucket_name": "example-repo",
        "mapped_prefix": "test/*",
        "mapped_prefix": "main/"
    },
}

s3 = s3r.client({"lakefs": lakefs, "lakefs-test": lakefs, "default": s3}, profiles)
s3.get_object(Bucket="example-old-bucket", Key="test/object.txt") # routes to example-repo in lakeFS
```

## License

MIT


[lakeFS]: <https://github.com/treeverse/lakeFS>
