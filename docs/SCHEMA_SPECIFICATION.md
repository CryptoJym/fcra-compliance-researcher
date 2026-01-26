## Data Contract: FCRA Compliance Matrix (Schema v1)

This repository produces and updates jurisdiction files that conform to the upstream schema located at `upstream/fcra-compliance-matrix/schema/v1.json`.
For CRA-only work, the canonical JSON schema lives at `schema/cra-matrix.schema.json`.

### Required Top-Level Structure
- `schema_version`: "v1"
- `metadata`: object
  - `jurisdiction_type`: one of [federal, state, county, city, industry]
  - `jurisdiction_code`: string (for `industry`, must be in [financial_services, government_contractor, education, healthcare, transportation])
  - `jurisdiction_name`: string
  - `last_updated`: ISO 8601 string
  - optional: `description`, `schema_version`
- `ban_the_box`: object
  - `applies`: boolean
  - `scope`: {private_employers?, public_employers?, contractors?}
  - `thresholds`: {min_employees?, min_contract_value?}
  - `timing`: {stage: one of [application, interview, conditional_offer], exceptions?: string[]}
  - `notes`?: string
- `criminal_history`: object
  - `restrictions`:
    - `arrests`: one of [never_report, case_by_case, report_anytime, unknown]
    - `convictions`: {lookback_years?, salary_exception?, types_excluded?: string[]}
  - `required_assessments`: {individualized?, factors?: string[], written_required?}
  - `notes`?: string
- `notice_requirements`: object
  - `job_postings`: {fair_chance_language?: boolean, required_text?: string}
  - `pre_adverse`: {required?: boolean, days_to_respond?: number|null, must_include?: string[]}
  - `final_adverse`: {required?: boolean, must_include?: string[]}
- `other_restrictions`: object (free-form)
- `enforcement`: {agency?: string, penalties?: object, private_right_of_action?: boolean|null, notes?: string}
- `citations`: {laws?: string[], regulations?: string[], cases?: string[], notes?: string}
- `preemptions`: {preempted_by?: string[], preempts?: string[], notes?: string}

### Patch Contract (what our agents produce)
- We generate a conservative JSON patch fragment that:
  - Includes `schema_version: "v1"` (stamped by extraction).
  - Fills missing/empty fields only; never overwrites non-empty existing values.
  - Respects enum values as defined by the schema (see “Enums”).

### Merge Rules
- `tools/apply_research_patch.py` applies patches with a merge strategy:
  - If destination field is missing or empty, it is populated from the patch.
  - If destination field is non-empty, it is left as-is (no overwrite).
  - Arrays are appended uniquely where applicable; scalar conflicts are resolved by keeping the existing value.

### Enums
- Enums are discovered automatically from `schema/v1.json` (when available) or via `SCHEMA_ENUMS_PATH` override.
- Key enum paths include:
  - `metadata.jurisdiction_type`: [federal, state, county, city, industry]
  - `ban_the_box.timing.stage`: [application, interview, conditional_offer]
  - `criminal_history.restrictions.arrests`: [never_report, case_by_case, report_anytime, unknown]

### Provenance
- Each synthesized claim should be traceable to at least one source with:
  - `source_url`: canonical URL (prefer official .gov or authority sites)
  - `snippet`: short excerpt where the claim is supported
  - `citation_type`: law|regulation|case|guidance
  - `confidence`: float (0–1)
- Provenance records are persisted in the vector DB (Qdrant when enabled) and optionally attached to the patch metadata.

### Typical Sources (search templates reference)
- Federal/state/city/county code and administrative code portals (e.g., “code of ordinances”, “administrative code”).
- Human rights/civil rights agencies (e.g., NYC Commission on Human Rights, state civil rights departments).
- Labor and employment departments; official guidance PDFs.
- Case law repositories (citations only, no full text unless public domain).

### Example Minimal Patch
```json
{
  "schema_version": "v1",
  "metadata": {
    "jurisdiction_type": "city",
    "jurisdiction_name": "San Francisco",
    "jurisdiction_code": "san_francisco",
    "last_updated": "2025-08-13T00:00:00Z"
  },
  "ban_the_box": {
    "applies": true,
    "timing": { "stage": "conditional_offer" }
  },
  "citations": { "laws": ["SF Police Code Art. 49"] }
}
```

