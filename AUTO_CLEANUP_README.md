# Tự động dọn dẹp file đính kèm Ticket

Ứng dụng này bao gồm tính năng tự động dọn dẹp các file đính kèm (hình ảnh và video) cũ hơn 3 tháng để tiết kiệm dung lượng lưu trữ.

## Cách hoạt động

1. Một Celery task `cleanup_old_attachments_task` đã được tạo để:
   - Tìm tất cả tickets, bình luận và phản hồi có file đính kèm cũ hơn 3 tháng
   - Xóa các file đính kèm tương ứng khỏi hệ thống file
   - Ghi lại nhật ký các hành động đã thực hiện

2. Quá trình dọn dẹp được lên lịch chạy tự động vào lúc 00:00 mỗi Chủ nhật hàng tuần sử dụng Celery Beat.

## Phạm vi xóa

Chức năng này sẽ xóa các file đính kèm trong các phần sau:
- Hình ảnh và video đính kèm trong ticket
- Hình ảnh trong bình luận (comments)
- Hình ảnh trong phản hồi (replies)

## Hướng dẫn triển khai trên Production

### 1. Cài đặt các gói cần thiết

Cập nhật các gói cần thiết:
```bash
pip install -r requirements.txt
```

### 2. Cấu hình systemd (cho Ubuntu/Debian)

1. Tạo thư mục log cho Celery:
```bash
sudo mkdir -p /var/log/celery/
sudo chown -R www-data:www-data /var/log/celery/
```

2. Sao chép file cấu hình systemd:
```bash
sudo cp deploy/celery.service /etc/systemd/system/
sudo cp deploy/celery-beat.service /etc/systemd/system/
```

3. Chỉnh sửa các file service để phù hợp với hệ thống của bạn:
   - Cập nhật `WorkingDirectory` thành đường dẫn đến thư mục dự án
   - Cập nhật đường dẫn đến Python virtual environment
   - Đảm bảo user/group phù hợp (thường là www-data)

4. Khởi động các dịch vụ:
```bash
sudo systemctl daemon-reload
sudo systemctl start celery
sudo systemctl start celery-beat
sudo systemctl enable celery
sudo systemctl enable celery-beat
```

### 3. Kiểm tra trạng thái dịch vụ

```bash
sudo systemctl status celery
sudo systemctl status celery-beat
```

## Chạy thủ công

Nếu bạn muốn chạy tác vụ dọn dẹp ngay lập tức:

1. Vào thư mục dự án và kích hoạt môi trường ảo (nếu có)
2. Chạy lệnh:
```bash
python manage.py shell
```

3. Trong shell, thực hiện:
```python
from ticket.tasks import cleanup_old_attachments_task
cleanup_old_attachments_task.delay()
```

## Xem nhật ký

Các thông tin về quá trình dọn dẹp sẽ được ghi vào:
- `/var/log/celery/worker.log` - Nhật ký worker
- `/var/log/celery/beat.log` - Nhật ký lịch trình
- Nhật ký ứng dụng Django của bạn

## Lưu ý quan trọng

1. Đảm bảo backup dữ liệu trước khi triển khai
2. Kiểm tra kỹ các đường dẫn trong file cấu hình
3. Nếu sử dụng Nginx/Apache, đảm bảo cấu hình proxy WebSocket đúng cách nếu cần
4. Kiểm tra quyền truy cập thư mục media

## Xử lý sự cố

Nếu gặp lỗi về quyền truy cập:
```bash
sudo chown -R www-data:www-data /path/to/your/project
sudo chmod -R 755 /path/to/your/project/media/
```

Nếu Celery không khởi động, kiểm tra log:
```bash
sudo journalctl -u celery.service
sudo journalctl -u celery-beat.service
```
