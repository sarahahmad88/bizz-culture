"""Streamlit UI only. Agent prompts, state transitions and scoring live elsewhere."""
import json
import os
from pathlib import Path
from statistics import mean

import streamlit as st
from config import CAVEAT, LEVELS, MAX_RESPONSE_CHARS, MODEL
from diagnostics import describe_error
from knowledge import all_knowledge, retrieve_context
from schemas import Setup
from storage import export_data, save_completed
from workflow import new_attempt, prepare_response, commit_response, complete_attempt, retry_attempt
from agents import conversation, evaluation

st.set_page_config(page_title="Culture Coach", page_icon="✳️", layout="wide")
st.markdown("<style>" + Path(__file__).with_name("styles.css").read_text() + "</style>", unsafe_allow_html=True)
for name, default in [("history", []), ("attempt", None), ("save_history", True), ("show_alternative", True)]:
    if name not in st.session_state:
        st.session_state[name] = default


def secret(name, default=""):
    try:
        return str(st.secrets.get(name, os.environ.get(name, default)))
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return os.environ.get(name, default)


with st.sidebar:
    st.markdown("## ✳ Culture Coach")
    page = st.radio("Navigation", ["Dashboard", "Start training", "Progress", "Learn", "Settings"], key="navigation")
    mode = st.radio("New attempt mode", ["Demo", "Live Groq"])
    with st.expander("Groq connection"):
        key_input = st.text_input("Groq API key", type="password", help="Leave empty to use a configured server key.")
        if secret("GROQ_API_KEY"):
            st.caption("Server key configured. Its value is never sent to this field.")
    key = key_input.strip() or secret("GROQ_API_KEY")
    model = secret("GROQ_MODEL", MODEL)
    st.caption("2 agents · no web-search API · session-only history")
    st.caption("Changing mode applies to new attempts. Existing attempts keep their mode.")


def error(exc):
    st.error(describe_error(exc, key))


def go_training():
    st.session_state.navigation = "Start training"


def generate_scenario(attempt):
    attempt["status"] = "generation_failed"  # retryable if the network or validation fails
    if attempt["mode"] == "Live Groq" and not key:
        raise ValueError("Add your Groq key in the sidebar before starting Live mode.")
    from llm_client import request_counter
    with st.status("Working now: Scenario & Conversation Agent · preparing your scenario", expanded=True) as status:
        generated = conversation.generate(Setup(**attempt["setup"]), attempt["knowledge"], attempt["mode"], key, model,
                                          request_counter(attempt, "scenario"))
        attempt["scenario"] = generated.model_dump()
        attempt["status"] = "ready"
        status.update(label="Scenario ready", state="complete", expanded=False)


def render_scorecard(attempt):
    result = attempt["result"]
    data = attempt["knowledge"]["dimensions"]
    if attempt["mode"] == "Demo":
        st.warning("Scripted demo: all ratings are fixed at 3/5. These numbers do not evaluate your writing.")
    st.subheader("Your practice scorecard")
    c1, c2, c3 = st.columns(3)
    c1.metric("Overall practice score", f"{result['overall']}/100" if result["overall"] is not None else "Not enough evidence")
    c2.metric("Scoring coverage", f"{result['coverage']:.0%}")
    c3.metric("Groq requests used", attempt["calls"])
    st.write(result["summary"])
    for dim, info in data.items():
        value = result["dimensions"].get(dim)
        if dim not in result["dimensions"]:
            st.caption(f"{info['label']}: N/A — not relevant to this scenario")
        elif value is None:
            st.caption(f"{info['label']}: Not enough evidence")
        else:
            st.progress(value / 5, text=f"{info['label']}: {value:.1f}/5")
    st.markdown("### Feedback on each response")
    for row in result["responses"]:
        label = f"{row['score']}/100" if row["score"] is not None else "Not enough evidence"
        with st.expander(f"Response {row['turn']} · {label}", expanded=row["turn"] == 1):
            st.markdown("**Your response**")
            st.write(attempt["turns"][row["turn"] - 1]["user"])
            for rating in row["ratings"]:
                value = f"{rating['score']}/5" if rating["score"] is not None else "Not enough evidence"
                st.write(f"{data[rating['dimension']]['label']}: {value}")
                if rating["evidence"]:
                    st.text("Evidence: “" + rating["evidence"] + "”")
                st.write(rating["reason"])
            st.write("**Strength:** " + row["strength"])
            st.write("**Try refining:** " + row["improvement"])
            if st.session_state.show_alternative:
                st.info("One possible alternative: " + row["alternative"])
            if row["uncertainty"]:
                st.caption(row["uncertainty"])
    st.info("Next practice: " + result["next_step"])
    st.caption(CAVEAT)
    previous = next((x for x in st.session_state.history if x["id"] == attempt["parent_id"]), None)
    if previous and previous["result"]["overall"] is not None and result["overall"] is not None:
        delta = result["overall"] - previous["result"]["overall"]
        st.write(f"Same-scenario retry: {delta:+d} points compared with your previous attempt.")
    st.download_button("Download this attempt", export_data([attempt]),
                       "culture-coach-attempt.json", "application/json", key="attempt_export")
    if st.button("Try the same scenario again", type="primary"):
        st.session_state.attempt = retry_attempt(attempt)
        st.rerun()


