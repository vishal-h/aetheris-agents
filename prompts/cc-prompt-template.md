# cc:prompt template

Every cc:prompt opens with these lines, in this order. Definitions of the round
types: `CLAUDE.md`, the ROUND TYPE paragraphs. Held-commit rule: harness
`docs/methodology/milestone-methodology.md` `[R43]`.

    ROUND TYPE: <code | documentation | mechanical>
    REPOS WITH A HELD COMMIT: <none | aetheris | aetheris-agents | both>
    SESSION: <new | current — and, if current, the state it relies on>

Then: the task; the state to verify before any write; the done-checks; what the
review packet must report (repository-qualified SHAs for every held commit).
