# Simplification decisions

1. Two agents replace the earlier five-agent proposal. Scenario generation and role-play share one agent; behavior analysis, dimension mapping and coaching share the second. Retrieval, arithmetic, state and history are ordinary Python functions.
2. Use the Groq SDK through CrewAI BaseLLM instead of LiteLLM. This makes the one-call budget explicit and avoids leaking the earlier `cache_breakpoint` metadata to Groq. Strict JSON schemas are validated locally without automatic LLM repairs.
3. Evaluate after the conversation, with one review per learner response. The final learner response skips an unnecessary partner reply. Normal first-attempt budgets are rounds + 1; retries of an existing scenario save its generation call.
4. Scores are provisional practice feedback using scenario-specific Hofstede lenses. No cultural/nationality score difference is used. The visual example's 2/3/4/2/3 would yield 56/100, not 78/100; code calculates the result.
5. Country context labels are self-described. Individual character preferences are explicitly fictional and are not inferred from a country label. There is no verified country-score dataset in this starter.
6. Two fixed scenario/role/goal combinations limit unreviewed scenario invention and keep the files manageable. Different experience levels change dialogue complexity/guidance and turn counts; all levels remain selectable without artificial unlocking.
7. Demo mode uses fixed scores and scripted replies, clearly labeled. It is an interface test, not a hidden keyword evaluator. Demo history is separated from live history.
8. Session-only history plus export is the intentionally simple storage option. Durable accounts/database, automatic progression, broad scenario authoring, imports, instructor review workflows and enterprise features are outside this version. The UI and deployment guide disclose these limits.
9. The UI remains in one file with small functions. Agent files contain no Streamlit code, and the scoring service has no provider dependency. This keeps common fixes localized.
