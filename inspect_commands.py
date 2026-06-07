import importlib
import django
import django_elasticsearch_dsl
import django.core.management as mg

settings = importlib.import_module('cinema.settings.base')
cmds = mg.get_commands()
print('DJANGO', django.get_version())
print('DJANGO_ELASTICSEARCH_DSL', django_elasticsearch_dsl.__version__)
print('IN INSTALLED', 'django_elasticsearch_dsl' in settings.INSTALLED_APPS)
print('SEARCH APP', 'search.apps.SearchConfig' in settings.INSTALLED_APPS)
print('count', len(cmds))
print('search_index' in cmds)
print([name for name in cmds if 'search' in name or 'index' in name or 'elastic' in name])
