from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import os
from ticket.models import Ticket, Comments, Reply
from django.conf import settings

class Command(BaseCommand):
    help = 'Delete ticket attachments older than 3 months'

    def handle(self, *args, **options):
        # Calculate the date 3 months ago
        three_months_ago = timezone.now() - timedelta(days=30)
        
        # Clean up Ticket attachments
        tickets = Ticket.objects.filter(created_on__lt=three_months_ago)
        for ticket in tickets:
            # Delete image if exists
            if ticket.image:
                try:
                    file_path = os.path.join(settings.MEDIA_ROOT, str(ticket.image))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        self.stdout.write(f'Deleted ticket image: {file_path}')
                except Exception as e:
                    self.stderr.write(f'Error deleting ticket image {ticket.image}: {str(e)}')
            
            # Delete video if exists
            if ticket.up_video:
                try:
                    file_path = os.path.join(settings.MEDIA_ROOT, str(ticket.up_video))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        self.stdout.write(f'Deleted ticket video: {file_path}')
                except Exception as e:
                    self.stderr.write(f'Error deleting ticket video {ticket.up_video}: {str(e)}')
        
        # Clean up Comments attachments
        comments = Comments.objects.filter(created_at__lt=three_months_ago)
        for comment in comments:
            if comment.image:
                try:
                    file_path = os.path.join(settings.MEDIA_ROOT, str(comment.image))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        self.stdout.write(f'Deleted comment image: {file_path}')
                except Exception as e:
                    self.stderr.write(f'Error deleting comment image {comment.image}: {str(e)}')
        
        # Clean up Reply attachments
        replies = Reply.objects.filter(created_at__lt=three_months_ago)
        for reply in replies:
            if reply.image:
                try:
                    file_path = os.path.join(settings.MEDIA_ROOT, str(reply.image))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        self.stdout.write(f'Deleted reply image: {file_path}')
                except Exception as e:
                    self.stderr.write(f'Error deleting reply image {reply.image}: {str(e)}')
        
        self.stdout.write(self.style.SUCCESS('Successfully cleaned up old attachments'))
