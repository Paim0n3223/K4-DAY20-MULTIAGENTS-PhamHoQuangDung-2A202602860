# Báo cáo Lab: Self evolving Agentic


## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Phạm Hồ Quang Dũng | 2A202602860 | Triển khai và chạy thí nghiệm với trợ giúp Codex; thông tin nhận diện suy ra từ tên repo. |

- Nhà cung cấp/model: Google Gemini, `google_genai:gemini-3.5-flash-lite`; temperature 0; recursion limit 60. Lệnh phụ chạy thí nghiệm đặt reasoning effort low, timeout 60 giây/request, không retry ngầm.
- Deep Agents 0.7.21, langchain-google-genai 4.4.0, langchain-core 1.6.6; Windows host, Ubuntu WSL; Python Linux 3.14.4. Kiểm thử trên Ubuntu: **32 passed**. Windows: 30 passed, 2 failed do thiếu `which`, `cat` (không phải lỗi logic harness).
- Đã hoàn tất 18/18 lượt chính thức: baseline 6/6, subagents 6/6, skills-auto 6/6. Có thêm 3 lượt skills-auto-dev trước freeze và một lượt curator (8999 token). Các lượt chính thức hoàn tất không lỗi API. Các lượt bị lỗi API/quota hoặc CRLF không dùng tính điểm mô hình; bản ghi lỗi tạm đã bỏ khi dọn bài nộp. Một lượt code-learn bị ngắt phiên công cụ không có usage đầy đủ; đã chạy lại cùng cấu hình trước khi có điểm.
- Chủ repo tạo commit hypotheses cf028b8, commit freeze skills 4a9e1ac và tag freeze tại commit sau (2026-10-06T17:28:39+07:00). verify_freeze báo checked 6 runs of skill conditions: OK. H1–H3 giữ nguyên văn bản trong commit hypotheses và skill không đổi từ tag. Sau khi hết quota ngày của project ban đầu, chủ repo thay key thuộc project khác; tiếp tục cùng model, cấu hình và skill, không chạy lại kết quả đã hoàn tất.

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
| code-learn | rule_type_hints | E | RULE: every public function ... has type annotations on all parameters and on the return value. |
| code-learn | rule_regression_tests | E | RULE: add tests/test_regressions.py ... at least 3; the file must pass. |
| code-learn | rule_changelog | E | RULE: record each fix in CHANGELOG.md under ... Unreleased ... at least 3 bullets. |
| data-learn | rule_money_in_cents | E | RULE: money values in answer.json are integer cents. |
| data-learn | rule_meta_block | E | RULE: answer.json has an object meta với source, rows_in (gồm trùng), rows_used (đơn riêng, biết tiền). |
| data-learn | rule_clean_csv | E | RULE: write workspace/clean.csv với order_id,timestamp_utc,region,amount_cents; một dòng/đơn biết tiền. |
| logs-learn | rule_service_names | E | RULE: service names ... lower-case with '-' replaced by '_'. |
| logs-learn | rule_sorted_errors | E | RULE: errors is sorted by service, then by timestamp_utc, ascending. |
| logs-learn | rule_schema_header | E | RULE: ... schema_version: 2 and generated_by: log-triage. |

Cả 9 check thất bại đều thuộc E. Check kỹ thuật đạt 18/18: code 7/7, data 5/5, logs 6/6. Đây là bằng chứng phủ định cho lỗi A–D ở bộ check này, không chứng minh mọi hành vi đều đúng. Skill có thể lưu quy ước thiếu trong đề; khả năng đọc và áp dụng đã đo ở Phần 3.4 và toàn bộ Phần 4. Không tính lỗi API hay CRLF vào taxonomy năng lực.

## 5. Điều kiện `subagents` (Phần 2.3)

