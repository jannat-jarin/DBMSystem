import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('student', 'Patient'), ('doctor', 'Doctor'), ('admin', 'Admin')], default='student', max_length=10)),
                ('age', models.IntegerField(blank=True, null=True)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='profiles/')),
                ('specialty', models.CharField(blank=True, default='', max_length=100)),
                ('department', models.CharField(blank=True, default='', max_length=100)),
                ('bio', models.TextField(blank=True, default='')),
                ('qualifications', models.CharField(blank=True, default='', max_length=255)),
                ('experience_years', models.PositiveIntegerField(default=0)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
