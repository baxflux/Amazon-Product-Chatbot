from django.db import models
from django.contrib.auth.models import User

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)  # For anonymous users
    message = models.TextField()
    is_user = models.BooleanField()  # True if user message, False if bot message
    sentiment = models.CharField(max_length=10, blank=True)  # Store sentiment for user messages
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{'User' if self.is_user else 'Bot'} ({self.timestamp}): {self.message}"
