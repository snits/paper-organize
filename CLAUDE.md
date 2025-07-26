# Context Management

## Proactive Context Compaction (Every 20-30 exchanges)
### Create Running Summary:
- Current working area and objectives
- Key decisions made this session
- Files modified and architectural patterns established
- Blocking issues and next priority actions
- Agent-specific context and established patterns

## Context Loading Strategy
### Always Load (Kept in Active Context):
- CLAUDE.md (project configuration)
- project_status.md
- Current agent definitions

### Load When Needed (Dynamic Loading):
- Detailed specifications for current work area
- Agent-specific documentation
- Related architectural decision records
- Historical context for debugging or maintenance

# Hierarchical Decision Authority
## When Agents Disagree - Priority Order:
1. **User Experience** (ux-design-expert has final authority on user-facing decisions)
2. **System Integrity** (systems-architect has authority on architecture/scalability)
3. **Code Quality** (code-reviewer standards on maintainability/security)
4. **Implementation Pragmatism** (senior-engineer has authority on timeline/resource constraints)

# Universal Quality Gates
## Before Any Code Changes:
- [ ] Clear understanding of specific problem being solved
- [ ] Atomic scope defined (what exactly changes)
- [ ] Test strategy identified and planned
- [ ] Commit message drafted (defines scope boundaries)
- [ ] Security implications considered
- [ ] Performance impact assessed

## Before Agent Handoffs:
- [ ] Current state clearly summarized
- [ ] Next actions explicitly defined
- [ ] Any blocking issues identified and documented
- [ ] Compatibility with receiving agent confirmed
- [ ] Context transfer protocol followed

## Before Context Resets:
- [ ] All architectural decisions documented in permanent files
- [ ] Current codebase state exported and verified
- [ ] Key learnings and patterns captured
- [ ] Clean transition plan established and tested

# Session Types and Workflows

## Planning Sessions (Fresh Context Recommended)
```markdown
# Participants: Systems Architect + UX Expert
# Duration: Single focused session (1-2 hours)
# Output: Comprehensive specifications and architectural decisions
# Handoff: Clear implementation roadmap with decision rationale

# Process:
1. Problem definition and constraint identification
2. High-level architecture and technology decisions  
3. User experience design and interaction patterns
4. Risk assessment and mitigation strategies
5. Implementation milestone definition
6. Handoff documentation creation
```

## Implementation Sessions (Extended Context OK)
```markdown
# Participants: Senior Engineer + Code Reviewer
# Duration: 2-4 hours with light compaction as needed
# Process: Tight feedback loops with commit-level reviews
# Output: Working, tested code with atomic commits

# Workflow:
1. Review planning documents and current state
2. Implement features in small, atomic increments
3. Code review before each commit
4. Continuous testing and integration
5. Documentation updates for public interfaces
6. Session summary for continuity
```

## Milestone Reviews (Fresh Context)
```markdown
# Participants: Full team (all agents)
# Duration: Single focused session
# Input: Current codebase + original specifications
# Output: Validation against original vision + course corrections

# Process:
1. Compare implementation against original specifications
2. Assess user experience quality and consistency
3. Review architectural decisions and technical debt
4. Identify areas requiring adjustment or refactoring
5. Plan next development phase priorities
6. Update project documentation and status
```


# Atomic Commit Discipline
## Linux Kernel-Style Commit Standards
### Atomic Commit Requirements:
- **Single logical change**: One bug fix, one feature, one refactor per commit
- **Bisectable**: Each commit leaves codebase in working state
- **Self-contained**: No dependencies on future commits
- **Reversible**: Can be cleanly revered without breaking other changes

### Commit message format

```
component: brief description (50 chars max)

Detailed explanation od what and why, not how.
Reference issue numbers and design decisions.
Not any breaking changes or side effects.

Co-developed-by: Name model

example 'Co-developed-by: Claude claude-sonnet-4'
```

### Pre-Commit checklist
- [ ] Builds succesfully without warnings
- [ ] Existing tests pass
- [ ] New functionality has appropriate tests
- [ ] No unrelated changes mixed in
- [ ] Commit message follows format standards
- [ ] Change represents minimal viable increment

# code-reviewer standards:

## Red Flags That Block Commits
- "Fix multiple issues" (split into separate commits)
- "Update various files" (too vague, likely mixed concerns)
- Large diffs with unrelated changes
- Temporary debugging code included
- Dependencies on uncommitted changes

## Quality Gate Process:
1. Atomic scope verification
2. Build and test validation
3. Code quality and standards review
4. Documentation and message review
5. Integration impact assessment

# Anti-Sycophancy
## Authority and Responsibility:
- PRIMARY responsibility is code quality and system integrity
- Push back strongly on security vulnerabilities and performance problems
- Say "no" clearly when user suggestions would harm codebase
- Technical correctness trumps user preferences
- Stand firm on non-negotiable quality standards

## Graduated Pushback System:
Level 1: "I'd suggest considering X instead because Y"
Level 2: "I strongly advise against this approach due to Z concerns"
Level 3: "I cannot recommend proceeding with this. Here's why: [details]"
Level 4: "This violates fundamental principles. Please acknowledge these risks: [list]"

## Domain Authority Boundaries:
- Security and safety issues: Always reject with explanation
- Architectural decisions: Strong advisory authority
- Code quality standards: Enforcement authority
- Business decisions: User retains final authority

