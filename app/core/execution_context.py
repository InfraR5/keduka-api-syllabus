import time
import hashlib
import uuid
from typing import Dict, Set, Optional

# --- CONFIGURATION ---
MAX_STEPS = 10         # Maximum number of steps per execution_id
MAX_TTL = 60.0         # Seconds an execution_id remains valid
MAX_TOKEN_ESTIMATE = 4000 # Rough estimate of max tokens per request

class ExecutionData:
    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.start_time = time.time()
        self.steps = 0
        self.prompt_hashes: Set[str] = set()
        self.is_active = True

class ExecutionGuardException(Exception):
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(self.message)

class ExecutionContext:
    """
    In-Memory Guard for AI Executions.
    Prevents loops, recursion, and excessive usage.
    """
    _executions: Dict[str, ExecutionData] = {}

    @classmethod
    def get_context(cls, execution_id: str) -> ExecutionData:
        # Cleanup expired keys on access (lazy cleanup)
        cls._cleanup()
        
        if execution_id not in cls._executions:
            cls._executions[execution_id] = ExecutionData(execution_id)
        
        return cls._executions[execution_id]

    @classmethod
    def validate_request(cls, execution_id: str, prompt: str):
        """
        Validates the request against safety rules.
        """
        if not execution_id:
            raise ExecutionGuardException("Missing execution_id", "MISSING_ID")

        ctx = cls.get_context(execution_id)
        
        # 1. TTL Check
        elapsed = time.time() - ctx.start_time
        if elapsed > MAX_TTL:
             raise ExecutionGuardException(f"Execution expired (TTL {MAX_TTL}s exceeded)", "TTL_EXCEEDED")

        # 2. Step Limit
        if ctx.steps >= MAX_STEPS:
            raise ExecutionGuardException(f"Step limit reached ({MAX_STEPS})", "MAX_STEPS_EXCEEDED")

        # 3. Recursive/Loop Check (Hash)
        prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
        if prompt_hash in ctx.prompt_hashes:
            raise ExecutionGuardException("Loop detected: Identical prompt repeated", "LOOP_DETECTED")
        
        # 4. Update State
        ctx.steps += 1
        ctx.prompt_hashes.add(prompt_hash)
        
        return True

    @classmethod
    def _cleanup(cls):
        """Remove expired contexts to free memory."""
        now = time.time()
        to_remove = [k for k, v in cls._executions.items() if (now - v.start_time) > MAX_TTL]
        for k in to_remove:
            del cls._executions[k]

    @classmethod
    def reset(cls):
        """Clear all contexts (Testing only)"""
        cls._executions = {}
