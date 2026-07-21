from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bts_monitoring.database.models.mission_rule_snapshot import (
    MissionRuleSnapshotModel,
)


class MissionRuleSnapshotRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_next_version(
        self,
        mission_id: str,
    ) -> int:
        statement = select(
            func.coalesce(
                func.max(
                    MissionRuleSnapshotModel.version
                ),
                0,
            )
        ).where(
            MissionRuleSnapshotModel.mission_id
            == mission_id
        )

        result = await self.session.execute(statement)

        current_version = int(result.scalar_one())

        return current_version + 1

    async def create(
        self,
        snapshot: MissionRuleSnapshotModel,
    ) -> MissionRuleSnapshotModel:
        self.session.add(snapshot)

        await self.session.flush()
        await self.session.refresh(snapshot)

        return snapshot

    async def get_latest(
        self,
        mission_id: str,
    ) -> MissionRuleSnapshotModel | None:
        statement = (
            select(MissionRuleSnapshotModel)
            .where(
                MissionRuleSnapshotModel.mission_id
                == mission_id
            )
            .order_by(
                MissionRuleSnapshotModel.version.desc()
            )
            .limit(1)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_version(
        self,
        *,
        mission_id: str,
        version: int,
    ) -> MissionRuleSnapshotModel | None:
        statement = select(
            MissionRuleSnapshotModel
        ).where(
            MissionRuleSnapshotModel.mission_id
            == mission_id,
            MissionRuleSnapshotModel.version
            == version,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def list_by_mission(
        self,
        mission_id: str,
    ) -> list[MissionRuleSnapshotModel]:
        statement = (
            select(MissionRuleSnapshotModel)
            .where(
                MissionRuleSnapshotModel.mission_id
                == mission_id
            )
            .order_by(
                MissionRuleSnapshotModel.version.desc()
            )
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())