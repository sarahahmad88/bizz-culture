# Beginner guide: GitHub website → Streamlit

You do not need to install Python, a terminal, or any development tools on your computer.

## 1. Download and extract

Download `culture-coach.zip`. Unzip it with your computer's built-in extraction feature. Open the `culture-coach` folder inside it. This folder contains the complete project.

## 2. Create a GitHub repository

Sign in at https://github.com. Click **+ → New repository**. Name it `culture-coach`. Choose **Private**, add a README if needed, and create the repository. This is a new training app; use a separate repository from Research Pop.

## 3. Upload the files

Choose **Add file → Upload files**. Drag the contents of the extracted `culture-coach` folder into GitHub, including the `agents`, `data` and `tests` folders. Upload the files, not the ZIP and not the enclosing folder. Commit to `main`.

Check that `app.py`, `requirements.txt`, `config.py`, `schemas.py`, `knowledge.py`, `workflow.py`, `scoring.py`, `storage.py`, `llm_client.py`, `diagnostics.py`, and `styles.css` appear at the repository root. The two agent files belong inside `agents/` and the knowledge JSON belongs inside `data/`.

If hidden folders do not upload, choose **Add file → Create new file**, enter `.streamlit/config.toml` as the filename, paste the supplied file's contents, and commit. Add `.gitignore` the same way if needed. Never create a GitHub file containing a real API key.

## 4. Create the Streamlit app

Visit https://share.streamlit.io and sign in with GitHub. Authorize the new private repository. Click **Create app** and choose your existing repository:

- Repository: `your-username/culture-coach`
- Branch: `main`
- Main file: `app.py`

In **Advanced settings**, select **Python 3.12**. Click **Deploy**. Streamlit installs the packages on its server. CrewAI has many dependencies even though this app uses only two agents, so the first installation can take time.

## 5. Try the demo first

Leave the mode set to **Demo**. Choose **Start training**, keep Beginner, and click **Create my scenario**. Read the brief and click **Begin conversation**. Enter three responses. Click **Get my response scores**.

The demo makes no AI calls. It uses scripted replies and fixed 3/5 ratings to demonstrate the interface. Its 60/100 score does not evaluate your writing. Demo scores are separated from live scores in Progress.

## 6. Add Groq for real feedback

Create a Groq key at https://console.groq.com/keys. In Streamlit, open the app's **Settings → Secrets** and paste:

```toml
GROQ_API_KEY = "your-real-key"
GROQ_MODEL = "openai/gpt-oss-120b"
```

Save the secrets and restart the app if necessary. You may instead enter your own key in the sidebar's **Groq connection** password field. Server keys are never prefilled into the browser.

Choose **Live Groq** in the sidebar, then start a new attempt. A completed Beginner attempt normally uses four Groq requests: scenario/opening, two partner replies, and one batch evaluation. Intermediate normally uses nine; Advanced normally uses sixteen. The final learner response does not need another partner reply.

No Gemini key, search key, vector database, OpenAI key, or additional tool subscription is required. Groq's normal inference quotas and charges apply.

## 7. Save your work

Results and history are held only in the current Streamlit session. Use **Download this attempt** or **Download session history** before closing the app. The app does not provide accounts, persistent cloud storage or import/restore. An exported JSON file can be opened in a text editor for your records.

The **Keep completed attempts** setting controls future history entries. Your active attempt stays available even with history off. The delete button clears the active attempt and current session's history. Previously downloaded files remain on your computer.

## 8. Fix common problems

| Problem | What to do |
|---|---|
| No module / installation failure | Confirm Python 3.12, exact requirements and the root folder layout; check Manage app → logs. |
| Missing Groq key | Add it in Streamlit Secrets or the sidebar; start Live mode only after adding a key. |
| 401/403 | Check the key and model permissions. |
| 429 | Check Groq's quota/rate-limit dashboard and wait for quota reset or update the account plan. Repeated retries will not create more quota. |
| 400 | Check `GROQ_MODEL`; use the default GPT-OSS model, which supports strict JSON schemas and low reasoning effort. |
| Timeout / invalid evaluation | Your existing turns are preserved. Retry the failed action manually. Retries can consume additional quota. |
| A response has no score | The evaluator found insufficient evidence for its relevant dimensions. N/A is different from zero. |
| Request budget reached | Three manual retries beyond the normal attempt budget are allowed. Export your work and start a new attempt if necessary. |
| History disappeared | Streamlit sessions are temporary; use downloaded exports for your records. |

## 9. Change the app later

Edit the appropriate file using GitHub's pencil button and commit. Change dialogue in `agents/conversation.py`, evaluation instructions in `agents/evaluation.py`, practice criteria and lessons in `data/knowledge.json`, arithmetic in `scoring.py`, and interface wording in `app.py`. Streamlit redeploys changes.

Keep owner-key deployments private, since viewers use the owner's quota. This simple starter has no authentication or global spending cap.
