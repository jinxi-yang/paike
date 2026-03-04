#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find garbled Chinese text in the project."""
import os
import sys

# Known garbled patterns found in comments - these are UTF-8 bytes misinterpreted as another encoding
# The garbled text looks like: 閰嶇疆, 瑙嗗浘, 鍏ㄥ眬, 璁插笀, etc.
# These are typically multi-byte characters in the CJK Unified Ideographs Extension range

def is_likely_garbled(text):
    """Check if text contains patterns typical of encoding corruption."""
    # These are specific garbled sequences found in the HTML
    garbled_patterns = [
        '閰嶇疆', '瑙嗗浘', '鍏ㄥ眬', '璁插笀', '鑺傦', '鍐茬獊',
        '鏂板鏁', '瀵艰埅鏍', '椤堕儴', '鐘舵', '鍒囨崲', '绠＄悊',
        '嶇疆', '鑺?', '獊', '鑺?'
    ]
    for p in garbled_patterns:
        if p in text:
            return True
    
    # General heuristic: look for runs of uncommon CJK characters
    # Characters in ranges that are rarely used in normal Chinese text
    uncommon_count = 0
    total_cjk = 0
    for ch in text:
        cp = ord(ch)
        if 0x4E00 <= cp <= 0x9FFF:  # CJK Unified Ideographs
            total_cjk += 1
            # These sub-ranges are less commonly used in modern Chinese
            if cp >= 0x9000 or (0x8B00 <= cp <= 0x8FFF) or (0x7F00 <= cp <= 0x82FF):
                uncommon_count += 1
    
    return False

def scan_file(filepath):
    """Scan a file for garbled Chinese text."""
    results = []
    try:
        with open(filepath, encoding='utf-8-sig') as f:
            for i, line in enumerate(f, 1):
                line_stripped = line.rstrip()
                # Check for specific garbled patterns
                garbled_patterns = [
                    '閰嶇疆', '瑙嗗浘', '鍏ㄥ眬', '璁插笀', '鑺傦', '鍐茬獊',
                    '鏂板鏁', '瀵艰埅鏍', '椤堕儴', '鐘舵', '鍒囨崲', '绠＄悊',
                    '嶇疆', '鑺?', '獊', '鍖哄垎',
                    # More patterns from scanning
                ]
                for p in garbled_patterns:
                    if p in line_stripped:
                        results.append((i, line_stripped))
                        break
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
    return results

def scan_directory(directory, extensions=None):
    """Scan all files in directory for garbled text."""
    if extensions is None:
        extensions = ['.html', '.py', '.js', '.json', '.md', '.txt', '.css']
    
    for root, dirs, files in os.walk(directory):
        # Skip hidden dirs and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in extensions:
                filepath = os.path.join(root, f)
                results = scan_file(filepath)
                if results:
                    rel = os.path.relpath(filepath, directory)
                    print(f"\n=== {rel} ===")
                    for line_no, content in results:
                        # Truncate long lines
                        if len(content) > 150:
                            content = content[:150] + '...'
                        print(f"  Line {line_no}: {content}")

if __name__ == '__main__':
    project_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Scanning {project_dir} for garbled Chinese text...\n")
    scan_directory(project_dir)
    print("\nDone.")
