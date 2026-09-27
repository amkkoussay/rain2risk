# Load validation results for Phase 6.
load_validation_data <- function(path = "validation/results/validation_results.csv") {
  read.csv(path, stringsAsFactors = FALSE)
}

validate_columns <- function(data) {
  required <- c("event_id", "date", "lat", "lon", "observed_flood", "risk_score", "risk_level", "cell_id")
  missing <- setdiff(required, names(data))
  if (length(missing) > 0) stop(paste("Missing columns:", paste(missing, collapse = ", ")))
  if (any(data$risk_score < 0 | data$risk_score > 100)) stop("Risk scores must be in 0..100")
  invisible(TRUE)
}
