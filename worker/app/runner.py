import time

from app.config import settings
from app.pipelines.stages import ApplicationDraftStage, MatchingStage, PipelineContext, ProfileExtractionStage, ResumeTailoringStage
from app.services.api_client import ApiClient


class PipelineRunner:
    def __init__(self) -> None:
        self.api_client = ApiClient()
        self.stages = [ProfileExtractionStage(), MatchingStage(), ResumeTailoringStage(), ApplicationDraftStage()]

    def process_forever(self) -> None:
        while True:
            claimed = self.api_client.claim_run()
            if not claimed:
                time.sleep(settings.worker_poll_seconds)
                continue

            run_id = claimed["id"]
            context = PipelineContext(run_id=run_id, job=claimed["job"], candidate=claimed["candidate"], stage_results={})

            try:
                for stage in self.stages:
                    context.stage_results[stage.name] = stage.run(context)

                self.api_client.complete_run(
                    run_id,
                    {
                        "status": "completed",
                        "score": context.stage_results["matching"]["fit_score"],
                        "stage_results": context.stage_results,
                        "tailored_resume": context.stage_results["resume_tailoring"]["tailored_resume"],
                        "cover_letter": context.stage_results["application_drafting"]["cover_letter"],
                        "recruiter_notes": context.stage_results["application_drafting"]["recruiter_notes"],
                    },
                )
            except Exception as exc:
                self.api_client.complete_run(
                    run_id,
                    {"status": "failed", "error_message": str(exc), "stage_results": context.stage_results},
                )


if __name__ == "__main__":
    PipelineRunner().process_forever()

