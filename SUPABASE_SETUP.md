# Supabase Setup Guide - Real-time Notifications

## 📋 Tổng quan

Hệ thống notifications sử dụng Supabase thay cho Redis để lưu trữ:
- **Online users**: Danh sách users đang online
- **Pending notifications**: Thông báo chờ gửi cho users offline
- **Notification counts**: Số lượng thông báo chưa đọc

## 🚀 Hướng dẫn Setup

### Bước 1: Tạo Tables trong Supabase

1. Đăng nhập vào [Supabase Dashboard](https://app.supabase.com)
2. Chọn project của bạn
3. Vào **SQL Editor** (biểu tượng database ở sidebar)
4. Tạo **New Query**
5. Copy toàn bộ nội dung file `supabase_setup.sql` và paste vào
6. Click **Run** để thực thi

### Bước 2: Cấu hình Environment Variables

Thêm vào file `.env`:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# Redis (optional - có thể bỏ nếu chỉ dùng Supabase)
REDIS_URL=
```

**Lấy Supabase credentials:**
1. Vào **Settings** → **API** trong Supabase Dashboard
2. Copy **Project URL** → paste vào `SUPABASE_URL`
3. Copy **anon public** key → paste vào `SUPABASE_KEY`

### Bước 3: Verify Tables

Chạy query sau trong SQL Editor để kiểm tra:

```sql
-- Kiểm tra tables đã được tạo
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('online_users', 'pending_notifications', 'notification_counts');
```

Kết quả phải trả về 3 tables.

## 📊 Cấu trúc Tables

### 1. `online_users`
```sql
- user_id (INTEGER, PRIMARY KEY)
- connected_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

### 2. `pending_notifications`
```sql
- id (BIGSERIAL, PRIMARY KEY)
- user_id (INTEGER)
- notification_id (INTEGER)
- message (TEXT)
- read (BOOLEAN)
- timestamp (TIMESTAMP)
- created_at (TIMESTAMP)
```

### 3. `notification_counts`
```sql
- user_id (INTEGER, PRIMARY KEY)
- unread_count (INTEGER)
- updated_at (TIMESTAMP)
```

## 🔧 Troubleshooting

### Lỗi: "Could not find the table 'public.pending_notifications'"

**Nguyên nhân:** Tables chưa được tạo trong Supabase

**Giải pháp:**
1. Chạy lại file `supabase_setup.sql` trong SQL Editor
2. Kiểm tra permissions của user
3. Verify rằng bạn đang ở đúng project

### Lỗi: "relation does not exist"

**Nguyên nhân:** Schema không đúng hoặc RLS chặn truy cập

**Giải pháp:**
```sql
-- Tắt RLS tạm thời để test
ALTER TABLE public.online_users DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.pending_notifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_counts DISABLE ROW LEVEL SECURITY;
```

### Lỗi: "permission denied"

**Nguyên nhân:** Thiếu quyền truy cập

**Giải pháp:**
```sql
-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
```

## 🧪 Testing

### Test trong Python Shell

```python
from tkt.supabase_client import *

# Test connection
client = get_supabase_client()
print(client)  # Should not be None

# Test add online user
add_online_user(1)

# Test check online
print(is_user_online(1))  # Should return True

# Test pending notification
store_pending_notification(1, {
    'id': 123,
    'message': 'Test notification',
    'read': False,
    'timestamp': '2024-12-04T12:00:00'
})

# Get pending notifications
notifications = get_pending_notifications(1)
print(notifications)

# Cleanup
remove_online_user(1)
clear_pending_notifications(1)
```

## 📝 Maintenance

### Cleanup Old Data

Chạy định kỳ để xóa notifications cũ:

```sql
-- Xóa pending notifications cũ hơn 7 ngày
DELETE FROM public.pending_notifications
WHERE created_at < NOW() - INTERVAL '7 days';

-- Xóa online users không active (optional)
DELETE FROM public.online_users
WHERE updated_at < NOW() - INTERVAL '1 hour';
```

### Monitor Tables

```sql
-- Số lượng users online
SELECT COUNT(*) FROM public.online_users;

-- Số lượng pending notifications
SELECT user_id, COUNT(*) as pending_count
FROM public.pending_notifications
GROUP BY user_id;

-- Top users với nhiều unread notifications
SELECT user_id, unread_count
FROM public.notification_counts
ORDER BY unread_count DESC
LIMIT 10;
```

## 🔐 Security Notes

1. **Row Level Security (RLS)** đã được enable
2. Users chỉ có thể xem data của chính họ
3. Service role key cần được bảo mật (không commit vào git)
4. Sử dụng anon key cho client-side operations

## 📚 References

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)
- [Django Channels](https://channels.readthedocs.io/)
