"""
Step 4 (optional NO2 enhancement) -- Sentinel-5P/TROPOMI tropospheric NO2 annual mean over the
Central Asian capitals via Google Earth Engine.

Credential note: the .env holds a Google OAuth *client* (client_id ...apps.googleusercontent.com +
client_secret). That is an INTERACTIVE credential: it requires a one-time browser consent to mint a
refresh token, and EE must be enabled on the associated Google Cloud project. It is NOT headless on
its own (a service-account JSON would be). Run this ONCE locally to complete the browser grant.

NO2 is a secondary layer (independent traffic/combustion gradient + Achakulwisut asthma input);
the paper's exposure and health results do not depend on it.

Setup:
  pip install earthengine-api
  Confirm Earth Engine is enabled for the Cloud project tied to the client (project number 80210843692).
Run:
  python scripts/pipeline/tropomi_gee.py   # opens a browser once; then exports NO2 to data/pipeline/
"""
import os
from paths import pipeline_path
def load_env(p):
    d = {}
    for line in open(p, encoding="utf-8"):
        if ":" in line:
            k, v = line.split(":", 1); d[k.strip().lower().replace(" ", "_")] = v.strip()
    return d

def main():
    import ee
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    env = load_env(os.path.join(root, ".env"))
    sa_email = env.get("email")                      # service account from .env
    key_file = os.path.join(root, "gee-service-account.json")   # <-- private-key JSON (download from GCP)
    if not os.path.exists(key_file):
        raise SystemExit("Missing gee-service-account.json (private key). GCP Console -> IAM -> "
                         "Service Accounts -> " + str(sa_email) + " -> Keys -> Add key -> JSON. "
                         "Place it at repo root. Also ensure the service account is EE-registered "
                         "and the Earth Engine API is enabled on its project.")
    project = sa_email.split("@")[1].split(".")[0]   # e.g. project-6304b1d4-...
    creds = ee.ServiceAccountCredentials(sa_email, key_file)
    ee.Initialize(creds, project=project)            # fully headless
    caps = {"Tashkent": (69.25, 41.31), "Almaty": (76.89, 43.24), "Astana": (71.45, 51.17),
            "Bishkek": (74.61, 42.87), "Dushanbe": (68.79, 38.56), "Ashgabat": (58.33, 37.96)}
    col = (ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_NO2")
           .select("tropospheric_NO2_column_number_density")
           .filterDate("2022-01-01", "2022-12-31"))
    annual = col.mean()
    out = {}
    for c, (lo, la) in caps.items():
        pt = ee.Geometry.Point([lo, la]).buffer(3000)
        v = annual.reduceRegion(ee.Reducer.mean(), pt, 1000).getInfo()
        out[c] = v
        print(c, v)
    import json
    json.dump(out, open(pipeline_path("tropomi_no2_capitals_2022.json"), "w"), indent=2)
    print("saved data/pipeline/tropomi_no2_capitals_2022.json")

if __name__ == "__main__":
    main()
