import json
from types import SimpleNamespace

from app.services import agent_chat_loop


def _message(content=None, tool_calls=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls or [])


def _response(message):
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _call(name, arguments, call_id):
    return SimpleNamespace(id=call_id, function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))


def test_loop_executes_multiple_tools_and_persists_trajectory(monkeypatch, db_session, tmp_path):
    responses = iter([
        _response(_message(tool_calls=[_call("search_video", {"query": "gravity"}, "one"), _call("ask_question", {"question": "What is gravity?"}, "two")])),
        _response(_message("Gravity pulls masses together [00:05].")),
        _response(_message(json.dumps({"passed": True, "citation_valid": True, "addresses_question": True, "feedback": ""}))),
    ])
    fake_client = SimpleNamespace(chat=SimpleNamespace(complete=lambda **kwargs: next(responses)))
    monkeypatch.setattr(agent_chat_loop, "get_mistral_client", lambda: fake_client)
    monkeypatch.setattr(agent_chat_loop.settings, "MISTRAL_API_KEY", "test-key")
    monkeypatch.setattr(agent_chat_loop, "TRAJECTORY_DIR", tmp_path)
    monkeypatch.setattr(agent_chat_loop, "search_video", lambda *args, **kwargs: [{"text": "Gravity", "start_time": 5.0, "end_time": 9.0, "similarity": 1.0}])
    monkeypatch.setattr(agent_chat_loop, "ask_video_question", lambda *args, **kwargs: {"answer": "Gravity [00:05]", "sources": [{"text": "Gravity", "start_time": 5.0, "end_time": 9.0, "similarity": 1.0}], "question": "What is gravity?", "video_id": "video-0"})

    result = agent_chat_loop.run_agent_loop("Find and explain gravity", "video-0", db_session, "loop-test")

    assert result["tool_call_count"] == 2
    assert result["verified"] is True
    trajectory = json.loads(next(tmp_path.glob("*.json")).read_text())
    assert [event["tool"] for event in trajectory["events"] if event["event"] == "tool"] == ["search_video", "ask_question"]


def test_default_and_baseline_modes_remain_callable(client, monkeypatch, tmp_path):
    monkeypatch.setattr(agent_chat_loop, "TRAJECTORY_DIR", tmp_path)
    loop = client.post("/api/v1/videos/video-0/agent-chat", json={"message": "What is gravity?", "session_id": "mode-loop"})
    baseline = client.post("/api/v1/videos/video-0/agent-chat?mode=baseline", json={"message": "What is gravity?", "session_id": "mode-base"})
    assert loop.status_code == baseline.status_code == 200
    assert loop.json()["mode"] == "loop"
    assert loop.json()["trajectory_id"]
    assert baseline.json()["mode"] == "baseline"
