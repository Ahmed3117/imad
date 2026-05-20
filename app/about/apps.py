from django.apps import AppConfig
from django.conf import settings


class AboutConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'about'

    def ready(self):
        """Patch admin.site.get_app_list after all apps are loaded."""
        from django.contrib import admin

        ADMIN_SIDEBAR_GROUPS = settings.ADMIN_SIDEBAR_GROUPS
        ADMIN_VISIBLE_MODEL_KEYS = settings.ADMIN_VISIBLE_MODEL_KEYS
        ADMIN_ORDERING = settings.ADMIN_ORDERING
        UNHANDLED_BADGE_MODELS = settings.UNHANDLED_BADGE_MODELS

        def apply_badge(model, model_key):
            model = model.copy()
            if model_key in UNHANDLED_BADGE_MODELS:
                try:
                    count = UNHANDLED_BADGE_MODELS[model_key]()
                    if count > 0:
                        model['name'] = f"{model['name']} ({count})"
                except Exception:
                    pass
            return model

        def get_app_list(self, request, app_label=None):
            app_dict = self._build_app_dict(request, app_label)
            if not app_dict:
                return []

            if app_label:
                app = app_dict.get(app_label)
                if not app or app_label not in ADMIN_ORDERING:
                    return []

                model_order = ADMIN_ORDERING[app_label]
                models = []
                for model in app['models']:
                    if model['object_name'] not in model_order:
                        continue
                    model_key = f"{app_label}.{model['object_name']}"
                    models.append(apply_badge(model, model_key))

                models.sort(key=lambda x: model_order.index(x['object_name']))
                app['models'] = models
                return [app] if models else []

            model_lookup = {}
            for app in app_dict.values():
                source_app_label = app['app_label']
                for model in app.get('models', []):
                    model_key = f"{source_app_label}.{model['object_name']}"
                    if model_key in ADMIN_VISIBLE_MODEL_KEYS:
                        model_lookup[model_key] = model

            app_list = []
            for group in ADMIN_SIDEBAR_GROUPS:
                models = [
                    apply_badge(model_lookup[model_key], model_key)
                    for model_key in group['models']
                    if model_key in model_lookup
                ]
                if not models:
                    continue
                app_list.append({
                    'name': group['name'],
                    'app_label': group['slug'],
                    'app_url': '',
                    'has_module_perms': True,
                    'models': models,
                })

            return app_list

        # Patch on the actual admin.site instance
        admin.site.get_app_list = get_app_list.__get__(admin.site, type(admin.site))
        # Also patch the class for any other AdminSite instances
        admin.AdminSite.get_app_list = get_app_list
