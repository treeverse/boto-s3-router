# Source bucket pattern Schema

```txt
#/properties/source_bucket_pattern#/definitions/profile/properties/source_bucket_pattern
```

Requests to buckets matching this pattern will use this profile

| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                         |
| :------------------ | :--------- | :------------- | :---------------------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [profiles.schema.json*](../schema/out/profiles.schema.json "open original schema") |

## source_bucket_pattern Type

`string` ([Source bucket pattern](profiles-definitions-profile-properties-source-bucket-pattern.md))

## source_bucket_pattern Examples

```json
"old-bucket"
```

```json
"old-bucket-prefix*"
```
