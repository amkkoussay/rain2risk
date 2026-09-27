# WorldCover metadata notes

The official ArcGIS ImageServer metadata for ESA WorldCover 2021 reports EPSG:4326, extent -180 to 180 longitude and -60 to 84 latitude, one U8 thematic band, 256x256 tiles, origin (-180, 84), and advertised levels of detail from 0.682666666666667 degrees per pixel down to 0.0000833333333333333 degrees per pixel. The provider code must read these values from the service metadata rather than embedding unexplained geographic constants.

The official ESA data access page identifies WorldCover 2021 v200, provides the product user manual and class resources, and links to WMS/WMTS, viewer, AWS Open Data, and downloads. The product is a global land-cover map and its class values are used as categorical pixel codes; cell fractions must be calculated from valid sampled pixels.

Sources:
- https://tiledimageservices.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/European_Space_Agency_WorldCover_2021_Land_Cover_WGS84_7/ImageServer?f=pjson
- https://esa-worldcover.org/en/data-access
