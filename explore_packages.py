#!/usr/bin/env python3
"""Script to explore Google ADK packages and generate documentation structure."""

import inspect
import pkgutil
import os
from pathlib import Path
import google.adk

def explore_package(package_name, package_obj):
    """Explore a package and return its structure."""
    info = {
        'name': package_name,
        'modules': [],
        'classes': [],
        'functions': [],
        'subpackages': []
    }
    
    try:
        package_path = os.path.dirname(package_obj.__file__) if hasattr(package_obj, '__file__') else None
        
        # Get subpackages
        if package_path:
            for _, name, ispkg in pkgutil.iter_modules([package_path]):
                if ispkg:
                    info['subpackages'].append(name)
        
        # Get members
        for name, obj in inspect.getmembers(package_obj):
            if inspect.isclass(obj) and obj.__module__.startswith('google.adk'):
                info['classes'].append({
                    'name': name,
                    'module': obj.__module__,
                    'doc': inspect.getdoc(obj) or ''
                })
            elif inspect.isfunction(obj) and obj.__module__.startswith('google.adk'):
                info['functions'].append({
                    'name': name,
                    'module': obj.__module__,
                    'doc': inspect.getdoc(obj) or ''
                })
    except Exception as e:
        info['error'] = str(e)
    
    return info

def main():
    """Main exploration function."""
    packages = {}
    
    # Get all subpackages
    adk_path = os.path.dirname(google.adk.__file__)
    for _, name, ispkg in pkgutil.iter_modules([adk_path]):
        if ispkg:
            try:
                package_obj = __import__(f'google.adk.{name}', fromlist=[name])
                packages[name] = explore_package(name, package_obj)
            except Exception as e:
                packages[name] = {'name': name, 'error': str(e)}
    
    # Print summary
    print("Google ADK Package Structure:")
    print("=" * 50)
    for pkg_name, pkg_info in sorted(packages.items()):
        print(f"\n📦 {pkg_name}")
        if 'error' in pkg_info:
            print(f"   ⚠️  Error: {pkg_info['error']}")
        else:
            if pkg_info['subpackages']:
                print(f"   📁 Subpackages: {', '.join(pkg_info['subpackages'])}")
            if pkg_info['classes']:
                print(f"   🏛️  Classes: {len(pkg_info['classes'])}")
                for cls in pkg_info['classes'][:5]:
                    print(f"      - {cls['name']}")
                if len(pkg_info['classes']) > 5:
                    print(f"      ... and {len(pkg_info['classes']) - 5} more")
            if pkg_info['functions']:
                print(f"   🔧 Functions: {len(pkg_info['functions'])}")
                for func in pkg_info['functions'][:5]:
                    print(f"      - {func['name']}")
                if len(pkg_info['functions']) > 5:
                    print(f"      ... and {len(pkg_info['functions']) - 5} more")
    
    return packages

if __name__ == '__main__':
    packages = main()
