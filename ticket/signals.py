from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils import timezone
from datetime import timedelta
import os
from django.conf import settings
from .models import Ticket, Comments, Reply
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from tkt.cloudinary_utils import CloudinaryImageHandler

def cleanup_old_attachments():
    """
    Hàm dọn dẹp file đính kèm cũ (local và Cloudinary)
    """
    logger = logging.getLogger(__name__)
    three_months_ago = timezone.now() - timedelta(days=30)
    cloudinary_handler = CloudinaryImageHandler()
    
    try:
        # Xóa file đính kèm trong Ticket
        tickets = Ticket.objects.filter(created_on__lt=three_months_ago)
        for ticket in tickets:
            if ticket.image:
                try:
                    # Xóa từ Cloudinary (nếu có)
                    cloudinary_handler.delete_from_cloudinary(ticket.image)
                    
                    # Xóa file local (nếu có)
                    file_path = os.path.join(settings.MEDIA_ROOT, str(ticket.image))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f'Đã xóa ảnh ticket local: {file_path}')
                except Exception as e:
                    logger.error(f'Lỗi khi xóa ảnh ticket {ticket.image}: {str(e)}')
            
            if ticket.up_video:
                try:
                    # Xóa từ Cloudinary (nếu có)
                    cloudinary_handler.delete_from_cloudinary(ticket.up_video)
                    
                    # Xóa file local (nếu có)
                    file_path = os.path.join(settings.MEDIA_ROOT, str(ticket.up_video))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f'Đã xóa video ticket local: {file_path}')
                except Exception as e:
                    logger.error(f'Lỗi khi xóa video ticket {ticket.up_video}: {str(e)}')
        
        # Xóa file đính kèm trong Comments
        comments = Comments.objects.filter(created_at__lt=three_months_ago)
        for comment in comments:
            if comment.image:
                try:
                    # Xóa từ Cloudinary (nếu có)
                    cloudinary_handler.delete_from_cloudinary(comment.image)
                    
                    # Xóa file local (nếu có)
                    file_path = os.path.join(settings.MEDIA_ROOT, str(comment.image))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f'Đã xóa ảnh bình luận local: {file_path}')
                except Exception as e:
                    logger.error(f'Lỗi khi xóa ảnh bình luận {comment.image}: {str(e)}')
        
        # Xóa file đính kèm trong Reply
        replies = Reply.objects.filter(created_at__lt=three_months_ago)
        for reply in replies:
            if reply.image:
                try:
                    # Xóa từ Cloudinary (nếu có)
                    cloudinary_handler.delete_from_cloudinary(reply.image)
                    
                    # Xóa file local (nếu có)
                    file_path = os.path.join(settings.MEDIA_ROOT, str(reply.image))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f'Đã xóa ảnh phản hồi local: {file_path}')
                except Exception as e:
                    logger.error(f'Lỗi khi xóa ảnh phản hồi {reply.image}: {str(e)}')
        
        logger.info('Hoàn thành dọn dẹp file đính kèm cũ')
    except Exception as e:
        logger.error(f'Lỗi trong quá trình dọn dẹp: {str(e)}')

def start_scheduler():
    """
    Khởi tạo và chạy scheduler
    """
    scheduler = BackgroundScheduler()
    # Chạy vào lúc 2h sáng mỗi ngày
    scheduler.add_job(
        cleanup_old_attachments,
        'cron',
        hour=2,
        minute=0,
        id='cleanup_attachments',
        name='Dọn dẹp file đính kèm cũ',
        replace_existing=True
    )
    scheduler.start()

class TicketConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ticket'
    
    def ready(self):
        # Chỉ chạy khi không phải lệnh migrate
        import os
        if os.environ.get('RUN_MAIN') or os.environ.get('RUN_WEB'):
            # Chạy ngay lần đầu
            cleanup_old_attachments()
            # Lên lịch chạy định kỳ
            start_scheduler()
