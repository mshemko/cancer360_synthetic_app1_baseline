"""Role-based access control for Cancer 360."""

from functools import wraps
from fastapi import HTTPException, status

# Role hierarchy: higher roles inherit permissions of lower roles
ROLE_HIERARCHY = {
    "admin": 100,
    "manager": 80,
    "clinician": 60,
    "cancer_nurse": 50,
    "mdt_coordinator": 40,
    "readonly": 10,
}

# Permission matrix
PERMISSIONS = {
    "ptl:read": ["readonly", "mdt_coordinator", "cancer_nurse", "clinician", "manager", "admin"],
    "ptl:write": ["cancer_nurse", "clinician", "manager", "admin"],
    "patient:read": ["readonly", "mdt_coordinator", "cancer_nurse", "clinician", "manager", "admin"],
    "patient:write": ["cancer_nurse", "clinician", "manager", "admin"],
    "action:read": ["readonly", "mdt_coordinator", "cancer_nurse", "clinician", "manager", "admin"],
    "action:create": ["mdt_coordinator", "cancer_nurse", "clinician", "manager", "admin"],
    "action:update": ["mdt_coordinator", "cancer_nurse", "clinician", "manager", "admin"],
    "action:delete": ["manager", "admin"],
    "dashboard:read": ["readonly", "mdt_coordinator", "cancer_nurse", "clinician", "manager", "admin"],
    "settings:read": ["manager", "admin"],
    "settings:write": ["admin"],
    "admin:all": ["admin"],
}


def check_permission(user: dict, permission: str) -> bool:
    """Check if user has the required permission."""
    role = user.get("role", "readonly")
    allowed_roles = PERMISSIONS.get(permission, [])
    return role in allowed_roles


def require_permission(permission: str):
    """Dependency factory that checks a specific permission."""
    def checker(user: dict):
        if not check_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}",
            )
        return user
    return checker


def team_filter(user: dict, query, pathway_model):
    """Apply team-based filtering if user is team-scoped."""
    role = user.get("role", "readonly")
    team = user.get("team")

    # Admins and managers see everything
    if role in ("admin", "manager"):
        return query

    # Team-scoped users see only their team's patients
    if team:
        return query.where(pathway_model.assigned_team == team)

    return query
