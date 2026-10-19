# Culture Coach · simple two-agent training app

Start with [DEPLOY.md](DEPLOY.md) for browser-only GitHub upload and Streamlit deployment. Run Demo first, then add one Groq API key for actual response analysis.

## What is included

- Two agent modules: Scenario & Conversation, and Evaluation & Feedback.
- Hofstede-informed, scenario-specific response ratings (0–5), calculated response scores (0–100), exact evidence and feedback.
- Exactly 3/8/15 learner responses by level. One setup call, one partner call for each non-final response, and one evaluation call. Successful first attempts use 4/9/16 provider requests; exact-scenario retries reuse the brief and save one request. No hidden planning, repair calls, automatic retries or web searches.
- Two fictional scenario templates: a workplace deadline concern and a university project plan.
- Dashboard, setup, scenario brief, conversation, scorecard, progress, lessons and privacy settings.
- A scripted demo with no network calls, distinct from Live Groq mode.
- Session-isolated history, exact-scenario retries, downloadable JSON and deletion controls.

## Module map

| File | Change here when… |
|---|---|
| `app.py` | Changing screens, buttons or UI text |
| `agents/conversation.py` | Changing scenario/role-play behavior |
| `agents/evaluation.py` | Changing evaluator instructions or demo feedback |
| `llm_client.py` | Changing provider integration or single-call enforcement |
| `schemas.py` | Changing structured agent output contracts |
| `data/knowledge.json` | Changing teaching examples, criteria or micro-lessons |
| `knowledge.py` | Changing deterministic context/rubric retrieval tools |
| `scoring.py` | Changing evidence checks, weighting or arithmetic |
| `workflow.py` | Changing attempt states or round control |
| `storage.py` | Changing session history/export behavior |
| `config.py` | Changing levels, default model or caveat |
| `diagnostics.py` | Changing safe error messages |
| `styles.css`, `.streamlit/config.toml` | Changing visual styling |
| `tests/test_core.py`, `tests/test_ui.py` | Checking behavior after changes |

## How the two agents work

CrewAI `Agent.execute_task` handles each small action with a custom `BaseLLM` adapter calling the Groq SDK. The adapter permits one provider request per action, validates Groq's strict JSON output with Pydantic, and gives CrewAI a final-answer wrapper. It uses no LiteLLM dependency or provider-routing prefix. Only standard role/content messages reach Groq, preventing the earlier internal cache-marker problem. Agent delegation, planning and automatic retries are disabled.

The agents use ordinary server-side Python retrieval tools (`retrieve_context`, `get_attempt_context`, `get_rubric`). These are called explicitly before generation/evaluation, with results passed to the agent. They are not autonomously selected LLM function calls. This deliberately saves tool-selection/follow-up calls and keeps approved context under code control. Scoring and storage are also plain Python.

The active scenario's knowledge/rubric is snapshotted once. Evaluation analyzes every learner response in the full conversation in a single batch. Each scored dimension needs an exact substring from that learner turn. Unknown dimensions, duplicate/missing turn IDs and unsupported evidence fail validation. No extra LLM call repairs them; the user can retry manually.

## Scoring and limitations

For each response, average its valid dimension ratings and divide by five to produce a 0–100 score. Null ratings are excluded; zero is retained. For the overall attempt, average available ratings within each relevant dimension and normalize the equally weighted dimension means. Python calculates every displayed number. No numerical overall score is shown without evidence. Learner response ratings themselves remain AI judgments, not deterministic measures.

These are **draft practice rubrics**, not a validated cultural assessment. Cultural context is represented by explicit fictional role preferences and relevant Hofstede lenses, not nationality-based scoring. There is no verified national-score dataset in the attachments or this bundle; country scores are never invented. The selected culture labels are included in the context, but do not determine the counterpart's personality or a learner's score. A cultural/domain expert should review the examples before using them for formal training research.

Demo ratings are all 3/5, regardless of wording; the UI says so. They preview the scorecard only. Live mode is required for personalized judgments.

## Scope choices

To keep the code simple, the app supports two preset context/role/goal combinations rather than every possible scenario. Culture labels are editable. Level recommendations/unlocking, authentication, persistent storage, import, instructor dashboards, voice and automated certification are not implemented. Levels are selectable. Dashboard/progress show real session data, with demo separated from live; no example history is seeded. A same-scenario retry keeps comparable rules and gets a new attempt ID.

The app holds data only in the current browser session. It does not write conversations to server files, and has no analytics. It does send live prompts/transcripts to Groq. Keep exported files private. Keep deployments using owner keys private or remove the server key and have users supply their own. This starter is not a large public service with user billing, authentication or abuse controls.

## References checked

- CrewAI agents and `execute_task`/custom LLM implementation: https://docs.crewai.com/en/concepts/agents and https://docs.crewai.com/en/learn/custom-llm
- Groq strict JSON schema support: https://console.groq.com/docs/structured-outputs
- GPT-OSS model: https://console.groq.com/docs/model/openai/gpt-oss-120b
- Hofstede framework and limits of interpreting national tendencies: https://geerthofstede.com/culture-geert-hofstede-gert-jan-hofstede/6d-model-of-national-culture/

See [VALIDATION.md](VALIDATION.md) for the checks actually run. No real API keys are included.
