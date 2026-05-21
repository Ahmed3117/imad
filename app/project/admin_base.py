"""
Custom UNFOLD ModelAdmin base that renders named fieldsets as tabs.
"""
from unfold.admin import ModelAdmin as UnfoldModelAdmin


class ModelAdmin(UnfoldModelAdmin):
    """
    UNFOLD ModelAdmin that automatically adds 'tab' class to named fieldsets
    so they render as horizontal tabs instead of vertical sections.

    UNFOLD's ``tabs`` template filter only includes fieldsets that have:
    1. "tab" in their classes, AND
    2. a truthy ``name`` attribute.

    Therefore we only add "tab" to fieldsets that already have a name.
    Fieldsets with ``name=None`` (the default single fieldset) are kept
    as normal vertical blocks so they don't disappear from the page.

    Fieldsets containing ``filter_horizontal`` or ``filter_vertical``
    widgets are also excluded from tabs because Django's ``SelectFilter2.js``
    initializes on page load and breaks inside hidden containers (width = 0).
    """

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        filter_fields = set(
            list(getattr(self, "filter_horizontal", ()))
            + list(getattr(self, "filter_vertical", ()))
        )
        result = []
        for name, options in fieldsets:
            opts = dict(options)
            classes = list(opts.get("classes", []))
            if name and "tab" not in classes:
                field_names = opts.get("fields", [])
                has_filter_widget = any(f in filter_fields for f in field_names)
                if not has_filter_widget:
                    classes.append("tab")
            opts["classes"] = classes
            result.append((name, opts))
        return result
