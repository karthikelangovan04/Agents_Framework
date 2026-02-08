#!/usr/bin/env python3
"""Get detailed information about AG-UI related packages (ag_ui, ag_ui_adk).

Use with backend venv: backend/.venv/bin/python adk/get_package_details_agui.py <module_name>
Example: get_package_details_agui.py ag_ui
         get_package_details_agui.py ag_ui.core
         get_package_details_agui.py ag_ui_adk
"""

import inspect
import sys
import importlib
import json


def get_package_details(module_name: str) -> dict:
    """Get detailed information about a module (e.g. ag_ui, ag_ui.core, ag_ui_adk)."""
    try:
        module = importlib.import_module(module_name)
        prefix = module.__name__
        if not prefix:
            prefix = module_name

        details = {
            "name": module_name,
            "module_doc": inspect.getdoc(module) or "",
            "file": getattr(module, "__file__", None),
            "version": getattr(module, "__version__", None),
            "classes": [],
            "functions": [],
            "constants": [],
        }

        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj):
                mod = getattr(obj, "__module__", "") or ""
                if not mod.startswith(prefix) and not mod.startswith(module_name.split(".")[0]):
                    continue
                class_info = {
                    "name": name,
                    "doc": inspect.getdoc(obj) or "",
                    "methods": [],
                    "signature": "",
                }
                if hasattr(obj, "__init__"):
                    try:
                        class_info["signature"] = str(inspect.signature(obj.__init__))
                    except Exception:
                        pass
                for method_name, method_obj in inspect.getmembers(obj, predicate=inspect.isfunction):
                    if method_name.startswith("_") and method_name not in ("__init__", "__call__"):
                        continue
                    try:
                        sig = str(inspect.signature(method_obj))
                        class_info["methods"].append({
                            "name": method_name,
                            "signature": sig,
                            "doc": inspect.getdoc(method_obj) or "",
                        })
                    except Exception:
                        pass
                details["classes"].append(class_info)

            elif inspect.isfunction(obj):
                mod = getattr(obj, "__module__", "") or ""
                if not mod.startswith(prefix) and not mod.startswith(module_name.split(".")[0]):
                    continue
                try:
                    sig = str(inspect.signature(obj))
                    details["functions"].append({
                        "name": name,
                        "signature": sig,
                        "doc": inspect.getdoc(obj) or "",
                    })
                except Exception:
                    pass

        return details
    except Exception as e:
        return {"name": module_name, "error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        module_name = sys.argv[1]
        details = get_package_details(module_name)
        print(json.dumps(details, indent=2, default=str))
    else:
        print("Usage: python get_package_details_agui.py <module_name>")
        print("  module_name: ag_ui | ag_ui.core | ag_ui.encoder | ag_ui_adk | etc.")
        sys.exit(1)
