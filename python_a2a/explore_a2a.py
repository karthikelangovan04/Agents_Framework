#!/usr/bin/env python3
"""Explore python-a2a library structure and generate documentation."""

import inspect
import json
from typing import Any, Dict, List

def explore_module(module_name: str) -> Dict[str, Any]:
    """Explore a module and return its structure."""
    try:
        module = __import__(module_name, fromlist=[''])
        info = {
            'name': module_name,
            'doc': inspect.getdoc(module) or '',
            'version': getattr(module, '__version__', 'unknown'),
            'classes': [],
            'functions': [],
            'submodules': []
        }
        
        # Get classes
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and obj.__module__ == module_name:
                class_info = {
                    'name': name,
                    'doc': inspect.getdoc(obj) or '',
                    'bases': [base.__name__ for base in obj.__bases__],
                    'methods': []
                }
                
                # Get methods
                for method_name, method_obj in inspect.getmembers(obj, predicate=inspect.isfunction):
                    if method_name not in ['__init__', '__new__']:
                        method_info = {
                            'name': method_name,
                            'doc': inspect.getdoc(method_obj) or '',
                            'signature': str(inspect.signature(method_obj))
                        }
                        class_info['methods'].append(method_info)
                
                info['classes'].append(class_info)
            
            elif inspect.isfunction(obj) and obj.__module__ == module_name:
                func_info = {
                    'name': name,
                    'doc': inspect.getdoc(obj) or '',
                    'signature': str(inspect.signature(obj))
                }
                info['functions'].append(func_info)
        
        return info
    except Exception as e:
        return {'name': module_name, 'error': str(e)}

def main():
    """Main exploration function."""
    import python_a2a
    
    print("Exploring python-a2a library...")
    print(f"Version: {python_a2a.__version__}")
    print(f"Package: {python_a2a.__name__}")
    print(f"Doc: {python_a2a.__doc__}\n")
    
    # Main modules to explore
    modules_to_explore = [
        'python_a2a',
        'python_a2a.server',
        'python_a2a.client',
        'python_a2a.models',
        'python_a2a.workflow',
        'python_a2a.mcp',
        'python_a2a.langchain',
        'python_a2a.discovery',
    ]
    
    results = {}
    
    for module_name in modules_to_explore:
        print(f"Exploring {module_name}...")
        try:
            results[module_name] = explore_module(module_name)
        except Exception as e:
            print(f"  Error: {e}")
            results[module_name] = {'error': str(e)}
    
    # Get main exports
    print("\nMain exports:")
    main_exports = [x for x in dir(python_a2a) if not x.startswith('_')]
    print(f"Total exports: {len(main_exports)}")
    
    # Key classes
    print("\nKey Classes:")
    key_classes = [
        'A2AServer', 'A2AClient', 'Message', 'Conversation', 
        'AgentCard', 'Flow', 'OpenAIA2AServer', 'AnthropicA2AServer'
    ]
    for cls_name in key_classes:
        if hasattr(python_a2a, cls_name):
            cls = getattr(python_a2a, cls_name)
            print(f"  {cls_name}: {inspect.getdoc(cls) or 'No doc'}")
    
    # Save results
    output = {
        'version': python_a2a.__version__,
        'main_exports': main_exports,
        'modules': results
    }
    
    with open('a2a_exploration.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print("\nExploration complete! Results saved to a2a_exploration.json")

if __name__ == '__main__':
    main()
