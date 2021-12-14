import fnmatch
import botocore

COPY_METHODS = {"copy", "copy_object", "copy_upload_part"}
LIST_METHODS = {"list_objects", "list_objects_v2", "list_object_version"}


def _route_bucket_and_key(api_params, config, map):
    for profile in config:
        mapping = config[profile]
        if "Bucket" in api_params:
            if fnmatch.fnmatch(api_params["Bucket"], mapping["source_bucket_pattern"]):
                if "Key" in api_params:
                    if "source_key_pattern" in mapping:
                        if not fnmatch.fnmatch(api_params["Key"], mapping["source_key_pattern"]):
                            continue
                    if "mapped_prefix" in mapping:
                        api_params["Key"] = mapping["mapped_prefix"] + api_params["Key"]
                if "mapped_bucket_name" in mapping:
                    api_params["Bucket"] = mapping["mapped_bucket_name"]

                return map.get(profile), api_params
    return map.get("default"), api_params


def _route_list_params(kwargs, config, map):
    if "Prefix" in kwargs:
        client_to_call, result_args = _route_bucket_and_key(
            api_params={"Bucket": kwargs.get("Bucket"), "Key": kwargs.get("Prefix")}, config=config, map=map)
        kwargs["Prefix"] = result_args["Key"]
    else:
        client_to_call, result_args = _route_bucket_and_key(api_params=kwargs, config=config, map=map)
    kwargs["Bucket"] = result_args["Bucket"]
    return client_to_call, kwargs


class PaginatorWrapper(object):
    """Wrapper for a boto paginator.

    Holds multiple paginators, one for each client, and dispatches calls to the appropriate
    paginator according to botos3router's mapping configuration
    """

    def __init__(self, mapping, config, operation_name):
        """Init PaginatorWrapper.

        Initialize paginator for each client.

         :param dict mapping: The mapping between the profiles to the s3 clients
         :param dict[dict] config: The configuration rules for the clients routing
         :param str operation_name: The operation name of the paginator
        """
        self.mapping = mapping
        self.config = config
        self.paginators = dict()
        for client in self.mapping:
            self.paginators[client] = self.mapping[client].get_paginator(operation_name)

    def paginate(self, **kwargs):
        """iterate over the pages of the paginator API operation results.

        accepts a PaginationConfig named argument that can be used to customize the pagination.
        """
        paginator_to_call, kwargs = _route_list_params(kwargs, self.config, self.paginators)
        return getattr(paginator_to_call, "paginate")(**kwargs)


