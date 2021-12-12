# Source key pattern Schema

```txt
#/properties/source_key_pattern#/definitions/profile/properties/source_key_pattern
```

Requests to keys matching this pattern will use this profile.

| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                         |
| :------------------ | :--------- | :------------- | :---------------------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [profiles.schema.json*](../schema/out/profiles.schema.json "open original schema") |

## source_key_pattern Type

`string` ([Source key pattern](profiles-definitions-profile-properties-source-key-pattern.md))

## source_key_pattern Examples

```json
"a/b/example-old-key*"
```

```json
"a/*/example-old-key"
```
