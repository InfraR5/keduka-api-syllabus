from fastapi import Request, HTTPException, status
from app.core.execution_context import ExecutionContext, ExecutionGuardException
import json

async def execution_guard(request: Request):
    """
    Dependency/Middleware to guard AI executions.
    Extracts execution_id and prompt to validate against limits.
    """
    exec_id = request.headers.get("X-Execution-ID")
    prompt = ""
    payload = {}

    # Read body safely to extract ID/Prompt if not in headers
    # Note: request.body() caches the result, allowing Pydantic to read it later.
    try:
        body_bytes = await request.body()
        if body_bytes:
            payload = json.loads(body_bytes)
            if not exec_id:
                exec_id = payload.get("execution_id")
            
            # extract prompt/input for hash check
            # Supports 'prompt', 'input', 'objetivo' (from existing schemas)
            prompt = payload.get("prompt") or payload.get("input") or payload.get("objetivo") or ""
    except Exception:
        # If body is not JSON or unreadable, we proceed with limited info
        pass

    # Fallback to query param
    if not exec_id:
        exec_id = request.query_params.get("execution_id")

    # RULE: Block if prompt missing? 
    # User said "Bloquear... prompt repetido". If no prompt, we can't hash.
    # We will hash an empty string if missing, which catches "looping empty calls"
    
    # Validation
    try:
        ExecutionContext.validate_request(exec_id, str(prompt))
    except ExecutionGuardException as e:
        # Log and Block
        print(f"[EXECUTION GUARD] BLOCKED: ID={exec_id} REASON={e.code} MSG={e.message}")
        
        err_status = status.HTTP_429_TOO_MANY_REQUESTS
        if e.code == "MISSING_ID":
            err_status = status.HTTP_400_BAD_REQUEST
            
        raise HTTPException(
            status_code=err_status,
            detail={
                "error": "Execution Blocked",
                "code": e.code,
                "message": e.message
            }
        )

    # Inject context info into request state if needed
    request.state.execution_id = exec_id
    print(f"[EXECUTION GUARD] ALLOWED: ID={exec_id} PromptLen={len(str(prompt))}")
