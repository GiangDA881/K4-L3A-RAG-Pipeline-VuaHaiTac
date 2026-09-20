# Individual contribution report

## Thông tin

- Họ và tên: Phan Trọng Hoàn
- Mã học viên: 2A202602954
- Nhóm: VuaHaiTac
- Repository/branch: `GiangDA881/K4-L3A-RAG-Pipeline-VuaHaiTac` / `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 7 — RRF | Hoàn thiện công thức tổng `1/(k+rank)`, gộp theo ID, copy item trước khi đổi score và method thành `hybrid`; sắp xếp giảm dần, giới hạn `top_k`, báo lỗi khi một danh sách đầu vào trùng ID. | `src/task7_reranking.py` | Done |
| Task 9 — Pipeline | Kết hợp dense và BM25, fuse một lần; dùng cosine gốc cao nhất để quyết định fallback. Giữ hybrid khi fallback rỗng, lỗi hoặc sai contract. | `src/task9_retrieval_pipeline.py` | Done |
| Task 8 — Kiểm tra cấu hình | Xử lý query rỗng và thiếu API key để pipeline bắt lỗi rõ ràng. Chưa triển khai upload/cache/timeout/parsing API thật. | `src/task8_pageindex_vectorless.py` | Partial |
| Kiểm thử và hỗ trợ Task 10 | Bổ sung test hồi quy; hoàn thiện hai helper `reorder_for_llm()` và `format_context()` để đáp ứng contract hiện có. | `tests/test_retrieval_pipeline.py`, `src/task10_generation.py` | Done |
| Hiệu chỉnh và báo cáo | Viết script lập index thử nghiệm riêng, chạy hai query, lưu score và kết quả pipeline; cập nhật báo cáo nhóm. | `src/calibrate_retrieval.py`, `reports/retrieval_calibration.json`, `group_project/evaluation/RESULT.md` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Tách hợp nhất thứ hạng khỏi quyết định fallback; dùng RRF với `k=60`.  
   **Lý do/evidence:** Cosine và BM25 không cùng thang đo; giữ nguyên input để còn đọc cosine gốc. Contract tests kiểm tra input không bị sửa, uniqueness, fuse một lần và ngưỡng dùng dense score.  
   **Trade-off:** RRF không dùng độ lớn score, nên cần một ngưỡng dense riêng để đánh giá độ tin cậy.

2. **Quyết định:** Hiệu chỉnh trên index MiniLM riêng và giới hạn phạm vi kết luận.  
   **Lý do/evidence:** BGE-M3 chưa có trọng số, index chính chưa có chunks khi thử. Dùng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 chiều), recursive 500/50, 9 tài liệu tạo 709 chunks. Query in-domain `0.8158` giữ hybrid; query ngoài domain `0.1776` thử fallback; chọn threshold `0.4967` là trung điểm làm tròn. Số liệu lưu trong `reports/retrieval_calibration.json`.  
   **Trade-off:** Đo được hành vi thực tế nhưng ngưỡng này không chuyển trực tiếp sang BGE-M3.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `python -m src.task7_reranking`; `python -m pytest tests/test_contracts.py tests/test_retrieval_pipeline.py -q`; hai query hiệu chỉnh (lữ hành quốc tế vs phân loại ảnh mèo/chó).
- Kết quả trước/sau nếu có: item hạng 2 dense + hạng 1 BM25 nhận đúng `1/62 + 1/61 = 0.03252247488101534` và đứng đầu fused. Lượt contract đầu `14/15`; sau khi hoàn thiện helper Task 10 thì `27 passed`. Query in-domain cosine `0.8158` giữ hybrid; query ngoài domain `0.1776` thử fallback, thiếu PageIndex nhưng pipeline vẫn giữ 5 hybrid results.
- Lỗi đã phát hiện và cách xử lý: helper Task 10 còn `NotImplementedError` làm fail contract; đã hoàn thiện `reorder_for_llm()` / `format_context()` và bổ sung test hồi quy.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: hai query chỉ đủ kiểm tra ban đầu; `SCORE_THRESHOLD=0.3` mặc định cho BGE-M3 chưa hiệu chỉnh, và PageIndex chưa có API key / tích hợp dịch vụ thật.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: hiệu chỉnh bằng BGE-M3 trên tập query trong/ngoài domain lớn hơn, rồi hoàn thiện PageIndex và kiểm tra safe refusal cùng nhóm.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-20
- Tên thành viên: Phan Trọng Hoàn
