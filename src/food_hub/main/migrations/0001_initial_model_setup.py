"""
Migration setting up the Ingredient, Nutrient, IngredientNutrient, User,
FoodDataSource, Profile, Meal, MealComponent, MealComponentIngredient
and MealComponentAmount models.
"""

import django.contrib.auth.models
import django.contrib.auth.validators
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="FoodDataSource",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Ingredient",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("external_id", models.IntegerField(null=True, unique=True)),
                ("name", models.CharField(max_length=50)),
                ("dataset", models.CharField(max_length=50)),
                (
                    "data_source",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="main.fooddatasource",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Nutrient",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=32, unique=True)),
                (
                    "unit",
                    models.CharField(
                        choices=[
                            ("KCAL", "calories"),
                            ("G", "grams"),
                            ("MG", "milligrams"),
                            ("UG", "micrograms"),
                        ],
                        max_length=10,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[
                            django.contrib.auth.validators.UnicodeUsernameValidator()
                        ],
                        verbose_name="username",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="email address"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "abstract": False,
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="IngredientNutrient",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("amount", models.FloatField()),
                (
                    "ingredient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="main.ingredient",
                    ),
                ),
                (
                    "nutrient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="main.nutrient"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="ingredient",
            name="nutrients",
            field=models.ManyToManyField(
                through="main.IngredientNutrient",
                to="main.nutrient",
            ),
        ),
        migrations.AddConstraint(
            model_name="ingredientnutrient",
            constraint=models.UniqueConstraint(
                models.F("ingredient"),
                models.F("nutrient"),
                name="unique_ingredient_nutrient",
            ),
        ),
        migrations.CreateModel(
            name="Meal",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateTimeField(default=django.utils.timezone.now)),
                ("name", models.CharField(max_length=50)),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="meals",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MealComponent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="meal_components",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("final_weight", models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name="MealComponentIngredient",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("amount", models.FloatField()),
                (
                    "ingredient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="main.ingredient",
                    ),
                ),
                (
                    "meal_component",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ingredients",
                        to="main.mealcomponent",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MealComponentAmount",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("amount", models.FloatField()),
                (
                    "component",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="main.mealcomponent",
                    ),
                ),
                (
                    "meal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="components",
                        to="main.meal",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="mealcomponentingredient",
            constraint=models.UniqueConstraint(
                models.F("meal_component"),
                models.F("ingredient"),
                name="unique_meal_component_ingredient",
            ),
        ),
        migrations.AddConstraint(
            model_name="mealcomponentamount",
            constraint=models.UniqueConstraint(
                models.F("meal"), models.F("component"), name="unique_meal_component"
            ),
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("age", models.PositiveIntegerField()),
                (
                    "activity_level",
                    models.CharField(
                        choices=[
                            ("S", "Sedentary"),
                            ("LA", "Low Active"),
                            ("A", "Active"),
                            ("VA", "Very Active"),
                        ],
                        max_length=2,
                    ),
                ),
                ("height", models.PositiveIntegerField()),
                (
                    "sex",
                    models.CharField(
                        choices=[("M", "Male"), ("F", "Female")], max_length=1
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("energy_requirement", models.PositiveIntegerField()),
                ("weight", models.PositiveIntegerField()),
            ],
        ),
    ]