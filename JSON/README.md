The QC scripts are built to rely on a JSON file containing settings and parameters for each step of the QC process.
`fix_jsons.py` and `fix_results_QC_json.py` were first built to update older projects to this JSON process. 
Because the QC scripts rely on the paths within the JSON files, it would be super lame and difficult to manually correct paths when
moving files around. Hopefully these scripts help!

I have not built a tool to attempt to import (create JSON files from scratch) an entire project.
I included my "one time use" bash scripts I first used. They are probably out of date and buggy, 
but they might help you get started. Proceed with caution :)

See [Sample and Run Organization](https://github.com/jlaw9/TRI_Scripts/wiki/1.1-Organize-Sequencing-Files#sample-and-run-organization)
for examples of how we organize our projects. 

Example calls:

```bash
# to fix/create the JSON files in a project directory.
# This would be helpful if you had to move a project to to another filesystem or server.
~/TRI_Scripts/JSON/fix_jsons.py -n /path/to/project -p /path/to/project -j /results/plugins/QCRunTransfer/scripts/Project.json

# to fix/create the JSON files for a single sample
~/TRI_Scripts/JSON/fix_jsons.py -n /path/to/project -s /path/to/sample -j /results/plugins/QCRunTransfer/scripts/Project.json

# to move the sample and fix the paths within the JSON files
~/TRI_Scripts/JSON/fix_jsons.py -n /new/path/to/project --move -s /path/to/sample -j /results/plugins/QCRunTransfer/scripts/Project.json
```
