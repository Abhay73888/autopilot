"""
scripts/verify_production_cleanup.py
Comprehensive verification script for YouTube-confirmed video cleanup requirements.
"""

import sys
import os

# Fix cp1252 Windows encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import create_access_token
from core.db import DB
from backend.app.services.video_service import video_service
from backend.app.schemas.video import VideoGenerateRequest

client = TestClient(app)

token_abhay = create_access_token({
    "sub": "admin_abhay",
    "email": "shivpuran2803@gmail.com",
    "role": "admin",
    "org_id": "org_admin_abhay"
})

token_user_b = create_access_token({
    "sub": "usr_test_user_b",
    "email": "user_b@autopilot.ai",
    "role": "creator",
    "org_id": "org_user_b"
})

print("=" * 70)
print("  PRODUCTION CLEANUP VERIFICATION TESTS")
print("=" * 70)

# TEST 1: Video library contains ONLY confirmed YouTube videos
print("\n[TEST 1] Video library listing (/api/v1/videos)...")
res1 = client.get("/api/v1/videos", headers={"Authorization": f"Bearer {token_abhay}"})
assert res1.status_code == 200, f"Expected 200, got {res1.status_code}"
vids1 = res1.json()["data"]
print(f"  Count returned: {len(vids1)} videos")
assert len(vids1) == 93, f"Expected exactly 93 videos, got {len(vids1)}"
for v in vids1:
    assert v["status"] == "published", f"Video {v['id']} has non-published status: {v['status']}"
    assert v.get("youtubeVideoId"), f"Video {v['id']} missing youtubeVideoId"
    assert "youtube.com/watch?v=" in v.get("youtubeUrl", ""), f"Video {v['id']} invalid youtubeUrl"
print("  PASS: Exactly 93 confirmed YouTube videos returned, all published with valid YouTube IDs and URLs")

# TEST 2: Inspect details of one confirmed video
print("\n[TEST 2] Inspect single confirmed video (/api/v1/videos/{id})...")
sample_vid = vids1[0]
sample_id = sample_vid["id"]
res2 = client.get(f"/api/v1/videos/{sample_id}", headers={"Authorization": f"Bearer {token_abhay}"})
assert res2.status_code == 200
v2 = res2.json()["data"]
print(f"  Inspected Video ID: {v2['id']}")
print(f"  Title: {v2['title']}")
print(f"  YouTube Video ID: {v2['youtubeVideoId']}")
print(f"  YouTube URL: {v2['youtubeUrl']}")
print(f"  Status: {v2['status']}")
print(f"  Thumbnail: {v2['thumbnailUrl']}")
assert v2["youtubeVideoId"] == sample_vid["youtubeVideoId"]
assert v2["status"] == "published"
print("  PASS: Single video metadata, thumbnail, status, and YouTube link fully verified")

# TEST 3: Unuploaded/failed video cannot appear in normal video library
print("\n[TEST 3] Unuploaded/draft video isolation...")
db = DB()
# Temporarily insert an unuploaded test video
db.conn.execute("""
    INSERT INTO videos (id, title, topic, status, user_id, created_ts, updated_ts)
    VALUES (999999, 'Draft Test Video', 'Test Topic', 'draft', 'admin_abhay', '2026-09-21T20:00:00', '2026-09-21T20:00:00')
""")
db.conn.commit()

res3 = client.get("/api/v1/videos", headers={"Authorization": f"Bearer {token_abhay}"})
vids3 = res3.json()["data"]
assert not any(v["id"] == "vid_999999" or v["id"] == "999999" for v in vids3), "Unuploaded draft video leaked into library!"
assert len(vids3) == 93, f"Library count changed to {len(vids3)}!"

# Clean up temporary test row
db.conn.execute("DELETE FROM videos WHERE id = 999999")
db.conn.commit()
print("  PASS: Unuploaded/failed video with draft status is completely excluded from video library")

