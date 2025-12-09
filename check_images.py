import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tkt.settings')
django.setup()

from ticket.models import Ticket, Comments, Reply

# Find tickets with images
tickets = Ticket.objects.filter(image__isnull=False).exclude(image__exact='')
print(f'Tickets with images: {tickets.count()}')
for ticket in tickets[:5]:
    print(f'  ID: {ticket.ticket_id}, Image: {ticket.image.name if ticket.image else "none"}')

print()

# Find comments with images
comments = Comments.objects.filter(image__isnull=False).exclude(image__exact='')
print(f'Comments with images: {comments.count()}')
for comment in comments[:3]:
    print(f'  ID: {comment.id}, Ticket: {comment.ticket_id}, Image: {comment.image.name if comment.image else "none"}')

print()

# Find replies with images
replies = Reply.objects.filter(image__isnull=False).exclude(image__exact='')
print(f'Replies with images: {replies.count()}')
for reply in replies[:3]:
    print(f'  ID: {reply.id}, Comment: {reply.comment_id}, Image: {reply.image.name if reply.image else "none"}')
