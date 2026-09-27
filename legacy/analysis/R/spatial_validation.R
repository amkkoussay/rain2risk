# Spatial validation companion script.
source("analysis/R/load_data.R")
data <- load_validation_data()
validate_columns(data)

# WGS84 geographic coordinates are EPSG:4326.
if (any(data$lat < -90 | data$lat > 90 | data$lon < -180 | data$lon > 180)) stop("Invalid geographic coordinates")
cat("CRS: EPSG:4326 (WGS84)\n")
cat("Events inside study area:", sum(data$lat >= 36.79 & data$lat <= 36.82 & data$lon >= 10.16 & data$lon <= 10.20), "of", nrow(data), "\n")

# Use sf when available for point geometry and spatial integrity checks.
if (requireNamespace("sf", quietly = TRUE)) {
  points <- sf::st_as_sf(data, coords = c("lon", "lat"), crs = 4326, remove = FALSE)
  if (any(!sf::st_is_valid(points))) stop("Invalid point geometry")
  cat("sf geometry check: PASS\n")
} else {
  cat("sf is not installed; coordinate checks above still ran. Install sf for full spatial geometry checks.\n")
}
