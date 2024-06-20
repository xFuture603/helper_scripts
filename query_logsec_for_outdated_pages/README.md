# Identify outdated pages in LogSeq

This script generates a LogSeq page with links to pages that have not been edited within a specified number of days. It helps you identify pages in your LogSeq graph that may need attention or updating.

## Use Cases

You might find this script useful if you want to periodically review and clean up outdated pages in your LogSeq graph. It provides a centralized list of pages that haven't been edited recently, making it easier to prioritize updates.

## Requirements

- Python 3

## Usage

The script can be run from the command line. It requires specifying the path to your LogSeq graph directory and the number of days to consider a page outdated.

```sh
python3 generate_outdated_pages.py --logseq_path /path/to/your/logseq/graph --days_threshold 30
```

## Arguments

- `--logseq_path` (required): Path to your LogSeq graph directory.
- `--days_threshold` (required): Number of days to consider a page outdated.

## Output

The script generates a markdown file (`outdated-pages.md`) in your LogSeq graph directory. This file contains links to pages that have not been edited in the specified number of days.

Each entry in the output file includes:

- A link to the outdated page.
- The date and time when the page was last edited.

## Example Output

Here's an example of what the `outdated-pages.md` file might look like:

```markdown
# Pages not edited in the last 30 days

- [[Page1]] - last edited at 2024-06-10 08:30:00
- [[Page2]] - last edited at 2024-06-05 14:00:00
```

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
