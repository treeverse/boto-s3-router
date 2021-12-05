import fnmatch
import botocore

COPY_METHODS = {"copy", "copy_object", "copy_upload_part"}
LIST_METHODS = {"list_objects", "list_objects_v2", "list_object_version"}


class PaginatorWrapper(object):
    """ This class wraps boto paginator """

    def __init__(self, mapping, config, kwargs):
        self.mapping = mapping
        self.config = config
        self.paginators = dict()
        for client in self.mapping:
            self.paginators[client] = self.mapping[client].get_paginator(kwargs["operation_name"])
        self.default = self.paginators.get("default")

    def paginate(self, **kwargs):
        for profile in self.config:
            mapping = self.config[profile]

            if fnmatch.fnmatch(kwargs["Bucket"], mapping.get("source_bucket_pattern")):
                if kwargs["Prefix"]:
                    if mapping.get("source_key_pattern"):
                        if not fnmatch.fnmatch(kwargs["Prefix"], mapping.get("source_key_pattern")):
                            continue
                    if mapping.get("mapped_prefix"):
                        kwargs["Prefix"] = mapping.get("mapped_prefix") + kwargs["Prefix"]
                if mapping.get("mapped_bucket_name"):
                    kwargs["Bucket"] = mapping.get("mapped_bucket_name")

                return getattr(self.paginators.get(profile), "paginate")(**kwargs)
        return getattr(self.default, "paginate")(**kwargs)


class BotwoBuilder(object):
    """ This class creates botwo client that wraps boto client:

        * Holds boto clients and routes the requests between them by bucket/prefix configuration.
        * Create its methods on the fly according to boto3 client AWS methods.
        * Holds special treatment for functions that operate on multiple buckets or keys

    """

    def __init__(self):
        self.default = None
        self.mapping = None
        self.config = None

    def create_client_class(self, mapping, config):
        if not isinstance(mapping, dict):
            raise TypeError("Invalid client mapping type: " + str(type(mapping)) + " expected dict")

        if not mapping.get("default"):
            raise ValueError("default client is required")
        self.mapping = mapping
        self.config = config
        self.default = mapping.get("default")

        for k, v in self.mapping.items():
            if not isinstance(v, botocore.client.BaseClient):
                raise TypeError("mapping: " + k + "Invalid client type: " + str(type(v)) + " expected boto.s3.client")

        for profile in self.config:
            if not self.mapping.get(profile):
                raise ValueError("profile: " + profile + " mapping is required")

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
            if kwargs.get("Bucket"):  # bucket operation
                res = self._route_params(kwargs)
                client_to_call = res[0]
                kwargs = res[1]

            return getattr(client_to_call, operation_name)(**kwargs)

        _api_call.__name__ = str(operation_name)
        return _api_call

    def _create_list_method(self, operation_name):
        def _api_call(_, *args, **kwargs):
            if args:
                raise TypeError("%s() only accepts keyword arguments." % operation_name)
            client_to_call = self.default
            if kwargs.get("Bucket") and not kwargs.get("Prefix"):
                res = self._route_params(kwargs)
                client_to_call = res[0]
            elif kwargs.get("Bucket") and kwargs.get("Prefix"):
                res = self._route_params({"Bucket": kwargs.get("Bucket"), "Key": kwargs.get("Prefix")})
                client_to_call = res[0]
                kwargs["Prefix"] = res[1]["Key"]
            kwargs["Bucket"] = res[1]["Bucket"]

            return getattr(client_to_call, operation_name)(**kwargs)

        _api_call.__name__ = str(operation_name)
        return _api_call

    def _create_copy_method(self, operation_name):
        def _api_call(_, *args, **kwargs):
            if args:
                raise TypeError("%s() only accepts keyword arguments." % operation_name)
            client_to_call_source = self.default
            client_to_call_dest = self.default
            if kwargs.get("CopySource"):  # copy operation
                if isinstance(kwargs["CopySource"], str):
                    raise TypeError("accepts only type dict as CopySource")
                res = self._route_params(kwargs["CopySource"])
                client_to_call_source = res[0]
                kwargs["CopySource"] = res[1]

            if kwargs.get("Bucket"):
                res = self._route_params(kwargs)
                client_to_call_dest = res[0]
                api_params = res[1]

            if client_to_call_source != client_to_call_dest:
                raise ValueError("client source and client destination are different")

            return getattr(client_to_call_source, operation_name)(**api_params)

        _api_call.__name__ = str(operation_name)
        return _api_call

    def _create_get_paginate_method(self, operation_name):
        def _paginator_api_call(*args, **kwargs):
            return PaginatorWrapper(self.mapping, self.config, kwargs)

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
            if kwargs.get("Delete"):  # delete objects operation
                for i, obj in enumerate(kwargs["Delete"]["Objects"]):
                    params = {"Bucket": kwargs.get("Bucket"), "Key": obj["Key"]}
                    res = self._route_params(params)
                    client_to_call = res[0]
                    bucket = res[1]["Bucket"]
                    kwargs["Delete"]["Objects"][i]["Key"] = res[1]["Key"]
                    # TODO (eden) fail if client to call not equal to previous
            kwargs["Bucket"] = bucket
            return getattr(client_to_call, operation_name)(**kwargs)

        _delete_objects_api_call.__name__ = str(operation_name)
        return _delete_objects_api_call

    def _route_params(self, api_params):
        for profile in self.config:
            mapping = self.config[profile]

            if fnmatch.fnmatch(api_params["Bucket"], mapping.get("source_bucket_pattern")):
                if api_params["Key"]:
                    if mapping.get("source_key_pattern"):
                        if not fnmatch.fnmatch(api_params["Key"], mapping.get("source_key_pattern")):
                            continue
                    if mapping.get("mapped_prefix"):
                        api_params["Key"] = mapping.get("mapped_prefix") + api_params["Key"]
                if mapping.get("mapped_bucket_name"):
                    api_params["Bucket"] = mapping.get("mapped_bucket_name")

                return self.mapping.get(profile), api_params
        return self.default, api_params
