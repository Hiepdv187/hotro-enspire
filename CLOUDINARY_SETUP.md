# Cloudinary Integration - Hướng dẫn

## 📋 Tổng quan
Project đã được cấu hình để **tất cả ảnh upload luôn sử dụng Cloudinary** từ sau cập nhật này.

## ✅ Những gì đã được thực hiện

### 1. **Cấu hình Cloudinary (tkt/settings.py)**
- ✅ Đã load `CLOUDINARY_URL` từ `.env`
- ✅ Đã set `DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'`
- ✅ Cloudinary được khởi tạo tự động khi server start

### 2. **Xóa Signal không phù hợp (accounts/models.py)**
- ✅ Xóa `resize_avatar` signal (không hoạt động với Cloudinary)
- ✅ Cloudinary tự động optimize ảnh thông qua URL transformations

### 3. **Template Tags & Filters (tkt/templatetags/image_filters.py)**
Tạo các template filters để dễ dàng sử dụng Cloudinary URLs:
- `image_url` - Lấy URL ảnh với fallback
- `cloudinary_image_url` - Thêm transformations (resize, quality)
- `avatar_url` - Lấy avatar với fallback
- `image_with_fallback` - Render `<img>` tag tự động

### 4. **Utility Module (tkt/cloudinary_utils.py)**
Tạo `CloudinaryImageHandler` class với các phương thức:
- `get_cloudinary_url()` - Lấy URL Cloudinary
- `optimize_image_url()` - Optimize ảnh (resize, quality)
- `get_avatar_url()` - Lấy avatar URL
- `delete_from_cloudinary()` - Xóa ảnh từ Cloudinary

### 5. **Form Validation (accounts/form.py & ticket/form.py)**
Thêm validation cho tất cả file uploads:
- ✅ Kiểm tra kích thước file (max 5MB avatar, 10MB images, 100MB videos)
- ✅ Kiểm tra định dạng file (JPG, PNG, GIF, WebP)
- ✅ Hiển thị thông báo lỗi rõ ràng cho user

### 6. **Templates (Updated)**
- ✅ `base.html` - Avatar URL với Cloudinary optimization + fallback
- ✅ `ticket_details.html` - Ticket images/comments với fallback + error handling
- ✅ Thêm `onerror` handlers để fallback về local nếu Cloudinary lỗi

## 🎯 Cách hoạt động

### Khi upload ảnh:
1. User chọn file ảnh
2. Form validation kiểm tra kích thước & định dạng
3. File được upload lên Cloudinary (tự động qua `DEFAULT_FILE_STORAGE`)
4. Database lưu URL từ Cloudinary

### Khi hiển thị ảnh:
```html
<!-- Avatar với optimization + fallback -->
<img src="{{ user.avatar.url }}?w=50&h=50&c=fill&q=auto&f=auto" 
     onerror="this.src='{% static 'media/avatars/avt.jpg' %}'">

<!-- Ticket image -->
<img src="{{ ticket.image.url }}?w=800&h=600&c_limit&q=auto"
     onerror="this.style.display='none'">
```

Cloudinary transformation URL examples:
- `w_500` - Set width to 500px
- `h_500` - Set height to 500px
- `c_fill` - Crop to fit
- `q_auto` - Automatic quality
- `f_auto` - Automatic format (WebP, etc.)

## 📦 Dependencies

Tất cả đã được install (check requirements.txt):
```
cloudinary>=1.35.0
django-cloudinary-storage>=0.3.0
```

## ⚙️ Environment Variables

`.env` file đã có:
```
CLOUDINARY_URL=cloudinary://987634864271975:ffv9j1vPTGZSsbZpqZ2rXcz0jAU@dcvcdw6gg
```

## 🚀 Cách sử dụng trong template

### Option 1: Direct URL (Recommended)
```html
<img src="{{ user.avatar.url }}?w=50&h=50&c=fill&q=auto" 
     onerror="this.src='{% static 'media/avatars/avt.jpg' %}'">
```

### Option 2: Sử dụng Template Filter (Advanced)
```html
{% load image_filters %}
<img src="{{ user.avatar|cloudinary_image_url:'w_50,h_50,c_fill,q_auto' }}">
```

### Option 3: Sử dụng Utility trong View
```python
from tkt.cloudinary_utils import CloudinaryImageHandler

avatar_url = CloudinaryImageHandler.optimize_image_url(
    user.avatar, 
    width=50, 
    height=50, 
    quality='auto'
)
```

## 🔧 Cách sử dụng CloudinaryImageHandler

```python
from tkt.cloudinary_utils import CloudinaryImageHandler

# Lấy avatar URL đã optimize
avatar_url = CloudinaryImageHandler.get_avatar_url(user, size=100)

# Lấy image URL với custom transformations
image_url = CloudinaryImageHandler.get_cloudinary_url(
    ticket.image, 
    transformations='w_800,h_600,c_limit,q_auto'
)

# Xóa ảnh từ Cloudinary
CloudinaryImageHandler.delete_from_cloudinary('folder/public_id')
```

## ✨ Cloudinary Transformation Cheatsheet

```
Resizing:
- w_500 - Width 500px
- h_500 - Height 500px
- c_fill - Crop to fill
- c_limit - Limit size without cropping

Quality:
- q_auto - Automatic quality
- q_80/90/100 - Set quality

Format:
- f_auto - Automatic format (WebP, etc.)
- f_jpg/png/gif - Force format

Combined Example:
?w_500&h_500&c_fill&q_auto&f_auto
```

## 🐛 Troubleshooting

### Image not loading?
1. Check Cloudinary credentials in `.env`
2. Check `CLOUDINARY_CONFIGURED` setting
3. Check browser console for 404 errors
4. Add `onerror` handlers in templates

### Upload failed?
1. Check file size (avatar max 5MB, images max 10MB)
2. Check file format (JPEG, PNG, GIF, WebP only)
3. Check Cloudinary account quota

### Slow image loading?
1. Add `?f_auto` to automatically serve best format
2. Use responsive images with `srcset`
3. Lazy load with `loading="lazy"`

## 📝 Model Changes

Avatar fields now upload to Cloudinary:
```python
# accounts/models.py - User.avatar
avatar = models.ImageField(
    upload_to=user_directory_path,  # avatars/
    default='avatars/avt.jpg',      # fallback
    blank=True, 
    null=True
)

# ticket/models.py - Ticket.image, Comments.image, Reply.image
image = models.ImageField(
    upload_to=user_directory_paths,  # media/
    blank=True, 
    null=True
)
```

## 📚 Next Steps (Optional)

1. **Responsive Images**: Add `srcset` for different screen sizes
2. **Lazy Loading**: Add `loading="lazy"` to img tags
3. **WebP Support**: Use `f_auto` transformation
4. **Image Processing**: Add filters/effects with Cloudinary
5. **Analytics**: Enable Cloudinary analytics

---

**Status**: ✅ All images from now on will use Cloudinary

