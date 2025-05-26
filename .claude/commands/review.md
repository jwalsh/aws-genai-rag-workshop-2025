# /review - Workshop Code and Notebook Review

Review Python code and workshop notebooks for quality, completeness, and best practices.

## Usage

```
/review <target> [options]
```

## Targets

### notebook <number>
Review a specific workshop notebook (01-05).

Example:
```
/review notebook 01
/review notebook 02
```

### code <path>
Review Python code in a specific file or directory.

Example:
```
/review code src/rag/pipeline.py
/review code src/agents/
```

### all
Perform a complete workshop review.

Example:
```
/review all
```

## Options

### --focus <area>
Focus the review on specific areas:
- `tangle` - Check org-mode tangle configuration
- `exercises` - Review exercise quality and difficulty
- `aws` - Focus on AWS service integration
- `security` - Security and credentials review
- `performance` - Performance and optimization
- `tests` - Test coverage and quality

Example:
```
/review notebook 01 --focus tangle
/review code src/rag/ --focus performance
```

### --fix
Attempt to fix common issues found during review.

Example:
```
/review notebook 01 --fix
/review code src/ --fix
```

## Review Process

When reviewing notebooks, I will:
1. Check tangle support and file organization
2. Verify code quality and style
3. Ensure progressive learning flow
4. Validate exercises and examples
5. Check AWS integration and costs
6. Verify documentation completeness

When reviewing code, I will:
1. Check PEP 8 compliance
2. Verify type hints and docstrings
3. Review error handling
4. Check AWS best practices
5. Assess test coverage
6. Look for security issues

## Output

The review will provide:
- Summary of findings
- Specific issues with line numbers
- Suggested improvements
- Priority of fixes (High/Medium/Low)
- Optionally, automatic fixes applied

## Examples

### Review Module 1 notebook with tangle focus:
```
/review notebook 01 --focus tangle
```

### Review all RAG code for performance:
```
/review code src/rag/ --focus performance
```

### Complete workshop review:
```
/review all
```

### Review and fix common issues in Module 2:
```
/review notebook 02 --fix
```

## Implementation Details

This command uses the prompts defined in:
- `prompts/notebook-review.txt` - For notebook reviews
- `prompts/python-code-review.txt` - For code reviews
- `prompts/workshop-completeness-check.txt` - For full workshop review

The review process will:
1. Load the appropriate review prompt
2. Analyze the specified files
3. Run linting and tests if applicable
4. Generate a detailed report
5. Optionally apply fixes