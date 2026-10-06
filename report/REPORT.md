# Báo cáo Lab: Self evolving Agentic


## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Phạm Hồ Quang Dũng | 2A202602860 | Triển khai và chạy thí nghiệm với trợ giúp Codex; thông tin nhận diện suy ra từ tên repo. |

- Nhà cung cấp/model: Google Gemini, `google_genai:gemini-3.5-flash-lite`; temperature 0; recursion limit 60. Lệnh phụ chạy thí nghiệm đặt reasoning effort low, timeout 60 giây/request, không retry ngầm.
- Deep Agents 0.7.21; Windows host, Ubuntu WSL; Python Linux 3.14.4. Kiểm thử trên Ubuntu: **32 passed**. Windows: 30 passed, 2 failed do thiếu `which`, `cat` (không phải lỗi logic harness).
- Baseline học hoàn tất: code 7/10 (223908 token), data 5/8 (129894 token), logs 6/9 (187886 token). Các lần lỗi API và lần code bị ảnh hưởng CRLF được lưu riêng, không dùng trong bảng chính thức. Subagents và skills-auto-dev đã hoàn tất ba tác vụ học mỗi điều kiện; cả 9 lần chính đều không lỗi API. Token bảng agent không gồm 8999 token curator và các lần thử bị lỗi.
- Commit/tag `freeze`: chưa tạo; chỉ tạo sau khi curator sinh và kiểm tra skill. Chưa chạy tác vụ đánh giá.

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)


- H1 (subagents so với baseline): Dự đoán điểm đánh giá tương đương baseline; token có thể tăng nếu có giao việc. Căn cứ học: code đều 7/10 (không giao việc), data đều 5/8 dù subagents gọi implementer và dùng 268863/129894 = 2.07 lần token. Reviewer có thể kiểm tra kỹ thuật, nhưng không suy ra các quy ước ẩn từ đặc tả.
- H2 (skills-auto so với baseline): Dự đoán skills-auto có điểm đánh giá cao nhất nhưng mức tăng nhỏ, có thể ngang baseline/subagents. Căn cứ học trước freeze: skill giúp changelog code, tăng trung bình 0.664 lên 0.697; data/logs không tăng. Skill thiếu chi tiết quy ước và agent có thể đọc nhưng không làm theo; các quy ước mới chưa có phản hồi để học.
- H3 (tác vụ học so với tác vụ đánh giá): Dự đoán mức cải thiện do skill trên học lớn hơn trên đánh giá vì phản hồi học là đầu vào curator; chênh lệch chỉ là dấu hiệu quá khớp cần kiểm chứng, không tự chứng minh quá khớp.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Có `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`, `execute`, `task`. `execute` chạy shell. Bằng chứng: `report/tour.txt`, mô hình giả, không gọi API.
2. Công cụ `task` khởi tạo subagent tạm `general-purpose`, có các công cụ như agent chính. Mỗi lần mặc định độc lập và chỉ thấy prompt được giao, trả một báo cáo cuối. Vì vậy agent chính phải truyền đủ yêu cầu và đường dẫn.
3. System prompt mặc định quan sát được là chuỗi rỗng. Câu từ `task`: “Put full detail in the prompt and state exactly what it should return”. Câu từ `execute`: “Quote paths containing spaces”. Mô tả execute có hướng dẫn đường dẫn tuyệt đối, nhưng harness dùng `PATHS_NOTE` chung để yêu cầu đường dẫn tương đối nhất quán với shell.

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)


| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| code-learn | rule_type_hints; rule_regression_tests; rule_changelog | E | Thiếu type hints đầy đủ; cần tests/test_regressions.py với ít nhất 3 test; CHANGELOG.md cần ít nhất 3 bullet fix dưới Unreleased. |
| data-learn | rule_money_in_cents; rule_meta_block; rule_clean_csv | E | Tiền phải là integer cents; thiếu meta với source/rows_in/rows_used và clean.csv theo schema yêu cầu. |
| logs-learn | rule_service_names; rule_sorted_errors; rule_schema_header | E | Tên service lowercase và dấu gạch dưới; errors phải sort theo service/timestamp; thiếu schema_version=2 và generated_by=log-triage. |

Cả 9 check thất bại đều thuộc E. Check kỹ thuật đạt 18/18: code 7/7, data 5/5, logs 6/6. Đây là bằng chứng phủ định cho lỗi A–D ở bộ check này, không chứng minh mọi hành vi đều đúng. Skill có thể lưu quy ước thiếu trong đề; khả năng áp dụng sẽ đo ở Phần 3.4. Không tính lỗi API hay CRLF vào taxonomy năng lực.

