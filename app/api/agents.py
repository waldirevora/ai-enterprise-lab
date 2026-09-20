from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.access.context import (
    PrincipalContext,
)
from app.access.dependencies import (
    require_rate_limited_principal_context,
)
from app.access.unit_grants import (
    UnitGrantUnavailableError,
    load_unit_access_grants,
)
from app.access.unit_scope import (
    UnitScopeDeniedError,
    UnitScopeUnavailableError,
    resolve_unit_scope,
)
from app.agents.schemas import (
    AgentRunRequest,
    AgentRunResponse,
)
from app.agents.service import (
    AgentNoContextError,
    AgentServiceError,
    run_enterprise_knowledge_agent,
)
from app.audit.logger import (
    emit_audit_event,
)


router = APIRouter(
    prefix="/v1/agents",
    tags=[
        "agents",
    ],
)


@router.post(
    "/enterprise-knowledge/run",
    response_model=AgentRunResponse,
)
async def run_enterprise_knowledge(
    request: AgentRunRequest,
    context: Annotated[
        PrincipalContext,
        Depends(
            require_rate_limited_principal_context
        ),
    ],
) -> AgentRunResponse:
    try:
        unit_grants = (
            await load_unit_access_grants(
                context
            )
        )

        scope_decision = (
            await resolve_unit_scope(
                context=context,
                question=request.message,
                unit_grants=unit_grants,
            )
        )

        return (
            await run_enterprise_knowledge_agent(
                request=request,
                organization_id=(
                    context.organization_id
                ),
                principal_id=(
                    context.principal_id
                ),
                question_classification=(
                    context.max_classification
                ),
                allowed_classifications=(
                    context
                    .allowed_classifications
                ),
                unit_grants=(
                    scope_decision.unit_grants
                ),
            )
        )

    except UnitScopeDeniedError as exc:
        emit_audit_event(
            event_type=(
                "authorization.unit_scope_denied"
            ),
            outcome="failure",
            organization_id=(
                context.organization_id
            ),
            principal_id=(
                context.principal_id
            ),
            classification=(
                context.max_classification
            ),
            reason_code=(
                "unit_scope_denied"
            ),
            metadata={
                "status_code": 404,
            },
        )

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "No authorized enterprise "
                "knowledge was found."
            ),
        ) from exc

    except UnitScopeUnavailableError as exc:
        emit_audit_event(
            event_type=(
                "authorization."
                "unit_scope_unavailable"
            ),
            outcome="unavailable",
            organization_id=(
                context.organization_id
            ),
            principal_id=(
                context.principal_id
            ),
            classification=(
                context.max_classification
            ),
            reason_code=(
                "unit_scope_backend_unavailable"
            ),
            metadata={
                "status_code": 503,
            },
        )

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Unit scope service unavailable."
            ),
        ) from exc

    except UnitGrantUnavailableError as exc:
        emit_audit_event(
            event_type=(
                "authorization."
                "unit_grants_unavailable"
            ),
            outcome="unavailable",
            organization_id=(
                context.organization_id
            ),
            principal_id=(
                context.principal_id
            ),
            classification=(
                context.max_classification
            ),
            reason_code=(
                "unit_grants_backend_unavailable"
            ),
            metadata={
                "status_code": 503,
            },
        )

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Unit authorization "
                "service unavailable."
            ),
        ) from exc

    except AgentNoContextError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "No authorized enterprise "
                "knowledge was found."
            ),
        ) from exc

    except AgentServiceError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Agent service unavailable."
            ),
        ) from exc
