# Build Feature / Script / Automation

## Objective

Build new features, scripts, or automations using a consistent, research-driven approach with TDD and Context7 MCP.

## Inputs

- Feature requirement or user story
- Existing codebase context
- Target library/API (if applicable)

## Steps

### Phase 1: Research (MANDATORY FIRST)

**Before writing ANY code:**

1. **Understand the requirement**
   - What exactly needs to be built?
   - What are the success criteria?
   - What are the constraints?

2. **Research with Context7**
   - Use `resolve-library-id` to find relevant library
   - Use `query-docs` to get current patterns and examples
   - Look for existing similar code in the codebase

3. **Check existing tools**
   - Look in `tools/` for existing utilities
   - Check if similar functionality exists

4. **Validate approach**
   - Confirm the research supports your approach
   - Get user confirmation before proceeding

### Phase 2: Test-Driven Development

5. **Write failing test (RED)**
   - Write one minimal test showing desired behavior
   - Must fail because feature doesn't exist yet
   - Use real code, not mocks

6. **Verify RED**
   - Run test, confirm it fails for expected reason
   - Don't proceed until test fails correctly

7. **Write minimal code (GREEN)**
   - Write simplest code to pass the test
   - No extra features, no "while I'm here" improvements

8. **Verify GREEN**
   - Run test, confirm it passes
   - Confirm no other tests broken

### Phase 3: Refactor, Verify & Clean

9. **Refactor** (if needed)
   - Clean up duplication
   - Improve names
   - Keep tests green

10. **Final verification**
    - Run full test suite
    - Verify no regressions

11. **Cleanup workspace**
    - Delete any temporary test files not needed
    - Remove debug print statements added during development
    - Clean up any files in `.tmp/` created during research
    - Ensure no loose/untracked files left behind
    - Run `git status` to verify clean state

## Outputs

- Working feature/script/automation
- Test(s) proving behavior
- No regressions
- Clean workspace (no trash files)

## Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Research reveals complexity | Discuss with user before proceeding |
| No existing tests | Create test file, follow TDD anyway |
| External API changes | Re-run Context7 research if errors occur |
| User changes requirements mid-build | Return to Phase 1 |
| 3+ fixes attempted | Question architecture, discuss with user |
| Temporary files created | Clean up before marking complete |

## File Organization

| File Type | Location |
|-----------|----------|
| Production code | `tools/` or project structure |
| Test files | Alongside code (e.g., `test_*.py`, `*_test.py`) |
| Temporary files | `.tmp/` (cleaned after use) |
| Research notes | Discard after use, don't save |