def show_attempt(attempt):
    setup = attempt["setup"]
    template = attempt["knowledge"]["template"]
    st.caption(f"{attempt['mode']} · {setup['my_culture']} → {setup['other_culture']} · {setup['level']} · {attempt['rounds']} rounds")
    st.write("**Goal:** " + template["goal"])
    if attempt["status"] == "generation_failed":
        st.warning("Scenario generation did not finish. Your setup is preserved.")
        if st.button("Retry scenario generation"):
            try:
                generate_scenario(attempt)
                st.rerun()
            except Exception as exc:
                error(exc)
        return
    if attempt["status"] == "completed":
        render_scorecard(attempt)
        return
    if attempt["status"] == "incomplete":
        st.warning("This attempt ended early and has no completed performance score.")
        st.download_button("Export unfinished attempt", export_data([attempt]), "unfinished-attempt.json", "application/json")
        return
    if attempt["status"] == "ready":
        st.subheader("Your communication challenge")
        st.write(attempt["scenario"]["brief"])
        st.info(template["preferences"])
        st.caption("Relevant lenses: " + ", ".join(attempt["knowledge"]["dimensions"][d]["label"] for d in template["relevant"]))
        st.caption(attempt["knowledge"]["review_status"])
        if st.button("Begin conversation", type="primary"):
            attempt["status"] = "conversing"
            st.rerun()
        return
    st.progress(len(attempt["turns"]) / attempt["rounds"],
                text=f"{len(attempt['turns'])} of {attempt['rounds']} responses completed")
    st.caption("Scores and personalized feedback arrive after the final response.")
    with st.chat_message("assistant"):
        st.write("**" + attempt["scenario"]["character"] + "**")
        st.write(attempt["scenario"]["opening"])
    for turn in attempt["turns"]:
        with st.chat_message("user"):
            st.write(turn["user"])
        if turn["ai"]:
            with st.chat_message("assistant"):
                st.write(turn["ai"])
    if attempt["status"] == "awaiting_evaluation":
        st.success("Conversation complete. One evaluation call will review all of your responses.")
        if st.button("Get my response scores", type="primary"):
            try:
                if attempt["mode"] == "Live Groq" and not key:
                    raise ValueError("Add a Groq API key in the sidebar to evaluate this attempt.")
                with st.status("Working now: Evaluation & Feedback Agent · reviewing every response") as status:
                    review = evaluation.evaluate(attempt, key, model)
                    complete_attempt(attempt, review)
                    if st.session_state.save_history:
                        st.session_state.history = save_completed(st.session_state.history, attempt)
                    status.update(label="Your feedback is ready", state="complete")
                st.rerun()
            except Exception as exc:
                error(exc)
        return
    level = setup["level"]
    if level != "Advanced":
        with st.expander("Practice hint" if level == "Beginner" else "Optional prompt"):
            st.write("Think about your goal, the other person's stated concern, and one constructive next step. Respectful disagreement is welcome.")
    with st.form("reply_" + attempt["id"] + "_" + str(len(attempt["turns"]))):
        text = st.text_area("Your response", max_chars=MAX_RESPONSE_CHARS, height=100)
        submitted = st.form_submit_button("Send response", type="primary")
    if submitted:
        try:
            text = prepare_response(attempt, text)
            reply = ""
            if len(attempt["turns"]) + 1 < attempt["rounds"]:
                if attempt["mode"] == "Live Groq" and not key:
                    raise ValueError("Add your Groq API key to continue this Live attempt.")
                with st.status("Working now: Scenario & Conversation Agent · replying"):
                    reply = conversation.respond(attempt, text, key, model).message
            commit_response(attempt, text, reply)
            st.rerun()
        except Exception as exc:
            error(exc)
    if st.button("End attempt early"):
        attempt["status"] = "incomplete"
        st.rerun()


if page == "Dashboard":
    st.markdown('<div class="eyebrow">PRACTICE ACROSS PERSPECTIVES</div>', unsafe_allow_html=True)
    st.title("Build confidence\nacross cultures.")
    st.write("Practice a real conversation. Understand your response. Try a better next step.")
    st.button("Start training ↗", type="primary", on_click=go_training)
    st.info("Choose Start training in the sidebar to begin. Demo is scripted and free of API calls; Live Groq gives personalized feedback.")
    live = [a for a in st.session_state.history if a["mode"] == "Live Groq"]
    scores = [a["result"]["overall"] for a in live if a["result"]["overall"] is not None]
    c1, c2, c3 = st.columns(3)
    c1.metric("Live attempts completed", len(live))
    c2.metric("Average live practice score", f"{mean(scores):.0f}/100" if scores else "—")
    c3.metric("Agents", "2")
    if st.session_state.attempt:
        st.write("Your current attempt is available under Start training.")
    else:
        st.markdown("### Your next conversation starts here.")
        st.write("Try raising a deadline concern, or agreeing on a shared project plan.")
    st.caption(CAVEAT)

