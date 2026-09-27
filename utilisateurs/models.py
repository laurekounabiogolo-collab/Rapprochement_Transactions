from django.db import models
from django.contrib.auth.models import AbstractUser  

class Utilisateur(AbstractUser):
    
    class Roles(models.TextChoices):
       AGENT_ERA = 'AGENT_ERA', 'Agent ERA'
       RESPONSABLE_ERA = 'RESPONSABLE_ERA', 'Responsable ERA'
       DIRECTEUR_OMT = 'DIRECTEUR_OMT',  'Directeur OMT'
   
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=30, choices=Roles.choices, default=Roles.AGENT_ERA)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.role}"
# Create your models here.
