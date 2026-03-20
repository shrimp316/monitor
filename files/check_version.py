import requests
import json
import os

# ───────────────────────────────────────────
# 설정
# ───────────────────────────────────────────
APPSTORE_ID = "6499560136"
PLAYSTORE_ID = "com.seasoninggames.endlessbricks"
APP_NAME = "벽돌 주식회사"
VERSION_FILE = "last_version.json"

# 카카오봇 설정 (GitHub Secrets에서 불러옴)
KAKAO_BOT_URL = os.environ.get("KAKAO_BOT_URL", "")  # 카카오봇 웹훅 URL


# ───────────────────────────────────────────
# 버전 조회 함수
# ───────────────────────────────────────────
def get_appstore_version():
    """App Store (iOS) 버전 조회"""
    try:
        url = f"https://itunes.apple.com/lookup?id={APPSTORE_ID}&country=kr"
        res = requests.get(url, timeout=10)
        data = res.json()
        if data["resultCount"] > 0:
            result = data["results"][0]
            return {
                "version": result["version"],
                "release_notes": result.get("releaseNotes", ""),
                "store_url": f"https://apps.apple.com/kr/app/id{APPSTORE_ID}"
            }
    except Exception as e:
        print(f"[App Store 오류] {e}")
    return None


def get_playstore_version():
    """Google Play (Android) 버전 조회"""
    try:
        from google_play_scraper import app
        result = app(PLAYSTORE_ID, lang="ko", country="kr")
        return {
            "version": result["version"],
            "release_notes": result.get("recentChanges", ""),
            "store_url": f"https://play.google.com/store/apps/details?id={PLAYSTORE_ID}"
        }
    except Exception as e:
        print(f"[Play Store 오류] {e}")
    return None


# ───────────────────────────────────────────
# 버전 저장/불러오기
# ───────────────────────────────────────────
def load_last_versions():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"appstore": None, "playstore": None}


def save_versions(versions):
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        json.dump(versions, f, ensure_ascii=False, indent=2)


# ───────────────────────────────────────────
# 카카오봇 알림 전송
# ───────────────────────────────────────────
def send_kakao_notification(store_name, version, release_notes, store_url):
    """카카오 오픈채팅 봇 웹훅으로 메시지 전송"""
    if not KAKAO_BOT_URL:
        print("[알림 생략] KAKAO_BOT_URL이 설정되지 않음")
        return

    notes_preview = release_notes[:100] + "..." if len(release_notes) > 100 else release_notes
    message = (
        f"🎮 [{APP_NAME}] 업데이트!\n"
        f"📦 스토어: {store_name}\n"
        f"🆕 버전: {version}\n"
        f"📝 업데이트 내용: {notes_preview or '정보 없음'}\n"
        f"🔗 {store_url}"
    )

    try:
        res = requests.post(
            KAKAO_BOT_URL,
            json={"message": message},
            timeout=10
        )
        print(f"[알림 전송 완료] {store_name} v{version} → 상태코드: {res.status_code}")
    except Exception as e:
        print(f"[알림 전송 실패] {e}")


# ───────────────────────────────────────────
# 메인 로직
# ───────────────────────────────────────────
def main():
    print("=== 버전 체크 시작 ===")

    last = load_last_versions()
    updated = False

    # App Store 체크
    ios = get_appstore_version()
    if ios:
        print(f"[App Store] 현재: {ios['version']} / 저장됨: {last['appstore']}")
        if ios["version"] != last["appstore"]:
            print("→ 새 버전 감지!")
            send_kakao_notification("App Store (iOS)", ios["version"], ios["release_notes"], ios["store_url"])
            last["appstore"] = ios["version"]
            updated = True
        else:
            print("→ 변경 없음")

    # Play Store 체크
    android = get_playstore_version()
    if android:
        print(f"[Play Store] 현재: {android['version']} / 저장됨: {last['playstore']}")
        if android["version"] != last["playstore"]:
            print("→ 새 버전 감지!")
            send_kakao_notification("Google Play (Android)", android["version"], android["release_notes"], android["store_url"])
            last["playstore"] = android["version"]
            updated = True
        else:
            print("→ 변경 없음")

    if updated:
        save_versions(last)
        print("=== 버전 파일 업데이트 완료 ===")
    else:
        print("=== 변경 없음, 종료 ===")


if __name__ == "__main__":
    main()
