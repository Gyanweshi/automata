import os
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class InstagramResearchTask:
    """Task to conduct research on the best way to post on Instagram for a brand like Maple."""

    brand_name: str = "Maple"
    research_questions: list[str] = field(default_factory=lambda: [
        "What are the optimal times to post on Instagram?",
        "What types of content perform best for a brand like Maple?",
        "How often should posts be scheduled?",
        "What are the key metrics to track for Instagram performance?",
        "What are some common mistakes brands make when posting on Instagram?"
    ])

    def execute(self) -> dict[str, Any]:
        """Execute the research task and return findings."""
        # Placeholder for actual research logic
        findings = {
            "optimal_post_times": ["10 AM", "4 PM"],
            "best_content_types": ["product images", "user-generated content", "educational posts"],
            "post_frequency": "3-5 times per week",
            "key_metrics": ["engagement rate", "reach", "followers growth"],
            "common_mistakes": ["posting too frequently", "not engaging with followers"]
        }
        return findings

if __name__ == '__main__':
    task = InstagramResearchTask()
    print(task.execute())
