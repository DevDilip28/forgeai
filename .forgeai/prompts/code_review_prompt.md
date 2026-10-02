# FORGEAI CODE REVIEW PROTOCOL

Review the provided code for correctness, maintainability, security, and performance.

## Review Criteria

### 1. Correctness

Check for:

- Bugs
- Incorrect logic
- Missing edge cases
- Incorrect API usage
- Runtime errors

### 2. Architecture

Check:

- Separation of responsibilities
- SOLID principles
- DRY violations
- Unnecessary coupling
- Maintainability

### 3. Type Safety

Check:

- Missing type hints
- Incorrect types
- Excessive use of `Any`
- Unsafe type assumptions

### 4. Error Handling

Check:

- Missing error handling
- Bare `except`
- Silent failures
- Poor error messages
- Incorrect exception handling

### 5. Security

Check:

- Input validation
- Secret exposure
- Unsafe file operations
- Command injection risks
- Authentication/authorization issues

### 6. Performance

Check:

- Unnecessary computation
- Repeated I/O
- Inefficient algorithms
- Excessive API calls
- Unnecessary memory usage

## Output Format

### Critical Issues

Issues that should be fixed before considering the code complete.

### Improvements

Non-critical improvements that would improve quality.

### Good Practices

Things that are already implemented correctly.

### Refactored Snippet

If useful, provide an improved code snippet.

## Code to Review

{code}
