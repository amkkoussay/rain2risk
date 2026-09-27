# Global data source notes

- Open-Meteo Elevation API documentation: https://open-meteo.com/en/docs/elevation-api
- ESA WorldCover data access: https://esa-worldcover.org/en/data-access
- Digital Earth Africa WorldCover OWS documentation: https://docs.digitalearthafrica.org/en/latest/data_specs/ESA_WorldCover_specs.html
- ArcGIS item for ESA WorldCover 2021: https://www.arcgis.com/home/item.html?id=7bec35d76dd54ea584f98d286571eb84
- ArcGIS ImageServer used for global WGS84 LERC tiles: https://tiledimageservices.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/European_Space_Agency_WorldCover_2021_Land_Cover_WGS84_7/ImageServer
- OpenStreetMap Overpass API: https://wiki.openstreetmap.org/wiki/Overpass_API

The live end-to-end test returned HTTP 200 and 80 cells for Tunis, Tokyo, and New York using the same POST /api/analyze flow. Elevation, WorldCover, and OSM are fetched for the selected local area; weather is fetched once for the selected point. WorldCover classes are read from ArcGIS global WGS84 LERC tiles at zoom level 12 using the lerc package.
