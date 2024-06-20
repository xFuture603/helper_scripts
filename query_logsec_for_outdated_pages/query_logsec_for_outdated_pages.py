#!/usr/bin/python3

"""
A script to create a page that links to outdated pages that are not edited
for $X amount of days in your LogSeq graph
"""

import os
import datetime
import re
import argparse

# Set up command-line argument parsing
parser = argparse.ArgumentParser(description='Generate a LogSeq page with links to outdated pages.')
parser.add_argument('--logseq_path', type=str, help='Path to your LogSeq graph')
parser.add_argument('--days_threshold', type=int, help='Number of days to consider a page outdated')

args = parser.parse_args()
logseq_path = args.logseq_path
days_threshold = args.days_threshold

# Regex pattern to exclude pages that start with a date in:
# YYYY-MM-DD, YYYY_MM_DD, or journals_YYYY_MM_DD format
exclude_pattern = re.compile(r'^(journals_)?\d{4}[-_]\d{2}[-_]\d{2}.*$')

# Get current date
now = datetime.datetime.now()

# Find all pages
pages = []
for root, dirs, files in os.walk(logseq_path):
    for file in files:
        if file.endswith(".md"):
            file_path = os.path.join(root, file)
            page_name = os.path.basename(file).replace(".md", "")
            # Exclude pages matching the specific pattern
            if exclude_pattern.match(page_name):
                continue
            modification_time = os.path.getmtime(file_path)
            modification_date = datetime.datetime.fromtimestamp(modification_time)
            # Check if the page has not been modified in the specified number of days
            if (now - modification_date).days > days_threshold:
                pages.append((page_name, modification_date))

# Generate a LogSeq page with links to outdated pages
output_path = os.path.join(logseq_path, "outdated-pages.md")
with open(output_path, "w", encoding='utf-8') as f:
    f.write(f"# Pages not edited in the last {days_threshold} days\n")
    for page_name, mod_date in pages:
        f.write(f"- [[{page_name}]] - last edited at {mod_date.strftime('%Y-%m-%d %H:%M:%S')}\n")

print(f"Generated {output_path} with {len(pages)} outdated pages.")