elif page == "Start training":
    st.title("Your practice studio")
    if st.session_state.attempt:
        if st.button("Set up a new attempt"):
            st.session_state.attempt = None
            st.rerun()
        show_attempt(st.session_state.attempt)
    else:
        data = all_knowledge()
        template_id = st.selectbox("Situation", list(data["templates"]), format_func=lambda k: data["templates"][k]["name"])
        template = data["templates"][template_id]
        with st.form("setup"):
            c1, c2 = st.columns(2)
            my_culture = c1.text_input("My cultural context", "Pakistan", max_chars=60)
            other_culture = c2.text_input("Other person's cultural context", "Japan", max_chars=60)
            st.text_input("Context / setting", template["context"], disabled=True)
            c1, c2 = st.columns(2)
            c1.text_input("My role", template["my_role"], disabled=True)
            c2.text_input("Other person's role", template["other_role"], disabled=True)
            st.text_area("Communication goal", template["goal"], disabled=True, height=85)
            level = st.selectbox("Experience level", list(LEVELS))
            st.caption("Beginner: 3 rounds · Intermediate: 8 rounds · Advanced: 15 rounds. Roles and goals stay fixed to the selected rubric.")
            st.caption(CAVEAT)
            start = st.form_submit_button("Create my scenario", type="primary")
        if start:
            try:
                setup = Setup(my_culture=my_culture.strip(), other_culture=other_culture.strip(), template=template_id, level=level)
                if mode == "Live Groq" and not key:
                    raise ValueError("Add your Groq API key in the sidebar or use Demo mode.")
                knowledge = retrieve_context(setup)
                # A local template is the recoverable placeholder if live generation fails.
                attempt = new_attempt(setup, mode, conversation.generate(setup, knowledge, "Demo"), knowledge)
                st.session_state.attempt = attempt
                generate_scenario(attempt)
                st.rerun()
            except Exception as exc:
                error(exc)

elif page == "Progress":
    st.title("Your learning journey")
    st.caption("History is isolated to this browser session. Download it before closing or restarting the app.")
    history_mode = st.selectbox("Attempt type", ["Live Groq", "Demo"])
    history = [a for a in st.session_state.history if a["mode"] == history_mode]
    if not history:
        st.info("No completed attempts yet. Finish a conversation to see your feedback here.")
    else:
        for attempt in history:
            label = attempt["knowledge"]["template"]["name"] + " · " + attempt["setup"]["level"] + " · " + attempt["created"][:16]
            with st.expander(label):
                result = attempt["result"]
                st.write("Practice score: " + (str(result["overall"]) + "/100" if result["overall"] is not None else "Not enough evidence"))
                st.write(result["summary"])
                st.write("Attempt ID: " + attempt["id"])
        # Plot only comparable attempts, keeping demo separate from live.
        if len(history) >= 2:
            group = st.selectbox("Comparable practice", sorted({(a["setup"]["template"], a["setup"]["level"]) for a in history}))
            comparable = [a for a in reversed(history) if (a["setup"]["template"], a["setup"]["level"]) == group and a["result"]["overall"] is not None]
            if len(comparable) >= 2:
                st.line_chart({"Practice score": [a["result"]["overall"] for a in comparable]})
                st.caption("Comparable scenario/level only; AI interpretation can vary. These scores do not prove real-world skill improvement.")
            else:
                st.info("Complete another comparable scored attempt before drawing a trend.")
        else:
            st.info("One attempt is not enough to show a trend.")
    st.download_button("Download session history", export_data(st.session_state.history), "culture-coach-history.json", "application/json")

elif page == "Learn":
    st.title("A little context. A better conversation.")
    data = all_knowledge()
    st.caption(CAVEAT)
    for dim in data["dimensions"].values():
        with st.container(border=True):
            st.subheader(dim["label"])
            st.write(dim["lesson"])
    st.link_button("Read about Hofstede's six dimensions", data["source"])
    st.caption("Practice criteria and lessons are draft teaching examples. No national score database is bundled.")

else:
    st.title("Settings & privacy")
    st.toggle("Keep completed attempts in this browser session", key="save_history")
    st.toggle("Show suggested alternative responses", key="show_alternative")
    st.write("Live mode sends the setup, fictional scenario and your conversation to Groq. Demo mode sends nothing to an AI provider. There are no accounts, analytics, shared history database or local transcript files.")
    st.write("Turning history off stops future completed attempts being added. The active attempt remains until you clear it. Existing session history remains until you delete it. Exports contain private conversation text unless you choose the summary-only export.")
    st.download_button("Export score summaries", export_data(st.session_state.history, False), "culture-coach-summaries.json", "application/json")
    st.caption("Summary exports omit raw turns and per-response reviews, but generated summaries may still contain personal information.")
    if st.button("Delete active attempt and session history"):
        st.session_state.attempt = None
        st.session_state.history = []
        st.success("Your active attempt and this session's history were cleared. Previously downloaded files are unchanged.")
    st.caption("Server keys fund all viewers' calls. Keep owner-key deployments private. This starter has no global spending limit or authentication.")

st.caption("Culture Coach · Practice, reflect, try again. · Your culture is context, not a score.")
