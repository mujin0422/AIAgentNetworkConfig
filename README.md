# Network AI Assistant

Network AI Assistant là trợ lý AI cho bài toán vận hành, kiểm tra và cấu hình thiết bị mạng Cisco trong môi trường GNS3. Dự án kết hợp `LangGraph`, `Ollama`, `Netmiko` và các tool tự động hóa để thu thập dữ liệu từ topology, phân tích sự cố và thực thi cấu hình khi được người dùng phê duyệt.

## Chức năng chính

- Thu thập topology và trạng thái node từ GNS3.
- Chạy các lệnh kiểm tra trên router/switch Cisco qua Telnet/SSH bằng Netmiko.
- Phân tích sự cố mạng bằng mô hình Analyst.
- Đề xuất kế hoạch cấu hình mới hoặc khắc phục lỗi.
- Thực thi cấu hình VLAN, trunk, sub-interface, OSPF, static route, MPLS.
- Hỗ trợ Human-in-the-Loop: mọi hành động cấu hình hoặc thao tác nhạy cảm đều yêu cầu xác nhận `yes/no`.
- Có 3 cách sử dụng:
  - CLI terminal
  - GUI desktop với `customtkinter`
  - Discord bot để điều khiển từ xa

##  Demo

[![Watch the video](https://img.youtube.com/vi/FEDlMY4MprY/0.jpg)](https://www.youtube.com/watch?v=FEDlMY4MprY)

## Kiến trúc

Hệ thống được tổ chức quanh workflow LangGraph:

1. `SupervisorAgent`
   - Điều phối luồng xử lý.
   - Chuyển truy vấn mới sang `network_expert`.
   - Sau khi có output từ tool, chuyển sang `analyst`.

2. `Network Expert`
   - Dùng `ChatOllama` cùng bộ tool mạng/GNS3.
   - Thu thập dữ liệu thiết bị, topology, ping, running-config.
   - Gọi các tool cấu hình khi được yêu cầu.

3. `Analyst`
   - Tổng hợp output từ tool.
   - Trả về báo cáo ngắn gọn bằng tiếng Việt theo 3 mục `### 1`, `### 2`, `### 3`.

## Phạm vi tool hiện có

### GNS3
- `get_topology_links`
- `check_nodes_status`
- `start_node`
- `stop_node`
- `restart_node`

### Kiểm tra thiết bị
- `execute_show_command`
- `get_running_config`
- `ping_test`
- `get_interface_ip`
- `get_routing_table`
- `get_ospf_neighbors`
- `get_vlan_switch_brief`
- `get_trunk_interfaces`

### Cấu hình
- `config_interface_ip`
- `config_ospf`
- `config_static_route`
- `config_mpls_ip_interface`
- `config_router_sub_interface`
- `config_vlan`
- `assign_vlan_access_port`
- `assign_vlan_access_range`
- `config_switch_trunk`
- `save_device_config`

## Yêu cầu môi trường

- Python 3.10+
- GNS3 Server đang chạy
- Project GNS3 tồn tại đúng `PROJECT_ID` đang hard-code trong code
- Ollama đang chạy local tại `http://localhost:11434`
- Model cho `NETWORK_EXPERT_MODEL` và `ANALYST_MODEL` đã được pull sẵn trong Ollama

## Cài đặt

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Cấu hình

### 1. File môi trường

Tạo file `.env` từ file mẫu:

```bash
copy .env_example .env
```

Lưu ý: repository hiện tại sử dụng tên file `.env_example`, không phải `.env.example`.

Các giá trị cần thiết:

```env
DISCORD_BOT_TOKEN=YOUR_TOKEN
DISCORD_CHANNEL_ID=YOUR_CHANNEL_ID
DISCORD_PREFIX=!net

OLLAMA_BASE_URL=http://localhost:11434
NETWORK_EXPERT_MODEL=YOUR_MODEL
NETWORK_EXPERT_NUM_PREDICT=768
NETWORK_EXPERT_TEMPERATURE=0.1

ANALYST_MODEL=YOUR_MODEL
ANALYST_NUM_PREDICT=1024
ANALYST_TEMPERATURE=0.1
ANALYST_MAX_TOOL_CHARS=512

SSH_TIMEOUT=15
SSH_AUTH_TIMEOUT=15
SSH_DELAY_FACTOR=1
SSH_SESSION_TIMEOUT=15
SSH_FAST_CLI=true
```

### 2. Danh sách thiết bị

File [config/devices.yaml](config/devices.yaml) chứa mapping tên thiết bị đến tham số kết nối Netmiko. Hiện tại code đang khai báo các thiết bị như:

- `P1`, `P2`
- `PE1`, `PE2`
- `CE-1A`, `CE-1B`, `CE-2A`, `CE-2B`
- `Switch1` đến `Switch4`

Mỗi mục cần có:

- `hostname`
- `port`
- `device_type`
- `username`
- `password`

### 3. GNS3

Trong code, GNS3 đang được hard-code:

- `GNS3_IP = 127.0.0.1`
- `GNS3_PORT = 3080`
- `PROJECT_ID = cc92102e-89e3-4f2d-8e66-47268c496baa`

Nếu khác môi trường của bạn, cần sửa trực tiếp trong:

- `src/main.py`
- `src/core_engine.py`
- `src/tools/gns3_tools.py`

## Cách chạy

### CLI

```bash
python -m src.main
```

Chế độ này:
- Kiểm tra kết nối GNS3 lúc khởi động
- Load thiết bị đầu tiên trong `devices.yaml`
- Cho phép nhập yêu cầu liên tục trong terminal
- Nếu agent muốn cấu hình, hệ thống sẽ hỏi `yes/no`

### GUI desktop

```bash
python -m src.app
```

Giao diện desktop được viết bằng `customtkinter`, hiển thị dạng chat và hỗ trợ xác nhận phê duyệt ngay trong luồng hỏi đáp.

### Discord bot

```bash
python -m src.discord_bot
```

Bot hỗ trợ:
- `!net <yêu cầu>`
- `!net status`
- Nếu đã đặt `DISCORD_CHANNEL_ID`, có thể chat trực tiếp trong channel đó mà không cần prefix
- Nút phê duyệt `Đồng ý` / `Từ chối` cho các lệnh cần xác nhận

Tài liệu bổ sung: [docs/discord_setup.md](docs/discord_setup.md)

## Ví dụ truy vấn

- `Kiểm tra trạng thái kết nối của P1`
- `Show ip interface brief trên PE1`
- `Ping từ P2 đến 10.10.10.1`
- `Kiểm tra OSPF neighbor trên PE2`
- `Cấu hình VLAN 10 trên Switch1`
- `Thực hiện cấu hình đã đề xuất`

Code trong `core_engine.py` có cơ chế regex để tự động đoán tên thiết bị từ query, ưu tiên các mẫu như `P1`, `P2`, `PE1`, `PE2`, `CE-1A`, `CE-1B`.

## Cấu trúc thư mục

```text
AAN/
|-- config/
|   `-- devices.yaml
|-- docs/
|   `-- discord_setup.md
|-- images/
|   `-- icon/send.png
|-- src/
|   |-- agents/
|   |   |-- analyst.py
|   |   |-- network_expert.py
|   |   `-- supervisor.py
|   |-- graph/
|   |   |-- state.py
|   |   `-- workflow.py
|   |-- tools/
|   |   |-- common_tools.py
|   |   |-- gns3_tools.py
|   |   |-- network_connection.py
|   |   |-- router_tools.py
|   |   `-- switch_tools.py
|   |-- app.py
|   |-- core_engine.py
|   |-- discord_bot.py
|   `-- main.py
|-- .env_example
|-- requirements.txt
`-- README.md
```

## Lưu ý về hiện trạng source code

- CLI (`src/main.py`) và Discord bot (`src/discord_bot.py`) đang là hai entrypoint sẵn sàng sử dụng.
- GUI (`src/app.py`) tự tạo graph riêng thay vì dùng chung `core_engine.py`.
- `src/main.py` hiện tại load thiết bị đầu tiên trong `devices.yaml`, trong khi `src/core_engine.py` có khả năng chọn thiết bị dựa trên query.
- Cấu hình GNS3 đang bị hard-code ở nhiều file, chưa đưa vào `.env`.

## Kiểm tra nhanh

Sau khi đã bật GNS3, Ollama và cài đúng model:

1. Chạy `python -m src.main`
2. Nhập: `Kiểm tra trạng thái P1`
3. Xác nhận hệ thống trả về:
   - output thu thập từ tool
   - phần báo cáo của Analyst
4. Thử một lệnh cấu hình và kiểm tra có bước phê duyệt `yes/no`

## Tài liệu liên quan

- [docs/discord_setup.md](docs/discord_setup.md)
- `configure.txt`
- `document.txt`
- `Test_case.md`
- `TODO_DISCORD.md`
