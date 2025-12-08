"""
Workflow Runner - Execute narrative development workflows.

This module provides a runner for the NA-xx workflow definitions,
enabling iterative, LLM-assisted story development.

Usage:
    from narrative.workflow_runner import WorkflowRunner

    runner = WorkflowRunner(story_id="my_mystery")
    runner.run_workflow("NA-01-StoryInception", {
        "premise": "A detective discovers her partner is the killer",
        "genre": "mystery"
    })
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional
from enum import Enum, auto
import os


class StepStatus(Enum):
    """Status of a workflow step."""
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()
    WAITING_USER = auto()


@dataclass
class StepResult:
    """Result of executing a workflow step."""
    step_id: str
    status: StepStatus
    outputs: dict[str, Any] = field(default_factory=dict)
    llm_response: Optional[str] = None
    user_input: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class WorkflowState:
    """Current state of a workflow execution."""
    workflow_id: str
    story_id: str
    current_step: str
    step_results: dict[str, StepResult] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    iteration_count: int = 0
    completed: bool = False

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "story_id": self.story_id,
            "current_step": self.current_step,
            "step_results": {
                k: {
                    "step_id": v.step_id,
                    "status": v.status.name,
                    "outputs": v.outputs,
                    "error": v.error,
                }
                for k, v in self.step_results.items()
            },
            "iteration_count": self.iteration_count,
            "completed": self.completed,
        }

    def save(self, path: Path) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class WorkflowRunner:
    """
    Executes narrative development workflows.

    Handles:
    - Loading workflow definitions
    - Executing steps (tools, LLM prompts, user interactions)
    - Managing state and context
    - Iteration and branching
    """

    def __init__(
        self,
        story_id: str,
        output_dir: str = "output",
        workflows_dir: Optional[str] = None,
        llm_callback: Optional[Callable[[str], str]] = None,
        user_callback: Optional[Callable[[str], str]] = None,
    ):
        """
        Initialize the workflow runner.

        Args:
            story_id: Unique identifier for this story project
            output_dir: Directory for outputs
            workflows_dir: Directory containing workflow JSON files
            llm_callback: Function to call for LLM responses (prompt -> response)
            user_callback: Function to call for user input (prompt -> response)
        """
        self.story_id = story_id
        self.output_dir = Path(output_dir) / story_id
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if workflows_dir:
            self.workflows_dir = Path(workflows_dir)
        else:
            self.workflows_dir = Path(__file__).parent / "workflows"

        self.llm_callback = llm_callback or self._default_llm_callback
        self.user_callback = user_callback or self._default_user_callback

        self.workflows: dict[str, dict] = {}
        self.current_state: Optional[WorkflowState] = None
        self._load_workflows()

    def _load_workflows(self) -> None:
        """Load all workflow definitions from the workflows directory."""
        for workflow_file in self.workflows_dir.glob("NA-*.json"):
            with open(workflow_file) as f:
                workflow = json.load(f)
                self.workflows[workflow["workflow_id"]] = workflow

    def _default_llm_callback(self, prompt: str) -> str:
        """Default LLM callback that returns a placeholder."""
        print(f"\n{'='*60}")
        print("LLM PROMPT:")
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        print("{'='*60}")
        return "[LLM response would go here - connect to actual LLM]"

    def _default_user_callback(self, prompt: str) -> str:
        """Default user callback that uses stdin."""
        print(f"\n{'='*60}")
        print("USER INPUT NEEDED:")
        print(prompt)
        print("{'='*60}")
        return input("Your response: ")

    def run_workflow(
        self,
        workflow_id: str,
        inputs: dict[str, Any],
        resume_from: Optional[str] = None,
    ) -> WorkflowState:
        """
        Run a workflow from the beginning or resume from a step.

        Args:
            workflow_id: ID of workflow to run (e.g., "NA-01")
            inputs: Input values for the workflow
            resume_from: Step ID to resume from (optional)

        Returns:
            Final workflow state
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_id}")

        workflow = self.workflows[workflow_id]

        # Initialize state
        self.current_state = WorkflowState(
            workflow_id=workflow_id,
            story_id=self.story_id,
            current_step=resume_from or workflow["steps"][0]["step_id"],
            context={**inputs},
        )

        # Load any existing artifacts
        self._load_existing_artifacts()

        # Execute steps
        steps = workflow["steps"]
        start_index = 0
        if resume_from:
            for i, step in enumerate(steps):
                if step["step_id"] == resume_from:
                    start_index = i
                    break

        for step in steps[start_index:]:
            self.current_state.current_step = step["step_id"]
            result = self._execute_step(step)
            self.current_state.step_results[step["step_id"]] = result

            if result.status == StepStatus.FAILED:
                # Check for failure handlers
                if "on_failure" in step:
                    self._handle_failure(step["on_failure"], result)
                else:
                    break

            if result.status == StepStatus.WAITING_USER:
                # Save state and wait for user
                self._save_state()
                break

            # Update context with outputs
            self.current_state.context.update(result.outputs)

            # Save progress
            self._save_state()

        # Check for iteration triggers
        if not self.current_state.completed:
            self._check_iteration_triggers(workflow)

        # Check if workflow is complete
        if all(
            r.status == StepStatus.COMPLETED
            for r in self.current_state.step_results.values()
        ):
            self.current_state.completed = True
            self._on_workflow_complete(workflow)

        return self.current_state

    def _execute_step(self, step: dict) -> StepResult:
        """Execute a single workflow step."""
        step_id = step["step_id"]
        print(f"\n>>> Executing step: {step_id} - {step['name']}")

        result = StepResult(step_id=step_id, status=StepStatus.IN_PROGRESS)

        try:
            # Handle different step types
            if "llm_prompt" in step:
                result = self._execute_llm_step(step, result)
            elif "tool" in step:
                result = self._execute_tool_step(step, result)
            elif step.get("type") == "user_interaction":
                result = self._execute_user_step(step, result)
            else:
                # Simple pass-through step
                result.status = StepStatus.COMPLETED

            # Run validation if specified
            if "validation" in step and result.status == StepStatus.COMPLETED:
                validation_passed = self._run_validation(step["validation"])
                if not validation_passed:
                    result.status = StepStatus.FAILED
                    result.error = "Validation failed"

        except Exception as e:
            result.status = StepStatus.FAILED
            result.error = str(e)

        return result

    def _execute_llm_step(self, step: dict, result: StepResult) -> StepResult:
        """Execute a step that requires LLM interaction."""
        prompt_template = step["llm_prompt"]

        # Substitute context variables into prompt
        prompt = self._substitute_variables(prompt_template)

        # Call LLM
        response = self.llm_callback(prompt)
        result.llm_response = response

        # Parse outputs from response
        if "outputs" in step:
            # Try to extract structured data from response
            result.outputs = self._parse_llm_outputs(response, step["outputs"])

        result.status = StepStatus.COMPLETED
        return result

    def _execute_tool_step(self, step: dict, result: StepResult) -> StepResult:
        """Execute a step that uses a narrative module tool."""
        tool_path = step["tool"]

        # Import and execute the tool
        # Format: "narrative.ClassName.method" or "narrative.function"
        parts = tool_path.split(".")

        if len(parts) >= 2:
            # This is a placeholder - in real implementation, would dynamically import
            print(f"  Would execute tool: {tool_path}")
            result.outputs = {
                "_tool": tool_path,
                "_note": "Tool execution placeholder - connect to actual module"
            }

        result.status = StepStatus.COMPLETED
        return result

    def _execute_user_step(self, step: dict, result: StepResult) -> StepResult:
        """Execute a step requiring user input."""
        prompt = step.get("prompt", "Please provide input:")
        prompt = self._substitute_variables(prompt)

        response = self.user_callback(prompt)
        result.user_input = response

        # Parse user response
        if response.lower() in ["skip", "defer"]:
            result.status = StepStatus.SKIPPED
        else:
            result.outputs["user_response"] = response
            result.status = StepStatus.COMPLETED

        return result

    def _substitute_variables(self, template: str) -> str:
        """Substitute {variable} placeholders with context values."""
        result = template
        for key, value in self.current_state.context.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, indent=2)
                else:
                    value_str = str(value)
                result = result.replace(placeholder, value_str)
        return result

    def _parse_llm_outputs(self, response: str, expected_outputs: list[str]) -> dict:
        """Parse expected outputs from LLM response."""
        outputs = {}

        # Try to parse as JSON first
        try:
            # Find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                parsed = json.loads(json_str)
                for key in expected_outputs:
                    if key in parsed:
                        outputs[key] = parsed[key]
        except json.JSONDecodeError:
            pass

        # Fallback: store full response keyed by first output name
        if not outputs and expected_outputs:
            outputs[expected_outputs[0]] = response

        return outputs

    def _run_validation(self, validations: list[str]) -> bool:
        """Run validation checks."""
        # Placeholder - would implement actual validation logic
        print(f"  Running validations: {validations}")
        return True

    def _handle_failure(self, handler: dict, result: StepResult) -> None:
        """Handle step failure according to handler config."""
        if handler.get("action") == "return_to_step":
            target = handler["target"]
            print(f"  Failure handler: returning to {target}")
            self.current_state.current_step = target
            self.current_state.iteration_count += 1

    def _check_iteration_triggers(self, workflow: dict) -> None:
        """Check if any iteration triggers should fire."""
        triggers = workflow.get("iteration_triggers", [])
        for trigger in triggers:
            condition = trigger["condition"]
            # Placeholder - would implement condition checking
            print(f"  Checking trigger: {condition}")

    def _load_existing_artifacts(self) -> None:
        """Load any existing artifacts from previous runs."""
        artifacts_to_load = [
            ("requirements.json", "story_requirements"),
            ("characters.json", "character_profiles"),
            ("initial_dag.json", "initial_dag"),
        ]

        for filename, context_key in artifacts_to_load:
            filepath = self.output_dir / filename
            if filepath.exists():
                with open(filepath) as f:
                    self.current_state.context[context_key] = json.load(f)
                print(f"  Loaded existing: {filename}")

    def _save_state(self) -> None:
        """Save current workflow state."""
        state_path = self.output_dir / "workflow_state.json"
        self.current_state.save(state_path)

    def _on_workflow_complete(self, workflow: dict) -> None:
        """Handle workflow completion."""
        print(f"\n{'='*60}")
        print(f"Workflow {workflow['workflow_id']} completed!")

        if "next_workflow" in workflow:
            print(f"Suggested next workflow: {workflow['next_workflow']}")

        print(f"Outputs saved to: {self.output_dir}")
        print(f"{'='*60}\n")

    def list_workflows(self) -> list[dict]:
        """List all available workflows."""
        return [
            {
                "id": w["workflow_id"],
                "name": w["name"],
                "description": w["description"],
            }
            for w in self.workflows.values()
        ]

    def get_workflow_status(self) -> dict:
        """Get status of current workflow execution."""
        if not self.current_state:
            return {"status": "no_workflow_running"}

        return {
            "workflow_id": self.current_state.workflow_id,
            "current_step": self.current_state.current_step,
            "completed_steps": [
                step_id
                for step_id, result in self.current_state.step_results.items()
                if result.status == StepStatus.COMPLETED
            ],
            "iteration_count": self.current_state.iteration_count,
            "completed": self.current_state.completed,
        }


