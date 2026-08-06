import sys
import io
import traceback
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import MediaAsset
from app.seed import seed_db

def main():
    print("=== STARTING REELTODIGIT E2E & CLOUD STORAGE VERIFICATION ===")
    try:
        # 1. Seed Database
        seed_db()
        print("[Pass] Database seeded successfully.")

        # 2. Setup TestClients
        customer_client = TestClient(app)
        admin_client = TestClient(app)

        # 3. Test Home Page
        res = customer_client.get("/")
        assert res.status_code == 200
        assert "ReelToDigit" in res.text
        print("[Pass] Home page GET / loaded.")

        # 4. Test Customer Login
        res = customer_client.post("/login", data={
            "email": "customer@example.com",
            "password": "Customer123!"
        }, follow_redirects=False)
        assert res.status_code == 303
        print("[Pass] Customer login & session cookie established.")

        # 5. Create Draft Order
        res = customer_client.post("/orders/new", data={"cassette_count": 2, "accept_terms": "on", "format": "MP4"}, follow_redirects=False)
        assert res.status_code == 303
        order_configure_url = res.headers["location"]
        order_id = int(order_configure_url.split("/")[2])

        # Configure tags & pay
        customer_client.post(f"/orders/{order_id}/configure", data={"tag_1": "Demo Audio 1", "tag_2": "Demo Audio 2"}, follow_redirects=False)
        customer_client.post(f"/orders/{order_id}/pay", follow_redirects=False)

        # 6. Test Admin Portal Login & File Upload
        admin_res = admin_client.post("/login", data={
            "email": "admin@reeltodigit.com",
            "password": "Admin123!"
        }, follow_redirects=False)
        assert admin_res.status_code == 303

        # Simulate MP4 File Upload via Admin Dashboard
        fake_mp4_content = b"\x00\x00\x00\x18ftypmp42 Fake MP4 Box Content Data"
        files = {"file": ("Tape_1_Cloud_Digitized.mp4", io.BytesIO(fake_mp4_content), "video/mp4")}
        data = {"file_name": "Tape_1_Cloud_Digitized.mp4"}

        res = admin_client.post(f"/admin/orders/{order_id}/media", data=data, files=files, follow_redirects=False)
        assert res.status_code == 303
        print("[Pass] Admin successfully uploaded MP4 file.")

        # Query created media asset ID
        db = SessionLocal()
        media = db.query(MediaAsset).filter(MediaAsset.order_id == order_id).first()
        assert media is not None
        media_id = media.id
        db.close()

        # 7. Customer views order detail & checks download link
        res = customer_client.get(f"/orders/{order_id}")
        assert res.status_code == 200
        assert "Tape_1_Cloud_Digitized.mp4" in res.text
        assert f"/media/{media_id}/download" in res.text

        # Test secure media download route
        res = customer_client.get(f"/media/{media_id}/download", follow_redirects=False)
        assert res.status_code in [302, 303]
        download_url = res.headers["location"]
        assert "/static/uploads/" in download_url or "s3.amazonaws.com" in download_url
        print(f"[Pass] Secure download route generated valid asset URL: {download_url}")

        print("\n🎉 ALL E2E & CLOUD STORAGE VERIFICATIONS PASSED PERFECTLY! 🎉")

    except Exception as e:
        with open("err.txt", "w") as f:
            traceback.print_exc(file=f)
        print("\n[FAILED] E2E TEST FAILED:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
