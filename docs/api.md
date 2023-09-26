# Chargeback API
The Chargeback REST API is used to query the back-end chargeback DB for user's usage metrics. It should only be used via the CLI to ensure user permissions are enforced.

## OpenAPI Docs
### /

#### GET
##### Summary:

Root

##### Responses

| Code | Description         |
| ---- | ------------------- |
| 200  | Successful Response |

### /health

#### GET
##### Summary:

Root

##### Responses

| Code | Description         |
| ---- | ------------------- |
| 200  | Successful Response |

### /report/users/{user_name}

#### GET
##### Summary:

Read Report User Range

##### Parameters

| Name       | Located in | Description | Required | Schema |
| ---------- | ---------- | ----------- | -------- | ------ |
| user_name  | path       |             | Yes      | string |
| start_date | query      |             | No       | string |
| end_date   | query      |             | No       | string |
| range      | query      |             | No       | string |

##### Responses

| Code | Description         |
| ---- | ------------------- |
| 200  | Successful Response |
| 422  | Validation Error    |

### /report/groups/{user_name}

#### GET
##### Summary:

Read Report Group Range

##### Parameters

| Name       | Located in | Description | Required | Schema |
| ---------- | ---------- | ----------- | -------- | ------ |
| user_name  | path       |             | Yes      | string |
| start_date | query      |             | No       | string |
| end_date   | query      |             | No       | string |
| range      | query      |             | No       | string |

##### Responses

| Code | Description         |
| ---- | ------------------- |
| 200  | Successful Response |
| 422  | Validation Error    |
