# Base R plots for the validation report.
source("analysis/R/load_data.R")
data <- load_validation_data()
validate_columns(data)
dir.create("validation/plots", recursive = TRUE, showWarnings = FALSE)

png("validation/plots/risk_vs_events.png", width = 900, height = 600)
plot(jitter(data$observed_flood), data$risk_score, xlab = "Observed flood (0/1)", ylab = "Risk score", main = "Risk score vs observed flood", pch = 19)
dev.off()

png("validation/plots/risk_distribution.png", width = 900, height = 600)
barplot(table(data$risk_level), main = "Risk level distribution", ylab = "Events")
dev.off()

png("validation/plots/spatial_validation_map.png", width = 900, height = 700)
plot(data$lon, data$lat, col = heat.colors(100)[pmax(1, pmin(100, round(data$risk_score) + 1))], pch = 19, xlab = "Longitude", ylab = "Latitude", main = "Historical events and risk scores")
box()
dev.off()
