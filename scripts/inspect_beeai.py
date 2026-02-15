
import inspect
import beeai_framework
from beeai_framework import backend, agents, tools

print("Top level:", dir(beeai_framework))
print("\nBackend:", dir(backend))
print("\nAgents:", dir(agents))
print("\nTools:", dir(tools))

try:
    from beeai_framework.backend.chat import ChatModel
    print("\nChatModel found in backend.chat")
except ImportError:
    print("\nChatModel NOT found in backend.chat")

try:
    from beeai_framework.tools.tool import Tool
    print("\nTool found in tools.tool")
except ImportError:
    print("\nTool NOT found in tools.tool")
