# Validate Test Coverage Command

Launch the test-coverage-validator agent to verify that the CLAUDE.md analysis matches the actual test implementation.

Usage: `/validate-coverage <test-suite-folder>`

Examples:
- `/validate-coverage TS_STCA-041`
- `/validate-coverage TS_MSAW-025`

The agent will:
1. Read the CLAUDE.md file in the specified test suite folder
2. Analyze all test XML files
3. Verify coverage claims, false positives, and gaps
4. Produce a comprehensive validation report

You are now launching the test-coverage-validator agent with the test suite folder: {{arg1}}

Use the Task tool with subagent_type="general-purpose" to launch the test-coverage-validator agent.

Pass the following prompt to the agent:

"You are the test-coverage-validator agent. Validate the test coverage analysis for the test suite in folder: {{arg1}}

Follow the validation process defined in .claude/agents/test-coverage-validator.md:

1. Read /Users/pierrelammers/Desktop/evaluation/{{arg1}}/CLAUDE.md
2. Extract all conditions, coverage claims, false positive claims, and gap claims
3. Read all test XML files in the test suite
4. Validate each claim against actual test implementation
5. Look for undocumented issues
6. Produce a comprehensive validation report

Be thorough, precise, and cite specific line numbers as evidence."
