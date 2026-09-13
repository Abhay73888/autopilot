# Permanent Agent Constraint: Comments Always Enabled

## Invariant Rule
The user has established a permanent, non-negotiable directive:
- **Under no circumstances should the comment section of any video be disabled or turned off.**
- All uploads to YouTube must have:
  - `status.selfDeclaredMadeForKids: false`
  - `status.privacyStatus: "public"`
  - `commentThreads` enabled and tested.
- If any script, agent, or pipeline attempts to disable comments or set `selfDeclaredMadeForKids = True`, it must fail with an assertion error.
