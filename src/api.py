"""FastAPI entry point for the earnings review workflow."""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException

from .errors import EarningsReviewError, api_error_detail
from .llm import get_provider
from .report_quality_guidance import GuidanceAcquisitionError
from .report_quality_numeric_grounding import NumericGroundingError
from .workflow import ReviewRequest, ReviewResponse, ReviewWorkflow, WorkflowValidationError
from .workflow_agents import WorkflowAgentError

app = FastAPI(title="Earnings Debate Agent API")


def get_workflow() -> ReviewWorkflow:
    return ReviewWorkflow(llm=get_provider())


@app.post("/reviews", response_model=ReviewResponse)
def create_review(
    request: ReviewRequest,
    workflow: ReviewWorkflow = Depends(get_workflow),
) -> ReviewResponse:
    try:
        return workflow.run(request)
    except EarningsReviewError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_api_detail()) from exc
    except (WorkflowValidationError, NumericGroundingError, GuidanceAcquisitionError) as exc:
        raise HTTPException(
            status_code=422,
            detail=api_error_detail(
                "workflow_validation_error",
                str(exc),
                source="workflow",
                retryable=False,
            ),
        ) from exc
    except WorkflowAgentError as exc:
        raise HTTPException(
            status_code=502,
            detail=api_error_detail(
                "workflow_agent_error",
                str(exc),
                source="llm",
                retryable=True,
                details={"error_type": exc.__class__.__name__},
            ),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=api_error_detail(
                "workflow_execution_error",
                "workflow execution failed",
                source="workflow",
                retryable=False,
                details={"error_type": exc.__class__.__name__},
            ),
        ) from exc