- Subagent: `explorer` đọc đặc tả/tìm nguyên nhân; `implementer` thực hiện và kiểm chứng; `reviewer` kiểm tra độc lập. Chia vai trò để giảm bỏ sót đặc tả và báo cáo hoàn thành thiếu bằng chứng.
- `subagent_calls`: code 0, data 1 (implementer), logs 2 (explorer, reviewer). Ba tác vụ đều bằng điểm baseline: 7/10, 5/8, 6/9.
- Chất lượng lời giao việc: data truyền đường dẫn và các quy tắc làm sạch, agent chính chạy lại script và đọc output. Logs chỉ giao yêu cầu tổng quát, không truyền schema và toàn bộ quy tắc; còn yêu cầu explorer viết file trái vai trò đọc. Reviewer báo đúng dù output còn timestamp/traceback và thiếu repeat_count. Agent chính đọc file, phát hiện schema sai, tự sửa lại; kết quả cuối đạt cả 6 check kỹ thuật. Đây là bằng chứng cần kiểm chứng báo cáo subagent.
- Token/thời gian: baseline trung bình 180563 token, 147.9 giây; subagents 263707 token, 240.7 giây (1.46 lần token, 1.63 lần thời gian). Code: 202173 token/166.7 giây; data: 268863/247.6; logs: 320086/307.8. Khả năng giao việc chưa đem lại tăng điểm trên học, nhưng không suy rộng sang đánh giá.


Đánh giá sau freeze: code gọi subagent 0 lần, data 2 lần (explorer, reviewer), logs 4 lần (explorer hai lần, implementer, reviewer). Code vẫn 7/11 như baseline; lời nhắc giao việc không bảo đảm agent thực sự giao việc. Data 4/9 so với baseline 5/9: march_orders_utc trả 48 trong khi yêu cầu là các đơn được tính vào doanh thu. Đối chiếu input cho thấy 48 đơn tháng 3 gồm đơn thiếu tiền, chỉ 44 đơn có số tiền; hai subagent đều xác nhận 48. Main chỉ đọc answer.json, không có kiểm tra phép tính độc lập; lời giao việc không truyền đầy đủ quy tắc loại missing khi đếm (liên quan A/B/D).

Logs đánh giá 0/10 so với baseline 6/10, error=None. Main chỉ gọi task bốn lần, không đọc output hoặc chạy kiểm tra; implementer/reviewer đều báo thành công và main lặp lại báo cáo. Checker bác cả valid_structure và các check còn lại. Trace không chứa output cuối hay nội bộ subagent, nên chưa xác định được nguyên nhân cụ thể; không khẳng định file thiếu chỉ từ điểm 0. Đây là bằng chứng về hạn chế kiểm chứng (B), không phải lỗi API. Quá trình giao việc còn yêu cầu reviewer xóa file, trái vai trò không sửa. Token đánh giá trung bình baseline 179580, subagents 222199; thời gian 137.2 và 214.6 giây.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Curator thật chạy một lần từ ba baseline học, 8999 token, 10.7 giây, sinh ba skill. Không xóa, không chạy lại và không sửa tay skill. Hai test curator ngoại tuyến đã đạt. Nội dung không chứa định danh đánh giá; validation chỉ là rào chắn tối thiểu, không chứng minh chất lượng.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| rigorous-code-compliance | Quy trình code tổng quát, không chứa tên hàm học | Type hints và changelog đúng; thiếu tên tests/test_regressions.py và tối thiểu 3 test/bullet. Có thể chỉ áp dụng một phần quy ước. | 8 dòng; description rộng cho sửa code/refactor/test; được đọc ở code và data. |
| structured-data-normalization | Quy trình dữ liệu tổng quát, nhưng ví dụ sentinel -999 bám vào dữ liệu học | UTC và cents hữu ích; phép float*100 có rủi ro làm tròn; meta không nêu keys cụ thể và thiếu clean.csv. | 8 dòng; description rộng JSON/CSV nhưng không được đọc ở cả ba lượt dev, kể cả data. |
| strict-schema-and-sorting | Dùng cho log/text sang JSON, không chứa đáp án | Chuẩn hóa service và sort đúng hướng; không ghi schema_version=2/generated_by=log-triage nên khó khôi phục quy ước ẩn. | 8 dòng; description khớp parsing logs; được đọc ở data và logs. |

Ở lượt chính thức, structured-data-normalization được đọc ở cả code-learn, data-learn và data-eval. Cả sáu lượt chính thức đều đọc ít nhất một skill; đối chiếu áp dụng ở mục 8.

