// Hand-written response models mirroring backend/app/organizations/schemas.py.
// No code-gen (json_serializable) yet -- small enough surface for Sprint 2
// that manual fromJson keeps the dependency list lighter; revisit if the
// number of models grows enough to justify the build_runner step.

class Organization {
  Organization({required this.id, required this.name});

  final String id;
  final String name;

  factory Organization.fromJson(Map<String, dynamic> json) {
    return Organization(id: json['id'] as String, name: json['name'] as String);
  }
}

class Workspace {
  Workspace({required this.id, required this.tenantId, required this.name});

  final String id;
  final String tenantId;
  final String name;

  factory Workspace.fromJson(Map<String, dynamic> json) {
    return Workspace(
      id: json['id'] as String,
      tenantId: json['tenant_id'] as String,
      name: json['name'] as String,
    );
  }
}

class OrganizationCreateResult {
  OrganizationCreateResult({required this.organization, required this.workspace});

  final Organization organization;
  final Workspace workspace;

  factory OrganizationCreateResult.fromJson(Map<String, dynamic> json) {
    return OrganizationCreateResult(
      organization: Organization.fromJson(json['organization'] as Map<String, dynamic>),
      workspace: Workspace.fromJson(json['workspace'] as Map<String, dynamic>),
    );
  }
}

class Membership {
  Membership({
    required this.organizationId,
    required this.organizationName,
    required this.roleName,
    required this.workspaceId,
    required this.status,
  });

  final String organizationId;
  final String organizationName;
  final String roleName;
  final String? workspaceId;
  final String status;

  factory Membership.fromJson(Map<String, dynamic> json) {
    return Membership(
      organizationId: json['organization_id'] as String,
      organizationName: json['organization_name'] as String,
      roleName: json['role_name'] as String,
      workspaceId: json['workspace_id'] as String?,
      status: json['status'] as String,
    );
  }
}

class MeResponse {
  MeResponse({required this.userId, required this.email, required this.memberships});

  final String userId;
  final String? email;
  final List<Membership> memberships;

  factory MeResponse.fromJson(Map<String, dynamic> json) {
    return MeResponse(
      userId: json['user_id'] as String,
      email: json['email'] as String?,
      memberships: (json['memberships'] as List)
          .map((e) => Membership.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class Member {
  Member({
    required this.id,
    required this.userId,
    required this.email,
    required this.roleName,
    required this.status,
    required this.invitedEmail,
  });

  final String id;
  final String? userId;
  final String? email;
  final String roleName;
  final String status;
  final String? invitedEmail;

  factory Member.fromJson(Map<String, dynamic> json) {
    return Member(
      id: json['id'] as String,
      userId: json['user_id'] as String?,
      email: json['email'] as String?,
      roleName: json['role_name'] as String,
      status: json['status'] as String,
      invitedEmail: json['invited_email'] as String?,
    );
  }
}