## 5. Điều kiện `subagents` (Phần 2.3)

- Subagent: `explorer` đọc đặc tả/tìm nguyên nhân; `implementer` thực hiện và kiểm chứng; `reviewer` kiểm tra độc lập. Chia vai trò để giảm bỏ sót đặc tả và báo cáo hoàn thành thiếu bằng chứng.
- `subagent_calls`: code 0, data 1 (implementer), logs 2 (explorer, reviewer). Ba tác vụ đều bằng điểm baseline: 7/10, 5/8, 6/9.
- Chất lượng lời giao việc: data truyền đường dẫn và các quy tắc làm sạch, agent chính chạy lại script và đọc output. Logs chỉ giao yêu cầu tổng quát, không truyền schema và toàn bộ quy tắc; còn yêu cầu explorer viết file trái vai trò đọc. Reviewer báo đúng dù output còn timestamp/traceback và thiếu repeat_count. Agent chính đọc file, phát hiện schema sai, tự sửa lại; kết quả cuối đạt cả 6 check kỹ thuật. Đây là bằng chứng cần kiểm chứng báo cáo subagent.
- Token/thời gian: baseline trung bình 180563 token, 147.9 giây; subagents 263707 token, 240.7 giây (1.46 lần token, 1.63 lần thời gian). Code: 202173 token/166.7 giây; data: 268863/247.6; logs: 320086/307.8. Khả năng giao việc chưa đem lại tăng điểm trên học, nhưng không suy rộng sang đánh giá.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Curator thật chạy một lần từ ba baseline học, 8999 token, 10.7 giây, sinh ba skill. Không xóa, không chạy lại và không sửa tay skill. Hai test curator ngoại tuyến đã đạt. Nội dung không chứa định danh đánh giá; validation chỉ là rào chắn tối thiểu, không chứng minh chất lượng.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| rigorous-code-compliance | Quy trình code tổng quát, không chứa tên hàm học | Type hints và changelog đúng; thiếu tên tests/test_regressions.py và tối thiểu 3 test/bullet. Có thể chỉ áp dụng một phần quy ước. | 8 dòng; description rộng cho sửa code/refactor/test; được đọc ở code và data. |
| structured-data-normalization | Quy trình dữ liệu tổng quát, nhưng ví dụ sentinel -999 bám vào dữ liệu học | UTC và cents hữu ích; phép float*100 có rủi ro làm tròn; meta không nêu keys cụ thể và thiếu clean.csv. | 8 dòng; description rộng JSON/CSV nhưng không được đọc ở cả ba lượt dev, kể cả data. |
| strict-schema-and-sorting | Dùng cho log/text sang JSON, không chứa đáp án | Chuẩn hóa service và sort đúng hướng; không ghi schema_version=2/generated_by=log-triage nên khó khôi phục quy ước ẩn. | 8 dòng; description khớp parsing logs; được đọc ở data và logs. |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

Bảng HỌC TRƯỚC FREEZE từ `report/table-dev.md`. Cột skills-auto là dev; điểm đánh giá chưa đo. `report/table.md` sẽ tạo lại sau các lần chính thức.

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 7/10 | 7/10 | 8/10 |
| data-learn | 5/8 | 5/8 | 5/8 |
| logs-learn | 6/9 | 6/9 | 6/9 |
| **Mean score - learning tasks** | 0.66 | 0.66 | 0.70 |
| **Mean score - evaluation tasks** | - | - | - |
| **Mean tokens per run** | 180,562 | 263,707 | 140,595 |
| **Runs that read a skill** | 0/3 | 0/3 | 3/3 |

Ba lượt dev có skills_read lần lượt 1, 2, 1; skills_modified đều false. Đã sao lưu nguyên vẹn vào results/skills-auto-dev trước lần đóng băng.

## 8. Phân tích

