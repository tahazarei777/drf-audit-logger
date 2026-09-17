from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(
                    choices=[
                        ('login', 'Login'), ('logout', 'Logout'),
                        ('login_failed', 'Login Failed'),
                        ('create', 'Create'), ('update', 'Update'),
                        ('delete', 'Delete'), ('custom', 'Custom'),
                    ],
                    db_index=True, max_length=32, verbose_name='Action',
                )),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Timestamp')),
                ('model_name', models.CharField(blank=True, db_index=True, help_text='Class name of the affected model (e.g., "Product").', max_length=100, verbose_name='Model Name')),
                ('object_id', models.CharField(blank=True, db_index=True, max_length=100, verbose_name='Object ID')),
                ('object_repr', models.CharField(blank=True, help_text='String representation of the object at event time.', max_length=255, verbose_name='Object Representation')),
                ('changes', models.JSONField(blank=True, null=True, verbose_name='Changes')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP Address')),
                ('user_agent', models.TextField(blank=True, verbose_name='User Agent')),
                ('metadata', models.JSONField(blank=True, help_text='For custom events: {"message_id": "...", "params": {...}}', null=True, verbose_name='Metadata')),
                ('user', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='audit_logs',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='User',
                )),
            ],
            options={
                'verbose_name': 'Audit Log',
                'verbose_name_plural': 'Audit Logs',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', '-timestamp'], name='drf_audit_l_user_id_2c5a4a_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['action', '-timestamp'], name='drf_audit_l_action_2f8b3c_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['model_name', 'object_id'], name='drf_audit_l_model_n_9d4e5f_idx'),
        ),
    ]