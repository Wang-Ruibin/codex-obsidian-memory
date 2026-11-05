Run the monthly health audit for the configured Obsidian memory vault.

Follow the vault's AGENTS.md and use the resolved paths supplied below, including custom layouts. Cover the four separate areas for knowledge, projects, reusable experience and conversations. Find duplicated facts, stale claims, conflicts, broken links, orphan nodes, duplicate project homes, duplicate branch identities and project-index drift in non-hidden Markdown notes. Resolve only issues supported by clear evidence. Mark uncertain conflicts for review.

Check GitHub projects by exact github_repo, local projects by registered project_id, and branches by case-sensitive working_branch. Respect exclusions and disabled local registrations; do not infer local identities or current work from names, body text or a default branch. Conversation checks are limited to structural frontmatter, conversation_id uniqueness, index membership and links. Do not read or summarize conversation bodies, access chat databases or transcripts, enable memory, or change title synchronization or consent settings.

Also review the shared experience index for duplicate topics, missing links, outdated applicability and source/branch mismatches. Check whether source repositories are now excluded and whether verification dates still support the claims. Recommend re-verification or retirement; never invent verification results or refresh a verification date merely because this audit ran.

In the configured report, update only the `updated` frontmatter date and latest-audit section with the month, scope, evidence-backed repairs, unresolved conflicts, archive recommendations and graph statistics. Any repairs to other notes must stay within the audit's scope and have clear evidence. Update the maintenance note only when this audit produces a durable maintenance conclusion. Replace the previous audit instead of appending a transcript.

Use the supplied current vault validator and its pre-audit results, not an old .automation/validate_graph.py. Verify project-home and branch-page counts, exact identities, local registrations, reusable-lesson provenance, conversation structure, broken links and orphan nodes before finishing. The runner repeats validation before marking the period complete.

Never delete, move or archive a file automatically; recommendations are labels only. Avoid adding pages solely to improve graph appearance. Give a visible, file-by-file knowledge-base writeback review in the configured language and follow the vault's completion rules. Never store credentials.
