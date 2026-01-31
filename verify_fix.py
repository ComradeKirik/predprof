import DBoperations
import sys

# Mock or setup necessary context if needed, but DBoperations seems standalone enough 
# with its own connection logic.

try:
    print("Attempting to recalculate score for contest 1...")
    result = DBoperations.recalculateUsersScore(1)
    print(f"Result: {result}")
    print("Success! No TypeError.")
except TypeError as e:
    print(f"FAILED with TypeError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FAILED with Exception: {e}")
    # Don't exit 1 if it's just 'Contest not existing' or logical error, 
    # we only care about TypeError crashing it.
