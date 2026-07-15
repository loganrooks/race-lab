# Codex cloud environment

Recommended settings for `loganrooks/race-lab`:

- Container image: `universal`
- Container caching: On
- Setup script: Manual — `bash .codex/setup.sh`
- Maintenance script: `bash .codex/maintenance.sh`
- Agent internet access: Off
- Secrets: none by default

Environment variables:

```text
CI=1
PYTHONUNBUFFERED=1
PIP_DISABLE_PIP_VERSION_CHECK=1
```

The setup script installs common review and validation tools, synchronizes
Python and JavaScript dependencies when their manifests exist, and runs the
canonical verification command. The maintenance script only refreshes project
dependencies when a cached container resumes.

Run the same checks locally or in a task with:

```bash
bash scripts/verify.sh
```

Do not add source-data credentials or API secrets merely for ordinary code
review. Create a separate ingestion environment if a future task genuinely
requires external data access.
