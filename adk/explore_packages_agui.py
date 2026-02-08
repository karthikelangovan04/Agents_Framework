#!/usr/bin/env python3
"""Explore AG-UI related packages (ag_ui, ag_ui_adk) and list modules/classes/functions.

Use with backend venv: backend/.venv/bin/python adk/explore_packages_agui.py
"""

import inspect
import pkgutil
import sys
import os


def explore_module(module_name: str) -> dict:
    """Explore a module and return structure (submodules, classes, functions)."""
    info = {
        "name": module_name,
        "submodules": [],
        "classes": [],
        "functions": [],
        "version": None,
        "file": None,
        "error": None,
    }
    try:
        mod = __import__(module_name, fromlist=[""])
        info["file"] = getattr(mod, "__file__", None)
        info["version"] = getattr(mod, "__version__", None)
        pkg_path = getattr(mod, "__path__", None)
        if pkg_path is not None:
            for _importer, name, ispkg in pkgutil.iter_modules(pkg_path, prefix=module_name + "."):
                info["submodules"].append(name)
        for name, obj in inspect.getmembers(mod):
            if name.startswith("_"):
                continue
            if inspect.isclass(obj) and (getattr(obj, "__module__", "") or "").startswith(module_name.split(".")[0]):
                info["classes"].append({
                    "name": name,
                    "module": getattr(obj, "__module__", ""),
                    "doc": (inspect.getdoc(obj) or "")[:200],
                })
            elif inspect.isfunction(obj) and (getattr(obj, "__module__", "") or "").startswith(module_name.split(".")[0]):
                info["functions"].append({
                    "name": name,
                    "module": getattr(obj, "__module__", ""),
                    "doc": (inspect.getdoc(obj) or "")[:200],
                })
    except Exception as e:
        info["error"] = str(e)
    return info


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("AG-UI package exploration")
    print("Python:", sys.executable)
    print("CWD / repo root:", root)
    print()

    packages = ["ag_ui", "ag_ui_adk"]
    all_info = {}

    for pkg in packages:
        try:
            info = explore_module(pkg)
            all_info[pkg] = info
            print(f"📦 {pkg}")
            if info.get("error"):
                print(f"   ⚠️  Error: {info['error']}")
            else:
                if info.get("version"):
                    print(f"   Version: {info['version']}")
                if info.get("file"):
                    print(f"   File: {info['file']}")
                if info.get("submodules"):
                    print(f"   Submodules: {', '.join(info['submodules'])}")
                if info.get("classes"):
                    print(f"   Classes: {len(info['classes'])}")
                    for c in info["classes"][:10]:
                        print(f"      - {c['name']}")
                    if len(info["classes"]) > 10:
                        print(f"      ... and {len(info['classes']) - 10} more")
                if info.get("functions"):
                    print(f"   Functions: {len(info['functions'])}")
                    for f in info["functions"][:10]:
                        print(f"      - {f['name']}")
                    if len(info["functions"]) > 10:
                        print(f"      ... and {len(info['functions']) - 10} more")
            print()
        except Exception as e:
            all_info[pkg] = {"name": pkg, "error": str(e)}
            print(f"📦 {pkg}: Error - {e}\n")

    # Submodules to also explore for details
    submodules = []
    for pkg, inf in all_info.items():
        if inf.get("submodules"):
            submodules.extend(inf["submodules"])
    return all_info, submodules


if __name__ == "__main__":
    main()
