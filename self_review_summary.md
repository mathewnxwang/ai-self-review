# Performance Self-Review Summary (2025)

## api-placement-service

- **Built a full offline/online evaluation + replay toolkit for placement AI (dozens of PRs):** delivered classifier/supervised/submissions/task-management/context/retrieval eval harnesses, standardized ground-truth objects, added `make` commands + Datadog-friendly logging, and introduced a robust replay script (single email, by placement, optional state persistence, config flow, DB rewind safety). **Accelerated experimentation/debugging while reducing risk of regressions via unit tests.**

- **Shipped a follow-up automation capability from prototype to “prod-ready” daily script:** implemented follow-up detection + Outlook draft generation, added timing gates (placement stage / days-to-expiration / days-since-contact), ignored GPT emails, added ERU-specific config, and iterated on prompt/content quality (salutation/signature, randomized body format). **Improved follow-up decision accuracy from ~50% → 94% on the eval set (16/17 correct) and enabled safe daily runs via draft-only controls.**

- **Significantly improved context management/retrieval quality and scalability for LLM tools:** introduced context management + eval for recall/precision tradeoffs; added LLM-based relevancy filtering, moved from email-level to **conversation/thread-level** grouping, always included most recent conversations, decomposed filtering into batched LLM calls to handle arbitrarily large histories, and added “compress irrelevant threads into summaries” fallback. **Turned on retrieval filtering for large placements (>100 emails; ~15% of tool calls) to reduce context dilution while preserving recall.**

- **Delivered Dynamic Context / “dynamic chat” backend foundation used by FE/operator workflows:** created a context generation tool that runs on every inbound email and stores query outputs; added a backend endpoint for FE, query schema updates (multi-phase), guards, repository/test refactors, and **citations** support to point users to where answers came from. **Optimized runtime/cost by batching query LLM calls when context is small (<100k tokens), covering >90% of placements.**

- **Modernized placement stage/progress modeling and reliability:** improved placement stage extraction used by downstream tools/UI (“pizza tracker”), fixed prod errors (bad/None stage values), and executed a multi-step migration from `placement_steps_status` → **`placement_stage`** (schema + inbound-email population + backfill). **Reduced ambiguity and simplified downstream logic.**

- **Raised overall system robustness and developer/operator safety:** fixed multiple production-impacting bugs (attachments `content_type=None`, reply-all, email lookup, DB write/rewind issues), improved logging, sped up replay backup/restore from **>20s to near-instant** by scoping to relevant tables, and added strict email-send gating (draft-only + handling-mode enum + comprehensive unit tests) after real-world mis-send risk surfaced.

## benji

- **Built a unified, scalable evaluation platform for Benji** by consolidating retrieval + generation evals into the orchestration service / `make run_eval` flow, adding FastAPI endpoints for deployment evals, and eliminating legacy notebook + Arize paths—reducing manual steps and making evals repeatable and easier to run across environments.  
- **Expanded evaluation coverage and decision-making signal** by adding automated metric tables for retrieval recall/threshold curves (incl. expanded char thresholds to 40k), citation quality, answer correctness, question-understanding, context-size, and cost/latency (“perf”)—enabling faster experiment iteration without bespoke analysis.  
- **Automated operational workflows for non-engineering stakeholders** by generating deployment-eval grading templates directly from eval runs, removing manual copy/paste and streamlining servicing-team review and rollout readiness.  
- **Delivered major retrieval quality improvements and experimentation capabilities** including dynamic character-based retrieval thresholds, context newline trimming, retrieval cleanup, and shipping a Cohere reranker stage (feature-flagged) with supporting config abstractions (`RetrievalConfig`) and added reranking unit tests.  
- **Modernized the production Slack architecture toward a PipelineManager-based design** by migrating Slack message handling (pre/process/post + formatting) into pipelines behind feature flags, adding Slack pipeline unit tests, and aligning eval execution to the same pipeline abstractions to prevent drift between “eval” and “prod” behavior.  
- **Improved reliability and correctness across Slack + Mobile** by fixing long-conversation handling (and JSON serialization bug), DM-specific PipelineManager issues, Slack API client regressions, mobile eval runs/distribution-type handling, and tenant-data correctness—reducing staging/prod breakages and improving response fidelity (e.g., preserving original questions in chat history).  
- **Strengthened data/ingestion and developer tooling** by preventing Pinecone ingestion failures via guaranteed max chunk sizing (with new ChunkingService unit tests), adding schema support (e.g., document type field), improving local/staging Pinecone targeting via dynamic `vectorstore_config`, increasing embeddings timeouts for high-concurrency evals, and adding Benji-specific make commands to speed up passing CI/quality checks.

