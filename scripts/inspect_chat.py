
import beeai_framework.backend.chat as chat_module
import inspect

print("Attributes in beeai_framework.backend.chat:")
for name, obj in inspect.getmembers(chat_module):
    if inspect.isclass(obj):
        print(f"Class: {name}")
