import asyncio
from ..events_listener import monitor_llm_call
from ..events_processor import log_event

def patch_anthropic_client(llm_client, method_path="messages.create"):
    """
    Patches the given LLM client's method_path with our LLM monitoring.
    """
    parts = method_path.split(".")
    target = llm_client
    for part in parts[:-1]:
        target = getattr(target, part)
    method_name = parts[-1]

    original_method = getattr(target, method_name)
    # Decorate with monitor_llm_call from events_listener
    if asyncio.iscoroutinefunction(original_method):
        patched_method = monitor_llm_call(original_method, channel="LLM", is_async=True)
    else:
        patched_method = monitor_llm_call(original_method, channel="LLM", is_async=False)

    setattr(target, method_name, patched_method)
    log_event("LLM_patch", {"method": method_path}, "LLM")