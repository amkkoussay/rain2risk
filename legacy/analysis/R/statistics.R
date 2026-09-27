# Basic validation statistics. No model fitting is done here.
source("analysis/R/load_data.R")
data <- load_validation_data()
validate_columns(data)
data$observed_flood <- as.integer(data$observed_flood)

spearman <- cor(data$risk_score, data$observed_flood, method = "spearman")
summary_table <- aggregate(observed_flood ~ risk_level, data = data, FUN = function(x) c(events = length(x), flood_rate = mean(x)))

cat("Spearman risk score vs observed flood:", round(spearman, 4), "\n")
print(summary_table)
cat("Mean Risk Engine score for flood events:", mean(data$risk_score[data$observed_flood == 1]), "\n")
cat("Mean Rainfall-only score for flood events:", mean(data$rainfall_only_score[data$observed_flood == 1]), "\n")
