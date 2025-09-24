# API Documentation Organization Guide

This document explains how the GoodPlay API documentation is organized in a modular structure to maintain clarity and avoid file bloat.

## 📁 Directory Structure

```
docs/
├── openapi.yaml              # Main OpenAPI specification
├── openapi/                  # Modular OpenAPI specifications
│   ├── core.yaml            # Authentication & user management
│   ├── social.yaml          # Social features & relationships
│   ├── games.yaml           # Game engine & sessions
│   └── leaderboards.yaml    # Impact scores & leaderboards
├── postman/                  # Postman collections and environments
│   ├── core_collection.json        # Core API collection
│   ├── social_collection.json      # Social API collection
│   ├── games_collection.json       # Games API collection
│   ├── leaderboards_collection.json # Leaderboards API collection
│   ├── GoodPlay_Local.postman_environment.json      # Local environment
│   └── GoodPlay_Production.postman_environment.json # Production environment
└── API_ORGANIZATION.md       # This documentation guide
```

## 🔧 Integration with Main Files

### OpenAPI Integration

The main `openapi.yaml` file should reference modular specifications:

```yaml
# In openapi.yaml, add references to module files
paths:
  # Core paths here...

# Import leaderboards paths
$ref: './docs/openapi/leaderboards.yaml#/paths'

components:
  schemas:
    # Core schemas here...

  # Import leaderboards schemas
  $ref: './docs/openapi/leaderboards.yaml#/components/schemas'
```

### Postman Integration

Create a master workspace that imports individual collections:

1. **GoodPlay Master Workspace**
   - Import Core API Collection
   - Import Leaderboards Collection (GOO-12)
   - Import Games Collection (GOO-8)
   - Import Social Collection (GOO-7)

## 📋 Module Standards

Each module should follow these standards:

### OpenAPI Modules
- **File naming**: `{feature}.yaml` (e.g., `leaderboards.yaml`)
- **Structure**: Include paths, components, and message constants
- **Message constants**: Document all response message keys for UI localization
- **Examples**: Provide comprehensive request/response examples
- **Security**: Define security requirements for each endpoint

### Postman Modules
- **File naming**: `{feature}_collection.json`
- **Environment variables**: Use consistent variable naming
- **Test scripts**: Include common test assertions
- **Examples**: Save response examples for each endpoint
- **Documentation**: Add descriptions for each request

## 🏷️ Message Constants Organization

Each module defines its own message constants in the OpenAPI file:

```yaml
# Example from leaderboards.yaml
leaderboards_constants: &leaderboards_constants
  - `IMPACT_SCORE_RETRIEVED_SUCCESS` - Impact score retrieved successfully
  - `LEADERBOARD_RETRIEVED_SUCCESS` - Leaderboard retrieved successfully
  - `INVALID_LEADERBOARD_TYPE` - Invalid leaderboard type
```

These constants are used consistently across:
- API responses
- OpenAPI documentation
- Postman test examples
- Frontend localization files

## 🔄 Maintenance Workflow

### When Adding New Features

1. **Create module files**:
   ```bash
   # Create OpenAPI module
   touch docs/openapi/{feature}.yaml

   # Create Postman collection
   touch docs/postman/{feature}_collection.json
   ```

2. **Follow module template** (see `leaderboards.yaml` as reference)

3. **Update main files** to reference new modules

4. **Test integration** with both OpenAPI validators and Postman

### When Updating Existing Features

1. **Update module file** (not main files)
2. **Maintain backward compatibility** in API responses
3. **Update message constants** if new responses are added
4. **Test with existing Postman collections**

## 🧪 Testing Strategy

### OpenAPI Validation
```bash
# Validate individual modules
swagger-codegen validate -i docs/openapi/leaderboards.yaml

# Validate main specification
swagger-codegen validate -i openapi.yaml
```

### Postman Testing
```bash
# Run collection with Newman
newman run docs/postman/leaderboards_collection.json \
  --environment environments/development.json \
  --reporters cli,json
```

## 📊 Benefits of Modular Organization

### For Development
- **Focused changes**: Developers work on specific module files
- **Reduced conflicts**: Multiple developers can work on different modules
- **Easier review**: Smaller, focused pull requests

### For Documentation
- **Clear organization**: Each feature's API is self-contained
- **Reduced file size**: Main files remain manageable
- **Better maintainability**: Changes are localized to relevant modules

### For Testing
- **Isolated testing**: Test individual feature sets independently
- **Faster execution**: Run only relevant test collections
- **Better debugging**: Issues are easier to trace to specific modules

## 🎯 Module Ownership

Each module should have clear ownership:

| Module | Feature | Owner | Status |
|--------|---------|-------|--------|
| `core.yaml` | Authentication & Core APIs | Backend Team | ✅ Complete |
| `social.yaml` | GOO-7 Social Graph Foundation | Backend Team | ✅ Complete |
| `games.yaml` | GOO-8 Game Engine Framework | Backend Team | ✅ Complete |
| `leaderboards.yaml` | GOO-12 Social Impact & Leaderboards | Backend Team | ✅ Complete |

## 📝 Migration Checklist

When migrating existing API documentation to modular structure:

- [ ] Extract feature-specific paths from main `openapi.yaml`
- [ ] Create dedicated module file
- [ ] Define module-specific message constants
- [ ] Add comprehensive examples
- [ ] Create corresponding Postman collection
- [ ] Update main files to reference modules
- [ ] Test integration
- [ ] Update documentation
- [ ] Train team on new structure

---

This modular approach ensures that as GoodPlay grows, the API documentation remains organized, maintainable, and easy to work with for both development and frontend integration.