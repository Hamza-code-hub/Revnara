"""Global permission catalog and default per-organization role grants.

Permission keys are code-defined capabilities, not something a tenant
configures itself (see Permission model docstring) -- versioned here,
not hardcoded inline at each call site (§2.8 Configuration Over
Hardcoding).

Adding a new key here only affects organizations created *after* the
change -- role_permissions rows are a point-in-time snapshot written at
org-creation time (app/organizations/router.py), not re-derived from this
dict on every request. Confirmed for real in Sprint 6: adding
`opportunities.manage` didn't retroactively grant it to a pre-existing
real org's roles, so a one-time backfill insert (permission row +
role_permissions grants) was needed for that org. Rolling out a new
permission to already-existing tenants needs the same kind of backfill,
not just adding it here.
"""

PERMISSIONS: dict[str, str] = {
    "members.invite": "Invite new team members",
    "members.remove": "Deactivate/remove team members",
    "members.manage_roles": "Change a team member's role",
    "org.manage": "Manage organization settings",
    "company.manage": "Manage company profile, team, skills, and portfolio",
    "opportunities.manage": "Create and import business development opportunities",
}

DEFAULT_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "owner": set(PERMISSIONS.keys()),
    "admin": {
        "members.invite",
        "members.remove",
        "members.manage_roles",
        "company.manage",
        "opportunities.manage",
    },
    # Unlike company.manage/members.*, opportunity creation is a
    # BD team member's actual day-to-day job, not an admin-only action --
    # granted to plain members by default.
    "member": {"opportunities.manage"},
}