class BotoS3RouterBuilder(object):
    """This class creates a botos3router client that wraps boto clients.

    * Holds boto clients and routes the requests between them by bucket/prefix configuration.
    * Create its methods on the fly according to boto3 client AWS methods.
    * Holds special treatment for functions that operate on multiple buckets or keys
    """

    def __init__(self):
        """Init BotoS3RouterBuilder."""
        self.default = None
        self.mapping = None
        self.config = None

    def build(self, mapping, config):
        """build BotoS3RouterBuilder client.

        initialize default client.
        create boto client methods.
        """
        if not isinstance(mapping, dict):
            raise TypeError("Invalid client mapping type: " + str(type(mapping)) + " expected dict")

        if "default" not in mapping:
            raise ValueError("default client is required")
        self.mapping = mapping
        self.config = config
        self.default = mapping.get("default")

        for k, v in self.mapping.items():
            if not isinstance(v, botocore.client.BaseClient):
                raise TypeError("mapping: " + k + "Invalid client type: " + str(type(v)) + " expected boto.s3.client")

        for profile in self.config:
            if not self.mapping.get(profile):
                raise ValueError("profile " + profile + " in config does not appear in mapping")
            if "source_bucket_pattern" not in self.config[profile]:
                raise ValueError("profile " + profile + " source_bucket_pattern is required")

        class_attributes = self._create_methods()
        cls = type("s3", (), class_attributes)
        return cls()

    def _create_methods(self):
        op_dict = {}
        operations = [func for func in dir(self.default) if
                      (callable(getattr(self.default, func)) and not func.startswith('_'))]
        for operation_name in operations:
            if operation_name == "get_paginator":
                op_dict[operation_name] = self._create_get_paginate_method(operation_name)
            elif operation_name == "can_paginate":
                op_dict[operation_name] = self._create_can_paginate_method(operation_name)
            elif operation_name == "delete_objects":
                op_dict[operation_name] = self._create_delete_objects_method(operation_name)
            elif operation_name in LIST_METHODS:
                op_dict[operation_name] = self._create_list_method(operation_name)
            elif operation_name in COPY_METHODS:
                op_dict[operation_name] = self._create_copy_method(operation_name)
            else:
                op_dict[operation_name] = self._create_api_method(operation_name)
        op_dict["meta"] = self.default.meta
        return op_dict

    def _create_api_method(self, operation_name):
        def _api_call(_, *args, **kwargs):
            if args:
                raise TypeError("%s() only accepts keyword arguments." % operation_name)
            client_to_call = self.default
            client_to_call, kwargs = _route_bucket_and_key(api_params=kwargs, config=self.config, map=self.mapping)

            return getattr(client_to_call, operation_name)(**kwargs)

        _api_call.__name__ = str(operation_name)
        return _api_call

    def _create_list_method(self, operation_name):
        def _api_call(_, *args, **kwargs):
            if args:
                raise TypeError("%s() only accepts keyword arguments." % operation_name)
            client_to_call, kwargs = _route_list_params(kwargs, self.config, self.mapping)
            return getattr(client_to_call, operation_name)(**kwargs)

        _api_call.__name__ = str(operation_name)
        return _api_call

    def _create_copy_method(self, operation_name):
        def _api_call(_, *args, **kwargs):
            if args:
                raise TypeError("%s() only accepts keyword arguments." % operation_name)
            client_to_call_source = self.default
            client_to_call_dest = self.default
            if "CopySource" in kwargs:  # copy operation
                if isinstance(kwargs["CopySource"], str):
                    raise TypeError("accepts only type dict as CopySource")
                client_to_call_source, kwargs["CopySource"] = _route_bucket_and_key(api_params=kwargs["CopySource"],
                                                                                    config=self.config,
                                                                                    map=self.mapping)

            res = _route_bucket_and_key(api_params=kwargs, config=self.config, map=self.mapping)
            client_to_call_dest, api_params = res

            if client_to_call_source != client_to_call_dest:
                raise ValueError("client source and client destination are different")

            return getattr(client_to_call_source, operation_name)(**api_params)

        _api_call.__name__ = str(operation_name)
        return _api_call

    def _create_get_paginate_method(self, operation_name):
        def _paginator_api_call(*args, **kwargs):
            return PaginatorWrapper(self.mapping, self.config, kwargs['operation_name'])

        _paginator_api_call.__name__ = str(operation_name)
        return _paginator_api_call

    def _create_can_paginate_method(self, operation_name):
        def _can_paginate_api_call(*args, **kwargs):
            return getattr(self.default, operation_name)(**kwargs)

        _can_paginate_api_call.__name__ = str(operation_name)
        return _can_paginate_api_call

    def _create_delete_objects_method(self, operation_name):
        def _delete_objects_api_call(_, *args, **kwargs):
            if args:
                raise TypeError("%s() only accepts keyword arguments." % operation_name)
            if "Delete" in kwargs:  # delete objects operation
                for i, obj in enumerate(kwargs["Delete"]["Objects"]):
                    client_to_call, result_agrs = _route_bucket_and_key(
                        api_params={"Bucket": kwargs.get("Bucket"), "Key": obj["Key"]},
                        config=self.config, map=self.mapping)
                    bucket = result_agrs["Bucket"]
                    kwargs["Delete"]["Objects"][i]["Key"] = result_agrs["Key"]
                    if i == 0:
                        prev_client = client_to_call
                    else:
                        if prev_client != client_to_call:
                            raise ValueError("can't delete objects that mapped to different clients")
                        prev_client = client_to_call

                kwargs["Bucket"] = bucket
                return getattr(client_to_call, operation_name)(**kwargs)

        _delete_objects_api_call.__name__ = str(operation_name)
        return _delete_objects_api_call
