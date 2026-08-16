from django.db import migrations


def create_initial_data(apps, schema_editor):
    DashboardConfiguration = apps.get_model('dashboard', 'DashboardConfiguration')
    DashboardWidget = apps.get_model('dashboard', 'DashboardWidget')
    
    # Create default dashboard configuration
    default_config, created = DashboardConfiguration.objects.get_or_create(
        name='Default Dashboard',
        defaults={
            'is_default': True
        }
    )
    
    # Create basic widgets
    widgets_data = [
        {
            'name': 'Welcome Widget',
            'widget_type': 'welcome',
            'title': 'Welcome',
            'description': 'Welcome message for the user',
            'is_enabled': True,
        },
        {
            'name': 'Profile Widget',
            'widget_type': 'profile',
            'title': 'Profile',
            'description': 'User profile information',
            'is_enabled': True,
        },
        {
            'name': 'Organizational Info Widget',
            'widget_type': 'organizational_info',
            'title': 'Organizational Info',
            'description': 'User\'s organizational information',
            'is_enabled': True,
        },
        {
            'name': 'Reports Statistic',
            'widget_type': 'statistic',
            'title': 'Reports Submitted',
            'description': 'Number of reports submitted',
            'is_enabled': True,
        },
        {
            'name': 'Members Statistic',
            'widget_type': 'statistic',
            'title': 'Active Members',
            'description': 'Number of active members',
            'is_enabled': True,
        },
        {
            'name': 'Volunteers Statistic',
            'widget_type': 'statistic',
            'title': 'Active Volunteers',
            'description': 'Number of active volunteers',
            'is_enabled': True,
        },
        {
            'name': 'Quick Actions Widget',
            'widget_type': 'quick_actions',
            'title': 'Quick Actions',
            'description': 'Commonly used actions',
            'is_enabled': True,
        },
        {
            'name': 'Notifications Widget',
            'widget_type': 'notification',
            'title': 'Notifications',
            'description': 'Recent notifications',
            'is_enabled': True,
        },
        {
            'name': 'Activity Feed Widget',
            'widget_type': 'activity',
            'title': 'Recent Activity',
            'description': 'Recent organizational activities',
            'is_enabled': True,
        },
    ]
    
    for widget_data in widgets_data:
        DashboardWidget.objects.get_or_create(
            name=widget_data['name'],
            defaults=widget_data
        )


def reverse_initial_data(apps, schema_editor):
    # Optional: remove the initial data
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_data, reverse_initial_data),
    ]