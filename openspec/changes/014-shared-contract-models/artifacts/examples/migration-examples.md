# Migration Examples: Shared Models

## Example 1: Pagination

### Before

`billing/list_invoices.yaml`

```yaml
method: POST
path: /v1/invoices/search
auth: bearer
description: Returns paginated invoices
request:
  body:
    type: object
    properties:
      pagination:
        type: object
        required: false
        properties:
          page:
            type: integer
            minimum: 1
            required: true
          size:
            type: integer
            minimum: 1
            maximum: 500
            required: true
response:
  status: 200
  body:
    type: object
errors: []
```

`users/list_users.yaml`

```yaml
method: POST
path: /v1/users/search
auth: bearer
description: Returns paginated users
request:
  body:
    type: object
    properties:
      pagination:
        type: object
        required: false
        properties:
          page:
            type: integer
            minimum: 1
            required: true
          size:
            type: integer
            minimum: 1
            maximum: 500
            required: true
response:
  status: 200
  body:
    type: object
errors: []
```

### After

`.apidev/models/common/pagination_request.yaml`

```yaml
contract_type: shared_model
name: PaginationRequest
description: Used by paginated list operations
model:
  type: object
  properties:
    page:
      type: integer
      minimum: 1
      required: true
    size:
      type: integer
      minimum: 1
      maximum: 500
      required: true
```

`billing/list_invoices.yaml`

```yaml
contract_type: operation
method: POST
path: /v1/invoices/search
auth: bearer
description: Returns paginated invoices
request:
  body:
    type: object
    properties:
      pagination:
        $ref: common.PaginationRequest
        required: false
response:
  status: 200
  body:
    type: object
errors: []
```

`users/list_users.yaml`

```yaml
contract_type: operation
method: POST
path: /v1/users/search
auth: bearer
description: Returns paginated users
request:
  body:
    type: object
    properties:
      pagination:
        $ref: common.PaginationRequest
        required: false
response:
  status: 200
  body:
    type: object
errors: []
```

## Example 2: Sort Descriptor

### Before

```yaml
request:
  body:
    type: object
    properties:
      sort:
        type: object
        required: false
        properties:
          field:
            type: string
            required: true
          direction:
            type: string
            enum: [asc, desc]
            required: true
```

### After

`.apidev/models/common/sort_descriptor.yaml`

```yaml
contract_type: shared_model
name: SortDescriptor
description: Used by search and list operations
model:
  type: object
  properties:
    field:
      type: string
      required: true
    direction:
      type: string
      enum: [asc, desc]
      required: true
```

Operation contract excerpt:

```yaml
request:
  body:
    type: object
    properties:
      sort:
        $ref: common.SortDescriptor
        required: false
```

## Example 3: Page Info In Response

### Before

```yaml
response:
  status: 200
  body:
    type: object
    properties:
      pageInfo:
        type: object
        properties:
          page:
            type: integer
            required: true
          size:
            type: integer
            required: true
          total:
            type: integer
            required: true
```

### After

`.apidev/models/common/page_info.yaml`

```yaml
contract_type: shared_model
name: PageInfo
description: Paging metadata for list responses
model:
  type: object
  properties:
    page:
      type: integer
      required: true
    size:
      type: integer
      required: true
    total:
      type: integer
      required: true
```

Operation contract excerpt:

```yaml
response:
  status: 200
  body:
    type: object
    properties:
      pageInfo:
        $ref: common.PageInfo
```
