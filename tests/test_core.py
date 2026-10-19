import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents import conversation, evaluation
from config import LEVELS
from diagnostics import describe_error
from knowledge import retrieve_context
from schemas import Setup, Reply, Evaluation, ResponseReview, Rating
from scoring import normalized_score, score_evaluation
from storage import export_data, save_completed
from workflow import new_attempt, prepare_response, commit_response, complete_attempt, retry_attempt


def make_attempt(level="Beginner", mode="Demo"):
    setup = Setup(my_culture="Pakistan", other_culture="Japan", template="deadline", level=level)
    knowledge = retrieve_context(setup)
    return new_attempt(setup, mode, conversation.generate(setup, knowledge, "Demo"), knowledge)


def finish_turns(attempt):
    for i in range(attempt["rounds"]):
        commit_response(attempt, f"I understand the goal. Could we review testing option {i+1}?",
                        "Please explain your proposed next step." if i + 1 < attempt["rounds"] else "")


class FakeGroq:
    def __init__(self, attempt):
        self.attempt = attempt
        self.requests = []
        self.chat = SimpleNamespace(completions=self)

    def create(self, **kwargs):
        self.requests.append(kwargs)
        name = kwargs["response_format"]["json_schema"]["name"]
        if name == "Scenario":
            value = self.attempt["scenario"]
        elif name == "Reply":
            value = {"message": "Thank you. What testing option would you recommend?"}
        else:
            value = evaluation.evaluate({**self.attempt, "mode": "Demo"}).model_dump()
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(value)))])

    def close(self):
        pass


