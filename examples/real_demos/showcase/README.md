# Evolution Showcase Snapshots

This folder stores the before and after snapshots generated from the real demo flow.

## Snapshot Pairs

- `agent.before.md` / `agent.after.md`
- `user.before.md` / `user.after.md`
- `skills.before.md` / `skills.after.md`

## What The Snapshots Should Tell

- `agent.*`: the runtime identity became more specific after real work
- `user.*`: the user profile became more concrete after live interaction
- `skills.*`: repeated work became a reusable asset instead of disappearing into logs

## Refresh

```bash
python scripts/run_real_demos.py
```

If the resulting snapshots no longer tell a clear before and after story, the product narrative probably needs attention before release.
