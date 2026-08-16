def test_ingest_captions(client):
    payload = {
        "captions": [
            {"text": "Newton observed that an apple falls directly towards the center of the Earth.", "start": 0.0, "end": 5.2},
            {"text": "Gravity is the fundamental force pulling masses towards each other.", "start": 5.2, "end": 10.5},
            {"text": "Without gravity, the Moon would drift away into deep outer space.", "start": 10.5, "end": 15.8}
        ],
        "language": "en"
    }
    response = client.post("/api/v1/videos/video-0/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "video-0"
    assert data["chunks_created"] >= 1

def test_semantic_search(client):
    payload = {
        "query": "apple falling gravity force",
        "top_k": 3
    }
    response = client.post("/api/v1/videos/video-0/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "video-0"
    assert isinstance(data["results"], list)
    if data["results"]:
        assert "start_time" in data["results"][0]
        assert "similarity" in data["results"][0]

def test_rag_qa(client):
    payload = {
        "question": "What keeps the Moon in orbit around the Earth?",
        "session_id": "test-session-rag"
    }
    response = client.post("/api/v1/videos/video-0/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert data["video_id"] == "video-0"

def test_dubbing_generation(client):
    payload = {
        "language": "es",
        "voice_gender": "female"
    }
    response = client.post("/api/v1/videos/video-0/dub", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "video-0"
    assert data["language"] == "es"
    assert data["status"] == "completed"

def test_get_dubbed_track(client):
    response = client.get("/api/v1/videos/video-0/dub/es")
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "video-0"
    assert data["language"] == "es"
    assert "segments" in data

def test_agent_chat_search_intent(client):
    response = client.post("/api/v1/videos/video-0/agent-chat", json={
        "message": "Where in the video does it talk about the Moon and gravity?",
        "session_id": "agent-session-1"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["type"] in ["search", "qa", "chat"]

def test_agent_chat_dub_intent(client):
    response = client.post("/api/v1/videos/video-0/agent-chat", json={
        "message": "Please generate a french voice dub audio track for this video",
        "session_id": "agent-session-2"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["type"] in ["dubbing", "chat", "qa"]