class CoreTests(unittest.TestCase):
    def test_normalization_retains_zero_excludes_null(self):
        self.assertEqual(normalized_score([2, 3, 4, 2, 3]), 56)
        self.assertEqual(normalized_score([0, None, 5]), 50)
        self.assertEqual(normalized_score([0]), 0)
        self.assertIsNone(normalized_score([None, None]))
        with self.assertRaises(ValueError):
            normalized_score([6])

    def test_exact_round_limits(self):
        for level, rounds in LEVELS.items():
            attempt = make_attempt(level)
            finish_turns(attempt)
            self.assertEqual(len(attempt["turns"]), rounds)
            self.assertEqual(attempt["status"], "awaiting_evaluation")
            with self.assertRaises(ValueError):
                commit_response(attempt, "duplicate final", "reply")

    def test_empty_and_failed_reply_do_not_advance(self):
        attempt = make_attempt()
        for text, reply in [("  ", "hello"), ("A reasonable concern", "")]:
            with self.assertRaises(ValueError):
                commit_response(attempt, text, reply)
        self.assertEqual(attempt["turns"], [])

    def test_schema_and_evidence_validation(self):
        attempt = make_attempt()
        finish_turns(attempt)
        valid = evaluation.evaluate(attempt)
        self.assertEqual(score_evaluation(attempt, valid)["overall"], 60)
        broken = valid.model_copy(deep=True)
        broken.responses[0].ratings[0].evidence = "A quote that never appeared"
        with self.assertRaises(ValueError):
            score_evaluation(attempt, broken)
        broken = valid.model_copy(deep=True)
        broken.responses[0].ratings[0].dimension = "indulgence"
        with self.assertRaises(ValueError):
            score_evaluation(attempt, broken)
        broken = valid.model_copy(deep=True)
        broken.responses.pop()
        with self.assertRaises(ValueError):
            score_evaluation(attempt, broken)

    def test_insufficient_evidence_is_not_a_zero(self):
        attempt = make_attempt()
        finish_turns(attempt)
        review = evaluation.evaluate(attempt)
        for row in review.responses:
            for rating in row.ratings:
                rating.score = None
                rating.evidence = ""
        result = score_evaluation(attempt, review)
        self.assertIsNone(result["overall"])
        self.assertTrue(all(row["score"] is None for row in result["responses"]))
        self.assertEqual(result["coverage"], 0)

    def test_retry_has_new_id_and_frozen_knowledge(self):
        attempt = make_attempt()
        finish_turns(attempt)
        complete_attempt(attempt, evaluation.evaluate(attempt))
        retry = retry_attempt(attempt)
        self.assertNotEqual(retry["id"], attempt["id"])
        self.assertEqual(retry["parent_id"], attempt["id"])
        self.assertEqual(retry["scenario"], attempt["scenario"])
        self.assertEqual(retry["knowledge"], attempt["knowledge"])
        retry["knowledge"]["template"]["goal"] = "modified"
        self.assertNotEqual(retry["knowledge"], attempt["knowledge"])
        self.assertEqual(retry["turns"], [])

    def test_history_is_copied_and_upserted(self):
        attempt = make_attempt()
        with self.assertRaises(ValueError):
            save_completed([], attempt)
        finish_turns(attempt)
        complete_attempt(attempt, evaluation.evaluate(attempt))
        history = save_completed([], attempt)
        self.assertEqual(len(save_completed(history, attempt)), 1)
        attempt["turns"][0]["user"] = "changed"
        self.assertNotEqual(history[0]["turns"], attempt["turns"])
        payload = json.loads(export_data(history, False))
        self.assertEqual(payload["attempts"][0]["turns"], [])
        self.assertEqual(payload["attempts"][0]["result"]["responses"], [])

    def test_actual_crewai_execution_call_counts_all_levels(self):
        # Real CrewAI execution; only Groq network boundary is replaced.
        from llm_client import request_counter
        for level, rounds in LEVELS.items():
            attempt = make_attempt(level, "Live Groq")
            client = FakeGroq(attempt)
            with patch("llm_client.Groq", return_value=client):
                conversation.generate(Setup(**attempt["setup"]), attempt["knowledge"], "Live Groq", "fake",
                                      on_request=request_counter(attempt, "scenario"))
                for i in range(rounds):
                    text = prepare_response(attempt, f"Could we review testing option {i+1} together?")
                    reply = conversation.respond(attempt, text, "fake").message if i + 1 < rounds else ""
                    commit_response(attempt, text, reply)
                complete_attempt(attempt, evaluation.evaluate(attempt, "fake"))
            self.assertEqual(len(client.requests), rounds + 1)
            self.assertEqual(attempt["calls"], rounds + 1)
            self.assertEqual(attempt["status"], "completed")
            self.assertEqual(len(attempt["result"]["responses"]), rounds)
            for request in client.requests:
                self.assertNotIn("tools", request)
                self.assertTrue(request["response_format"]["json_schema"]["strict"])
                self.assertTrue(all(set(m) == {"role", "content"} for m in request["messages"]))

    def test_groq_marker_cleanup_and_second_call_guard(self):
        from llm_client import OneCallGroq
        client = FakeGroq(make_attempt())
        adapter = OneCallGroq("fake", Reply, client=client)
        messages = [{"role": "system", "content": "Hi", "cache_breakpoint": True}]
        adapter.call(messages)
        self.assertEqual(client.requests[0]["messages"][0], {"role": "system", "content": "Hi"})
        self.assertTrue(messages[0]["cache_breakpoint"])
        with self.assertRaises(RuntimeError):
            adapter.call(messages)
        self.assertEqual(len(client.requests), 1)

    def test_real_sdk_serializes_expected_request(self):
        import httpx
        from groq import Groq
        from llm_client import OneCallGroq
        bodies = []
        def handler(request):
            bodies.append(json.loads(request.content))
            return httpx.Response(200, json={"id": "test", "created": 0,
                "model": "openai/gpt-oss-120b", "object": "chat.completion",
                "choices": [{"index": 0, "finish_reason": "stop", "message": {
                    "role": "assistant", "content": '{"message":"Could we discuss the options?"}'}}]})
        with Groq(api_key="fake", max_retries=0,
                  http_client=httpx.Client(transport=httpx.MockTransport(handler))) as client:
            adapter = OneCallGroq("fake", Reply, client=client)
            adapter.call([{"role": "user", "content": "Let's discuss the plan", "cache_breakpoint": True}])
        self.assertEqual(len(bodies), 1)
        self.assertEqual(bodies[0]["response_format"]["type"], "json_schema")
        self.assertNotIn("cache_breakpoint", bodies[0]["messages"][0])
        self.assertEqual(adapter.output.message, "Could we discuss the options?")

    def test_failed_request_preserves_turn_and_counts_attempt(self):
        attempt = make_attempt(mode="Live Groq")
        with patch("llm_client.Groq", return_value=FakeGroq(attempt)) as constructor:
            constructor.return_value.create = lambda **kwargs: (_ for _ in ()).throw(RuntimeError("Temporary failure"))
            with self.assertRaises(Exception):
                conversation.respond(attempt, "Can we discuss the risk?", "fake")
        self.assertEqual(attempt["turns"], [])
        self.assertEqual(attempt["calls"], 1)

    def test_budget_stops_before_request(self):
        from llm_client import request_counter
        attempt = make_attempt(mode="Live Groq")
        attempt["calls"] = attempt["rounds"] + 4
        with self.assertRaises(RuntimeError):
            request_counter(attempt, "evaluation")()
        self.assertEqual(attempt["calls"], attempt["rounds"] + 4)

    def test_errors_redact_credentials_and_explain_quota(self):
        self.assertNotIn("gsk_secret", describe_error(RuntimeError("bad gsk_secret"), "gsk_secret"))
        exc = RuntimeError("sensitive body")
        exc.status_code = 429
        self.assertIn("429", describe_error(exc))
        self.assertNotIn("sensitive body", describe_error(exc))


if __name__ == "__main__":
    unittest.main()
