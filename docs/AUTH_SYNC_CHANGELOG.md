# Changelog - Auth & Sync Fix

## [Unreleased] - 2025-01-08

### 🔒 Security & Authentication

#### Added
- **Server-only user creation**: Users can ONLY be created through server (no local fallback)
- **Strict server mode**: New config option `strict_server_mode` fully disables local database
- **User synchronization**: New method `sync_users()` to fetch user list from server
- **User existence check**: New method `check_user_exists()` to validate username/email before registration
- **Permission alias**: Added `get_permissions()` as alias for `get_my_permissions()`

#### Changed
- **`hybrid_auth.py::create_user()`**: Removed local user creation fallback
- **`hybrid_auth.py::authenticate()`**: Server authentication now has priority over local
- **`hybrid_auth.py::__init__()`**: Local auth manager is disabled when `strict_server_mode=True`
- **`client_api.py`**: Added 3 new methods for server communication

#### Fixed
- ❌ **Issue #1**: Users created locally were not synchronized with server
- ❌ **Issue #2**: Login used outdated local database instead of server

#### Configuration
```json
{
  "security": {
    "auth": {
      "strict_server_mode": true,    // NEW: Disable local DB
      "fallback_to_local": false     // NEW: Disable fallback
    }
  }
}
```

### 📝 Documentation

#### Added
- `docs/SERVER_SYNC_AUTH_FIX.md` - Server implementation specification (for server developer)
- `docs/CLIENT_SYNC_AUTH_FIX.md` - Client changes documentation
- `docs/AUTH_FIX_SUMMARY.md` - Quick start guide
- `docs/WORK_SUMMARY.md` - Work summary and checklist

### 🧪 Testing

#### Added
- `tests/test_server_sync.py` - Comprehensive test suite for sync functionality
  - Test 1: Server info retrieval
  - Test 2: User existence check
  - Test 3: User list synchronization
  - Test 4: User registration
  - Test 5: Login and permissions
- `test_server_sync.bat` - Batch file to run tests easily

### 🔄 Server Requirements (TODO)

#### Required Endpoints (not yet implemented on server):
- [ ] `GET /api/client/users/sync` - Synchronize user list
- [ ] `POST /api/client/users/check` - Check username/email existence

#### Improvements (TODO on server):
- [ ] Enhanced validation in `POST /api/client/register`
- [ ] Rate limiting on registration (5/hour per IP)
- [ ] Database indexes on username/email
- [ ] Unit tests for new endpoints

### 📋 Migration Guide

#### For Developers
1. Update `config.json` with new settings
2. Pass `docs/SERVER_SYNC_AUTH_FIX.md` to server developer
3. After server implementation, run `test_server_sync.bat`
4. Test login and registration through server

#### Breaking Changes
- ⚠️ **Local user creation is disabled**: All users MUST be created through server
- ⚠️ **Strict mode**: If `strict_server_mode=true` and server is unavailable, login will fail
- ⚠️ **No local fallback for user creation**: Even in hybrid mode, users can only be created on server

### 🐛 Known Issues

#### Non-Critical
- Type checker warnings in `hybrid_auth.py` (self.local_auth can be None in strict mode)
- Fallback methods (`list_users`, `get_user`, etc.) still try to use local DB if available

#### To Be Addressed
- Add graceful degradation for strict mode when server is down
- Add offline mode with limited functionality
- Cache user credentials securely for offline access

---

## Version History

### v1.5.1 (Current)
- Authentication and sync improvements (this changelog)

### v1.5.0
- Client API integration

### v1.4.x
- RBAC system
- 2FA support

---

**Date**: 2025-01-08  
**Status**: ✅ Client ready | ⏳ Server implementation pending
