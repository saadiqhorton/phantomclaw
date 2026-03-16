#!/usr/bin/env python3
import os
import sys

def count_lines(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for line in f)
    except Exception:
        # Ignore files that cannot be read as utf-8 or are binary
        return 0

def is_executable(filepath):
    return os.access(filepath, os.X_OK)

def main():
    root_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    stats = {
        'Python': {'files': 0, 'lines': 0},
        'Markdown': {'files': 0, 'lines': 0},
        'Shell': {'files': 0, 'lines': 0},
        'Executable (Scripts)': {'files': 0, 'lines': 0},
        'Other': {'files': 0, 'lines': 0}
    }
    
    # Common directories to ignore
    ignore_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', '.gemini', 'dist', 'build'}
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Modify dirnames in-place to skip hidden directories and ignored ones
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ignore_dirs]
        
        for file in filenames:
            # Skip hidden files and the tracker script itself
            if file.startswith('.') or file == 'track_loc.py':
                continue
                
            filepath = os.path.join(dirpath, file)
            # Skip symlinks
            if os.path.islink(filepath):
                continue
                
            lines = count_lines(filepath)
            
            # Categorize the file
            if file.endswith('.py'):
                cat = 'Python'
            elif file.endswith('.md'):
                cat = 'Markdown'
            elif file.endswith('.sh'):
                cat = 'Shell'
            elif is_executable(filepath) and '.' not in file:
                cat = 'Executable (Scripts)'
            else:
                # You can add more mappings here if needed
                cat = 'Other'
                
            stats[cat]['files'] += 1
            stats[cat]['lines'] += lines

    total_files = sum(s['files'] for s in stats.values())
    total_lines = sum(s['lines'] for s in stats.values())
    
    print("\n# Lines of Code Summary\n")
    print(f"| Language | Files | Lines of Code | Percentage |")
    print(f"| :--- | :--- | :--- | :--- |")
    
    # Sort categories by line count descending
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['lines'], reverse=True)
    
    for cat, data in sorted_stats:
        if data['files'] > 0:
            pct = (data['lines'] / total_lines * 100) if total_lines > 0 else 0
            print(f"| {cat} | {data['files']:,} | {data['lines']:,} | {pct:.1f}% |")
            
    print(f"| **Total** | **{total_files:,}** | **{total_lines:,}** | **100%** |")
    print()

if __name__ == '__main__':
    main()
