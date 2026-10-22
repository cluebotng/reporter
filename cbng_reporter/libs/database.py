class DatabaseRouter:
    """
    Only our own tables are migrated.

    Django's own apps (auth, contenttypes, social auth) are intentionally never migrated, nothing requires their tables.
    The bot tables are unmanaged models, so are never touched.
    """

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return app_label == "cbng_reporter"
