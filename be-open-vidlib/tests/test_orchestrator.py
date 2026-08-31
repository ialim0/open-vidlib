"""Tests for Question Decomposition Orchestrator."""

from unittest.mock import MagicMock, patch
import json
from app.services.orchestrator_service import (
    detect_decomposition,
    compose_sub_answers,
    verify_composite,
    run_orchestrated_agent,
)


def test_detect_decomposition_multipart():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "is_multipart": True,
        "sub_questions": [
            "Where is Newton introduced in the video?",
            "What is Newton's connection to gravity?"
        ]
    })
    mock_response.choices = [mock_choice]
    mock_client.chat.complete.return_value = mock_response

    sub_qs = detect_decomposition(mock_client, "Find where Newton is introduced, then explain his connection to gravity.")
    assert len(sub_qs) == 2
    assert "Newton" in sub_qs[0]


def test_detect_decomposition_single_part():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "is_multipart": False,
        "sub_questions": []
    })
    mock_response.choices = [mock_choice]
    mock_client.chat.complete.return_value = mock_response

    sub_qs = detect_decomposition(mock_client, "What is gravity?")
    assert sub_qs == []


def test_compose_sub_answers():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Sir Isaac Newton is introduced at [00:05] and discovered gravity when seeing an apple fall [00:54]."
    mock_response.choices = [mock_choice]
    mock_client.chat.complete.return_value = mock_response

    sub_questions = ["Where is Newton introduced?", "What is his connection to gravity?"]
    sub_results = [
        {"answer": "Newton is introduced at [00:05] watching an apple fall."},
        {"answer": "He connected it to gravity pulling objects [00:54]."}
    ]
    composed = compose_sub_answers(mock_client, "Find Newton and explain gravity", sub_questions, sub_results)
    assert "[00:05]" in composed
    assert "[00:54]" in composed


def test_verify_composite_success():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "passed": True,
        "citation_valid": True,
        "all_subparts_addressed": True,
        "missing_subparts": [],
        "feedback": "Good answer."
    })
    mock_response.choices = [mock_choice]
    mock_client.chat.complete.return_value = mock_response

    verification = verify_composite(
        mock_client,
        "Find Newton and explain gravity",
        "Newton is introduced at [00:05] and discovered gravity [00:54].",
        ["Where is Newton introduced?", "What is his connection to gravity?"],
        {5, 54}
    )
    assert verification["passed"] is True
    assert verification["citation_valid"] is True


def test_orchestrator_single_part_falls_through(db_session):
    with patch("app.services.orchestrator_service.detect_decomposition", return_value=[]):
        with patch("app.services.orchestrator_service.run_agent_loop") as mock_loop:
            mock_loop.return_value = {
                "type": "qa",
                "answer": "Gravity pulls objects [00:05].",
                "sources": [{"start_time": 5.0, "text": "Gravity"}],
                "tool_call_count": 1,
                "verified": True,
                "degraded": False,
                "trajectory_id": "traj_single_123",
            }
            res = run_orchestrated_agent("What is gravity?", "video-0", db_session)
            assert res["mode"] == "orchestrated"
            assert res["answer"] == "Gravity pulls objects [00:05]."
            mock_loop.assert_called_once()


def test_orchestrator_multipart_dispatch(db_session):
    with patch("app.services.orchestrator_service.detect_decomposition", return_value=["Part 1?", "Part 2?"]):
        with patch("app.services.orchestrator_service.run_agent_loop") as mock_loop:
            mock_loop.side_effect = [
                {
                    "type": "qa",
                    "answer": "Answer 1 at [00:05].",
                    "sources": [{"start_time": 5.0, "text": "Evidence 1"}],
                    "tool_call_count": 1,
                    "verified": True,
                    "degraded": False,
                    "trajectory_id": "traj_part1",
                },
                {
                    "type": "qa",
                    "answer": "Answer 2 at [00:54].",
                    "sources": [{"start_time": 54.0, "text": "Evidence 2"}],
                    "tool_call_count": 2,
                    "verified": True,
                    "degraded": False,
                    "trajectory_id": "traj_part2",
                }
            ]
            with patch("app.services.orchestrator_service.compose_sub_answers", return_value="Composite: Answer 1 [00:05] and Answer 2 [00:54]"):
                with patch("app.services.orchestrator_service.verify_composite", return_value={"passed": True, "citation_valid": True, "all_subparts_addressed": True}):
                    res = run_orchestrated_agent("Multi-part question", "video-0", db_session)
                    assert res["mode"] == "orchestrated"
                    assert res["tool_call_count"] == 3
                    assert res["verified"] is True
                    assert len(res["sources"]) == 2
                    assert "traj_part1" in res["sub_trajectories"]
                    assert "traj_part2" in res["sub_trajectories"]


def test_orchestrator_endpoint_mode(client):
    with patch("app.api.v1.endpoints.mistral_endpoints.run_orchestrated_agent") as mock_orch:
        mock_orch.return_value = {
            "type": "qa",
            "content": "Orchestrated answer [00:05]",
            "answer": "Orchestrated answer [00:05]",
            "sources": [{"start_time": 5.0, "end_time": 54.0, "text": "evidence", "similarity": 1.0}],
            "mode": "orchestrated",
            "tool_call_count": 2,
            "steps": 2,
            "verified": True,
            "degraded": False,
            "trajectory_id": "orch_traj_123",
        }
        res = client.post(
            "/api/v1/videos/video-0/agent-chat?mode=orchestrated",
            json={"message": "Find Newton and explain gravity", "session_id": "test-session"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["mode"] == "orchestrated"
        assert data["trajectory_id"] == "orch_traj_123"
        mock_orch.assert_called_once()
