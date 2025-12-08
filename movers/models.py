from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class MoverService(models.Model):
	owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mover_services")
	name = models.CharField(max_length=200)
	description = models.TextField()
	location = models.CharField(max_length=200)
	phone = models.CharField(max_length=50)
	email = models.EmailField(blank=True)
	provides_cleaning = models.BooleanField(default=False)
	rate_per_km = models.DecimalField(max_digits=10, decimal_places=2, default=50, help_text="Charge per kilometer")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return self.name

	@property
	def rating_summary(self):
		agg = self.ratings.aggregate(avg=models.Avg("score"), count=models.Count("id"))
		return {
			"average": round(agg["avg"] or 0, 1),
			"count": agg["count"] or 0,
		}


class MoverRating(models.Model):
	service = models.ForeignKey(MoverService, on_delete=models.CASCADE, related_name="ratings")
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mover_ratings")
	score = models.PositiveSmallIntegerField()
	comment = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]
		unique_together = ("service", "user")  # one rating per user per service

	def __str__(self):
		return f"{self.service.name} - {self.score} by {self.user}" 
