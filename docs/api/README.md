# API Documentation

## Overview
The intelligent-biostats API provides endpoints for statistical analysis, data management, and AI-powered insights.

## Authentication
All API endpoints require authentication. Use the following header:
```
Authorization: Bearer <your_token>
```

## Endpoints

### Data Management
- `POST /api/data/upload` - Upload new dataset
- `GET /api/data/{dataset_id}` - Retrieve dataset
- `DELETE /api/data/{dataset_id}` - Delete dataset

### Statistical Analysis
- `POST /api/analysis/descriptive` - Get descriptive statistics
- `POST /api/analysis/inferential` - Perform inferential analysis
- `POST /api/analysis/correlation` - Calculate correlations

### AI Insights
- `POST /api/ai/recommend` - Get AI recommendations
- `POST /api/ai/learn` - Train AI model
- `GET /api/ai/models` - List available models

## Error Codes
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

## Rate Limiting
API calls are limited to 100 requests per minute per user. 