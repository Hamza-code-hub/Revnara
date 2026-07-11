"""Global permission catalog and default per-organization role grants.

Permission keys are code-defined capabilities, not something a tenant
configures itself (see Permission model docstring) -- versioned here,
not hardcoded inline at each call site (§2.8 Configuration Over
Hardcoding).
"""

PERMISSIONS: dict[str, str] = {
    "members.invite": "Invite new team members",
    "members.remove": "Deactivate/remove team members",
    "members.manage_roles": "Change a team member's role",
    "org.manage": "Manage organization settings",
    "company.manage": "Manage company profile, team, skills, and portfolio",
}

DEFAULT_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "owner": set(PERMISSIONS.keys()),
    "admin": {
        "members.invite",
        "members.remove",
        "members.manage_roles",
        "company.manage",
    },
    "member": set(),
}