## 7. Kết quả so sánh (Phần 4.3, 4.4)

Bảng dưới dán từ lab.compare, khớp đủ 18 lượt chính thức trong report/table.md. Mỗi điều kiện có ba tác vụ học và ba tác vụ đánh giá.

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 7/10 | 7/10 | 9/10 |
| data-learn | 5/8 | 5/8 | 5/8 |
| logs-learn | 6/9 | 6/9 | 7/9 |
| code-eval | 7/11 | 7/11 | 7/11 |
| data-eval | 5/9 | 4/9 | 5/9 |
| logs-eval | 6/10 | 0/10 | 7/10 |
| **Mean score - learning tasks** | 0.66 | 0.66 | 0.77 |
| **Mean score - evaluation tasks** | 0.60 | 0.36 | 0.63 |
| **Mean tokens per run** | 180,071 | 242,953 | 181,488 |
| **Runs that read a skill** | 0/6 | 0/6 | 6/6 |

Kết quả scripts/check_breakdown.py:

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval     18/18         0/12         179,580      0/3
baseline      learn    18/18         0/9          180,562      0/3
subagents     eval     11/18         0/12         222,198      0/3
subagents     learn    18/18         0/9          263,707      0/3
skills-auto   eval     17/18         2/12         141,231      3/3
skills-auto   learn    18/18         3/9          221,744      3/3
```

Cả 18 lượt có error=None. Sáu lượt skills-auto có skills_modified=false và verify_freeze xác nhận đúng bộ skill đã đóng băng. Các lượt lỗi API/CRLF đã được loại khỏi bảng và bản nộp; không tính chúng như điểm 0 của agent. Việc tiếp tục sau lỗi dùng cùng cấu hình.

Kết quả trước freeze giữ ở results/skills-auto-dev: code 8/10, data 5/8, logs 6/9; skills_read lần lượt 1,2,1. Lượt chính thức: code-learn 9/10, data-learn 5/8, logs-learn 7/9; skills_read 3,3,1. Đánh giá: code 7/11, data 5/9, logs 7/10; skills_read 1,3,1. Tất cả kết quả dev và chính thức đều không sửa skill.

## 8. Phân tích

1. Trên học, baseline/subagents đều trung bình 0.664; skill chính thức đạt 0.768, tăng 0.104 (10.37 điểm phần trăm). Trên đánh giá, baseline 0.597, subagents 0.360, skill 0.631: skill tăng 0.033 (3.33 điểm phần trăm), nhờ logs tăng một check; code và data không tăng. Code học tăng 7/10 lên 9/10 nhưng code đánh giá vẫn 7/11, phù hợp dấu hiệu khả năng chuyển giao hạn chế. H1 không được ủng hộ trong lần đo này, chủ yếu do subagents logs 0/10. H2 được ủng hộ về thứ hạng quan sát được; H3 được ủng hộ về chênh lệch học/đánh giá, nhưng nhiễu ở câu 6 khiến chưa thể kết luận quá khớp hay lợi ích có ý nghĩa thống kê.
2. Baseline đạt toàn bộ check kỹ thuật nhưng không đạt quy ước. Skill đạt 3/9 quy ước học (type_hints, changelog ở code; sorted_errors ở logs) và 2/12 quy ước đánh giá (changelog, sorted_errors). Kỹ thuật đánh giá giảm từ 18/18 xuống 17/18 vì code sửa test trái yêu cầu. Cả ba quy ước mới rule_version_bump, rule_sorted_keys_format và rule_source_line đều không đạt ở mọi điều kiện; skill không có hướng dẫn các quy ước mới này và không nhận phản hồi đánh giá để học chúng.
3. Bằng chứng giúp đạt: code học chính thức đọc cả ba skill và đạt type hints/changelog; logs đọc strict-schema-and-sorting và đạt sorted_errors ở cả học/đánh giá. Bằng chứng không giúp: code vẫn thiếu regression đúng tên và số lượng vì skill chỉ nói test tổng quát; code đánh giá thêm test vào tests/test_bookings.py trong sandbox dù đề cấm, mất tests_not_modified. Test gốc trong repo không bị sửa. Data dev bỏ qua structured-data-normalization; data chính thức đọc cả ba skill nhưng vẫn trượt cents/meta/clean.csv. Data-eval ghi metadata với source_file/input_rows thay vì meta với source/rows_in/rows_used, giữ USD và thiếu CSV; skill thiếu quy ước chính xác, việc đọc không đủ để suy ra chúng. Logs vẫn không đạt service_names/schema_header dù đọc đúng skill. Cần phân biệt việc đọc, làm theo và làm theo đúng yêu cầu.
4. Chi phí trên cùng sáu tác vụ: baseline trung bình 180071 token/142.5 giây; subagents 242953/227.7 (tăng khoảng 35% token và 60% thời gian); skill 181488/157.5 (tăng khoảng 0.8% token và 10.5% thời gian). Hiệu suất mean(score)/mean(tokens)*100000 lần lượt 0.350, 0.211, 0.385. Skill tốt nhất theo phép đo này; subagents chưa đáng chi phí trong lần đo. Bảng không gồm curator 8999 token, ba lượt dev, lượt lỗi hoặc lượt ngắt không ghi đủ usage; tổng chi phí thực cao hơn. Thời gian gồm công cụ, rate limiter và nạp thư viện, không chỉ inference. Đây là hiệu suất quan sát được trên mẫu nhỏ, không phải kết luận tổng quát về đa tác tử.
5. Curator chỉ dùng baseline role=learn, feedback và vết học. Skill đã sinh trước mọi điểm/vết đánh giá, không chỉnh sau khi thấy kết quả; H1–H3 đã commit trước freeze và giữ nguyên. validate_skill chặn marker đánh giá/tên đường dẫn không an toàn; không thấy đáp án hoặc định danh đánh giá trong skill. Ví dụ sentinel -999 bám vào dữ liệu học là dấu hiệu cần thận trọng về quá khớp; validator không chặn mọi cách diễn đạt lại nên không chứng minh tuyệt đối không rò rỉ. Mức tăng học lớn hơn đánh giá cũng có thể do nhiễu, chưa đủ bằng chứng kết luận quá khớp.
6. Cùng bộ skill không chỉnh sửa, mức biến động trước/sau freeze như sau:

| Tác vụ học | Dev trước freeze | Chính thức sau freeze | Chênh lệch điểm chuẩn hóa |
|---|---|---|---|
| code | 8/10 | 9/10 | +0.100 |
| data | 5/8 | 5/8 | 0.000 |
| logs | 6/9 | 7/9 | +0.111 |
| Trung bình | 0.697 | 0.768 | +0.070 |

Chênh lệch +0.070 khi skill giữ nguyên bằng khoảng 68% mức tăng +0.104 so với baseline học ở bảng chính thức. Dev chỉ tăng +0.033 so với baseline. Số skill đọc cũng thay đổi; SDK bỏ qua temperature=0, nên không coi lần đo là deterministic. Không gán mọi chênh lệch cho hiệu quả học; cần lặp độc lập nhiều lần nếu muốn ước lượng lợi ích và khoảng dao động tin cậy.

## 9. Hạn chế và tính hợp lệ

1. Chỉ ba tác vụ mỗi vai trò, có các quy ước do giảng viên thiết kế; kết quả không đại diện mọi bài toán thực tế.
2. Mỗi cấu hình có một lượt chính thức mỗi tác vụ; sampling mặc định và nhiễu dev/chính thức làm giảm độ chắc chắn của thứ hạng và mức cải thiện.
3. Chỉ một model/free tier. Quota ngày làm gián đoạn, sau đó dùng key thuộc project khác để hoàn tất cùng model và cấu hình. Đổi project và thời điểm chạy có thể ảnh hưởng độ trễ; không có bằng chứng đổi cấu hình mô hình. Lượt code học bị ngắt phiên công cụ không có đủ usage, khiến tổng chi phí thực không xác định đầy đủ.
4. Trace giữ luồng chính, còn token cộng cả subagent. Không thấy nội bộ subagent hoặc output đã bị dọn sau chấm, nên không thể quy nguyên nhân chính xác cho lỗi logs-eval chỉ từ điểm 0.
5. Các kết quả kỹ thuật dựa vào checker sẵn có; đạt checker không chứng minh mọi hành vi đều đúng. Chuẩn hóa LF trong bản sao sandbox cần thiết cho hash test ở Linux, không thay đổi nguồn repo.

## 10. Kết luận

Harness đạt 32 test trên Linux, hoàn tất 18 lượt chính thức và cả sáu lượt skill vượt kiểm tra freeze. Skill có điểm trung bình học/đánh giá 0.768/0.631, cao hơn baseline 0.664/0.597 và có hiệu suất điểm trên token tốt nhất trong lần đo này. Lợi ích tập trung vào một số quy ước đã học, còn quy ước mới chưa cải thiện và code đánh giá mất một check kỹ thuật. Subagents tốn thêm token nhưng giảm điểm đánh giá, đặc biệt khi main tin báo cáo mà không kiểm tra output. Nên cải tiến truyền yêu cầu và kiểm chứng của main, rồi lặp nhiều lần để tách hiệu quả khỏi nhiễu.

## Phụ lục

- Lệnh đã chạy (theo thứ tự): cài editable trong Ubuntu WSL; pytest (report/tests.txt); tour (report/tour.txt); run_experiment baseline learn; subagents learn; run_curator một lần; skills-auto learn; lưu bản dev. Sau commit/tag: baseline eval; subagents eval; skills-auto all, tiếp tục cùng lệnh sau lỗi phiên. Daily quota từng dừng ở data-eval; các bản lỗi tạm đã bỏ khỏi bài nộp. Sau khi chủ repo thay key thuộc project khác, tiếp tục bốn tác vụ còn lại cùng cấu hình. verify_freeze OK cho đủ 6 lượt; check_breakdown và lab.compare đã chạy offline. Chi tiết lệnh/cấu hình trong report/RUNBOOK.md.
- Thử thách mở rộng: không thực hiện Phần 6 tùy chọn.
- Kiểm tra trước nộp: chạy lại toàn bộ 32 test ngoại tuyến trên Ubuntu WSL đạt; verify_freeze xác nhận 6 lượt OK; 18 bản ghi chính thức khớp bảng và trace; các tệp/hàm được bảo vệ khớp repo gốc. Đã rà khóa API trong file nộp và lịch sử Git, không phát hiện; .env và .venv được bỏ qua. Bỏ các bản lỗi API/CRLF và bảng dev trùng, giữ 3 lượt dev để phân tích nhiễu.

## Trạng thái thực hiện

Phần 0–5 bắt buộc đã hoàn tất: code, 32 test Linux, 18/18 lượt chính thức, phân tích skill/nhiễu, bảng so sánh và báo cáo. Phần 6 tùy chọn không thực hiện. Commit hypotheses và freeze/tag do chủ repo tạo; commit báo cáo/kết quả cuối và push vẫn do chủ repo thực hiện sau khi review. Không sửa skill hoặc tạo lại tag freeze.

Ghi nhận runtime: SDK cảnh báo Gemini 3.5 Flash-Lite dùng sampling mặc định cố định và bỏ qua `temperature`. Vì vậy `LAB_TEMPERATURE=0` là cấu hình gửi vào, không phải bằng chứng mô hình chạy deterministic; dùng cùng mặc định giữa các điều kiện.

Khắc phục môi trường: hash test gốc trong checkout CRLF là `efb5e7650d4f03356e8353d209fbcfe81505ce2fd648bd558d5ada6e8b92ff19`, còn dạng LF là `79e05f4cc2e62a4f606d210b0b08a2cc21777245bc2f6ad244a126e9a2aee00d`, khớp checker. Chỉ chuẩn hóa bản sao sandbox; nguồn repo được giữ nguyên.


Tài liệu đối chiếu: README mục 5 (sản phẩm nộp); GUIDE phần 2.3 (ngữ cảnh giao việc), 3.3–3.4 (skill và mức áp dụng), 4.0–4.4 (freeze, nhiễu); guides/pseudocode/05_skill_quality.md (description và chất lượng skill).