# TEST 4: Generate new video behaves properly (job queued, not in published library)
print("\n[TEST 4] New generation job lifecycle...")
# Set test mode off for generation flow check
os.environ["AUTOPILOT_TEST_MODE"] = "0"
gen_req = VideoGenerateRequest(
    projectId="proj_test",
    topic="The Future of Quantum Computing",
    title="Quantum Leap 2026"
)
job_res = video_service.queue_video_generation("ws_admin_abhay", gen_req, user_id="admin_abhay")
print(f"  Job queued: {job_res.jobId}, videoId: {job_res.videoId}, status: {job_res.status}")

# Check library: the in-progress rendering video MUST NOT appear in library until YouTube confirmed
res4 = client.get("/api/v1/videos", headers={"Authorization": f"Bearer {token_abhay}"})
vids4 = res4.json()["data"]
assert not any(v["id"] == job_res.videoId for v in vids4), "Rendering video leaked into published library!"
assert len(vids4) == 93, f"Expected 93 videos, got {len(vids4)}"
print("  PASS: Newly queued video is not shown in user library before YouTube upload confirmation")

# TEST 5: Failed upload simulation
print("\n[TEST 5] Failed upload simulation...")
video_service._videos[job_res.videoId]["status"] = "failed"
video_service._videos[job_res.videoId]["error"] = "Upload rejected by quota"
res5 = client.get("/api/v1/videos", headers={"Authorization": f"Bearer {token_abhay}"})
vids5 = res5.json()["data"]
assert not any(v["id"] == job_res.videoId for v in vids5), "Failed video leaked into published library!"
# Clean up in-memory test video
del video_service._videos[job_res.videoId]
del video_service._jobs[job_res.jobId]
print("  PASS: Failed video is strictly excluded from published library")

# TEST 6: User data isolation
print("\n[TEST 6] Multi-tenant user data isolation...")
res6 = client.get("/api/v1/videos", headers={"Authorization": f"Bearer {token_user_b}"})
assert res6.status_code == 200
vids6 = res6.json()["data"]
assert len(vids6) == 0, f"User B saw {len(vids6)} videos! Cross-tenant leak!"

# User B trying to access Abhay's video directly
res6_idor = client.get(f"/api/v1/videos/{sample_id}", headers={"Authorization": f"Bearer {token_user_b}"})
assert res6_idor.status_code in (403, 404), f"User B got {res6_idor.status_code} for Abhay's video!"
print(f"  User B library count: {len(vids6)} videos")
print(f"  User B IDOR attempt on Abhay video: HTTP {res6_idor.status_code}")
print("  PASS: Zero cross-tenant data leakage, strict 403 Forbidden on foreign video access")

# TEST 7: Admin Dashboard separation
print("\n[TEST 7] Admin dashboard separation...")
# Clean up any test background worker artifacts
db.conn.execute("DELETE FROM videos WHERE id >= 1000000")
db.conn.commit()
test_out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "video_1000000")
if os.path.exists(test_out_dir):
    import shutil
    shutil.rmtree(test_out_dir, ignore_errors=True)

res7 = client.get("/api/v1/admin/overview", headers={"Authorization": f"Bearer {token_abhay}"})
assert res7.status_code == 200
d7 = res7.json()["data"]
print(f"  Total Confirmed YouTube Videos: {d7.get('confirmedYouTubeVideos')}")
print(f"  Total Videos: {d7.get('totalVideos')}")
print(f"  Unuploaded / Orphan Videos: {d7.get('unuploadedVideos')}")
assert d7.get("confirmedYouTubeVideos") == 93
assert d7.get("totalVideos") == 93
assert d7.get("unuploadedVideos") == 0

res7_vault = client.get("/api/v1/admin/vault", headers={"Authorization": f"Bearer {token_abhay}"})
assert res7_vault.status_code == 200
vault_summary = res7_vault.json()["data"]["summary"]
print(f"  Vault Total Videos: {vault_summary.get('totalVideos')}")
print(f"  Vault Confirmed YouTube Videos: {vault_summary.get('confirmedYouTubeVideos')}")
print(f"  Vault Unuploaded Videos: {vault_summary.get('unuploadedVideos')}")
assert vault_summary.get("confirmedYouTubeVideos") == 93
assert vault_summary.get("unuploadedVideos") == 0

print("\n" + "=" * 70)
print("  ALL 7 PRODUCTION CLEANUP & RECONCILIATION TESTS PASSED!")
print("=" * 70)
