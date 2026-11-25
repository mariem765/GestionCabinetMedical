from django.core.exceptions import ValidationError  # Exception utilisée pour signaler une donnée invalide
from django.core.validators import FileExtensionValidator  # Validator qui limite les extensions de fichier autorisées
from django.db import models  # Module contenant models.Model et les types de champs
from django.utils import timezone  # Pour obtenir la date et l'heure actuelles (timezone.now())


class Appointment(models.Model):  # Entité associative autonome : relie un médecin et un patient (avec son propre id)

    class Status(models.TextChoices):  # Énumération des statuts possibles d'un rendez-vous
        PENDING = "PENDING", "En attente"  # Valeur stockée en base = "PENDING", libellé affiché = "En attente"
        CONFIRMED = "CONFIRMED", "Confirmé"  # Rendez-vous confirmé
        CANCELLED = "CANCELLED", "Annulé"  # Rendez-vous annulé

    reason = models.TextField()  # Motif du rendez-vous : TextField = texte long sans limite de longueur
    prescription = models.FileField(  # Ordonnance scannée déposée par le médecin après la consultation
        upload_to="prescriptions/",  # Les fichiers seront enregistrés dans MEDIA_ROOT/prescriptions/
        blank=True,  # Facultatif : l'ordonnance n'existe pas encore au moment de la prise de rendez-vous
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],  # Seuls les fichiers .pdf sont acceptés
    )  # Fin du champ prescription
    status = models.CharField(  # Statut du rendez-vous
        max_length=10,  # Assez long pour stocker la plus longue valeur ("CONFIRMED" / "CANCELLED")
        choices=Status.choices,  # Limite les valeurs possibles à celles de la classe Status
        default=Status.PENDING,  # Valeur par défaut : "En attente"
    )  # Fin du champ status
    duration_minutes = models.PositiveIntegerField(default=30)  # Durée en minutes (entier positif), 30 par défaut
    appointment_date = models.DateTimeField()  # Date ET heure du rendez-vous (doit être dans le futur, voir clean())
    created_at = models.DateTimeField(auto_now_add=True)  # Rempli automatiquement une seule fois, à la création
    updated_at = models.DateTimeField(auto_now=True)  # Mis à jour automatiquement à chaque save()

    doctor = models.ForeignKey(  # 1ère relation one-to-many : un médecin a plusieurs rendez-vous (rôle "praticien")
        "AccountApp.Doctor",  # Modèle cible écrit sous forme "app.Modele" (évite les imports circulaires)
        on_delete=models.CASCADE,  # Si le médecin est supprimé, ses rendez-vous sont supprimés aussi
        related_name="appointments",  # Permet d'écrire doctor.appointments.all()
    )  # Fin de la clé étrangère doctor
    patient = models.ForeignKey(  # 2ème relation one-to-many indépendante : un patient a plusieurs rendez-vous ("demandeur")
        "AccountApp.Patient",  # Modèle cible : Patient de l'application AccountApp
        on_delete=models.CASCADE,  # Si le patient est supprimé, ses rendez-vous sont supprimés aussi
        related_name="appointments",  # Permet d'écrire patient.appointments.all()
    )  # Fin de la clé étrangère patient

    class Meta:  # Options du modèle (tri, contraintes...)
        ordering = ["appointment_date"]  # Tri par défaut : du rendez-vous le plus proche au plus lointain
        constraints = [  # Liste des contraintes appliquées au niveau de la base de données
            models.UniqueConstraint(  # Contrainte d'unicité (forme moderne qui remplace unique_together)
                fields=["doctor", "appointment_date"],  # Un médecin ne peut pas avoir 2 rendez-vous à la même date/heure
                name="unique_doctor_appointment_date",  # Nom obligatoire et unique de la contrainte en base
            )  # Fin de la UniqueConstraint
        ]  # Fin de la liste des contraintes

    def clean(self):  # Validation métier (appelée par full_clean(), ModelForm et admin — PAS par save())
        super().clean()  # On conserve les validations du parent
        if self.appointment_date is None:  # Si la date n'est pas encore renseignée...
            return  # ...on ne peut rien vérifier (l'erreur "champ obligatoire" sera levée ailleurs)
        date_changed = True  # Par défaut on considère que la date est nouvelle (cas de la création)
        if self.pk:  # Si l'objet a déjà une clé primaire, il existe en base → c'est une modification
            old_date = (  # On récupère l'ancienne date enregistrée en base
                Appointment.objects.filter(pk=self.pk)  # On cherche le rendez-vous actuel en base
                .values_list("appointment_date", flat=True)  # On ne récupère que la colonne appointment_date
                .first()  # On prend la première (et unique) valeur, ou None
            )  # Fin de la récupération de l'ancienne date
            date_changed = old_date != self.appointment_date  # True seulement si la date a été modifiée
        if date_changed and self.appointment_date <= timezone.now():  # Nouvelle date ET pas dans le futur ?
            raise ValidationError(  # Alors on refuse avec une erreur liée au champ appointment_date
                {"appointment_date": "La date du rendez-vous doit être postérieure à maintenant."}  # {champ: message}
            )  # Fin du raise → un rendez-vous passé reste modifiable si on ne touche pas à sa date

    def __str__(self):  # Représentation textuelle d'un rendez-vous
        return f"{self.patient} avec {self.doctor} le {self.appointment_date:%d/%m/%Y %H:%M}"  # Ex : "Sara T avec Dr Ali Ben le 20/11/2026 10:00"
