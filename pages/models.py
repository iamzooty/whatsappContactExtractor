from django.db import models

# Create your models here.
class Documents(models.Model):
    name = models.CharField(max_length=120, blank=True)
    documents = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Document #{self.id}"