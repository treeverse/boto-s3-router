# Boto S3 Router

Interact with S3-compatible services side-by-side with S3, without making any changes to your code. This package provides a Boto3-like client that routes requests between S3 clients according to the bucket and the key in the request.

## Why use Boto S3 Router

Consider the following code, downloading an object from one bucket and uploading it to another after some manipulation:

```python
def calculate(s3_client):
    obj = s3_client.get_object(Bucket="bucket1", Key="a/b/c/obj")
    obj2 = do_something_to_obj(obj)
    s3_client.put_object(Body=obj2, Bucket="bucket2", Key="a/b/c/obj")
```

Suppose you want to migrate only `bucket2` to an S3-compatible service like lakeFS or MinIO.
Normally, you would have to refactor your code to allow using two S3 clients instead of just one.
Boto S3 Router allows you to do that without making any changes to the `calculate` function!

## Installation

### Prerequisites

Boto S3 Router requires Python >= 3.6 to run.


### Using pip 

```sh
pip install boto-s3-router
```

### Setuptools

Install via [Setuptools](http://pypi.python.org/pypi/setuptools).

```sh
python setup.py install --user
```

## Basic Usage

```python
import boto3
import boto_s3_router as s3r

# Initialize two boto S3 clients:
s3_east = boto3.client('s3', region_name='us-east-1', signature_version='v4',)
s3_west = boto3.client('s3', region_name='us-west-1')

# Define rules for routing between the clients:
profiles = {
    "s3_west": {
        "source_bucket_pattern": "example-bucket",
        "mapped_bucket_name": "new-bucket",
        "mapped_prefix": "test/"
    },
    "s3_east": {
        "source_bucket_pattern": "example-bucket-prefix*",
        "source_key_pattern": "a/*",
        "mapped_prefix": "test/"
    }
}

# Define the mapping between the profiles to the Boto clients:
client_mapping = {"s3_west": s3_west, "s3_east": s3_east, "default":s3_east }

# Initialize the client:
client = s3r.client(client_mapping, profiles)

# Use Boto S3 Router as you would use any Boto client:
client.put_object(Bucket="bucket", Prefix="a/b/obj") # routs to s3_west, the object will be "new-bucket/test/a/b/obj
```

## Usage with [lakeFS]
When you use Boto to access S3 and want to migrate only a subset of your data to lakeFS, Boto S3 Router allows you to use lakeFS and S3 side-by-side with minimum code changes.

Consider the following code, accessing objects in two S3 buckets:

```python
import boto3

s3 = boto3.client('s3')
s3.get_object(Bucket="bucket-a", Key="test/object.txt")
s3.get_object(Bucket="bucket-b", Key="test/object.txt")
```

Now suppose only `bucket-a` was migrated to lakeFS, and that the new repository in lakeFS is called `example-repo`. You can route only requests to this specific bucket to lakeFS, with all other requests still being routed to S3:

```python
import boto3
import boto_s3_router as s3r

s3 = boto3.client('s3')
lakefs = boto3.client('s3', endpoint_url='https://lakefs.example.com')

profiles = {
   "lakefs":{
        "source_bucket_pattern": "bucket-a",
        "mapped_bucket_name": "example-repo",
        "mapped_prefix": "dev/"
    }
}

s3 = s3r.client({"lakefs": lakefs, "default": s3}, profiles)

# All code accessing S3 stays the same as before:
s3.get_object(Bucket="bucket-a", Key="test/object.txt") # routes to example-repo (dev branch) in lakeFS
s3.get_object(Bucket="bucket-b", Key="test/object.txt") # routes to AWS S3
```

## Configuration

```
s3 = s3r.client(client_mapping, profiles)
```

As can be seen in the examples above, Boto S3 Router is initialized using two configuration parameters:

* `client_mapping`: The mapping between profile names to S3 clients. A `default` client is required.
   
   For example, if `s3` and `minio` are Boto S3 clients, the `client_mapping` can be:
   ```json
   {
     "profile1": s3, 
     "profile2": minio,
     "default": s3
   }
   ```
   
* `profiles` -  A mapping between profile name to profile:
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

Apache-2.0 License


[lakeFS]: <https://github.com/treeverse/lakeFS>
