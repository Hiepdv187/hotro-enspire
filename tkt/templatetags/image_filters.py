from django import template
from django.utils.safestring import mark_safe
from django.conf import settings

register = template.Library()


@register.filter
def image_url(image_field, default_url=None):
    """
    Lọc để lấy URL của ảnh từ CloudinaryImageField hoặc local file
    Sử dụng: {{ user.avatar|image_url:"{% static 'media/avatars/avt.jpg' %}" }}
    
    Args:
        image_field: ImageField object
        default_url: URL fallback nếu không có ảnh
    
    Returns:
        URL của ảnh từ Cloudinary hoặc fallback
    """
    if image_field:
        try:
            return image_field.url
        except Exception:
            return default_url or ''
    return default_url or ''


@register.filter
def cloudinary_image_url(image_field, transformations=''):
    """
    Lấy URL Cloudinary với transformations (resize, quality, etc.)
    
    Ví dụ:
        {{ user.avatar|cloudinary_image_url:"w_500,h_500,c_fill,q_auto" }}
        {{ ticket.image|cloudinary_image_url:"w_800,h_600,c_limit" }}
    
    Args:
        image_field: CloudinaryField hoặc ImageField
        transformations: Chuỗi Cloudinary transformation (ví dụ: "w_500,h_500")
    
    Returns:
        URL đã optimize từ Cloudinary
    """
    if not image_field:
        return ''
    
    try:
        base_url = image_field.url
        
        # Chỉ áp dụng transformations nếu là Cloudinary URL (có /upload/)
        if transformations and '/upload/' in base_url and settings.CLOUDINARY_CONFIGURED:
            # Chèn transformations vào URL Cloudinary
            # Format: https://res.cloudinary.com/cloud_name/image/upload/[transformations]/path
            url_parts = base_url.split('/upload/')
            return f"{url_parts[0]}/upload/{transformations}/{url_parts[1]}"
        
        # Trả về URL gốc cho local files hoặc khi không có transformations
        return base_url
    except Exception:
        return ''


@register.filter
def cloudinary_video_url(video_field, transformations=''):
    """
    Lấy URL Cloudinary cho video với transformations
    
    Ví dụ:
        {{ ticket.up_video|cloudinary_video_url:"q_auto,f_auto" }}
        {{ video|cloudinary_video_url:"w_1280,h_720,c_limit,q_auto" }}
    
    Args:
        video_field: VideoField hoặc FileField
        transformations: Chuỗi Cloudinary transformation cho video
    
    Returns:
        URL đã optimize từ Cloudinary
    """
    if not video_field:
        return ''
    
    try:
        base_url = video_field.url
        
        # Chỉ áp dụng transformations nếu là Cloudinary URL (có /upload/)
        if transformations and '/upload/' in base_url and settings.CLOUDINARY_CONFIGURED:
            # Chèn transformations vào URL Cloudinary
            # Format: https://res.cloudinary.com/cloud_name/video/upload/[transformations]/path
            url_parts = base_url.split('/upload/')
            return f"{url_parts[0]}/upload/{transformations}/{url_parts[1]}"
        
        # Trả về URL gốc cho local files
        return base_url
    except Exception:
        return ''


@register.filter
def avatar_url(user, size='50x50'):
    """
    Lấy avatar URL của user với fallback
    
    Ví dụ:
        {{ request.user|avatar_url:"100x100" }}
        {{ user|avatar_url }}
    
    Args:
        user: User object
        size: Kích thước avatar (mặc định: 50x50)
    
    Returns:
        URL avatar từ Cloudinary hoặc fallback local
    """
    if not hasattr(user, 'avatar'):
        return '/static/media/avatars/avt.jpg'
    
    if user.avatar:
        try:
            url = user.avatar.url
            # Nếu là Cloudinary URL, thêm transformation cho optimization
            if 'cloudinary.com' in url:
                width, height = size.split('x') if 'x' in size else ('50', '50')
                # Sử dụng path-based transformation thay vì query params
                if '/upload/' in url:
                    url_parts = url.split('/upload/')
                    return f"{url_parts[0]}/upload/w_{width},h_{height},c_fill,q_auto,f_auto/{url_parts[1]}"
            return url
        except Exception:
            pass
    
    # Fallback
    return '/static/media/avatars/avt.jpg'


@register.inclusion_tag('_image_tag.html')
def image_with_fallback(image_field, fallback_url, alt_text='Image', css_class=''):
    """
    Template tag để render <img> với fallback
    
    Ví dụ:
        {% image_with_fallback user.avatar "{% static 'media/avatars/avt.jpg' %}" "User Avatar" "avatar" %}
    
    Lợi ích:
        - Tự động handle fallback
        - Tự động add Cloudinary transformations
        - Bảo vệ khỏi broken images
    """
    if image_field:
        try:
            src = image_field.url
            # Optimize Cloudinary images với path-based transformation
            if 'cloudinary.com' in src and '/upload/' in src:
                url_parts = src.split('/upload/')
                src = f"{url_parts[0]}/upload/q_auto,f_auto/{url_parts[1]}"
        except Exception:
            src = fallback_url
    else:
        src = fallback_url
    
    return {
        'src': src,
        'alt': alt_text,
        'css_class': css_class,
    }
