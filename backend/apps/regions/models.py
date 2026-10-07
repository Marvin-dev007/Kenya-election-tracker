from django.db import models

class Region(models.Model):
    REGION_TYPES = [
        ('county', 'County'),
        ('constituency', 'Constituency'),
        ('ward', 'Ward'),
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    region_type = models.CharField(max_length=20, choices=REGION_TYPES)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    center_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    center_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    population = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_region_type_display()})"
    
    class Meta:
        ordering = ['name']
