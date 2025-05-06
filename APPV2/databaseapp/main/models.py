from django.db import models

class CriticalPoint(models.Model):
    param = models.CharField(max_length=100)  # Убираем unique=True
    check_type = models.CharField(max_length=50, choices=[
        ('borders', 'Мин/Макс'),
        ('exact_value', 'Точное значение (Float)'),
        ('string_value', 'Точное значение (String)'),
        ('day_count', 'Дней до сегодняшнего')
    ])
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    exact_value = models.FloatField(null=True, blank=True)
    measure_of_calculation = models.CharField(max_length=50, choices=[
        ('None', 'Просто число'),
        ('GB', 'Gb')
    ], default='None')
    day_count = models.IntegerField(null=True, blank=True)
    string_value = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.param} ({self.check_type})"