1. Trên học, baseline/subagents đều trung bình 0.664; skills-auto-dev 0.697, tăng 0.033 điểm chuẩn hóa. Chỉ code tăng một check. Chưa có điểm đánh giá nên chưa kiểm chứng H1–H3 hoặc kết luận về quá khớp.
2. Check kỹ thuật: cả ba điều kiện đều 18/18. Quy ước: baseline 0/9, subagents 0/9, skills-auto-dev 1/9. Skill giúp rule_changelog; tác dụng lên quy ước mới của đánh giá còn chờ đo.
3. Code đọc rigorous-code-compliance, sửa CHANGELOG.md dưới Unreleased và đạt rule_changelog. Vẫn thiếu type hints đầy đủ dù có chỉ dẫn; tạo rồi xóa tests/test_extra.py, không có tests/test_regressions.py. Data đọc hai skill khác nhưng bỏ qua structured-data-normalization, nên vẫn trượt cents/meta/clean.csv. Logs đọc skill đúng nhưng giữ service có dấu gạch ngang và ưu tiên timestamp thay vì service; header quy ước không được skill nêu cụ thể. Đây là hai dạng không đọc skill phù hợp và đọc nhưng không áp dụng đầy đủ.
4. Token trung bình: baseline 180563, subagents 263707, skill dev 140595; thời gian 147.9/240.7/135.5 giây. Điểm chuẩn hóa trung bình trên 100000 token tương ứng khoảng 0.37/0.25/0.50, chỉ là thống kê mô tả của ba lượt học; chưa gồm curator. Đa tác tử chưa đem lại tăng điểm dù dùng nhiều token hơn. Không dùng các tỷ lệ này như kết luận tổng quát từ một lần chạy.
5. Curator chỉ dùng baseline role=learn và feedback quy tắc; không đọc điểm/vết/data đánh giá. validate_skill kiểm tra marker đánh giá và tên đường dẫn. Không có đáp án số hoặc định danh đánh giá trong skill; ví dụ -999 vẫn bám vào dữ liệu học, là hạn chế tổng quát hóa. Skill được giữ nguyên, không chỉnh tay; validation không đủ để loại mọi dạng rò rỉ diễn đạt lại.
6. Điểm học trước freeze đã lưu nguyên vẹn trong skills-auto-dev: 8/10, 5/8, 6/9. Chưa có lần sau freeze nên chưa tính chênh lệch nhiễu. Sau khi chủ repo commit giả thuyết và tạo tag, phải chạy lại cả học/đánh giá với cùng skill và đối chiếu.

## 9. Hạn chế và tính hợp lệ


1. Chỉ ba tác vụ học và ba tác vụ đánh giá: mẫu nhỏ, không suy rộng sang mọi bài toán.
2. Mỗi cấu hình dự kiến một lần chính thức; tính ngẫu nhiên và lỗi dịch vụ làm giảm độ chắc chắn, kể cả nhiệt độ 0.
3. Chỉ một model và free tier; quota/thời gian chờ có thể gây thiếu dữ liệu, không được đồng nhất với chất lượng agent.
4. Trace chỉ giữ luồng chính, còn token cộng cả subagent. Runner đã dùng stream values để giữ trạng thái nhận được trước lỗi, nhưng vẫn không thấy nội bộ từng subagent.

## 10. Kết luận

Harness đã triển khai và đạt 32 test trên Linux. Trên ba tác vụ học, subagents không tăng điểm dù token tăng 46%. Skill tự sinh chỉ giúp một check changelog, tăng trung bình 0.033 điểm chuẩn hóa. Việc đọc và áp dụng skill còn không ổn định; skill thiếu một số quy ước. Chưa chạy đánh giá, nên kết luận này là tạm thời và phải kiểm chứng sau freeze.


## Phụ lục

- Lệnh đã chạy (theo thứ tự): cài editable trong Ubuntu WSL; pytest (report/tests.txt); tour (report/tour.txt); run_experiment baseline learn; subagents learn; run_curator một lần; skills-auto learn; lưu bản dev. Chi tiết lệnh/cấu hình trong report/RUNBOOK.md.
- Thử thách mở rộng: không thực hiện Phần 6 tùy chọn.
- Ghi chú khác:

## Trạng thái thực hiện

Báo cáo này là bản đang thực hiện, chưa phải bản nộp hoàn chỉnh. Chỉ ghi số đo quan sát được; không tạo skill hoặc kết quả giả để lấp phần còn thiếu. Phần 0–3 đã hoàn tất; đang chờ chủ repo tự commit hypotheses, commit freeze skills và tạo tag freeze theo report/RUNBOOK.md. Sau đó mới chạy Phần 4 và hoàn thiện báo cáo chính thức.

Ghi nhận runtime: SDK cảnh báo Gemini 3.5 Flash-Lite dùng sampling mặc định cố định và bỏ qua `temperature`. Vì vậy `LAB_TEMPERATURE=0` là cấu hình gửi vào, không phải bằng chứng mô hình chạy deterministic; dùng cùng mặc định giữa các điều kiện.

Khắc phục môi trường: hash test gốc trong checkout CRLF là `efb5e7650d4f03356e8353d209fbcfe81505ce2fd648bd558d5ada6e8b92ff19`, còn dạng LF là `79e05f4cc2e62a4f606d210b0b08a2cc21777245bc2f6ad244a126e9a2aee00d`, khớp checker. Chỉ chuẩn hóa bản sao sandbox; nguồn repo được giữ nguyên.
