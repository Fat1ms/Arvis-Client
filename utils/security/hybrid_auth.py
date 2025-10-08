"""
Hybrid Authentication Manager
Гибридный менеджер аутентификации (локальная + удаленная)
"""

from typing import Optional, Tuple

from utils.logger import ModuleLogger
from utils.security.auth import AuthManager as LocalAuthManager
from utils.security.auth import User
from utils.security.rbac import Role
from utils.security.remote_auth_client import RemoteAuthClient


class HybridAuthManager:
    """
    Hybrid authentication manager that supports both local and remote authentication
    Supports fallback to local auth if remote server is unavailable
    """

    def __init__(self, config=None, use_remote: bool = True):
        """
        Initialize hybrid auth manager

        Args:
            config: Configuration dict
            use_remote: Enable remote authentication (True by default)
        """
        self.logger = ModuleLogger("HybridAuthManager")
        self.config = config or {}

        # Initialize local auth manager (always available as fallback)
        self.local_auth = LocalAuthManager(config)

        # Initialize remote auth client
        self.use_remote = use_remote and self.config.get("auth.use_remote_server", False)
        self.remote_client: Optional[RemoteAuthClient] = None

        if self.use_remote:
            server_url = self.config.get("auth.remote_server_url", "")
            if server_url:
                try:
                    self.remote_client = RemoteAuthClient(server_url, timeout=10)
                    # Test connection
                    if self.remote_client.health_check():
                        self.logger.info(f"✓ Connected to remote auth server: {server_url}")
                    else:
                        self.logger.warning(f"⚠ Remote auth server unreachable: {server_url}")
                        self.logger.warning("→ Falling back to local authentication")
                        self.remote_client = None
                except Exception as e:
                    self.logger.error(f"Failed to initialize remote auth client: {e}")
                    self.logger.warning("→ Falling back to local authentication")
                    self.remote_client = None
            else:
                self.logger.info("Remote auth server URL not configured, using local auth")

        # Current user
        self.current_user: Optional[User] = None

    def authenticate(
        self, username: str, password: str, totp_code: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[User]]:
        """
        Authenticate user (tries remote first, falls back to local)

        Args:
            username: Username
            password: Password
            totp_code: Optional 2FA code

        Returns:
            Tuple of (success, error_message, user)
        """
        # Try remote authentication first
        if self.remote_client:
            try:
                success, response = self.remote_client.login(username, password, device_name="Arvis Desktop")

                if success:
                    # Check if 2FA is required
                    if response.get("require_2fa"):
                        return False, "2FA required", None

                    # Convert remote response to local User object
                    user = self._create_user_from_remote(response)
                    self.current_user = user
                    self.logger.info(f"✓ Remote authentication successful: {username}")
                    return True, None, user

                # Remote auth failed, try local
                self.logger.warning(f"Remote authentication failed: {response.get('error', 'Unknown error')}")
                self.logger.info("→ Trying local authentication...")

            except Exception as e:
                self.logger.error(f"Remote authentication error: {e}")
                self.logger.info("→ Falling back to local authentication")

        # Use local authentication
        try:
            session = self.local_auth.authenticate(username, password)
            
            if session:
                # Get user from session
                user = self.local_auth.get_user_by_id(session.user_id)
                if user:
                    self.current_user = user
                    self.logger.info(f"✓ Local authentication successful: {username}")
                    return True, None, user
                else:
                    self.logger.error(f"User not found for session: {session.user_id}")
                    return False, "User not found", None
            else:
                self.logger.warning(f"Local authentication failed: Invalid credentials")
                return False, "Invalid username or password", None
                
        except PermissionError as e:
            # Account locked
            self.logger.warning(f"Local authentication failed: {e}")
            return False, str(e), None
        except Exception as e:
            self.logger.error(f"Local authentication error: {e}")
            return False, str(e), None

    def guest_login(self) -> Tuple[bool, Optional[str], Optional[User]]:
        """
        Login as guest (tries remote first, falls back to local)

        Returns:
            Tuple of (success, error_message, user)
        """
        # Try remote guest login first
        if self.remote_client:
            try:
                success, response = self.remote_client.guest_login()

                if success:
                    user = self._create_user_from_remote(response)
                    self.current_user = user
                    self.logger.info("✓ Remote guest login successful")
                    return True, None, user

                self.logger.warning(f"Remote guest login failed: {response.get('error', 'Unknown error')}")
                self.logger.info("→ Trying local guest login...")

            except Exception as e:
                self.logger.error(f"Remote guest login error: {e}")
                self.logger.info("→ Falling back to local guest login")

        # Use local guest login
        result = self.local_auth.guest_login()

        if result[0]:
            self.current_user = result[2]
            self.logger.info("✓ Local guest login successful")

        return result

    def logout(self) -> bool:
        """
        Logout current user

        Returns:
            Success status
        """
        # Logout from remote server
        if self.remote_client and self.remote_client.is_authenticated():
            try:
                self.remote_client.logout()
                self.logger.info("✓ Remote logout successful")
            except Exception as e:
                self.logger.error(f"Remote logout error: {e}")

        # Logout from local
        if self.current_user:
            self.local_auth.logout(self.current_user.user_id)
            self.current_user = None
            self.logger.info("✓ Local logout successful")

        return True

    def check_permission(self, user: User, permission: str) -> bool:
        """
        Check if user has permission (tries remote first, falls back to local)

        Args:
            user: User object
            permission: Permission string (e.g., "module.weather")

        Returns:
            True if user has permission
        """
        # Try remote permission check first
        if self.remote_client and self.remote_client.is_authenticated():
            try:
                allowed = self.remote_client.check_permission(permission)
                self.logger.debug(f"Remote permission check: {permission} = {allowed}")
                return allowed
            except Exception as e:
                self.logger.error(f"Remote permission check error: {e}")
                self.logger.info("→ Falling back to local permission check")

        # Use local RBAC
        from utils.security.rbac import get_rbac_manager

        rbac = get_rbac_manager()
        allowed = rbac.check_permission(user.role, permission)
        self.logger.debug(f"Local permission check: {permission} = {allowed}")
        return allowed

    def _create_user_from_remote(self, remote_data: dict) -> User:
        """
        Create User object from remote authentication response

        Args:
            remote_data: Response from remote server

        Returns:
            User object
        """
        from datetime import datetime

        role_str = remote_data.get("role", "user")
        role = Role[role_str.upper()] if hasattr(Role, role_str.upper()) else Role.USER

        user = User(
            user_id=remote_data.get("user_id", "remote_user"),
            username=remote_data.get("username", "Unknown"),
            role=role,
            password_hash="",  # Not needed for remote auth
            salt="",  # Not needed for remote auth
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
            is_active=True,
            require_2fa=False,
        )

        return user

    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user"""
        return self.current_user

    def is_remote_auth_active(self) -> bool:
        """Check if remote authentication is active"""
        return self.remote_client is not None and self.remote_client.is_authenticated()

    def create_user(self, username: str, password: str, email: Optional[str] = None, role: str = "user") -> Optional[User]:
        """
        Create new user (tries remote first, falls back to local)

        Args:
            username: Username
            password: Password
            email: Optional email
            role: User role (guest, user, power_user, admin)

        Returns:
            Created User object or None
        """
        # Try remote creation first
        if self.remote_client and self.remote_client.is_authenticated():
            try:
                success, response = self.remote_client.create_user(username, password, email, role)

                if success and response:
                    # Convert response to User object
                    user = self._create_user_from_remote(response)
                    self.logger.info(f"✓ User created on remote server: {username}")
                    return user

                error = response.get("error", "Unknown error") if response else "No response"
                self.logger.warning(f"Remote user creation failed: {error}")
                
                # If error is authentication-related, fall back to local
                if "Authentication required" in str(error) or "Admin access required" in str(error):
                    self.logger.info("→ Admin rights required on remote server, trying local creation...")
                else:
                    self.logger.info("→ Falling back to local user creation")

            except Exception as e:
                self.logger.error(f"Remote user creation error: {e}")
                self.logger.info("→ Falling back to local user creation")

        # Use local user creation
        try:
            # Convert string role to Role enum
            from utils.security.rbac import Role as RoleEnum
            role_enum = RoleEnum[role.upper()] if hasattr(RoleEnum, role.upper()) else RoleEnum.USER
            
            user = self.local_auth.create_user(username, password, role_enum)
            
            if user:
                self.logger.info(f"✓ User created locally: {username}")
                return user
            else:
                self.logger.error("Local user creation failed")
                return None

        except Exception as e:
            self.logger.error(f"Local user creation error: {e}")
            return None

    def list_users(self) -> list:
        """
        Get list of all users (tries remote first, falls back to local)

        Returns:
            List of users
        """
        # Try remote list first
        if self.remote_client and self.remote_client.is_authenticated():
            try:
                success, users = self.remote_client.list_users()

                if success and users:
                    self.logger.info(f"✓ Retrieved {len(users)} users from remote server")
                    return users

                self.logger.warning("Remote user list failed, falling back to local")

            except Exception as e:
                self.logger.error(f"Remote user list error: {e}")
                self.logger.info("→ Falling back to local user list")

        # Use local user list
        try:
            users = self.local_auth.list_users()
            self.logger.info(f"✓ Retrieved {len(users)} users locally")
            return users

        except Exception as e:
            self.logger.error(f"Local user list error: {e}")
            return []

    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get user by ID (tries remote first, falls back to local)

        Args:
            user_id: User ID

        Returns:
            User object or None
        """
        # Try remote get first
        if self.remote_client and self.remote_client.is_authenticated():
            try:
                success, user_data = self.remote_client.get_user(user_id)

                if success and user_data:
                    user = self._create_user_from_remote(user_data)
                    return user

            except Exception as e:
                self.logger.error(f"Remote get user error: {e}")

        # Use local get
        return self.local_auth.get_user_by_id(user_id)

    def update_user(self, user_id: str, **kwargs) -> bool:
        """
        Update user (tries remote first, falls back to local)

        Args:
            user_id: User ID
            **kwargs: Fields to update (email, role, is_active)

        Returns:
            Success status
        """
        # Try remote update first
        if self.remote_client and self.remote_client.is_authenticated():
            try:
                success, _ = self.remote_client.update_user(
                    user_id,
                    email=kwargs.get("email"),
                    role=kwargs.get("role"),
                    is_active=kwargs.get("is_active")
                )

                if success:
                    self.logger.info(f"✓ User updated on remote server: {user_id}")
                    return True

                self.logger.warning("Remote user update failed, falling back to local")

            except Exception as e:
                self.logger.error(f"Remote user update error: {e}")

        # Use local update
        return self.local_auth.update_user(user_id, **kwargs)

    def delete_user(self, user_id: str) -> bool:
        """
        Delete user (tries remote first, falls back to local)

        Args:
            user_id: User ID

        Returns:
            Success status
        """
        # Try remote delete first
        if self.remote_client and self.remote_client.is_authenticated():
            try:
                success = self.remote_client.delete_user(user_id)

                if success:
                    self.logger.info(f"✓ User deleted on remote server: {user_id}")
                    return True

                self.logger.warning("Remote user delete failed, falling back to local")

            except Exception as e:
                self.logger.error(f"Remote user delete error: {e}")

        # Use local delete
        return self.local_auth.delete_user(user_id)


# Global instance
_hybrid_auth_manager = None


def get_hybrid_auth_manager(config=None) -> HybridAuthManager:
    """Get or create global hybrid auth manager instance"""
    global _hybrid_auth_manager
    if _hybrid_auth_manager is None:
        _hybrid_auth_manager = HybridAuthManager(config)
    return _hybrid_auth_manager
