#!/usr/bin/env python3
"""
Script to clean up old generic student encodings and prioritize proper names
"""

import os
import glob
import json
from datetime import datetime

def cleanup_old_encodings():
    """Remove old STUDENT_0xx encodings to prioritize proper names"""
    
    encodings_path = "models/precomputed_encodings"
    
    if not os.path.exists(encodings_path):
        print("Encodings directory not found!")
        return
    
    # Find old generic student files
    old_files = glob.glob(os.path.join(encodings_path, "STUDENT_*.json"))
    
    print(f"Found {len(old_files)} old generic student files")
    
    # Create backup directory
    backup_dir = os.path.join("backups", f"old_encodings_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(backup_dir, exist_ok=True)
    
    moved_count = 0
    for old_file in old_files:
        try:
            filename = os.path.basename(old_file)
            backup_path = os.path.join(backup_dir, filename)
            
            # Move to backup instead of deleting
            os.rename(old_file, backup_path)
            moved_count += 1
            print(f"Moved {filename} to backup")
            
        except Exception as e:
            print(f"Error moving {old_file}: {e}")
    
    print(f"\nCleanup complete!")
    print(f"- Moved {moved_count} old files to backup")
    print(f"- Backup location: {backup_dir}")
    
    # List remaining files
    remaining_files = glob.glob(os.path.join(encodings_path, "*.json"))
    print(f"- {len(remaining_files)} proper name encodings remain")
    
    # Show some examples
    if remaining_files:
        print("\nRemaining students:")
        for file in sorted(remaining_files)[:10]:  # Show first 10
            filename = os.path.basename(file).replace('.json', '')
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    name = data.get('name', filename)
                    print(f"  - {filename}: {name}")
            except:
                print(f"  - {filename}")
        
        if len(remaining_files) > 10:
            print(f"  ... and {len(remaining_files) - 10} more")

if __name__ == "__main__":
    cleanup_old_encodings()
