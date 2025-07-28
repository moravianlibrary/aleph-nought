# Aleph Client

A Python client library for interacting with Aleph library systems through multiple service interfaces: **OAI-PMH**, **X-Server**, and **Z39.50**.

This package provides specialized clients for each protocol, as well as a unified `AlephClient` class that bundles these clients for convenient access.

---

## Overview

Aleph is a widely used library management system offering several APIs to access bibliographic and catalog data:

* **OAI-PMH (Open Archives Initiative Protocol for Metadata Harvesting)**
  Harvest and retrieve MARC records via the standardized OAI protocol.

* **X-Server API**
  A proprietary Aleph API supporting searches, record retrieval, and paginated results.

* **Z39.50**
  A standard library information retrieval protocol commonly used for searching and retrieving bibliographic records.

---

## Clients

### AlephOAIClient

Client to interact with Aleph's OAI-PMH interface.

* Supports harvesting records from multiple configured OAI sets.
* Fetch individual MARC records by document number.
* Check OAI service availability.

More info on OAI-PMH protocol:
[https://www.openarchives.org/OAI/openarchivesprotocol.html#ProtocolSyntax](https://www.openarchives.org/OAI/openarchivesprotocol.html#ProtocolSyntax)

---

### AlephXClient

Client to interact with the Aleph X-Server API.

* Perform searches by field and value.
* Fetch paginated results from the server.
* Retrieve a single system number for unique queries.

For detailed X-Server operations, see:
[https://developers.exlibrisgroup.com/aleph/apis/aleph-x-services/](https://developers.exlibrisgroup.com/aleph/apis/aleph-x-services/)

---

### AlephZ3950Client

Client for Aleph's Z39.50 interface using the YAZ C++ library bindings.

* Search for MARC21 records using PQF query syntax.
* Manages native connections to the Z39.50 service.
* Requires the YAZ library to be installed.

YAZ toolkit:
[https://www.indexdata.com/yaz/](https://www.indexdata.com/yaz/)

---

## AlephClient

A unified client that wraps all three service clients (OAI, X, Z39.50).

* Provides convenient properties to access the configured services.
* Raises errors if a requested service is not configured.
* Designed for flexible use with multiple Aleph configurations.

---

## Installation

### Installing from GitHub using version tag

You can install the package directly from GitHub for a specific version tag:

```bash
pip install git+https://github.com/moravianlibrary/aleph-nought.git@v1.2.3
```

*Replace `v1.2.3` with the desired version tag*

To always install the most recent version, use the latest tag:

```bash
pip install git+https://github.com/moravianlibrary/aleph-nought.git@latest
```


### Installing YAZ

* **On Debian/Ubuntu:**

```bash
sudo apt update
sudo apt install yaz
```

* **On Fedora:**

```bash
sudo dnf install yaz
```

* **On macOS (using Homebrew):**

```bash
brew install yaz
```

*To use the YAZ command-line client, run the `yaz-client` command.*

### Installing local 

Install required dependencies using `pip`:

```bash
pip install -r requirements.txt
```

> **Note:** The `AlephZ3950Client` depends on the YAZ toolkit and Python bindings, which must be installed separately.

---

## Versions

- **0.1.x**
    Initial release series supporting:
    - AlephOAIClient for OAI-PMH services
    - AlephXClient for Aleph X-Server API
    - AlephZ3950Client using YAZ toolkit bindings
    - AlephClient as a unified client wrapper
    - **0.1.0**  
        First stable release with core functionality for all clients.
- **latest**
    Always points to the most up-to-date stable version of the client.

---

## Usage Example

```python
from aleph_nought import AlephClient, AlephConfig

config = AlephConfig(
    base="mybase",
    oai=oai_config,     # Optional AlephOAIConfig instance
    x=x_config,         # Optional AlephXConfig instance
    z3950=z3950_config  # Optional AlephZ3950Config instance
)

client = AlephClient(config)

# Access OAI client
records = list(client.OAI.list_records(from_date="2023-01-01T00:00:00Z", to_date="2023-06-30T23:59:59Z"))

# Use X-Server client to search system numbers
system_numbers = list(client.X.find_system_numbers("TITLE", "Python"))

# Search Z39.50
marc_records = client.Z3950.search("@attr 1=4 'Python Programming'")
```
