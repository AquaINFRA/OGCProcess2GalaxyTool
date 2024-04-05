# Run with Rscript ./OTB_MeanShiftSmoothing.R
#--file otb_band_math_test_input.txt
#--fOut float --fOutpos float --processingMemory 1024 --spatialR 5 --rangeR 15
#--thresHold 0.1 --maxIter 100 --rangeRamp 0 --modeSearch False
#--outputType png
#--outputFormat download --outputData test1.png

library("httr2")
library("jsonlite")
library("getopt")

args <- commandArgs(trailingOnly = TRUE)
option_specification <- matrix(c(
  "input", "i1", 1, "character",
  "fout", "i2", 1, "character",
  "foutpos", "i3", 1, "character",
  "ram", "i4", 1, "integer",
  "spatialr", "i5", 2, "integer",
  "ranger", "i6", 2, "double",
  "thres", "i7", 2, "double",
  "maxiter", "i8", 2, "integer",
  "rangeramp", "i9", 2, "double",
  "modesearch", "i10", 1, "character",
  "fout_out", "i11", 1, "character",
  "foutpos_out", "i12", 1, "character",
  "server", "i13", 1, "character",
  "process", "i14", 1, "character",
  "output_data", "o", 1, "character"
), byrow = TRUE, ncol = 4)
options <- getopt(option_specification)

input <- options$input
fout <- options$fout
foutpos <- options$foutpos
ram <- options$ram
spatialr <- options$spatialr
ranger <- options$ranger
thres <- options$thres
maxiter <- options$maxiter
rangeramp <- options$rangeramp
modesearch <- options$modesearch
fout_out <- options$fout_out
foutpos_out <- options$foutpos_out
server <- options$server
process <- options$process
output_data <- options$output_data
output_format <- "getUrl"

cat("\n file: ", input)
cat("\n fout: ", fout)
cat("\n foutpos: ", foutpos)
cat("\n processing_memory: ", ram)
cat("\n spatialr: ", spatialr)
cat("\n ranger: ", ranger)
cat("\n threshold: ", thres)
cat("\n maxiter: ", maxiter)
cat("\n rangeramp: ", rangeramp)
cat("\n modesearch: ", modesearch)
cat("\n fout_out: ", fout_out)
cat("\n foutpos_out: ", foutpos_out)
cat("\n server: ", server)
cat("\n process: ", process)

base_url <- server
execute <- paste0("processes/", process, "/execution")
get_status <- "jobs/"
get_result <- "/results"

#file_urls <- readLines(file, warn = FALSE)

#il_list <- lapply(file_urls, function(url) {
#  list("href" = url)
#})

json_data <- list(
  "inputs" = list(
    "in" = list(
      "href" = input
    ),
    "fout" = fout,
    "foutpos" = foutpos,
    "ram" = ram,
    "spatialr" = spatialr,
    "ranger" = ranger,
    "thres" = thres,
    "maxiter" = maxiter,
    "rangeramp" = rangeramp,
    "modesearch" = modesearch
  ),
  "outputs" = list(
    "fout" = list(
      "format" = list(
        "mediaType" = fout_out
      ),
      "transmissionMode" = "reference"
    ),
    "foutpos" = list(
      "format" = list(
        "mediaType" = foutpos_out
      ),
      "transmissionMode" = "reference"
    )
  )
)

make_response_body_readable <- function(body) {
  hex <- c(body)
  int_values <- as.integer(hex)
  raw_vector <- as.raw(int_values)
  readable_output <- rawToChar(raw_vector)
  json_object <- jsonlite::fromJSON(readable_output)
  return(json_object)
}

tryCatch({
  # Request 1
  resp1 <- request(paste0(base_url, execute)) %>%
    req_headers(
      "accept" = "/*",
      "Prefer" = "respond-async;return=representation",
      "Content-Type" = "application/json"
    ) %>%
    req_body_json(json_data) %>%
    req_perform()
  response <- make_response_body_readable(resp1$body)
  status_code1 <- resp1$status_code
  if (status_code1 == 201) {
    status <- "running"
    attempt <- 1
    while (status == "running") {
      # Request 2
      resp2 <- request(paste0(base_url, get_status, response$jobID)) %>%
        req_headers(
          "accept" = "application/json"
        ) %>%
        req_perform()
      status_code2 <- resp2$status_code
      if (status_code2 == 200) {
        response2 <- make_response_body_readable(resp2$body)
        cat("\n", response2$status)
        if (response2$status == "successful") {
          status <- "successful"
          # Request 3
          resp3 <- request(paste0(
            base_url,
            get_status, response2$jobID, get_result
          )) %>%
            req_headers(
              "accept" = "application/json"
            ) %>%
            req_perform()
          status_code3 <- resp3$status_code
          if (status_code3 == 200) {
            response3 <- make_response_body_readable(resp3$body)
            if (output_format == "download") {
              options(timeout = 600)
              download.file(response3$fout$href,
                destfile = paste0("output1.", options$outputType),
                mode = "wb"
              )
              download.file(response3$foutpos$href,
                destfile = paste0("output2.", options$outputType),
                mode = "wb"
              )
            } else if (output_format == "getUrl") {
              writeLines(paste(response3$fout$href, response3$foutpos$href,
                           sep = "\n"
                         ), con = "output.txt")
            }
          } else if (status_code3 == 404) {
            print("The requested URI was not found.")
          } else if (status_code3 == 500) {
            print("A server error occurred.")
          } else {
            print(paste("HTTP", status_code3, "Error:", resp3$status_message))
          }
        } else if (response2$status == "failed") {
          status <- "failed"
          message("An error occurred. For further details, check OGC Job status through https://ospd.geolabs.fr:8300/ogc-api/jobs/", response2$jobID)
          q(status = 1)
        }
      } else {
        status <- "failed"
        print(paste("HTTP", status_code2, "Error:", resp2$status_message, "An error occurred. For further details, check OGC Job status through https://ospd.geolabs.fr:8300/ogc-api/jobs/", response2$jobID))
        q(status = 1)
      }
      Sys.sleep(3)
    }
    print(status)
  } else if (status_code1 == 400) {
    print("A query parameter has an invalid value.")
  } else if (status_code1 == 404) {
    print("The requested URI was not found.")
  } else if (status_code1 == 500) {
    print("The requested URI was not found.")
  } else {
    print(paste("HTTP", status_code1, "Error:", resp1$status_message))
  }
}, error = function(e) {
  message("An error occurred:", e)
  # Exit with code 1
  q(status = 1)
})