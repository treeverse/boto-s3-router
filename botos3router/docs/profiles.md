# Boto S3 Router profiles Schema

```txt
http://treeverse.io/boto-s3-router/schema/profile.json
```

A mapping between profile names to profiles

| Abstract               | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                        |
| :--------------------- | :--------- | :------------- | :---------------------- | :---------------- | :-------------------- | :------------------ | :-------------------------------------------------------------------------------- |
| Cannot be instantiated | Yes        | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [profiles.schema.json](../schema/out/profiles.schema.json "open original schema") |

## Boto S3 Router profiles Type

`object` ([Boto S3 Router profiles](profiles.md))

# Boto S3 Router profiles Properties

| Property              | Type     | Required | Nullable       | Defined by                                                                                                                                |
| :-------------------- | :------- | :------- | :------------- | :---------------------------------------------------------------------------------------------------------------------------------------- |
| Additional Properties | `object` | Optional | cannot be null | [Boto S3 Router profiles](profiles-definitions-profile.md "http://treeverse.io/boto-s3-router/schema/profile.json#/additionalProperties") |

## Additional Properties

Additional properties are allowed, as long as they follow this schema:

A mapping between a bucket pattern and a key pattern to a new bucket name. Optionally, includes a prefix to prepend to the key name.

*   is optional

*   Type: `object` ([Details](profiles-definitions-profile.md))

*   cannot be null

*   defined in: [Boto S3 Router profiles](profiles-definitions-profile.md "http://treeverse.io/boto-s3-router/schema/profile.json#/additionalProperties")

### additionalProperties Type

`object` ([Details](profiles-definitions-profile.md))

### additionalProperties Default Value

The default value is:

```json
{}
```

### additionalProperties Examples

```json
{
  "source_bucket_pattern": "example-old-bucket",
  "source_key_pattern": "example-old-key",
  "mapped_bucket_name": "example-repo",
  "mapped_prefix": "main/"
}
```

# Boto S3 Router profiles Definitions

## Definitions group profile

Reference this group by using

```json
{"$ref":"http://treeverse.io/boto-s3-router/schema/profile.json#/definitions/profile"}
```

| Property                                        | Type     | Required | Nullable       | Defined by                                                                                                                                                                             |
| :---------------------------------------------- | :------- | :------- | :------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [source_bucket_pattern](#source_bucket_pattern) | `string` | Required | cannot be null | [Boto S3 Router profiles](profiles-definitions-profile-properties-source-bucket-pattern.md "#/properties/source_bucket_pattern#/definitions/profile/properties/source_bucket_pattern") |
| [source_key_pattern](#source_key_pattern)       | `string` | Optional | cannot be null | [Boto S3 Router profiles](profiles-definitions-profile-properties-source-key-pattern.md "#/properties/source_key_pattern#/definitions/profile/properties/source_key_pattern")          |
| [mapped_bucket_name](#mapped_bucket_name)       | `string` | Optional | cannot be null | [Boto S3 Router profiles](profiles-definitions-profile-properties-mapped-bucket-name.md "#/properties/mapped_bucket_name#/definitions/profile/properties/mapped_bucket_name")          |
| [mapped_prefix](#mapped_prefix)                 | `string` | Optional | cannot be null | [Boto S3 Router profiles](profiles-definitions-profile-properties-mapped-prefix.md "#/properties/mapped_prefix#/definitions/profile/properties/mapped_prefix")                         |

### source_bucket_pattern

Requests to buckets matching this pattern will use this profile

`source_bucket_pattern`

*   is required

*   Type: `string` ([Source bucket pattern](profiles-definitions-profile-properties-source-bucket-pattern.md))

*   cannot be null

*   defined in: [Boto S3 Router profiles](profiles-definitions-profile-properties-source-bucket-pattern.md "#/properties/source_bucket_pattern#/definitions/profile/properties/source_bucket_pattern")

#### source_bucket_pattern Type

`string` ([Source bucket pattern](profiles-definitions-profile-properties-source-bucket-pattern.md))

#### source_bucket_pattern Examples

```json
"old-bucket"
```

```json
"old-bucket-prefix*"
```

### source_key_pattern

Requests to keys matching this pattern will use this profile.

`source_key_pattern`

*   is optional

*   Type: `string` ([Source key pattern](profiles-definitions-profile-properties-source-key-pattern.md))

*   cannot be null

*   defined in: [Boto S3 Router profiles](profiles-definitions-profile-properties-source-key-pattern.md "#/properties/source_key_pattern#/definitions/profile/properties/source_key_pattern")

#### source_key_pattern Type

`string` ([Source key pattern](profiles-definitions-profile-properties-source-key-pattern.md))

#### source_key_pattern Examples

```json
"a/b/example-old-key*"
```

```json
"a/*/example-old-key"
```

### mapped_bucket_name

The bucket name to use when routing the request to the destination client

`mapped_bucket_name`

*   is optional

*   Type: `string` ([Mapped bucket name](profiles-definitions-profile-properties-mapped-bucket-name.md))

*   cannot be null

*   defined in: [Boto S3 Router profiles](profiles-definitions-profile-properties-mapped-bucket-name.md "#/properties/mapped_bucket_name#/definitions/profile/properties/mapped_bucket_name")

#### mapped_bucket_name Type

`string` ([Mapped bucket name](profiles-definitions-profile-properties-mapped-bucket-name.md))

#### mapped_bucket_name Examples

```json
"new-bucket"
```

### mapped_prefix

An optional string to prepend to the key when routing the request to the destination client.

`mapped_prefix`

*   is optional

*   Type: `string` ([Mapped prefix](profiles-definitions-profile-properties-mapped-prefix.md))

*   cannot be null

*   defined in: [Boto S3 Router profiles](profiles-definitions-profile-properties-mapped-prefix.md "#/properties/mapped_prefix#/definitions/profile/properties/mapped_prefix")

#### mapped_prefix Type

`string` ([Mapped prefix](profiles-definitions-profile-properties-mapped-prefix.md))

#### mapped_prefix Examples

```json
"main/"
```

```json
"example-lakefs-branch/"
```
