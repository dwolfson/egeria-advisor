
import pkgutil
import beeai_framework

print("Modules in beeai_framework:")
for importer, modname, ispkg in pkgutil.walk_packages(beeai_framework.__path__, prefix="beeai_framework."):
    print(modname)
