# Prisma SD-WAN WAN STATS (Preview)
The purpose of this script is to retrieve WAN statistics for all circuits during the hours of 8:00 AM to 5:00 PM PST. It calculates and reports the minimum, maximum, and average usage, as well as the total number of minutes each circuit exceeds 70% utilization.

#### License
MIT

#### Requirements
* Active CloudGenix Account - Please generate your API token and add it to cloudgenix_settings.py
* Python >=3.7

#### Installation:
 Scripts directory. 
 - **Github:** Download files to a local directory, manually run the scripts. 
 - pip install -r requirements.txt

### Examples of usage:
 Please generate your API token and add it to cloudgenix_settings.py
 
 1. ./wan_stats.py -D "2025-01-06"
      - Provide the date you want the WAN stats for 

### Caveats and known issues:
 - This is a PREVIEW release, hiccups to be expected. Please file issues on Github for any problems.

#### Version
| Version | Build | Changes |
| ------- | ----- | ------- |
| **1.0.0** | **b1** | Initial Release. |

#### For more info
 * Get help and additional Prisma SD-WAN Documentation at <https://docs.paloaltonetworks.com/prisma/cloudgenix-sd-wan.html>
