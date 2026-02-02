#!/usr/bin/env python3
"""Comprehensive analysis of a2a-sdk package - all classes, methods, and structure."""

import inspect
import sys
import importlib
import pkgutil
import os
import json
from typing import Any, Dict, List, Set
from pathlib import Path

def get_class_details(cls: type, module_name: str) -> Dict[str, Any]:
    """Get detailed information about a class."""
    class_info = {
        'name': cls.__name__,
        'module': cls.__module__,
        'doc': inspect.getdoc(cls) or '',
        'bases': [base.__name__ for base in cls.__bases__ if base != object],
        'methods': [],
        'properties': [],
        'class_methods': [],
        'static_methods': [],
        'init_signature': ''
    }
    
    # Get __init__ signature
    if hasattr(cls, '__init__'):
        try:
            class_info['init_signature'] = str(inspect.signature(cls.__init__))
        except:
            pass
    
    # Get all members
    for name, obj in inspect.getmembers(cls):
        # Skip private attributes unless they're special methods
        if name.startswith('_') and name not in ['__init__', '__call__', '__str__', '__repr__', '__eq__', '__hash__']:
            continue
        
        # Methods
        if inspect.isfunction(obj) or inspect.ismethod(obj):
            try:
                sig = str(inspect.signature(obj))
                method_info = {
                    'name': name,
                    'signature': sig,
                    'doc': inspect.getdoc(obj) or '',
                    'is_abstract': inspect.isabstractmethod(obj) if hasattr(inspect, 'isabstractmethod') else False
                }
                
                if inspect.ismethod(obj) and isinstance(obj, classmethod):
                    class_info['class_methods'].append(method_info)
                elif inspect.isfunction(obj) and isinstance(obj, staticmethod):
                    class_info['static_methods'].append(method_info)
                else:
                    class_info['methods'].append(method_info)
            except Exception as e:
                pass
        
        # Properties
        elif isinstance(obj, property):
            prop_info = {
                'name': name,
                'doc': inspect.getdoc(obj) or '',
                'fget': obj.fget.__name__ if obj.fget else None,
                'fset': obj.fset.__name__ if obj.fset else None,
                'fdel': obj.fdel.__name__ if obj.fdel else None
            }
            class_info['properties'].append(prop_info)
    
    return class_info

def get_module_details(module_name: str) -> Dict[str, Any]:
    """Get detailed information about a module."""
    try:
        module = importlib.import_module(module_name)
        
        details = {
            'name': module_name,
            'file': getattr(module, '__file__', ''),
            'doc': inspect.getdoc(module) or '',
            'version': getattr(module, '__version__', ''),
            'classes': [],
            'functions': [],
            'constants': [],
            'submodules': []
        }
        
        # Get all members
        for name, obj in inspect.getmembers(module):
            # Skip private members
            if name.startswith('_'):
                continue
            
            # Classes
            if inspect.isclass(obj) and obj.__module__ == module_name:
                try:
                    class_info = get_class_details(obj, module_name)
                    details['classes'].append(class_info)
                except Exception as e:
                    details['classes'].append({
                        'name': name,
                        'error': str(e)
                    })
            
            # Functions
            elif inspect.isfunction(obj) and obj.__module__ == module_name:
                try:
                    sig = str(inspect.signature(obj))
                    func_info = {
                        'name': name,
                        'signature': sig,
                        'doc': inspect.getdoc(obj) or ''
                    }
                    details['functions'].append(func_info)
                except Exception as e:
                    pass
            
            # Constants (uppercase names that aren't classes/functions)
            elif name.isupper() and not inspect.isclass(obj) and not inspect.isfunction(obj):
                details['constants'].append({
                    'name': name,
                    'value': str(obj),
                    'type': type(obj).__name__
                })
        
        return details
    except Exception as e:
        return {'name': module_name, 'error': str(e)}

