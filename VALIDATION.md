# Validation · 2026-10-19

## Completed

- Installed and resolved pinned direct dependencies on Python 3.12.14: CrewAI 1.15.23, Streamlit 1.64.0, Groq 1.7.0 and Pydantic 2.12.5. Direct package requirement checks found no compatibility mismatches.
- Checked official CrewAI custom-LLM/agent documentation and Groq strict-JSON/model documentation. The actual installed CrewAI execution path was exercised, not merely imported.
- Python syntax compilation completed for project modules.
- Fifteen offline tests passed. They cover scoring/null/zero behavior, exact 3/8/15 rounds, empty/failed submissions, evidence and dimension validation, unsupported scoring, retry snapshots, history isolation/export, real CrewAI task execution against a fake Groq boundary, single-call limits, cache-marker stripping, real Groq SDK serialization with a mock HTTP transport, failure state, quota messaging and the Streamlit demo journey.
- The real CrewAI task loop with a mocked Groq client used exactly 4, 9 and 16 provider requests for the three levels. Each learner response received its own review in the batched result. No extra reasoning/repair calls were made by CrewAI.
- Streamlit AppTest exercised Dashboard, Start training, scenario generation/brief, chat, empty input validation, scorecard, retry, Progress, Learn, Settings, missing-key validation, deletion and early exit.
- Started the Streamlit server successfully in the execution environment.

## Not completed

- No real Groq request was made: credentials were not supplied. Actual account access, schema acceptance, model behavior, quota, latency and quality of feedback require a first Live Groq test after deployment.
- Desktop/mobile screenshots and manual keyboard checks were not completed. The environment had no browser executable and the attempted Chromium download returned an invalid archive. Responsive styling, focus styles and reduced-motion rules are implemented, but browser visual verification remains outstanding.
- No Streamlit Community Cloud deployment was performed; the user has a browser-only deployment guide.
- Cultural/domain expert validation is not complete. The teaching examples and anchored practice rubric are draft material, not validated national profiles or psychological measures. No country scores were generated.

## Developer test command

After installing the requirements in a development environment:

```bash
python -m unittest discover -s tests -v
```

The execution environment had SOCKS proxy variables set without a SOCKS support package. Those proxy variables were removed for offline testing only, so fake clients could be constructed normally. This is not required for a normal Streamlit deployment.
