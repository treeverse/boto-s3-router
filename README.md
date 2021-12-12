# Boto S3 Router

Interact with S3-compatible services side-by-side with S3, without making any changes to your code. This package provides a boto3-like client that routes requests between S3 clients according to the bucket and the key in the request.

## Why use Boto S3 Router

Consider the following code, downloading an object from one bucket and uploading it to another after some manipulation:

```python
def calculate(s3_client):
    obj = s3_client.get_object(Bucket="bucket1", Key="a/b/c/obj")
    obj2 = do_something_to_obj(obj)
    s3_client.put_object(Body=obj2, Bucket="bucket2", Key="a/b/c/obj")
```

Suppose you want to migrate only `bucket2` to an S3-compatible storage like lakeFS or MinIO. 
Normally, you would have to refactor your code to accomodate for two S3 clients instead of just one.
Boto S3 Router allows you to do that without making any changes to the `calculate` function!

## Installation

Boto S3 Router requires Python >= 3.6 to run.

### pip install

If the python package is hosted on a repository, you can install directly using:

```sh
pip install git+https://github.com/treeverse/botos3router.git
```

### Setuptools

Install via [Setuptools](http://pypi.python.org/pypi/setuptools).

```sh
python setup.py install --user
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
        "source_bucket_pattern": "bucket*",
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
        "mapped_prefix": "test/"
    },
}

s3 = s3r.client({"lakefs": lakefs, "lakefs-test": lakefs, "default": s3}, profiles)
s3.get_object(Bucket="example-old-bucket", Key="test/object.txt") # routes to example-repo in lakeFS
```

## Configuration

```
s3 = s3r.client(client_mapping, profiles)
```

As can be seen in the examples above, Boto S3 Router is initialized using two configuration parameters:

* `client_mapping`: The mapping between profile names to S3 clients. A `default` client is required.
   
   For example:
   ```json
   {"profile1": s3, "profile2": minio, "default": s3}
   ```
   
* profiles -  A mapping between profile name to profile:
  ```json
  {
      "profile1":
      {
          "source_bucket_pattern": "example-bucket",
          "source_key_pattern": "a/*",
          "mapped_bucket_name": "new-bucket",
          "mapped_prefix": "test/"
      },
      "profile2":
      {
          "source_bucket_pattern": "bucket",
          "mapped_bucket_name": "bucket-a"
      }
  }
  ```
  A profile can have the following properties:
  | Property              | Description                                                                                 | Required |
  |-----------------------|---------------------------------------------------------------------------------------------|----------|
  | source_bucket_pattern | Requests to buckets matching this pattern will use this profile.                            | Yes      |
  | source_key_pattern    | Requests to keys matching this pattern will use this profile.                               | No       |
  | mapped_bucket_name    | The bucket name to use when routing the request to the destination client                   | No       |
  | mapped_prefix         | An optional string to prepend to the key when routing the request to the destination client | No       |
  

## License

MIT


[lakeFS]: <https://github.com/treeverse/lakeFS>
