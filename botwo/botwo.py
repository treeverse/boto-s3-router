import fnmatch

SPECIAL_METHODS = {"get_paginator", "delete_objects"}
COPY_METHODS = {"copy", "copy_object", "copy_upload_part"}


def client(client_mapping, config):
    botwo = Botwo()
    return botwo.create_client_class(client_mapping, config)


class Paginatwo(object):

    def __init__(self, mapping, kwargs, client1, client2, client1_name, client2_name):
        self.mapping = mapping
        self.client1_name = client1_name
        self.client2_name = client2_name
        self.paginator1 = client1.get_paginator(kwargs["operation_name"])
        self.paginator2 = client2.get_paginator(kwargs["operation_name"])

    def paginate(self, **kwargs):
        paginator_to_call = self.paginator1
        for map in self.mapping:
            if fnmatch.fnmatch(kwargs["Bucket"], map["bucket_name"]):
                if map.get("client"):
                    if map.get("client") == self.client2_name:
                        paginator_to_call = self.paginator2
                    elif map.get("client") == self.client1_name:
                        paginator_to_call = self.paginator1
                    else:
                        raise ValueError("Invalid client name " + map.get("client"))
                else:
                    raise ValueError("client isn't provided")

                if map.get("mapped_bucket_name"):
                    kwargs["Bucket"] = map.get("mapped_bucket_name")
                if kwargs.get("Prefix"):
                    if map.get("key_prefix"):
                        kwargs["Prefix"] = map.get("keu_prefix") + kwargs["Prefix"]
                break
        return getattr(paginator_to_call, "paginate")(**kwargs)


class Botwo(object):
    def __init__(self):
        self.client1 = None
        self.client2 = None
        self.default_client = None
        self.client1_name = None
        self.client2_name = None
        self.mapping = None
        self.meta = None

    def create_client_class(self, client_mapping, config):
        if type(client_mapping) is not dict:
            raise TypeError("Invalid client mapping type: " + str(type(client_mapping)) + " expected dict")
        if len(client_mapping) != 2:
            raise TypeError("two clients is expected")

        names = list(client_mapping)
        self.client1_name = names[0]
        self.client1 = client_mapping.get(names[0])
        self.client2_name = names[1]
        self.client2 = client_mapping.get(names[1])

        self.mapping = self._parse_config(config)
        class_attributes = self._create_methods()

        bases = [Botwo]
        cls = type("s3", tuple(bases), class_attributes)
        return cls

    def _parse_config(self, config):
        if len(config) == 0:
            raise ValueError("default client is not provided")
        if config[-1].get("bucket_name") == "*":
            if config[-1].get("client") == self.client1_name:
                self.default_client = self.client1
            elif config[-1].get("client") == self.client2_name:
                self.default_client = self.client2
        else:
            raise ValueError("default client is not provided")
        self.meta = self.default_client.meta
        return config

    def _create_methods(self):
        op_dict = {}
        operations = [func for func in dir(self.default_client) if
                      (callable(getattr(self.default_client, func)) and not func.startswith('_'))]
        for operation_name in operations:
            if operation_name in SPECIAL_METHODS:
                op_dict[operation_name] = self._create_special_method(operation_name)
            elif operation_name in COPY_METHODS:
                op_dict[operation_name] = self._create_copy_method(operation_name)
            else:
                op_dict[operation_name] = self._create_api_method(operation_name)
        return op_dict

    def _create_api_method(self, operation_name):
        def _api_call(*args, **kwargs):
            if args:
                raise TypeError("%s() only accepts keyword arguments." % operation_name)
            client_to_call = self.default_client
            if kwargs.get("Bucket"):  # bucket operation
                full_path = kwargs["Bucket"] + "/" + kwargs["Key"]
                res = self._route_params(full_path, kwargs, is_copy=False)
                client_to_call = res[0]
                api_params = res[1]

            return getattr(client_to_call, operation_name)(**api_params)

        _api_call.__name__ = str(operation_name)
        return _api_call

    def _create_copy_method(self, operation_name):
        def _api_call(*args, **kwargs):
            if args:
                raise TypeError("%s() only accepts keyword arguments." % operation_name)
            client_to_call_source = self.default_client
            client_to_call_dest = self.default_client
            if kwargs.get("CopySource"):  # copy operation
                res = self._route_params(kwargs["CopySource"], kwargs, is_copy=True)
                client_to_call_source = res[0]
                api_params = res[1]

            if api_params.get("Bucket"):
                full_dest_path = api_params["Bucket"] + "/" + api_params["Key"]
                res = self._route_params(full_dest_path, api_params, is_copy=False)
                client_to_call_dest = res[0]
                api_params = res[1]

            if client_to_call_source != client_to_call_dest:
                raise ValueError("client source and client destination are different")

            return getattr(client_to_call_source, operation_name)(**api_params)

        _api_call.__name__ = str(operation_name)
        return _api_call

    def _create_special_method(self, operation_name):
        def _paginator_api_call(*args, **kwargs):
            if args:
                raise TypeError("%s() only accepts keyword arguments." % operation_name)
            return Paginatwo(self.mapping, kwargs, self.client1, self.client2, self.client1_name, self.client2_name)

        def _delete_objects_api_call(*args, **kwargs):
            if args:
                raise TypeError("%s() only accepts keyword arguments." % operation_name)
            # TODO
            return None

        if operation_name == "get_paginator":
            _paginator_api_call.__name__ = str(operation_name)
            return _paginator_api_call
        if operation_name == "delete_objects":
            _delete_objects_api_call.__name__ = str(operation_name)
            return _delete_objects_api_call

    def _route_params(self, path, api_params, is_copy):
        client_to_call = self.default_client
        for map in self.mapping:
            if fnmatch.fnmatch(path, map.get("bucket_name")):
                if map.get("client"):
                    if map.get("client") == self.client2_name:
                        client_to_call = self.client2
                    elif map.get("client") == self.client1_name:
                        client_to_call = self.client1
                    else:
                        raise ValueError("Invalid client name " + map.get("client"))
                else:
                    raise ValueError("client isn't provided")

                if not is_copy:
                    if map.get("mapped_bucket_name"):
                        api_params["Bucket"] = map.get("mapped_bucket_name")
                    if map.get("key_prefix"):
                        api_params["Key"] = map.get("key_prefix") + api_params["Key"]
                else:
                    source_path = api_params["CopySource"].split("/")
                    source_bucket = source_path[0]
                    source_key = "/".join(source_path[1::])
                    if map.get("mapped_bucket_name"):
                        source_bucket = map.get("mapped_bucket_name")
                    if map.get("key_prefix"):
                        source_key = map.get("key_prefix") + api_params["Key"]
                    api_params["CopySource"] = source_bucket + "/" + source_key
                break
        return client_to_call, api_params
