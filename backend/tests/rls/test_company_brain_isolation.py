"""Real RLS tests (Sprint 4, DB4.1) for the Company Brain tables --
skills, team_members, team_member_skills, portfolio_items, case_studies,
files -- against a real Postgres connection (see conftest.py's skip guard
if RLS_TEST_DATABASE_URL isn't set). Same scenario shapes as
test_cross_tenant_isolation.py's Sprint 3 tests, applied to the four
directly tenant-scoped new tables plus the one join table among them.
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from tests.rls.conftest import create_tenant, set_context


async def _insert_skill(session: AsyncSession, *, tenant_id: uuid.UUID, name: str) -> uuid.UUID:
    skill_id = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO skills (id, tenant_id, name, created_at, updated_at, version, legal_hold) "
            "VALUES (:id, :tid, :name, now(), now(), 1, false)"
        ),
        {"id": str(skill_id), "tid": str(tenant_id), "name": name},
    )
    return skill_id


async def _insert_team_member(
    session: AsyncSession, *, tenant_id: uuid.UUID, name: str
) -> uuid.UUID:
    member_id = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO team_members "
            "(id, tenant_id, name, is_active, created_at, updated_at, version, legal_hold) "
            "VALUES (:id, :tid, :name, true, now(), now(), 1, false)"
        ),
        {"id": str(member_id), "tid": str(tenant_id), "name": name},
    )
    return member_id


async def _insert_portfolio_item(
    session: AsyncSession, *, tenant_id: uuid.UUID, title: str
) -> uuid.UUID:
    item_id = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO portfolio_items "
            "(id, tenant_id, title, created_at, updated_at, version, legal_hold) "
            "VALUES (:id, :tid, :title, now(), now(), 1, false)"
        ),
        {"id": str(item_id), "tid": str(tenant_id), "title": title},
    )
    return item_id


async def _insert_case_study(
    session: AsyncSession, *, tenant_id: uuid.UUID, title: str
) -> uuid.UUID:
    case_study_id = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO case_studies "
            "(id, tenant_id, title, created_at, updated_at, version, legal_hold) "
            "VALUES (:id, :tid, :title, now(), now(), 1, false)"
        ),
        {"id": str(case_study_id), "tid": str(tenant_id), "title": title},
    )
    return case_study_id


async def _insert_file(session: AsyncSession, *, tenant_id: uuid.UUID) -> uuid.UUID:
    file_id = uuid.uuid4()
    storage_path = f"{tenant_id}/{uuid.uuid4()}_proposal.pdf"
    await session.execute(
        text(
            "INSERT INTO files "
            "(id, tenant_id, bucket, storage_path, original_filename, status, "
            "created_at, updated_at, version, legal_hold) "
            "VALUES (:id, :tid, 'company-files', :path, 'proposal.pdf', 'pending', "
            "now(), now(), 1, false)"
        ),
        {"id": str(file_id), "tid": str(tenant_id), "path": storage_path},
    )
    return file_id


@pytest.mark.asyncio
async def test_tenant_a_cannot_select_tenant_b_skills(pg_session: AsyncSession) -> None:
    org_a, _, owner_a = await create_tenant(pg_session, name=f"RLS Company A {uuid.uuid4()}")
    org_b, _, owner_b = await create_tenant(pg_session, name=f"RLS Company B {uuid.uuid4()}")

    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    await _insert_skill(pg_session, tenant_id=org_a, name="Flutter")
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    await _insert_skill(pg_session, tenant_id=org_b, name="PostgreSQL")
    await pg_session.commit()

    # set_config's third argument (true = transaction-local) means the
    # context above reset when the commit ended that transaction -- it
    # must be re-set before the query below runs in the new transaction.
    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    result = await pg_session.execute(text("SELECT name FROM skills"))
    visible_names = {row[0] for row in result.all()}

    assert visible_names == {"PostgreSQL"}


@pytest.mark.asyncio
async def test_tenant_a_cannot_insert_skill_claiming_tenant_b(pg_session: AsyncSession) -> None:
    org_a, _, owner_a = await create_tenant(pg_session, name=f"RLS Company A {uuid.uuid4()}")
    org_b, _, owner_b = await create_tenant(pg_session, name=f"RLS Company B {uuid.uuid4()}")

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)

    with pytest.raises(DBAPIError, match="row-level security"):
        await _insert_skill(pg_session, tenant_id=org_a, name="Should Be Rejected")
    await pg_session.rollback()


@pytest.mark.asyncio
async def test_tenant_a_cannot_select_tenant_b_team_members(pg_session: AsyncSession) -> None:
    org_a, _, owner_a = await create_tenant(pg_session, name=f"RLS Company A {uuid.uuid4()}")
    org_b, _, owner_b = await create_tenant(pg_session, name=f"RLS Company B {uuid.uuid4()}")

    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    await _insert_team_member(pg_session, tenant_id=org_a, name="Alex Rivera")
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    await _insert_team_member(pg_session, tenant_id=org_b, name="Jordan Lee")
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    result = await pg_session.execute(text("SELECT name FROM team_members"))
    visible_names = {row[0] for row in result.all()}

    assert visible_names == {"Jordan Lee"}


@pytest.mark.asyncio
async def test_tenant_a_cannot_select_tenant_b_portfolio_items(pg_session: AsyncSession) -> None:
    org_a, _, owner_a = await create_tenant(pg_session, name=f"RLS Company A {uuid.uuid4()}")
    org_b, _, owner_b = await create_tenant(pg_session, name=f"RLS Company B {uuid.uuid4()}")

    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    await _insert_portfolio_item(pg_session, tenant_id=org_a, title="Tenant A Project")
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    await _insert_portfolio_item(pg_session, tenant_id=org_b, title="Tenant B Project")
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    result = await pg_session.execute(text("SELECT title FROM portfolio_items"))
    visible_titles = {row[0] for row in result.all()}

    assert visible_titles == {"Tenant B Project"}


@pytest.mark.asyncio
async def test_tenant_a_cannot_select_tenant_b_case_studies(pg_session: AsyncSession) -> None:
    org_a, _, owner_a = await create_tenant(pg_session, name=f"RLS Company A {uuid.uuid4()}")
    org_b, _, owner_b = await create_tenant(pg_session, name=f"RLS Company B {uuid.uuid4()}")

    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    await _insert_case_study(pg_session, tenant_id=org_a, title="Tenant A Case Study")
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    await _insert_case_study(pg_session, tenant_id=org_b, title="Tenant B Case Study")
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    result = await pg_session.execute(text("SELECT title FROM case_studies"))
    visible_titles = {row[0] for row in result.all()}

    assert visible_titles == {"Tenant B Case Study"}


@pytest.mark.asyncio
async def test_tenant_a_cannot_select_tenant_b_files(pg_session: AsyncSession) -> None:
    org_a, _, owner_a = await create_tenant(pg_session, name=f"RLS Company A {uuid.uuid4()}")
    org_b, _, owner_b = await create_tenant(pg_session, name=f"RLS Company B {uuid.uuid4()}")

    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    await _insert_file(pg_session, tenant_id=org_a)
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    file_b = await _insert_file(pg_session, tenant_id=org_b)
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    result = await pg_session.execute(text("SELECT id FROM files"))
    visible_ids = {row[0] for row in result.all()}

    assert visible_ids == {file_b}


@pytest.mark.asyncio
async def test_team_member_skills_join_table_reaches_through_to_tenant(
    pg_session: AsyncSession,
) -> None:
    """team_member_skills has no tenant_id of its own -- its policy reaches
    through to team_members.tenant_id (supabase/rls/team_member_skills.sql),
    same pattern as role_permissions.sql. Confirms that reach-through
    actually isolates tenants rather than trivially allowing everything."""
    org_a, _, owner_a = await create_tenant(pg_session, name=f"RLS Company A {uuid.uuid4()}")
    org_b, _, owner_b = await create_tenant(pg_session, name=f"RLS Company B {uuid.uuid4()}")

    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    member_a = await _insert_team_member(pg_session, tenant_id=org_a, name="Alex Rivera")
    skill_a = await _insert_skill(pg_session, tenant_id=org_a, name="Flutter")
    await pg_session.execute(
        text(
            "INSERT INTO team_member_skills (id, team_member_id, skill_id, created_at) "
            "VALUES (:id, :mid, :sid, now())"
        ),
        {"id": str(uuid.uuid4()), "mid": str(member_a), "sid": str(skill_a)},
    )
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    result = await pg_session.execute(text("SELECT count(*) FROM team_member_skills"))
    assert result.scalar_one() == 0

    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    result = await pg_session.execute(text("SELECT count(*) FROM team_member_skills"))
    assert result.scalar_one() == 1


@pytest.mark.asyncio
async def test_anonymous_no_context_sees_zero_rows_across_company_brain_tables(
    pg_session: AsyncSession,
) -> None:
    org_a, _, owner_a = await create_tenant(pg_session, name=f"RLS Company A {uuid.uuid4()}")
    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    await _insert_skill(pg_session, tenant_id=org_a, name="Flutter")
    await _insert_team_member(pg_session, tenant_id=org_a, name="Alex Rivera")
    await _insert_portfolio_item(pg_session, tenant_id=org_a, title="Project")
    await _insert_case_study(pg_session, tenant_id=org_a, title="Case Study")
    await _insert_file(pg_session, tenant_id=org_a)
    await pg_session.commit()

    # Deliberately no set_context call from here -- a fresh, contextless
    # transaction must see nothing on any of these tenant-scoped tables.
    for table in ("skills", "team_members", "portfolio_items", "case_studies", "files"):
        result = await pg_session.execute(text(f"SELECT count(*) FROM {table}"))
        assert result.scalar_one() == 0, f"{table} leaked rows with no session context set"
