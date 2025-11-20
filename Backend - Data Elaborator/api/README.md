# Earthquake Monitoring System

## description

API to manage zones, misurators and alert_misurations

## Exposed APIs


### Get Zones


Get all zones

Parameters:
- N/A

Returns:
- List of all zones

| Method | URL |
|--------|-----|
| GET | /zones/ |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|
| skip | query |  | Optional |
| limit | query |  | Optional |

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Create Zone


Create a new zone

Parameters:
- City

Returns:
- Newly Created Zone

| Method | URL |
|--------|-----|
| POST | /zones/ |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|

##### Request Body
| Field | Type | Description | Required |
|-------|------|-------------|----------|
| city | string |  | Required |

##### Response (201)
| Field | Type | Description |
|-------|------|-------------|
| city | string |  |
| id | integer |  |

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Get Zone


Get a specific zone by id

Parameters
- Zone ID

Returns
- Single Zone

| Method | URL |
|--------|-----|
| GET | /zones/{zone_id} |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|
| zone_id | path |  | Required |

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|
| city | string |  |
| id | integer |  |

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Update Zone


Update a zone by id

Parameters:
- Zone ID
- City

Returns:
- Updated Zone

| Method | URL |
|--------|-----|
| PUT | /zones/{zone_id} |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|
| zone_id | path |  | Required |

##### Request Body
| Field | Type | Description | Required |
|-------|------|-------------|----------|
| city | N/A |  | Optional |

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|
| city | string |  |
| id | integer |  |

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Delete Zone


Delete a Zone

Parameters:
- Zone ID

Returns:
- Succesfulness msg

| Method | URL |
|--------|-----|
| DELETE | /zones/{zone_id} |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|
| zone_id | path |  | Required |

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Get Misurators


Get all misurators with optional filters

Parameters:
- N/A

Returns:
- List of Misurators

| Method | URL |
|--------|-----|
| GET | /misurators/ |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|
| skip | query |  | Optional |
| limit | query |  | Optional |
| active | query |  | Optional |
| zone_id | query |  | Optional |

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Create Misurator


Create new misurator

Parameters:
- active
- zone_id

Returns:
- Created Misurator

| Method | URL |
|--------|-----|
| POST | /misurators/ |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|

##### Request Body
| Field | Type | Description | Required |
|-------|------|-------------|----------|
| active | boolean |  | Required |
| zone_id | integer |  | Required |

##### Response (201)
| Field | Type | Description |
|-------|------|-------------|
| active | boolean |  |
| zone_id | integer |  |
| id | integer |  |

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Get Misurator


Get specific misurator by id

Parameters:
- Misurator ID

Returns:
- Specific Misurator

| Method | URL |
|--------|-----|
| GET | /misurators/{misurator_id} |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|
| misurator_id | path |  | Required |

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|
| active | boolean |  |
| zone_id | integer |  |
| id | integer |  |

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Update Misurator


Update Misurator

Parameters:
- active
- zone_id

Returns:
- Updated Misurator

| Method | URL |
|--------|-----|
| PUT | /misurators/{misurator_id} |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|
| misurator_id | path |  | Required |

##### Request Body
| Field | Type | Description | Required |
|-------|------|-------------|----------|
| active | N/A |  | Optional |
| zone_id | N/A |  | Optional |

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|
| active | boolean |  |
| zone_id | integer |  |
| id | integer |  |

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Activate Misurator


Activate misurator

Parameters:
- Misurator ID

Returns:
- Succesfulness msg

| Method | URL |
|--------|-----|
| PUT | /misurators/{misurator_id}/activate |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|
| misurator_id | path |  | Required |

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Deactivate Misurator


Deactivate misurator

Parameters:
- Misurator ID

Returns:
- Succesfullness msg

| Method | URL |
|--------|-----|
| PUT | /misurators/{misurator_id}/deactivate |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|
| misurator_id | path |  | Required |

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Get Misurations


Get all misurations with optional filters

Parameters:
- Skip  (skip x records)
- Limit (maximum records)

Returns:
- List of all zones

| Method | URL |
|--------|-----|
| GET | /misurations/ |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|
| skip | query |  | Optional |
| limit | query |  | Optional |
| misurator_id | query |  | Optional |
| start_date | query |  | Optional |
| end_date | query |  | Optional |

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Create Misuration


Create a new misuration

Parameters:
- value
- misurator_id

Returns:
- Created Misuration

| Method | URL |
|--------|-----|
| POST | /misurations/ |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|

##### Request Body
| Field | Type | Description | Required |
|-------|------|-------------|----------|
| value | integer |  | Required |
| misurator_id | integer |  | Required |

##### Response (201)
| Field | Type | Description |
|-------|------|-------------|
| value | integer |  |
| misurator_id | integer |  |
| id | integer |  |
| created_at | string |  |

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Get Misuration


Get specific misuration by id

Parameters:
- Misuration ID

Returns:
- Specific Misuration

| Method | URL |
|--------|-----|
| GET | /misurations/{misuration_id} |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|
| misuration_id | path |  | Required |

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|
| value | integer |  |
| misurator_id | integer |  |
| id | integer |  |
| created_at | string |  |

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Get Zone Misurators


Get all misurators of a specific zone

Parameters:
- zone_id

Returns:
- List of all Misurators of a specific Zone

| Method | URL |
|--------|-----|
| GET | /zones/{zone_id}/misurators |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|
| zone_id | path |  | Required |

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Get Misurator Misurations


Get all misurations of a specific misurator

Parameters:
- misurator_id
- hours

Returns:
- List of all Misurations of specific Misurator in the last X Hours

| Method | URL |
|--------|-----|
| GET | /misurators/{misurator_id}/misurations |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|
| misurator_id | path |  | Required |
| hours | query | Last X hours | Optional |

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Get Zones Stats


Get statistics for all zones

Parameters:
- N/A

Returns:
- total zones
- total misurators
- total active misurators

| Method | URL |
|--------|-----|
| GET | /stats/zones |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|

---

### Get Misurator Stats


Gets stats of a specific misurator

Parameters:
- Misurator ID

Returns:
- misurator_id
- total_misurations
- avg_value
- min_value
- max_value
- period_days

| Method | URL |
|--------|-----|
| GET | /stats/misurators/{misurator_id} |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|
| misurator_id | path |  | Required |
| days | query | Ultimi N giorni | Optional |

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|

##### Response (422)
| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |

---

### Read Root




| Method | URL |
|--------|-----|
| GET | / |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|

---

### Health Check


Application and Database health check

Parameters:
- N/A

Returns:
- status
- connection
- timestamp

| Method | URL |
|--------|-----|
| GET | /health |

#### Parameters
| Name | In | Description | Required |
|------|----|-------------|----------|

##### Response (200)
| Field | Type | Description |
|-------|------|-------------|

---
