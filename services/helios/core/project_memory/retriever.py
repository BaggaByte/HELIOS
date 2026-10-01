from helios.core.project_memory.store import get_project_context


def build_memory_context_prompt(project_id: str) -> str:
    """
    Builds a text prompt containing the current project memory context
    to be injected into the ChatEngine's system prompt.
    """
    ctx = get_project_context(project_id)

    prompt = "### PROJECT MEMORY CONTEXT ###\n"
    prompt += f"Summary: {ctx['summary']}\n\n"

    if ctx["known_technologies"]:
        techs = ", ".join(list(ctx["known_technologies"]))
        prompt += f"Known Technologies: {techs}\n\n"

    if ctx["completed_actions"]:
        prompt += "Completed Actions:\n"
        for action in ctx["completed_actions"]:
            prompt += f"- {action}\n"
        prompt += "\n"

    if ctx["key_findings"]:
        prompt += "Key Findings So Far:\n"
        for finding in ctx["key_findings"]:
            prompt += f"- {finding}\n"
        prompt += "\n"

    prompt += (
        "Use this context to avoid repeating actions and to inform your analysis.\n"
    )
    prompt += "##############################\n"

    return prompt
