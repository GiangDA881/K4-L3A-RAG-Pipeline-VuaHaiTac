"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Chủ đề: Du lịch Việt Nam (lịch trình, địa điểm, ẩm thực, quy định địa phương).

Nguồn là văn bản Công báo Chính phủ: Luật Du lịch 2017, Nghị định 168/2017/NĐ-CP
và Nghị định 94/2021/NĐ-CP. Tải PDF gốc vào data/landing/legal/, ghi đè file cùng
tên khi chạy lại — không tạo bản sao.
"""

from pathlib import Path

import requests


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

LEGAL_DOCUMENTS = [
    {
        "filename": "luat-du-lich-2017.pdf",
        "title": "Luật Du lịch số 09/2017/QH14",
        "page_url": "https://congbao.chinhphu.vn/van-ban/luat-so-09-2017-qh14-24241/18448.htm",
        "file_url": (
            "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2017/6/24241/"
            "18448-1-2017515-51609-2017-qh14.pdf"
        ),
    },
    {
        "filename": "nghi-dinh-168-2017-nd-cp.pdf",
        "title": "Nghị định 168/2017/NĐ-CP quy định chi tiết Luật Du lịch",
        "page_url": "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-168-2017-nd-cp-26028/21615.htm",
        "file_url": (
            "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2017/12/26028/"
            "21615-1-2018429-430168-2017-nd-cp.pdf"
        ),
    },
    {
        "filename": "nghi-dinh-94-2021-nd-cp.pdf",
        "title": "Nghị định 94/2021/NĐ-CP sửa đổi mức ký quỹ lữ hành",
        "page_url": "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-94-2021-nd-cp-34718.htm",
        "file_url": (
            "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2021/10/34718/"
            "37380-1-2021931-93294-2021-nd-cp.pdf"
        ),
    },
]


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải PDF chính sách từ Công báo và ghi đè file cùng tên."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for document in LEGAL_DOCUMENTS:
        destination = DATA_DIR / document["filename"]
        response = requests.get(
            document["file_url"],
            headers={"User-Agent": USER_AGENT},
            timeout=60,
        )
        response.raise_for_status()
        if not response.content.startswith(b"%PDF"):
            raise RuntimeError(f"Not a PDF: {document['filename']}")
        if len(response.content) <= 1024:
            raise RuntimeError(f"PDF too small: {document['filename']}")
        destination.write_bytes(response.content)
        print(f"Saved: {destination} ({len(response.content)} bytes)")
        print(f"  Source: {document['page_url']}")


if __name__ == "__main__":
    setup_directory()
    download_documents()
