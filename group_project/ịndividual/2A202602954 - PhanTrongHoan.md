# Báo cáo đóng góp cá nhân

## Thông tin

- **Họ và tên:** Phan Trọng Hoàn
- **Mã học viên:** 2A202602954
- **Nhóm:** VuaHaiTac
- **Repository/branch:** `GiangDA881/K4-L3A-RAG-Pipeline-VuaHaiTac` / `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi thực hiện | File minh chứng | Trạng thái |
| --- | --- | --- | --- |
| Task 7 — RRF | Hoàn thiện công thức tổng `1/(k+rank)`, gộp theo ID, copy item trước khi đổi score và method thành `hybrid`; sắp xếp giảm dần, giới hạn `top_k`, báo lỗi khi một danh sách đầu vào trùng ID. | `src/task7_reranking.py` | Done |
| Task 9 — Pipeline | Kết hợp dense và BM25, fuse một lần; dùng cosine gốc cao nhất để quyết định fallback. Giữ hybrid khi fallback rỗng, lỗi hoặc sai contract. | `src/task9_retrieval_pipeline.py` | Done |
| Task 8 — Kiểm tra cấu hình | Xử lý query rỗng và thiếu API key để pipeline bắt lỗi rõ ràng. Chưa triển khai upload/cache/timeout/parsing API thật. | `src/task8_pageindex_vectorless.py` | Partial |
| Kiểm thử và hỗ trợ Task 10 | Bổ sung test hồi quy; hoàn thiện hai helper `reorder_for_llm()` và `format_context()` để đáp ứng contract hiện có. | `tests/test_retrieval_pipeline.py`, `src/task10_generation.py` | Done trong phạm vi test/helper |
| Hiệu chỉnh và báo cáo | Viết script lập index thử nghiệm riêng, chạy hai query, lưu score và kết quả pipeline; cập nhật báo cáo nhóm. | `src/calibrate_retrieval.py`, `reports/retrieval_calibration.json`, `group_project/evaluation/RESULT.md` | Done cho thử nghiệm MiniLM |

## Quyết định kỹ thuật quan trọng

1. **Tách hợp nhất thứ hạng khỏi quyết định fallback.** Dùng RRF với `k=60` vì cosine và BM25 không cùng thang đo, giữ nguyên input để còn đọc cosine gốc. Trade-off RRF không sử dụng độ lớn score, nên cần một ngưỡng dense riêng để đánh giá độ tin cậy.
2. **Hiệu chỉnh trên index MiniLM riêng và giới hạn phạm vi kết luận.** BGE-M3 chưa có trọng số, index chính chưa có chunks. Tôi dùng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 chiều), recursive 500/50, trên 9 tài liệu tạo 709 chunks. Trade-off đo được hành vi thực tế nhưng ngưỡng này không chuyển trực tiếp sang BGE-M3.

## Kiểm thử và kết quả

- `python -m src.task7_reranking`: item đứng thứ 2 trong dense và thứ 1 trong BM25 nhận đúng `1/62 + 1/61 = 0.03252247488101534` và đứng đầu kết quả fused.
- `python -m pytest tests/test_contracts.py tests/test_retrieval_pipeline.py -q`: **27 passed**. Test kiểm tra input không bị sửa, uniqueness, giới hạn kết quả, fuse một lần, ngưỡng dùng dense score, timeout và provider lỗi.
- Lượt contract test đầu đạt **14/15**; lỗi do helper Task 10 còn `NotImplementedError`. Sau khi hoàn thiện hai helper và bổ sung test hồi quy, cả hai file test đều pass.

| Query hiệu chỉnh | Best dense cosine | Quyết định với threshold `0.4967` |
| --- | ---: | --- |
| Điều kiện kinh doanh dịch vụ lữ hành quốc tế tại Việt Nam là gì? | 0.8157963753 | Giữ hybrid |
| Làm thế nào để huấn luyện mạng nơ-ron tích chập phân loại ảnh mèo và chó? | 0.1776284575 | Thử fallback |

Tôi chọn **0.4967** là trung điểm làm tròn của hai score, chỉ cho thử nghiệm MiniLM này. Query trong domain tìm được nội dung về lữ hành trong Luật Du lịch; top dense của query ngoài domain là đoạn bảng xe không liên quan. Khi gọi `retrieve()` thật, cả hai query trả 5 hybrid results; query ngoài domain gặp lỗi thiếu cấu hình PageIndex nhưng pipeline vẫn tiếp tục và giữ kết quả. Số liệu và output được lưu trong JSON minh chứng.

## Điều còn hạn chế

- Hai query chỉ đủ kiểm tra ban đầu, chưa chứng minh ngưỡng tối ưu. `SCORE_THRESHOLD=0.3` mặc định cho BGE-M3 vẫn chưa hiệu chỉnh.
- PageIndex chưa có API key và chưa hoàn thiện tích hợp dịch vụ thật. Test timeout/provider lỗi dùng mock; lần chạy thật chỉ xác nhận xử lý thiếu cấu hình.
- Kết quả hybrid cho query ngoài domain chưa bảo đảm đủ evidence. Generation end-to-end và safe refusal chưa hoàn thiện trong đợt này; chưa có kết quả đánh giá A/B toàn pipeline.
- Bước tiếp theo: hiệu chỉnh bằng BGE-M3 trên tập query trong/ngoài domain lớn hơn, sau đó hoàn thiện PageIndex và kiểm tra safe refusal cùng nhóm.

## Xác nhận đóng góp

Nội dung báo cáo được đối chiếu với commit, test và dữ liệu thử nghiệm nêu trên; phần hoàn thành và phần còn hạn chế được ghi riêng để phục vụ kiểm tra, demo.

- **Ngày:** 20/09/2026
- **Thành viên:** Phan Trọng Hoàn
