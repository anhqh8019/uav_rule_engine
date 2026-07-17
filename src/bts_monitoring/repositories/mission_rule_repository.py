from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bts_monitoring.database.models.mission_rule import (
    MissionRuleModel,
)


class MissionRuleRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_by_mission_and_event(
        self,
        *,
        mission_id: str,
        event_type: str,
    ) -> MissionRuleModel | None:
        statement = select(MissionRuleModel).where(
            MissionRuleModel.mission_id == mission_id,
            MissionRuleModel.event_type == event_type,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def list_by_mission(
        self,
        mission_id: str,
    ) -> list[MissionRuleModel]:
        statement = (
            select(MissionRuleModel)
            .where(
                MissionRuleModel.mission_id
                == mission_id
            )
            .order_by(
                MissionRuleModel.event_type.asc()
            )
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def list_active_by_mission(
        self,
        mission_id: str,
    ) -> list[MissionRuleModel]:
        statement = (
            select(MissionRuleModel)
            .where(
                MissionRuleModel.mission_id
                == mission_id,
                MissionRuleModel.status == "active",
                MissionRuleModel.enabled.is_(True),
            )
            .order_by(
                MissionRuleModel.event_type.asc()
            )
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def delete(
        self,
        rule: MissionRuleModel,
    ) -> None:
        await self.session.delete(rule)