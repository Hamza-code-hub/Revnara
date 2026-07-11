// Hand-written response models mirroring backend/app/organizations/schemas.py.
// No code-gen (json_serializable) yet -- small enough surface for Sprint 2
// that manual fromJson keeps the dependency list lighter; revisit if the
// number of models grows enough to justify the build_runner step.

class Organization {
  Organization({
    required this.id,
    required this.name,
    this.description,
    this.industry,
    this.website,
    this.foundedYear,
  });

  final String id;
  final String name;
  final String? description;
  final String? industry;
  final String? website;
  final int? foundedYear;

  factory Organization.fromJson(Map<String, dynamic> json) {
    return Organization(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      industry: json['industry'] as String?,
      website: json['website'] as String?,
      foundedYear: json['founded_year'] as int?,
    );
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

// Sprint 4 (Company Brain) models, mirroring backend/app/company/schemas.py
// and backend/app/files/schemas.py.

class Skill {
  Skill({required this.id, required this.name, this.category});

  final String id;
  final String name;
  final String? category;

  factory Skill.fromJson(Map<String, dynamic> json) {
    return Skill(
      id: json['id'] as String,
      name: json['name'] as String,
      category: json['category'] as String?,
    );
  }
}

class TeamMember {
  TeamMember({
    required this.id,
    required this.name,
    this.title,
    this.email,
    this.bio,
    this.hourlyRate,
    this.currency,
    this.weeklyAvailabilityHours,
    required this.isActive,
    required this.skills,
  });

  final String id;
  final String name;
  final String? title;
  final String? email;
  final String? bio;
  final double? hourlyRate;
  final String? currency;
  final int? weeklyAvailabilityHours;
  final bool isActive;
  final List<Skill> skills;

  factory TeamMember.fromJson(Map<String, dynamic> json) {
    return TeamMember(
      id: json['id'] as String,
      name: json['name'] as String,
      title: json['title'] as String?,
      email: json['email'] as String?,
      bio: json['bio'] as String?,
      hourlyRate: (json['hourly_rate'] as num?)?.toDouble(),
      currency: json['currency'] as String?,
      weeklyAvailabilityHours: json['weekly_availability_hours'] as int?,
      isActive: json['is_active'] as bool,
      skills: (json['skills'] as List)
          .map((e) => Skill.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class PortfolioItem {
  PortfolioItem({
    required this.id,
    required this.title,
    this.description,
    this.clientName,
    this.technologies,
    this.projectUrl,
    this.classification,
  });

  final String id;
  final String title;
  final String? description;
  final String? clientName;
  final String? technologies;
  final String? projectUrl;
  final String? classification;

  factory PortfolioItem.fromJson(Map<String, dynamic> json) {
    return PortfolioItem(
      id: json['id'] as String,
      title: json['title'] as String,
      description: json['description'] as String?,
      clientName: json['client_name'] as String?,
      technologies: json['technologies'] as String?,
      projectUrl: json['project_url'] as String?,
      classification: json['classification'] as String?,
    );
  }
}

class CaseStudy {
  CaseStudy({
    required this.id,
    this.portfolioItemId,
    required this.title,
    this.summary,
    this.content,
    this.outcomeMetrics,
    this.classification,
  });

  final String id;
  final String? portfolioItemId;
  final String title;
  final String? summary;
  final String? content;
  final String? outcomeMetrics;
  final String? classification;

  factory CaseStudy.fromJson(Map<String, dynamic> json) {
    return CaseStudy(
      id: json['id'] as String,
      portfolioItemId: json['portfolio_item_id'] as String?,
      title: json['title'] as String,
      summary: json['summary'] as String?,
      content: json['content'] as String?,
      outcomeMetrics: json['outcome_metrics'] as String?,
      classification: json['classification'] as String?,
    );
  }
}

class CompanyFile {
  CompanyFile({
    required this.id,
    required this.storagePath,
    required this.originalFilename,
    this.contentType,
    this.sizeBytes,
    required this.status,
  });

  final String id;
  final String storagePath;
  final String originalFilename;
  final String? contentType;
  final int? sizeBytes;
  final String status;

  factory CompanyFile.fromJson(Map<String, dynamic> json) {
    return CompanyFile(
      id: json['id'] as String,
      storagePath: json['storage_path'] as String,
      originalFilename: json['original_filename'] as String,
      contentType: json['content_type'] as String?,
      sizeBytes: json['size_bytes'] as int?,
      status: json['status'] as String,
    );
  }
}

class SignedUpload {
  SignedUpload({
    required this.fileId,
    required this.uploadUrl,
    required this.token,
    required this.storagePath,
  });

  final String fileId;
  final String uploadUrl;
  final String token;
  final String storagePath;

  factory SignedUpload.fromJson(Map<String, dynamic> json) {
    return SignedUpload(
      fileId: json['file_id'] as String,
      uploadUrl: json['upload_url'] as String,
      token: json['token'] as String,
      storagePath: json['storage_path'] as String,
    );
  }
}
