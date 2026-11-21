import sys
sys.path.insert(0, 'backend')
from app.config import get_settings
get_settings.cache_clear()
from app.config import settings
from app.services.llm_service import llm_service, ToolSpec, ToolAction
from pydantic import BaseModel, Field

print("=" * 60)
print("TASK 1: Live Gemini Connectivity Test")
print("=" * 60)
print("Configured model:", settings.gemini_model)
print("Provider:", llm_service.require_provider())
resp1 = llm_service.chat([{"role": "user", "content": "Respond with ONLY the word PONG"}])
print("Task 1 Response:", resp1.strip())
assert "PONG" in resp1.strip().upper(), "Failed to get PONG"
print(">>> TASK 1 PASSED!")

print("\n" + "=" * 60)
print("TASK 2: Structured JSON Generation Test")
print("=" * 60)
class PlacementAnalysisTest(BaseModel):
    student_name: str = Field(description="Student full name")
    placement_readiness_score: int = Field(description="Score between 0 and 100")
    recommended_domains: list[str] = Field(description="1-3 domains")
    strengths: list[str] = Field(description="Top strengths")

resp2 = llm_service.complete_json(
    schema=PlacementAnalysisTest,
    system="You are an expert campus placement advisor. Return structured JSON conforming to the schema.",
    user="Student Bob Vance: 82% placement readiness, strong in Backend Development and Cloud Architecture, good problem solving.",
    temperature=0.1
)
print("Task 2 Output:\n", resp2.model_dump_json(indent=2))
assert isinstance(resp2, PlacementAnalysisTest), "Validation error"
assert resp2.placement_readiness_score > 0, "Invalid score"
print(">>> TASK 2 PASSED!")

print("\n" + "=" * 60)
print("TASK 3: Native Gemini Tool Calling Test")
print("=" * 60)
deterministic_tool = ToolSpec(
    name="get_cutoff_requirements",
    description="Get deterministic minimum cutoff CGPA and required DSA questions for a company tier.",
    parameters={
        "type": "object",
        "properties": {
            "tier": {"type": "string", "enum": ["tier_1", "tier_2", "tier_3"], "description": "Company tier"}
        },
        "required": ["tier"]
    }
)

def execute_cutoff_requirements(tier: str) -> dict:
    cutoffs = {
        "tier_1": {"min_cgpa": 8.5, "min_dsa_problems": 300, "status": "Dream Company"},
        "tier_2": {"min_cgpa": 7.5, "min_dsa_problems": 150, "status": "Core Tech"},
        "tier_3": {"min_cgpa": 6.5, "min_dsa_problems": 50, "status": "Mass Recruiter"},
    }
    return cutoffs.get(tier, {"error": "Unknown tier"})

system = "You are a campus placement bot. Use get_cutoff_requirements to answer requirements questions."
conversation = [{"role": "user", "content": "What are the cutoff requirements for tier_1 companies?"}]

action = llm_service.choose_tool(system, conversation, [deterministic_tool])
print("Step 1 Action from Gemini:", action)
assert isinstance(action, ToolAction), "Gemini did not return ToolAction"
assert action.tool == "get_cutoff_requirements", f"Wrong tool: {action.tool}"
assert action.arguments.get("tier") == "tier_1", f"Wrong args: {action.arguments}"

# Step 2: Application executes registered function deterministically
result = execute_cutoff_requirements(action.arguments["tier"])
print("Step 2 Executed tool result:", result)

# Step 3: Return result to Gemini
conversation.append({
    "role": "assistant",
    "content": f'I called the tool "{action.tool}" with arguments {action.arguments}.'
})
conversation.append({
    "role": "user",
    "content": f"TOOL RESULT (success): {result}"
})

final_answer = llm_service.choose_tool(system, conversation, [deterministic_tool])
print("Step 4 Final Answer from Gemini:\n", final_answer)
assert isinstance(final_answer, str) and len(final_answer) > 0, "Final answer was empty"
print(">>> TASK 3 PASSED!")

print("\nALL TASKS 1, 2, 3 COMPLETED SUCCESSFULLY!")
