import asyncio
from app.core.execution_context import ExecutionContext, ExecutionGuardException

def test_guard():
    print("Testing Execution Guard Logic...")
    
    # 1. New ID
    try:
        ExecutionContext.validate_request("exec-1", "Prompt A")
        print("PASS: First request allowed")
    except Exception as e:
        print(f"FAIL: First request blocked: {e}")

    # 2. Same Prompt (Loop)
    try:
        ExecutionContext.validate_request("exec-1", "Prompt A")
        print("FAIL: Loop not detected")
    except ExecutionGuardException as e:
        if e.code == "LOOP_DETECTED":
            print("PASS: Loop detected")
        else:
            print(f"FAIL: Wrong error code: {e.code}")

    # 3. Step Limit
    try:
        for i in range(15):
            ExecutionContext.validate_request("exec-1", f"Prompt {i}")
    except ExecutionGuardException as e:
        if e.code == "MAX_STEPS_EXCEEDED":
            print("PASS: Max Steps Exceeded detected")
        else:
            print(f"FAIL: Unexpected error during step limit test: {e.code}")
    else:
        print("FAIL: Max Steps not enforced")

    print("Test Complete.")

if __name__ == "__main__":
    test_guard()
