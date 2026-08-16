def test_get_transcripts_for_video(client):
    response = client.get("/api/v1/transcripts/video/video-0")
    assert response.status_code == 200
    transcripts = response.json()
    assert isinstance(transcripts, list)
    assert len(transcripts) > 0
    assert "full_text" in transcripts[0]
    assert transcripts[0]["language"] in ["en", "fr"]

def test_get_flashcards_for_video(client):
    response = client.get("/api/v1/flashcards/video/video-0")
    assert response.status_code == 200
    flashcards = response.json()
    assert isinstance(flashcards, list)
    assert len(flashcards) > 0
    assert "question" in flashcards[0]
    assert "options" in flashcards[0]
    assert isinstance(flashcards[0]["options"], list)

def test_get_flashcards_by_language(client):
    response = client.get("/api/v1/flashcards/video/video-0?lang=fr")
    assert response.status_code == 200
    flashcards = response.json()
    assert all(fc["language"] == "fr" for fc in flashcards)

def test_chat_with_video(client):
    response = client.post("/api/v1/chat/video/video-0", json={
        "session_id": "test-session-1",
        "message": "What is gravity in simple terms?",
        "language": "en"
    })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "session_id" in data
    assert data["session_id"] == "test-session-1"

def test_get_chat_history(client):
    # After chatting above
    response = client.get("/api/v1/chat/video/video-0/history/test-session-1")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-1"
    assert len(data["messages"]) >= 2
