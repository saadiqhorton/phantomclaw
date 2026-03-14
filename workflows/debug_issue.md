# Debug Issue

## Objective

Debug problems systematically using root cause analysis, not guessing.

## Inputs

- Bug description or error message
- Steps to reproduce
- Relevant logs/traces

## Steps

### Phase 1: Research & Reproduce (MANDATORY FIRST)

**Before attempting ANY fix:**

1. **Gather full context**
   - Read error messages completely (don't skip)
   - Get full stack traces
   - Note exact line numbers and file paths

2. **Reproduce consistently**
   - Can you trigger it reliably?
   - What are the exact steps?
   - If not reproducible → gather more data first

3. **Check recent changes**
   - Git diff to see what changed
   - New dependencies or config changes?

4. **Research with Context7**
   - Use `query-docs` to understand the library/API involved
   - Look up error patterns if external

### Phase 2: Root Cause Investigation

5. **Gather evidence**
   - Add diagnostic logging
   - Check each component boundary
   - Verify data flow

6. **Trace to root cause**
   - Where does the bad value originate?
   - What called this with bad value?
   - Keep tracing until source found
   - Fix at source, not symptom

### Phase 3: Hypothesis & Test

7. **Form single hypothesis**
   - "I think X is the root cause because Y"
   - Write it down explicitly

8. **Test minimally**
   - Make smallest change to test hypothesis
   - One variable at a time

9. **Verify before continuing**
   - Did it work? → Phase 4
   - Didn't work? → Form NEW hypothesis
   - Don't add more fixes on top

### Phase 4: Fix & Verify

10. **Create failing test**
    - Write test reproducing the bug
    - Must fail before fix

11. **Implement fix**
    - Fix the root cause identified
    - One change at a time

12. **Verify fix**
    - Test passes now?
    - No other tests broken?
    - Original symptom resolved?

13. **Cleanup workspace**
    - Remove any debug logging added
    - Delete temporary test files
    - Clean up `.tmp/` if used
    - Verify no loose files left behind
    - Run `git status` to verify clean state

14. **If 3+ fixes attempted**
    - STOP and question the architecture
    - Discuss with user before continuing

## Outputs

- Root cause identified
- Failing test case
- Fix verified
- No regressions
- Clean workspace (no trash files)

## Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Can't reproduce | Gather more data, don't guess |
| Multiple symptoms | Fix one at a time, verify each |
| 3+ fixes failed | Question architecture, discuss with user |
| Truly environmental | Document findings, implement handling |
| Error unclear | Use Context7 to research the error |
| Debug files created | Clean up before marking complete |

## File Organization

| File Type | Location |
|-----------|----------|
| Debug/logging code | Remove after fix |
| Temporary test files | Delete after verification |
| Research notes | Discard after use |
| `.tmp/` files | Clean after use |

## Systematic Debugging Principles

- **NO FIXES WITHOUT ROOT CAUSE** - Find the why before fixing
- **One hypothesis at a time** - Don't shotgun fix
- **Evidence before claims** - Verify before saying fixed
- **Minimal changes** - Don't over-engineer
