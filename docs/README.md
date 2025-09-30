# GoodPlay API Documentation

This directory contains comprehensive API documentation for the GoodPlay backend platform.

## 📁 Documentation Structure

### OpenAPI Specifications

- **[openapi.yaml](./openapi.yaml)** - Main API specification file
- **[openapi/core.yaml](./openapi/core.yaml)** - Core authentication & user management
- **[openapi/admin.yaml](./openapi/admin.yaml)** - Admin dashboard & management (GOO-20)
- **[openapi/social.yaml](./openapi/social.yaml)** - Social features & relationships
- **[openapi/games.yaml](./openapi/games.yaml)** - Game engine, sessions & tournaments
- **[openapi/donations.yaml](./openapi/donations.yaml)** - Virtual wallet & donation system

### Postman Collections

- **[postman/core_collection.json](./postman/core_collection.json)** - Core API endpoints
- **[postman/admin_collection.json](./postman/admin_collection.json)** - Admin management APIs
- **[postman/games_collection.json](./postman/games_collection.json)** - Game engine APIs
- **[postman/social_collection.json](./postman/social_collection.json)** - Social features APIs

### Environment Files

- **[postman/GoodPlay_Local.postman_environment.json](./postman/GoodPlay_Local.postman_environment.json)** - Local development
- **[postman/GoodPlay_Admin.postman_environment.json](./postman/GoodPlay_Admin.postman_environment.json)** - Admin interface
- **[postman/GoodPlay_Production.postman_environment.json](./postman/GoodPlay_Production.postman_environment.json)** - Production

## 🔧 Using the Documentation

### OpenAPI/Swagger UI

1. **Local Swagger UI**: Import `openapi.yaml` into Swagger UI for interactive documentation
2. **Online Validation**: Use [Swagger Editor](https://editor.swagger.io/) to validate specifications
3. **Code Generation**: Generate client SDKs using OpenAPI Generator

```bash
# Generate TypeScript client
npx @openapitools/openapi-generator-cli generate \
  -i docs/openapi.yaml \
  -g typescript-axios \
  -o frontend/src/api
```

### Postman Collections

1. **Import Collections**: Import JSON files into Postman
2. **Set Environment**: Configure environment variables for your target (Local/Production/Admin)
3. **Authentication Flow**:
   - Set `baseUrl`, `test_email`, `test_password` in environment
   - Run login endpoint to get tokens
   - Tokens are automatically set for subsequent requests

#### Admin Collection Setup

1. Import `admin_collection.json` and `GoodPlay_Admin.postman_environment.json`
2. Set admin credentials in environment:
   ```json
   {
     "admin_username": "your_admin_username",
     "admin_password": "your_admin_password"
   }
   ```
3. Run "Admin Login" to get admin tokens
4. Execute admin endpoints with proper authorization

## 📊 API Modules Overview

### Core Module
- User registration & authentication
- Profile management
- Password reset & validation
- JWT token management

### Admin Module (GOO-20)
- **Authentication**: Admin login with enhanced security
- **Dashboard**: Multi-view dashboards (overview, user management, financial, monitoring)
- **User Management**: Bulk operations, suspension, activation, role management
- **System Monitoring**: Real-time metrics, performance analytics, alerts
- **Security**: RBAC, audit logging, suspicious activity detection

### Social Module
- Friend relationships & social interactions
- Achievement system & leaderboards
- Social challenges & competitions

### Games Module
- Game engine & plugin management
- Session tracking with cross-device sync
- Tournament & team management
- Challenge system with matchmaking

### Donations Module
- Virtual wallet & credit system
- Donation processing & receipts
- Payment gateway integration
- Impact tracking & reporting

## 🛡️ Security & Authentication

### Standard Users
- JWT Bearer tokens (1 hour expiry)
- Refresh tokens (30 days)
- Role-based access control

### Admin Users
- Enhanced JWT tokens with admin claims
- Role-based permissions (super_admin, admin, moderator, analyst)
- IP whitelisting support
- Multi-factor authentication
- Session timeout management
- Comprehensive audit logging

## 📝 Response Constants

All APIs use constant message keys for UI localization:

```json
{
  "success": true,
  "message": "USER_LOGIN_SUCCESS",
  "data": { ... }
}
```

Constants are documented in each module's OpenAPI specification under the `*_constants` section.

### Admin Constants Examples
- `ADMIN_LOGIN_SUCCESS`
- `DASHBOARD_OVERVIEW_SUCCESS`
- `USER_SUSPENDED_SUCCESS`
- `BULK_ACTION_COMPLETED`
- `ALERT_ACKNOWLEDGED_SUCCESS`

## 🔍 Testing Workflows

### Standard API Testing
1. Health Check → Register User → Login → Test Protected Endpoints
2. Use environment variables for dynamic values
3. Automated token management in Postman

### Admin API Testing
1. Health Check → Admin Login → Test Admin Endpoints
2. Test different permission levels with different admin roles
3. Verify audit logging and security features

### Collection Tests
Run entire collections for automated testing:
```bash
newman run core_collection.json -e GoodPlay_Local.postman_environment.json
newman run admin_collection.json -e GoodPlay_Admin.postman_environment.json
```

## 📈 Performance Requirements

### Admin Dashboard
- Dashboard load time: <2 seconds
- Real-time data refresh via WebSocket
- Support for 20+ concurrent admin users
- 99.9% uptime monitoring

### API Performance
- Response time: <100ms (95th percentile)
- Error rate: <0.1%
- Concurrent users: 1000+
- Data retention: 24 months

## 🆘 Support & Issues

For API documentation issues or improvements:
1. Check existing [GitHub Issues](https://github.com/goodplay/backend/issues)
2. Create new issue with `documentation` label
3. Include API module and specific endpoint in issue title

## 📚 Additional Resources

- [Flask-JWT-Extended Documentation](https://flask-jwt-extended.readthedocs.io/)
- [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0)
- [Postman Collection Format](https://schema.postman.com/)
- [MongoDB Best Practices](https://docs.mongodb.com/manual/administration/production-notes/)