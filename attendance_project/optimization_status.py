#!/usr/bin/env python3
"""
Script to show the current optimization status of the attendance system
"""

import os
import glob
import json

def show_optimization_status():
    """Display the current optimization status"""
    
    print("=" * 60)
    print("SMART ATTENDANCE SYSTEM - OPTIMIZATION STATUS")
    print("=" * 60)
    
    # Check precomputed encodings
    encodings_path = "models/precomputed_encodings"
    if os.path.exists(encodings_path):
        all_encodings = glob.glob(os.path.join(encodings_path, "*.json"))
        proper_name_encodings = [f for f in all_encodings if not os.path.basename(f).startswith('STUDENT_')]
        old_generic_encodings = [f for f in all_encodings if os.path.basename(f).startswith('STUDENT_')]
        
        print(f"PRECOMPUTED ENCODINGS:")
        print(f"  Total encoding files: {len(all_encodings)}")
        print(f"  Proper name encodings: {len(proper_name_encodings)}")
        print(f"  Old generic encodings: {len(old_generic_encodings)}")
        
        if proper_name_encodings:
            print(f"\nPROPER NAME STUDENTS:")
            for encoding_file in sorted(proper_name_encodings):
                filename = os.path.basename(encoding_file)
                student_id = os.path.splitext(filename)[0]
                try:
                    with open(encoding_file, 'r') as f:
                        data = json.load(f)
                        name = data.get('name', student_id)
                        encodings_count = len(data.get('encodings', []))
                        print(f"    {student_id}: {name} ({encodings_count} encodings)")
                except:
                    print(f"    {student_id}: (error reading file)")
        
        if old_generic_encodings:
            print(f"\nOLD GENERIC ENCODINGS (should be cleaned up):")
            for encoding_file in old_generic_encodings:
                filename = os.path.basename(encoding_file)
                print(f"    {filename}")
    else:
        print("PRECOMPUTED ENCODINGS: Directory not found")
    
    # Check backup files
    backup_dirs = glob.glob("backups/old_encodings_*")
    if backup_dirs:
        print(f"\nBACKUP STATUS:")
        print(f"  Backup directories: {len(backup_dirs)}")
        for backup_dir in sorted(backup_dirs):
            backup_files = glob.glob(os.path.join(backup_dir, "*.json"))
            print(f"    {os.path.basename(backup_dir)}: {len(backup_files)} files")
    
    # Check ground truth template
    if os.path.exists("ground_truth_template.csv"):
        with open("ground_truth_template.csv", 'r') as f:
            lines = f.readlines()
            print(f"\nGROUND TRUTH TEMPLATE:")
            print(f"  File exists: Yes")
            print(f"  Total lines: {len(lines)}")
            if len(lines) > 1:
                # Check if it uses proper names
                sample_line = lines[1].strip()
                if 'STUDENT_' in sample_line:
                    print(f"  Uses proper names: No (still has generic names)")
                else:
                    print(f"  Uses proper names: Yes")
                print(f"  Sample entry: {sample_line}")
    else:
        print(f"\nGROUND TRUTH TEMPLATE: File not found")
    
    # Check student folders
    student_photos_path = "student_photos"
    if os.path.exists(student_photos_path):
        student_folders = [f for f in os.listdir(student_photos_path) 
                          if os.path.isdir(os.path.join(student_photos_path, f))
                          and not f.startswith('.')]
        print(f"\nSTUDENT FOLDERS:")
        print(f"  Total folders: {len(student_folders)}")
        print(f"  Sample folders: {student_folders[:5]}")
    
    # Optimization recommendations
    print(f"\nOPTIMIZATION STATUS:")
    
    if proper_name_encodings and len(proper_name_encodings) >= 15:
        print(f"  Status: OPTIMIZED")
        print(f"  Recommendation: System is ready for fast testing")
        print(f"  Benefits:")
        print(f"    - No dataset reprocessing needed")
        print(f"    - Uses proper student names")
        print(f"    - Fast startup time")
        print(f"    - Improved accuracy")
    else:
        print(f"  Status: NEEDS OPTIMIZATION")
        print(f"  Recommendation: Run student registration to create proper name encodings")
    
    print("=" * 60)

if __name__ == "__main__":
    show_optimization_status()
