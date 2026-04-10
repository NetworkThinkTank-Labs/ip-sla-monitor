# IP SLA Monitor

**Python-based IP SLA monitoring tool with Cisco DNA Center and NetBox integration for automated network performance tracking and reporting.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Blog Post:** [Monitoring IP SLAs with Python, DNA Center, and NetBox](https://networkthinktank.blog)
>
> ---
>
> ## Table of Contents
>
> - [Overview](#overview)
> - - [Features](#features)
>   - - [Architecture](#architecture)
>     - - [Prerequisites](#prerequisites)
>       - - [Installation](#installation)
>         - - [Configuration](#configuration)
>           - - [Usage](#usage)
>             - - [Sample Output](#sample-output)
>               - - [Project Structure](#project-structure)
>                 - - [Contributing](#contributing)
>                   - - [Related Projects](#related-projects)
>                     - - [License](#license)
>                      
>                       - ---
>
> ## Overview
>
> IP SLA Monitor is a Python automation tool that collects IP SLA (Service Level Agreement) metrics from Cisco network devices via **Cisco DNA Center** APIs and correlates them with device inventory data from **NetBox**. It provides automated monitoring, alerting, and reporting for network performance metrics including latency, jitter, packet loss, and availability.
>
> This project was created as part of the [NetworkThinkTank](https://networkthinktank.blog) series on network automation with Python.
>
> ## Features
>
> - **DNA Center Integration** - Retrieve IP SLA operation data, device health, and path traces via the Cisco DNA Center REST API
> - - **NetBox Integration** - Enrich monitoring data with device metadata, site information, and IP address management from NetBox
>   - - **Performance Reporting** - Generate JSON and CSV reports with latency, jitter, packet loss, and MOS scores
>     - - **Threshold Alerting** - Configurable thresholds for latency, jitter, and packet loss with console and log-based alerts
>       - - **Scheduled Monitoring** - Run continuous monitoring loops with configurable polling intervals
>         - - **Sample Outputs** - Includes example output files for reference andtesting
>          
>           - ## Architecture
>          
>           - ```
>             +----------------+      +--------------------+      +----------------+
>             |  IP SLA        |      |   IP SLA Monitor   |      |   NetBox       |
>             |  Operations    |<---->|   (Python)         |<---->|   DCIM/IPAM    |
>             |  on Devices    |      |                    |      |                |
>             +----------------+      +--------+-----------+      +----------------+
>                                              |
>                                     +--------v-----------+
>                                     |  Cisco DNA Center  |
>                                     |  REST API          |
>                                     +--------------------+
>             ```
>
> ## Prerequisites
>
> - Python 3.9 or higher
> - - Cisco DNA Center (2.x+) with API access enabled
>   - - NetBox (3.x+) instance with API token
>     - - Network devices with IP SLA operations configured
>      
>       - ## Installation
>      
>       - 1. **Clone the repository:**
>        
>         2. ```bash
>            git clone https://github.com/NetworkThinkTank-Labs/ip-sla-monitor.git
>            cd ip-sla-monitor
>            ```
>
> 2. **Create a virtual environment:**
>
> 3. ```bash
>    python -m venv venv
>    source venv/bin/activate  # Linux/macOS
>    ```
>
> 3. **Install dependencies:**
>
> 4. ```bash
>    pip install -r requirements.txt
>    ```
>
> 4. **Configure environment variables:**
>
> 5. ```bash
>    cp .env.example .env
>    # Edit .env with your DNA Center and NetBox credentials
>    ```
>
> ## Configuration
>
> Create a `.env` file in the project root (or copy from `.env.example`):
>
> ```env
> # Cisco DNA Center
> DNAC_HOST=https://sandboxdnac.cisco.com
> DNAC_USERNAME=devnetuser
> DNAC_PASSWORD=Cisco123!
> DNAC_VERIFY_SSL=False
>
> # NetBox
> NETBOX_URL=https://netbox.example.com
> NETBOX_TOKEN=your-netbox-api-token
> NETBOX_VERIFY_SSL=True
>
> # Monitoring Settings
> POLL_INTERVAL=300
> LATENCY_THRESHOLD_MS=100
> JITTER_THRESHOLD_MS=30
> PACKET_LOSS_THRESHOLD_PCT=1.0
> OUTPUT_DIR=./output
> ```
>
> ## Usage
>
> ### Run the main IP SLA monitor
>
> ```bash
> python ip_sla_monitor.py
> ```
>
> ### Query DNA Center for device and SLA data
>
> ```bash
> python dnac_integration.py
> ```
>
> ### Enrich data with NetBox device information
>
> ```bash
> python netbox_integration.py
> ```
>
> ### Run a single collection cycle (no loop)
>
> ```bash
> python ip_sla_monitor.py --once
> ```
>
> ## Sample Output
>
> ### JSON Report (output/ip_sla_report.json)
>
> ```json
> {
>   "report_timestamp": "2026-04-10T14:30:00Z",
>   "source": "DNA Center + NetBox",
>   "summary": {
>     "total_operations": 12,
>     "passing": 10,
>     "failing": 2,
>     "avg_latency_ms": 45.2
>   },
>   "operations": [
>     {
>       "sla_id": 100,
>       "source_device": "core-rtr-01",
>       "destination": "10.1.1.1",
>       "type": "icmp-echo",
>       "latest_rtt_ms": 23,
>       "avg_latency_ms": 25.4,
>       "jitter_ms": 3.2,
>       "packet_loss_pct": 0.0,
>       "status": "OK",
>       "netbox_site": "HQ-DC1",
>       "netbox_role": "core-router"
>     }
>   ]
> }
> ```
>
> ### CSV Report (output/ip_sla_report.csv)
>
> ```
> sla_id,source_device,destination,type,latest_rtt_ms,avg_latency_ms,jitter_ms,packet_loss_pct,status,netbox_site,netbox_role
> 100,core-rtr-01,10.1.1.1,icmp-echo,23,25.4,3.2,0.0,OK,HQ-DC1,core-router
> 101,core-rtr-01,10.2.1.1,icmp-echo,48,52.1,8.7,0.5,OK,HQ-DC1,core-router
> 200,branch-rtr-01,10.1.1.1,icmp-echo,110,115.3,35.2,2.1,ALERT,Branch-NYC,branch-router
> ```
>
> ## Project Structure
>
> ```
> ip-sla-monitor/
>   ip_sla_monitor.py        # Main monitoring script
>   dnac_integration.py       # DNA Center API integration
>   netbox_integration.py     # NetBox API integration
>   requirements.txt          # Python dependencies
>   .env.example              # Environment variable template
>   output/                   # Sample output files
>     ip_sla_report.json      # Sample JSON report
>     ip_sla_report.csv       # Sample CSV report
>   LICENSE                   # MIT License
>   README.md                 # This file
> ```
>
> ## Contributing
>
> Contributions are welcome! Please:
>
> 1. Fork the repository
> 2. 2. Create a feature branch (`git checkout -b feature/my-feature`)
>    3. 3. Commit your changes (`git commit -am 'Add new feature'`)
>       4. 4. Push to the branch (`git push origin feature/my-feature`)
>          5. 5. Open a Pull Request
>            
>             6. ## Related Projects
>            
>             7. - [network-backup-automation](https://github.com/NetworkThinkTank-Labs/network-backup-automation) - Automated network device backups with Python and Netmiko
>                - - [home-lab-guide](https://github.com/NetworkThinkTank-Labs/home-lab-guide) - Build a home lab like a pro
>                 
>                  - ## License
>                 
>                  - This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
>                 
>                  - ---
>
> Made with coffee by [NetworkThinkTank](https://networkthinktank.blog)