## document-extraction

- **Built and shipped the Total Rewards (TR) AI document extraction pipeline inside the existing Document Extraction service**, delivering end-to-end scaffolding (pipelines + FastAPI support + eval harness) to consolidate extraction projects, reduce service sprawl/maintenance, and enable TR engineers/stakeholders to collaborate in a shared codebase.

- **Enabled scalable, spec-driven extraction by dynamically generating extraction schemas from source-of-truth data**, including JSON-based spec generation, coverage/document-type parameterization, typed spec/property modeling, and support for more complex plan structures (e.g., **2-tier in-/out-of-network for medical + dental** and a dedicated **network_structure** field).

- **Improved data quality and downstream usability by enforcing typed outputs and stronger validation**, moving from free-form strings to **type-aware extraction (USD/percent/frequency/units)**, adding “not found”/omit behaviors, consolidating type validation across pipelines, and hardening ancillary-text handling—reducing noisy/incorrect outputs and aligning results with Salesforce/consumer requirements.

- **Operationalized evaluation and ground-truth workflows to accelerate iteration and stakeholder input**, adding synthetic eval scaffolding, an interactive eval CLI, “pipeline output only” mode for ad-hoc testing, caching fixes keyed by plan/document type, and automated ground-truth/spec refreshes (first via Google Sheets, then **querying Snowflake** for faster, more robust updates).

- **Increased extraction robustness and reliability through targeted OCR/LLM improvements**, including prompt upgrades, spammy-log reduction, always-on local OCR logging, and a critical **fallback from LLM OCR to pdfplumber** to mitigate missing/omitted SBC pages discovered during UAT (preventing production-impacting failures from unsafe-content misclassification).

- **Drove measurable model-quality gains and consistency improvements via experimentation and metrics**, running/maintaining eval suites and experiments (e.g., LLM call decomposition; page targeting; employee-perspective percentage direction), and delivering a **consistency improvement from 75% → 100%** by introducing a comparison LLM call—while monitoring recall/TP accuracy and preventing regressions.

- **Demonstrated strong ownership and production support**, rapidly addressing UAT/production issues (type bugs, unit/frequency fixes, enum cleanup/removal, validation retries, model/provider investigation with rollback when Bedrock/Anthropic support blocked deployment) and adding unit tests/README/process cleanup to keep the system maintainable as scope expanded.

## platform

- **Improved determinism and output consistency for LLM workflows** by explicitly disabling sorting for Benji LLM fields across *all* execution modes (streaming, Slack, and local eval), preventing unintended reordering and making results more reproducible and comparable.  
- **Increased reliability of TR extraction/OCR in production-like scenarios** by adding a **pdfplumber fallback** when the LLM OCR response fails (e.g., due to OpenAI “unsafe content” false positives), preventing full-page omissions (notably first-page drops on SBC documents).  
- **Delivered measurable quality gains** by validating the OCR fallback via eval runs and confirming **improved metrics over baseline**, reducing extraction regressions discovered during UAT.  
- **Strengthened platform process and governance** by setting up a **TR contract review project**, establishing clearer contract ownership/review workflows to improve correctness, reduce integration risk, and support scaling across teams.  
- **Demonstrated cross-team collaboration and iteration based on feedback** by rapidly addressing UAT-discovered issues and incorporating peer input (e.g., leveraging @bsgilber’s fallback idea) to harden the platform’s document extraction pipeline.

## tr-contract-review

- Updated and clarified the **tr-contract-review** project README (May 2025), improving onboarding and day-to-day usability by documenting project purpose, setup/usage, and expected workflows for reviewers/contributors.  
- Strengthened **process consistency** by codifying guidance in a single source of truth, reducing ambiguity and churn during contract review work (fewer back-and-forth questions and quicker ramp-up for new engineers).  
- Improved **maintainability and team alignment** by ensuring documentation stayed current with the project’s state, helping cross-functional partners (e.g., legal/compliance/engineering) reference the same procedures and expectations.

