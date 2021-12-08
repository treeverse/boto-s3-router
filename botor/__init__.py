from botor.botor import BotorBuilder


def client(client_mapping, profiles):
    """Create a botor client that routes between boto clients by configuration.

    :param dict client_mapping: The mapping between the profiles to the s3 clients. default client is required.
                               For example, {"profile1": s3, "profile2": minio, "default": s3}

    :param dict[dict] profiles: The rules for the clients routing. For example,
       profiles = {
           "profile1": {
               "source_bucket_pattern": "example-bucket" (required - the bucket name to route from;
                                                          supports wildcard matching (example-bucket*))
               "source_key_pattern": "a/*", (optional - the prefix to route from; route all bucket if not specified
                                                       ;supports wildcard matching (prefix/a/*))
               "mapped_bucket_name": "new-bucket", (optional - the new bucket name to use;
                                                   bucket name unchanged if not specified)
               "mapped_prefix": "test/" (optional - add prefix to new files inside the bucket.
               For example,(put_object(Bucket="example-bucket", "Key"="a/obj.py") --> new-bucket/test/a/obj.py))
           },}

    :returns: botor client that maps 1:1 with boto API
    """
    router = BotorBuilder()
    return router.build(client_mapping, profiles)

# def resource(*args, **kwargs):
# TODO (issue 3)