def create_story_project(
    story_id: str,
    premise: str,
    genre: str,
    output_dir: str = "output",
    llm_callback: Optional[Callable[[str], str]] = None,
) -> WorkflowRunner:
    """
    Convenience function to create a new story project and start the workflow.

    Args:
        story_id: Unique identifier for this story
        premise: The story premise/logline
        genre: Primary genre
        output_dir: Where to save outputs
        llm_callback: Optional LLM callback function

    Returns:
        Initialized WorkflowRunner ready to execute
    """
    runner = WorkflowRunner(
        story_id=story_id,
        output_dir=output_dir,
        llm_callback=llm_callback,
    )

    # Store initial inputs
    initial_inputs = {
        "premise": premise,
        "genre": genre,
        "story_id": story_id,
    }

    # Save initial inputs
    inputs_path = Path(output_dir) / story_id / "inputs.json"
    inputs_path.parent.mkdir(parents=True, exist_ok=True)
    with open(inputs_path, "w") as f:
        json.dump(initial_inputs, f, indent=2)

    return runner


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run narrative development workflows")
    parser.add_argument("action", choices=["new", "run", "status", "list"])
    parser.add_argument("--story-id", "-s", help="Story project ID")
    parser.add_argument("--premise", "-p", help="Story premise")
    parser.add_argument("--genre", "-g", help="Story genre")
    parser.add_argument("--workflow", "-w", help="Workflow ID to run")
    parser.add_argument("--output", "-o", default="output", help="Output directory")

    args = parser.parse_args()

    if args.action == "list":
        runner = WorkflowRunner(story_id="temp", output_dir=args.output)
        print("\nAvailable Workflows:")
        for wf in runner.list_workflows():
            print(f"  {wf['id']}: {wf['name']}")
            print(f"      {wf['description']}")

    elif args.action == "new":
        if not all([args.story_id, args.premise, args.genre]):
            print("Error: --story-id, --premise, and --genre required for 'new'")
        else:
            runner = create_story_project(
                story_id=args.story_id,
                premise=args.premise,
                genre=args.genre,
                output_dir=args.output,
            )
            print(f"Created story project: {args.story_id}")
            print(f"Run workflows with: python workflow_runner.py run -s {args.story_id} -w NA-01")

    elif args.action == "run":
        if not all([args.story_id, args.workflow]):
            print("Error: --story-id and --workflow required for 'run'")
        else:
            runner = WorkflowRunner(story_id=args.story_id, output_dir=args.output)

            # Load existing inputs
            inputs_path = Path(args.output) / args.story_id / "inputs.json"
            if inputs_path.exists():
                with open(inputs_path) as f:
                    inputs = json.load(f)
            else:
                inputs = {}

            state = runner.run_workflow(args.workflow, inputs)
            print(f"\nWorkflow status: {'COMPLETE' if state.completed else 'IN PROGRESS'}")

    elif args.action == "status":
        if not args.story_id:
            print("Error: --story-id required for 'status'")
        else:
            state_path = Path(args.output) / args.story_id / "workflow_state.json"
            if state_path.exists():
                with open(state_path) as f:
                    state = json.load(f)
                print(f"\nStory: {args.story_id}")
                print(f"Workflow: {state['workflow_id']}")
                print(f"Current step: {state['current_step']}")
                print(f"Completed: {state['completed']}")
            else:
                print(f"No workflow state found for story: {args.story_id}")
