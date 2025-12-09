"""
Cloudinary Utilities Module
Xử lý upload, optimize, và xoá ảnh từ Cloudinary
"""
import cloudinary
import cloudinary.uploader
from django.conf import settings
from django.core.files.base import ContentFile
import os


class CloudinaryImageHandler:
    """Xử lý upload ảnh lên Cloudinary"""
    
    @staticmethod
    def get_cloudinary_url(image_field, transformations=''):
        """
        Lấy URL của ảnh từ Cloudinary với optional transformations
        
        Args:
            image_field: CloudinaryField object
            transformations: Chuỗi Cloudinary transformation
                            Ví dụ: "w_500,h_500,c_fill,q_auto"
        
        Returns:
            str: URL đầy đủ từ Cloudinary
        """
        if not image_field:
            return None
        
        try:
            base_url = image_field.url
            
            if transformations and 'cloudinary.com' in base_url:
                # Chèn transformations vào URL
                if '/upload/' in base_url:
                    parts = base_url.split('/upload/')
                    return f"{parts[0]}/upload/{transformations}/{parts[1]}"
            
            return base_url
        except Exception as e:
            print(f"Error getting Cloudinary URL: {e}")
            return None
    
    @staticmethod
    def optimize_image_url(image_field, width=None, height=None, quality='auto'):
        """
        Optimize ảnh từ Cloudinary bằng cách thêm query parameters
        
        Args:
            image_field: CloudinaryField object
            width: Chiều rộng mong muốn (px)
            height: Chiều cao mong muốn (px)
            quality: Chất lượng (auto, 80, 90, 100)
        
        Returns:
            str: URL đã optimize
        """
        if not image_field:
            return None
        
        try:
            base_url = image_field.url
            
            # Xây dựng transformation string
            transformations = []
            if width:
                transformations.append(f"w_{width}")
            if height:
                transformations.append(f"h_{height}")
            if width and height:
                transformations.append("c_fill")  # crop-fill mode
            transformations.append(f"q_{quality}")
            transformations.append("f_auto")  # auto format
            
            transformation_str = ','.join(transformations)
            
            # Nếu là Cloudinary URL, chèn transformations
            if 'cloudinary.com' in base_url and '/upload/' in base_url:
                parts = base_url.split('/upload/')
                return f"{parts[0]}/upload/{transformation_str}/{parts[1]}"
            
            return base_url
        except Exception as e:
            print(f"Error optimizing image URL: {e}")
            return image_field.url if image_field else None
    
    @staticmethod
    def get_avatar_url(user, size=50, quality='auto'):
        """
        Lấy avatar URL của user với optimization
        
        Args:
            user: User object
            size: Kích thước avatar (px)
            quality: Chất lượng (auto, 80, 90)
        
        Returns:
            str: URL avatar đã optimize hoặc fallback
        """
        if not hasattr(user, 'avatar') or not user.avatar:
            return '/static/media/avatars/avt.jpg'
        
        try:
            url = user.avatar.url
            
            # Nếu là Cloudinary URL, optimize
            if 'cloudinary.com' in url:
                return CloudinaryImageHandler.optimize_image_url(
                    user.avatar, 
                    width=size, 
                    height=size, 
                    quality=quality
                )
            
            return url
        except Exception:
            return '/static/media/avatars/avt.jpg'
    
    @staticmethod
    def delete_from_cloudinary(public_id):
        """
        Xoá ảnh từ Cloudinary
        
        Args:
            public_id: Public ID của ảnh trên Cloudinary
        
        Returns:
            bool: True nếu xoá thành công
        """
        if not settings.CLOUDINARY_CONFIGURED:
            return False
        
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get('result') == 'ok'
        except Exception as e:
            print(f"Error deleting from Cloudinary: {e}")
            return False
    
    @staticmethod
    def upload_file(file, folder='general', tags=None):
        """
        Upload file lên Cloudinary
        
        Args:
            file: File object
            folder: Folder trên Cloudinary (avatars, tickets, etc.)
            tags: List các tags
        
        Returns:
            dict: Kết quả upload từ Cloudinary API
        """
        if not settings.CLOUDINARY_CONFIGURED:
            return None
        
        try:
            result = cloudinary.uploader.upload(
                file,
                folder=f"hotro-enspire/{folder}",
                resource_type='auto',
                tags=tags or [],
            )
            return result
        except Exception as e:
            print(f"Error uploading to Cloudinary: {e}")
            return None


def get_fallback_avatar_url():
    """Lấy URL fallback mặc định cho avatar"""
    return '/static/media/avatars/avt.jpg'


def is_cloudinary_enabled():
    """Kiểm tra Cloudinary có được bật không"""
    return getattr(settings, 'CLOUDINARY_CONFIGURED', False)