def discover_all_modules(package_name: str) -> List[str]:
    """Discover all modules in a package recursively."""
    modules = [package_name]
    try:
        package = importlib.import_module(package_name)
        package_path = os.path.dirname(package.__file__) if hasattr(package, '__file__') else None
        
        if package_path:
            for _, name, ispkg in pkgutil.walk_packages([package_path], prefix=f'{package_name}.'):
                modules.append(name)
    except Exception as e:
        print(f"Error discovering modules: {e}", file=sys.stderr)
    
    return sorted(modules)

def analyze_a2a_sdk() -> Dict[str, Any]:
    """Comprehensive analysis of a2a-sdk package."""
    print("Starting comprehensive analysis of a2a-sdk...")
    
    # Discover all modules
    print("Discovering all modules...")
    all_modules = discover_all_modules('a2a')
    print(f"Found {len(all_modules)} modules")
    
    # Analyze each module
    results = {
        'package': 'a2a-sdk',
        'version': '',
        'modules': {},
        'summary': {
            'total_modules': len(all_modules),
            'total_classes': 0,
            'total_functions': 0,
            'total_methods': 0
        }
    }
    
    # Get version from main package
    try:
        a2a_main = importlib.import_module('a2a')
        results['version'] = getattr(a2a_main, '__version__', 'unknown')
        results['package_file'] = getattr(a2a_main, '__file__', '')
    except:
        pass
    
    # Analyze each module
    for module_name in all_modules:
        print(f"Analyzing {module_name}...")
        module_details = get_module_details(module_name)
        results['modules'][module_name] = module_details
        
        # Update summary
        if 'error' not in module_details:
            results['summary']['total_classes'] += len(module_details['classes'])
            results['summary']['total_functions'] += len(module_details['functions'])
            for cls in module_details['classes']:
                if 'methods' in cls:
                    results['summary']['total_methods'] += len(cls.get('methods', []))
                    results['summary']['total_methods'] += len(cls.get('class_methods', []))
                    results['summary']['total_methods'] += len(cls.get('static_methods', []))
    
    return results

def print_summary(results: Dict[str, Any]):
    """Print a summary of the analysis."""
    print("\n" + "="*80)
    print("A2A-SDK COMPREHENSIVE ANALYSIS SUMMARY")
    print("="*80)
    print(f"Package: {results['package']}")
    print(f"Version: {results['version']}")
    print(f"Total Modules: {results['summary']['total_modules']}")
    print(f"Total Classes: {results['summary']['total_classes']}")
    print(f"Total Functions: {results['summary']['total_functions']}")
    print(f"Total Methods: {results['summary']['total_methods']}")
    print("\n" + "-"*80)
    print("MODULES BREAKDOWN:")
    print("-"*80)
    
    for module_name, module_data in sorted(results['modules'].items()):
        if 'error' in module_data:
            print(f"\n❌ {module_name}: ERROR - {module_data['error']}")
        else:
            num_classes = len(module_data['classes'])
            num_functions = len(module_data['functions'])
            print(f"\n📦 {module_name}")
            print(f"   Classes: {num_classes}, Functions: {num_functions}")
            
            if module_data['classes']:
                print("   Key Classes:")
                for cls in module_data['classes'][:5]:
                    num_methods = len(cls.get('methods', [])) + len(cls.get('class_methods', [])) + len(cls.get('static_methods', []))
                    print(f"      • {cls['name']} ({num_methods} methods)")
                if len(module_data['classes']) > 5:
                    print(f"      ... and {len(module_data['classes']) - 5} more classes")

def main():
    """Main function."""
    results = analyze_a2a_sdk()
    
    # Print summary
    print_summary(results)
    
    # Save to JSON
    output_file = 'a2a_sdk_comprehensive_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Comprehensive analysis complete!")
    print(f"📄 Detailed results saved to: {output_file}")
    
    return results

if __name__ == '__main__':
    results = main()
