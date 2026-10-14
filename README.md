# SEPOMEX INEGI Bridge

A high-performance data bridge connecting **SEPOMEX** (Mexican Postal Service) and **INEGI** (National Institute of Statistics and Geography) datasets. This project processes, normalizes, and links official Mexican geographical catalogs into an optimized **SQLite** database, exposing a clean REST API built with **FastAPI**.

---

## 🚀 Key Features

* **Cross-Reference Data Mapping:** Bridges official 5-digit postal codes (`SEPOMEX`) with official geo-statistical codes (`CVEGEO` from `INEGI`) via municipality keys (`cvegeo_mun`).
* **FastAPI REST Endpoints:** High-performance asynchronous endpoints with automatic Swagger/OpenAPI documentation.
* **Lightweight & Portable:** Fully containerized with **Docker** and backed by a localized SQLite database for zero-friction setup.
* **Search & Filter Capabilities:** Look up settlements by postal code or query local INEGI communities filtered by municipality.

---

## 🛠️ Tech Stack

* **Language:** Python 3.10+
* **Framework:** FastAPI / Uvicorn
* **Database:** SQLite (with optimized indexes)
* **Data Processing:** Pandas
* **Containerization:** Docker

---

## 📁 Project Structure

```text
├── build_database.py       # Script to build and index the SQLite database
├── cli_search.py           # Command-line interface for quick local searches
├── Dockerfile              # Container definition
├── .dockerignore           # Excluded files for Docker build
├── .gitignore              # Git ignore rules
├── License                 # Project license
├── main.py                 # FastAPI application and endpoints
├── process_catalogs.py     # Data cleaning and normalization pipeline
├── README.md               # Project documentation
├── requirements.txt        # Production dependencies
└── requierements-dev.txt   # Development and tooling dependencies
```
## 📊 Data Sources & Raw Files

The raw data processed by the pipeline originates from official Mexican government portals:

1. **SEPOMEX (Postal Codes & Settlements):** 
   * Download the official postal code database (usually in text/TXT format separated by pipes `|` or Excel) from the [Correos de México / SEPOMEX Portal](http://www.dgis.salud.gob.mx/contenidos/intercambio/codigo_postal_gobmx.html).
   * Place the source file in your working directory so `process_catalogs.py` can parse and normalize it.

2. **SEPOMEX (Geo-statistical Localities):** 
   * Download the Marco Geoestadístico and locality catalogs from the [Correos de México / SEPOMEX Portal](http://www.dgis.salud.gob.mx/contenidos/intercambio/localidades_gobmx.html).
   * Ensure the locality files match the expected format for the SQLite ingestion script (`build_database.py`).

##⚙️ Installation & Setup
---
1. Clone the Repository

git clone [https://github.com/your-username/sepomex-inegi-bridge.git](https://github.com/your-username/sepomex-inegi-bridge.git)
cd sepomex-inegi-bridge

2. Set Up a Virtual Environment (Recommended)

python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

3. Install Dependencies

pip install -r requirements.txt

4. Build the Local Database

Run the pipeline to process raw catalogs and generate the optimized SQLite database (mexico_geo_catalog.db):
python process_catalogs.py
python build_database.py


##🚀 Running the API
---
Start the FastAPI development server using Uvicorn:

uvicorn main:app --reload

Once running, you can access:
Interactive API Docs (Swagger UI): http://localhost:8000/docs
Alternative Docs (ReDoc): http://localhost:8000/redoc


🐳 Running with Docker 
---
You can easily build and run the service inside a Docker container:

# Build the Docker image
docker build -t sepomex-inegi-api .

# Run the container
docker run -d -p 8000:8000 --name geo-api sepomex-inegi-api

📄 License
---
Distributed under the terms of the License file included in this repository.

