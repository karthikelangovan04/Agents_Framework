#!/usr/bin/env python3
"""Get detailed information about a specific Google ADK package."""

import inspect
import sys
import importlib

def get_package_details(package_name):
    """Get detailed information about a package."""
    try:
        module = importlib.import_module(f'google.adk.{package_name}')
        
        details = {
            'name': package_name,
            'doc': inspect.getdoc(module) or '',
            'classes': [],
            'functions': [],
            'constants': []
        }
        
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and obj.__module__.startswith('google.adk'):
                class_info = {
                    'name': name,
                    'doc': inspect.getdoc(obj) or '',
                    'methods': [],
                    'signature': str(inspect.signature(obj.__init__)) if hasattr(obj, '__init__') else ''
                }
                
                # Get public methods
                for method_name, method_obj in inspect.getmembers(obj, predicate=inspect.isfunction):
                    if not method_name.startswith('_') or method_name in ['__init__', '__call__']:
                        try:
                            sig = str(inspect.signature(method_obj))
                            class_info['methods'].append({
                                'name': method_name,
                                'signature': sig,
                                'doc': inspect.getdoc(method_obj) or ''
                            })
                        except:
                            pass
                
                details['classes'].append(class_info)
            
            elif inspect.isfunction(obj) and obj.__module__.startswith('google.adk'):
                try:
                    sig = str(inspect.signature(obj))
                    details['functions'].append({
                        'name': name,
                        'signature': sig,
                        'doc': inspect.getdoc(obj) or ''
                    })
                except:
                    pass
        
        return details
    except Exception as e:
        return {'name': package_name, 'error': str(e)}

if __name__ == '__main__':
    if len(sys.argv) > 1:
        package_name = sys.argv[1]
        details = get_package_details(package_name)
        import json
        print(json.dumps(details, indent=2, default=str))
    else:
        print("Usage: python get_package_details.py <package_name>")
