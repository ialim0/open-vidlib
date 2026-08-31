def test_list_videos(client):
    response = client.get("/api/v1/videos")
    assert response.status_code == 200
    videos = response.json()
    assert isinstance(videos, list)
    assert len(videos) == 3

def test_filter_videos_by_category(client):
    response = client.get("/api/v1/videos?category=Science")
    assert response.status_code == 200
    videos = response.json()
    assert all(v["category"] == "Science" for v in videos)

def test_get_video_detail(client):
    response = client.get("/api/v1/videos/video-0")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "video-0"
    assert data["category"] == "Science"
    assert "transcripts" in data
    assert "flashcards" in data

def test_get_nonexistent_video(client):
    response = client.get("/api/v1/videos/nonexistent-id")
    assert response.status_code == 404
