# Chạy lab trong Ubuntu WSL

Chạy từ PowerShell tại thư mục gốc của repo. Môi trường Windows `.venv` dùng được cho phần không gọi shell Linux; toàn bộ test và tác vụ thật dùng Ubuntu.

## Môi trường

```powershell
wsl -d Ubuntu -- bash -lc 'python3 -m venv .venv/wsl && .venv/wsl/bin/python -m pip install --no-compile -e .'
wsl -d Ubuntu -- .venv/wsl/bin/python -m pytest tests
wsl -d Ubuntu -- .venv/wsl/bin/python scripts/tour.py
```

Môi trường `.venv/wsl` nằm trong thư mục đã được Git bỏ qua và chỉ dùng từ Ubuntu WSL. `.env` nằm ở gốc repo, cần `LAB_MODEL=google_genai:gemini-3.5-flash-lite` và `GOOGLE_API_KEY` còn hiệu lực. Không commit khóa.

## Trình tự bắt buộc

1. Chạy baseline trên ba tác vụ học, rồi subagents trên ba tác vụ học.
2. Phân loại lỗi từ `run.json` và `trace.md` của learning baseline.
3. Chạy curator tối đa theo giới hạn của GUIDE; đọc skill, chỉ giữ/xóa, không sửa tay.
4. Chạy skills-auto trên tác vụ học để kiểm tra skill được đọc và áp dụng.
5. Điền H1–H3 trong báo cáo; commit `hypotheses`, sau đó commit `freeze skills` và tag `freeze`.
6. Sao lưu `results/skills-auto` thành `results/skills-auto-dev` trước lần chính thức.
7. Chạy baseline và subagents trên tác vụ đánh giá; chạy skills-auto trên cả sáu tác vụ.
8. Chạy `verify_freeze.py`, `lab.compare`, `check_breakdown.py` rồi hoàn thiện báo cáo.

```powershell
wsl -d Ubuntu -- .venv/wsl/bin/python -u report/run_experiment.py --condition baseline --tasks learn
wsl -d Ubuntu -- .venv/wsl/bin/python -u report/run_experiment.py --condition subagents --tasks learn
wsl -d Ubuntu -- .venv/wsl/bin/python -u report/run_curator.py
wsl -d Ubuntu -- .venv/wsl/bin/python -u report/run_experiment.py --condition skills-auto --tasks learn
```

Các lệnh đánh giá chỉ chạy sau khi đã ghi nhận và commit giả thuyết, đóng băng skill. Không coi lỗi 401/404/429/503 hoặc lỗi môi trường là bằng chứng về năng lực mô hình. Giữ các lần lỗi trong thư mục sao lưu trước khi chạy lại; dùng cùng model và cấu hình giữa các điều kiện. Nếu hết quota, tiếp tục từ tác vụ chưa hoàn tất khi quota phục hồi.

## Giới hạn cách đo

Token cộng mọi lần gọi mô hình, kể cả subagent. Tool call, subagent call và skill read đếm ở luồng chính. Runner dùng stream values, giữ trạng thái cuối nhận được nếu có lỗi; vẫn không thấy nội bộ subagent. Thư mục làm việc tạm bị dọn sau khi chấm; nguồn trong `tasks/` được giữ nguyên.

## Chạy có giới hạn thời gian chờ

```powershell
wsl -d Ubuntu -- .venv/wsl/bin/python -u report/run_experiment.py --condition baseline --tasks learn
```

Lệnh phụ này dùng timeout 60 giây/request, không retry ngầm, tối đa hai lần thử khi lỗi 429/503, chờ 30 giây giữa các lần. Gemini dùng reasoning effort `low`, nhiệt độ vẫn theo `.env`. Các lần lỗi được lưu tại `results/api-attempts/`; tác vụ hoàn tất không bị chạy lại. Dùng cùng cấu hình này cho mọi điều kiện.

Ghi nhận runtime: SDK cảnh báo Gemini 3.5 Flash-Lite dùng sampling mặc định cố định và bỏ qua `temperature`. Vì vậy `LAB_TEMPERATURE=0` là cấu hình gửi vào, không phải bằng chứng mô hình chạy deterministic; dùng cùng mặc định giữa các điều kiện.

Giới hạn tốc độ: 0.14 request/giây (khoảng một lần mỗi 7.2 giây), dùng chung model/rate limiter giữa agent chính và subagent. Quota quan sát được là 15 request/phút; vẫn phải theo dõi token/phút và request/ngày. Runner dùng stream values để giữ trace nhận được trước khi ngoại lệ xảy ra.

Checkout Windows dùng CRLF nhưng checker code hash test gốc ở dạng LF. Runner chỉ chuẩn hóa CRLF→LF cho các tệp Python trong bản sao sandbox trước khi agent chạy, không sửa `tasks/` trong repo. Baseline code đầu tiên trước sửa môi trường được lưu riêng và không dùng trong bảng chính thức.

## Git do chủ repo thực hiện

Codex chỉ đọc trạng thái Git. Mọi stage, commit, tag đóng băng và push do chủ repo chạy sau khi xem báo cáo/skill. Khi hoàn tất Phần 3 và điền giả thuyết, dùng:

```powershell
git add src/lab report results skills/auto
git commit -m "hypotheses"
git commit --allow-empty -m "freeze skills"
git tag freeze
```

Không chạy đánh giá trước khi có hai commit và tag này. Chưa có lệnh push tự động. Nếu tag freeze đã tồn tại, không ghi đè: kiểm tra lịch sử và báo cáo trước.

## Tiếp tục sau khi chủ repo đã tạo tag

Kết quả Phần 3.4 đã được chuyển vào `results/skills-auto-dev`; không cần chuyển lại. Giữ nguyên `skills/auto/` từ đây. Dùng cùng lệnh phụ và cấu hình như các lượt học:

```powershell
wsl -d Ubuntu -- .venv/wsl/bin/python -u report/run_experiment.py --condition baseline --tasks eval
wsl -d Ubuntu -- .venv/wsl/bin/python -u report/run_experiment.py --condition subagents --tasks eval
wsl -d Ubuntu -- .venv/wsl/bin/python -u report/run_experiment.py --condition skills-auto --tasks all
wsl -d Ubuntu -- .venv/wsl/bin/python scripts/verify_freeze.py
wsl -d Ubuntu -- .venv/wsl/bin/python -m lab.compare > report/table.md
wsl -d Ubuntu -- .venv/wsl/bin/python scripts/check_breakdown.py
```

Chạy kiểm tra freeze trong WSL, cùng nền tảng với runner để hash đường dẫn tương đối nhất quán. Sau các lượt này, cập nhật mục 7–10 của báo cáo và so sánh điểm học chính thức với bản dev. Mọi commit báo cáo cuối và push vẫn do chủ repo làm.
