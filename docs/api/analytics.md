# Analytics Endpoints

## Overview
The analytics endpoints provide insights into application usage, including chat statistics, document management, link sharing, and overall system usage patterns.

## Chat Analytics
```http
GET /analytics/chat
```
Retrieve chat-related analytics data.

### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| startDate | string | No | 30 days ago | Start date (ISO format) |
| endDate | string | No | now | End date (ISO format) |
| conversationId | string | No | - | Filter by specific conversation |

### Response
**Success (200 OK):**
| Field | Type | Description |
|-------|------|-------------|
| totalMessages | number | Total number of messages |
| averageResponseTime | number | Average response time in seconds |
| userEngagement | object | User engagement metrics |
| conversationStats | Array<object> | Statistics per conversation |

**User Engagement Object:**
| Field | Type | Description |
|-------|------|-------------|
| activeUsers | number | Number of active users |
| messagesPerUser | number | Average messages per user |
| retentionRate | number | User retention rate |

**Conversation Stats Object:**
| Field | Type | Description |
|-------|------|-------------|
| id | string | Conversation identifier |
| messageCount | number | Number of messages |
| duration | number | Duration in minutes |
| userSatisfaction | number | User satisfaction score |

## Document Analytics
```http
GET /analytics/documents
```
Retrieve document-related analytics data.

### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| startDate | string | No | 30 days ago | Start date (ISO format) |
| endDate | string | No | now | End date (ISO format) |
| type | string | No | - | Filter by document type |

### Response
**Success (200 OK):**
| Field | Type | Description |
|-------|------|-------------|
| totalDocuments | number | Total number of documents |
| storageUsage | object | Storage usage metrics |
| documentTypes | Array<object> | Statistics by document type |

**Storage Usage Object:**
| Field | Type | Description |
|-------|------|-------------|
| totalSize | number | Total storage used in bytes |
| averageSize | number | Average document size |
| usageTrend | Array<number> | Daily storage usage trend |

**Document Type Object:**
| Field | Type | Description |
|-------|------|-------------|
| type | string | Document MIME type |
| count | number | Number of documents |
| totalSize | number | Total size in bytes |

## Link Analytics
```http
GET /analytics/links
```
Retrieve link-related analytics data.

### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| startDate | string | No | 30 days ago | Start date (ISO format) |
| endDate | string | No | now | End date (ISO format) |
| domain | string | No | - | Filter by domain |

### Response
**Success (200 OK):**
| Field | Type | Description |
|-------|------|-------------|
| totalLinks | number | Total number of processed links |
| processingStats | object | Link processing statistics |
| domainStats | Array<object> | Statistics by domain |

**Processing Stats Object:**
| Field | Type | Description |
|-------|------|-------------|
| averageTime | number | Average processing time |
| successRate | number | Successful processing rate |
| errorRate | number | Error rate |

**Domain Stats Object:**
| Field | Type | Description |
|-------|------|-------------|
| domain | string | Domain name |
| count | number | Number of links |
| averageSize | number | Average content size |

## Usage Analytics
```http
GET /analytics/usage
```
Retrieve overall system usage analytics.

### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| startDate | string | No | 30 days ago | Start date (ISO format) |
| endDate | string | No | now | End date (ISO format) |
| granularity | string | No | daily | Time granularity (hourly/daily/weekly) |

### Response
**Success (200 OK):**
| Field | Type | Description |
|-------|------|-------------|
| activeUsers | number | Number of active users |
| apiCalls | object | API call statistics |
| resourceUsage | object | System resource usage |
| featureUsage | Array<object> | Usage by feature |

**API Calls Object:**
| Field | Type | Description |
|-------|------|-------------|
| total | number | Total API calls |
| byEndpoint | object | Calls by endpoint |
| errorRate | number | Error rate percentage |

**Resource Usage Object:**
| Field | Type | Description |
|-------|------|-------------|
| cpu | number | CPU usage percentage |
| memory | number | Memory usage in MB |
| storage | number | Storage usage in GB |

**Feature Usage Object:**
| Field | Type | Description |
|-------|------|-------------|
| feature | string | Feature name |
| usageCount | number | Number of uses |
| averageDuration | number | Average duration in seconds |

### Example Usage
```typescript
const getChatAnalytics = async (startDate?: string, endDate?: string) => {
  const params = new URLSearchParams();
  if (startDate) params.append('startDate', startDate);
  if (endDate) params.append('endDate', endDate);
  
  const response = await fetch(`http://localhost:5000/analytics/chat?${params}`);
  return await response.json();
};

const getUsageAnalytics = async (granularity: 'hourly' | 'daily' | 'weekly' = 'daily') => {
  const response = await fetch(`http://localhost:5000/analytics/usage?granularity=${granularity}`);
  return await response.json();
};
```

### Notes
- Analytics data is aggregated and cached for performance
- Data retention period is configurable
- All timestamps are in ISO format
- Metrics are calculated based on server-side logs
- Analytics endpoints support pagination for large datasets
- Data can be exported in various formats (JSON, CSV)
- Rate limiting may apply to prevent abuse
- Privacy considerations are applied to user data 