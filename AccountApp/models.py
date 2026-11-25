from django.contrib.auth.models import AbstractUser  # Classe abstraite de Django contenant username, password, email, first_name, last_name...
from django.core.exceptions import ValidationError  # Exception levée quand une donnée ne respecte pas une règle de validation
from django.core.validators import MinLengthValidator, RegexValidator  # Validators prêts à l'emploi : longueur minimale et expression régulière
from django.db import models  # Module contenant models.Model et tous les types de champs (CharField, DateField...)
from django.utils import timezone  # Utilitaires de date/heure qui respectent le fuseau horaire du projet (TIME_ZONE)


# ======================= Validators réutilisables =======================

phone_validator = RegexValidator(  # Validator pour le téléphone (utilisé par Doctor ET Patient)
    r'^\d{8}$',  # ^ = début, \d{8} = exactement 8 chiffres, $ = fin
    "Le téléphone doit contenir exactement 8 chiffres.",  # Message affiché si la règle n'est pas respectée
)  # Fin de la déclaration du validator téléphone

cin_validator = RegexValidator(  # Validator pour le numéro de CIN du patient
    r'^\d{8}$',  # Le CIN tunisien est composé d'exactement 8 chiffres
    "Le CIN doit contenir exactement 8 chiffres.",  # Message d'erreur du CIN
)  # Fin de la déclaration du validator CIN


def validate_past_date(value):  # Méthode 1 : fonction validator personnalisée (reçoit la valeur du champ)
    if value >= timezone.localdate():  # On compare avec la date du jour (date locale, sans l'heure)
        raise ValidationError(  # Si la date est aujourd'hui ou dans le futur, on lève une erreur
            "La date de naissance doit être antérieure à la date du jour."  # Message de l'erreur
        )  # Fin du raise ; si aucune erreur n'est levée, la valeur est considérée valide


# ======================= Modèle User personnalisé =======================

class User(AbstractUser):  # Notre modèle utilisateur hérite de AbstractUser (déclaré dans AUTH_USER_MODEL)
    pass  # Aucun champ supplémentaire : il sert uniquement de point d'extension pour le futur


# ======================= Modèle Specialty =======================

class Specialty(models.Model):  # Une spécialité médicale (Cardiologie, Dermatologie, Pédiatrie...)
    name = models.CharField(max_length=100, unique=True)  # Nom de la spécialité, unique pour éviter les doublons

    class Meta:  # Options du modèle
        verbose_name_plural = "Specialties"  # Pluriel correct affiché dans l'admin (sinon "Specialtys")

    def __str__(self):  # Représentation textuelle de l'objet (admin, shell, listes déroulantes)
        return self.name  # On affiche simplement le nom de la spécialité


# ======================= Modèle Doctor =======================

class Doctor(User):  # Héritage multi-tables : Doctor a sa propre table liée à User par user_ptr (OneToOne)
    license_number = models.CharField(  # Numéro d'inscription à l'ordre des médecins
        max_length=6,  # Longueur maximale = 6 caractères
        unique=True,  # Identifiant métier : deux médecins ne peuvent pas avoir le même numéro
        validators=[MinLengthValidator(6)],  # Longueur minimale = 6 → donc longueur fixe exactement égale à 6
    )  # Fin du champ license_number
    phone = models.CharField(max_length=8, validators=[phone_validator])  # Téléphone du médecin : 8 chiffres
    specialties = models.ManyToManyField(  # Relation plusieurs-à-plusieurs Doctor <-> Specialty (sans classe through)
        Specialty,  # Modèle cible de la relation
        related_name="doctors",  # Permet d'écrire specialty.doctors.all() pour la relation inverse
        blank=True,  # Un médecin peut être créé sans spécialité (champ facultatif dans les formulaires)
    )  # Fin du champ specialties

    class Meta:  # Options du modèle Doctor
        verbose_name = "Doctor"  # Nom affiché dans l'admin

    def __str__(self):  # Représentation textuelle d'un médecin
        return f"Dr {self.first_name} {self.last_name}"  # first_name / last_name sont hérités de User


# ======================= Modèle Patient =======================

class Patient(User):  # Héritage multi-tables : un patient est aussi un User (patient.pk == user.pk)
    national_id = models.CharField(  # Numéro de CIN du patient
        max_length=8,  # 8 caractères maximum
        unique=True,  # Identifiant métier unique : deux patients ne peuvent pas avoir le même CIN
        validators=[cin_validator],  # Vérifie qu'il contient exactement 8 chiffres
    )  # Fin du champ national_id
    phone = models.CharField(max_length=8, validators=[phone_validator])  # Téléphone du patient : 8 chiffres
    birth_date = models.DateField(validators=[validate_past_date])  # Date de naissance + Méthode 1 (validator)

    class Meta:  # Options du modèle Patient
        verbose_name = "Patient"  # Nom affiché dans l'admin

    def clean(self):  # Méthode 2 : validation au niveau du modèle (appelée par full_clean(), ModelForm, admin)
        super().clean()  # On appelle d'abord le clean() parent pour garder les validations de User
        if self.birth_date and self.birth_date >= timezone.localdate():  # Si la date existe et n'est pas dans le passé
            raise ValidationError(  # On lève une erreur rattachée au champ birth_date
                {"birth_date": "La date de naissance doit être dans le passé."}  # Dictionnaire {champ: message}
            )  # Fin du raise

    def __str__(self):  # Représentation textuelle d'un patient
        return f"{self.first_name} {self.last_name}"  # Prénom + nom hérités de User
