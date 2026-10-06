"""Import explicitly selected legacy skill JSONL; never scan user homes automatically.

Layer: adapters
Context: context
Owns: importing one explicitly selected legacy skill JSONL file
Does not own: the CLI argv and store construction (entry/composition)
Entry points: import_file, main
Contracts: INV-SKILL-IMPORT-001
Moved the previous implementation (behaviour unchanged unless noted).

The previous implementation `main()` (argparse, `PostgresStore(database_url())`, `FileArtifacts`) is entry/composition
work and moves to `entry.cli` / `composition` (keeps the `-m` form if pinned); this
module keeps the injected-store functions only.
"""
from pathlib import Path

from codex_harness.context.application.skill_import import SkillImport
from codex_harness.context.domain.skills.import_ import MAX_INPUT_BYTES, source_document, validate_source
from codex_harness.kernel.errors import require
from codex_harness.kernel.ids import canonical


def import_file(path, project, source, store, artifacts):
    validate_source(source)
    require(Path(path).is_file(), 'Import source must be a regular file')
    with Path(path).open('rb') as stream:
        data = stream.read(MAX_INPUT_BYTES + 1)
    require(len(data) <= MAX_INPUT_BYTES, 'Import exceeds byte limit')
    receipt = artifacts.put(canonical(source_document(data, source)), 'legacy-skill-jsonl')
    return SkillImport(store).ingest(project, source, data, receipt['ref'])
