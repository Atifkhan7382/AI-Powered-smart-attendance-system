#!/usr/bin/env python3
"""
Script to update ground truth template with proper student names
"""

import os
import glob
import csv
from datetime import datetime

def update_ground_truth_template():
    """Update ground truth template to use proper student names"""
    
    # Get list of proper name encodings
    encodings_path = "models/precomputed_encodings"
    if not os.path.exists(encodings_path):
        print("❌ Encodings directory not found!")
        return
    
    encoding_files = glob.glob(os.path.join(encodings_path, "*.json"))
    # Only get proper name encodings (not STUDENT_xxx)
    proper_name_files = [f for f in encoding_files if not os.path.basename(f).startswith('STUDENT_')]
    
    if not proper_name_files:
        print("❌ No proper name encodings found!")
        return
    
    # Extract student IDs from filenames
    student_ids = []
    for file_path in proper_name_files:
        filename = os.path.basename(file_path)
        student_id = os.path.splitext(filename)[0]
        student_ids.append(student_id)
    
    student_ids.sort()
    print(f"Found {len(student_ids)} students with proper names:")
    for sid in student_ids:
        print(f"  - {sid}")
    
    # Create updated ground truth template
    template_file = "ground_truth_template.csv"
    backup_file = f"ground_truth_template_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Backup existing file if it exists
    if os.path.exists(template_file):
        os.rename(template_file, backup_file)
        print(f"Backed up existing template to: {backup_file}")
    
    # Create new template with proper names
    with open(template_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['image_name', 'student_id', 'present'])
        
        # Write sample entries for each student
        for i, student_id in enumerate(student_ids):
            # Create sample entries for different classroom photos
            writer.writerow(['group_photo1.jpg', student_id, 1])
            writer.writerow(['group_photo2.jpg', student_id, 1 if i % 2 == 0 else 0])  # Alternate presence
            writer.writerow(['group_photo3.jpg', student_id, 1 if i % 3 != 0 else 0])  # Different pattern
    
    print(f"\n✅ Updated ground truth template created: {template_file}")
    print(f"📊 Template contains {len(student_ids)} students with proper names")
    print(f"📝 Sample entries created for group_photo1.jpg, group_photo2.jpg, group_photo3.jpg")
    
    # Show first few lines of the new template
    print(f"\nFirst few lines of new template:")
    with open(template_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i < 10:  # Show first 10 lines
                print(f"  {line.strip()}")
            else:
                break
    
    print(f"\n💡 You can now edit {template_file} to match your actual classroom photos")

if __name__ == "__main__":
    update_ground_truth_template()
