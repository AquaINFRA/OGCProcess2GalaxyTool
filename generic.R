# Example command: Rscript ./generic.R --server https://ospd.geolabs.fr:8300/ogc-api/ --process OTB.BandMath --il https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/31/U/ET/2019/4/S2B_31UET_20190421_0_L2A/TCI.tif --out float --ram 128 --exp im1b3,im1b2,im1b1 --outputData bandMathOutput
# Example command: Rscript ./generic.R --server https://ospd.geolabs.fr:8300/ogc-api/ --process OTB.MeanShiftSmoothing --in https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/31/U/ET/2019/4/S2B_31UET_20190421_0_L2A/TCI.tif --fout float --foutpos float --ram 128 --spatialr 5 --ranger 15.0 --thres 0.1 --maxiter 100 --rangeramp 0.0 --modesearch true --outputData meanShiftSmoothingOutput

library("httr2")
library("jsonlite")
library("getopt")

getParameters <- function(){
    args <- commandArgs(trailingOnly = TRUE)

    names <- list()
    params <- list()

    for (x in 1:length(args)) {
        if(x %% 2 == 0) {
            param <- gsub("--", "", args[x-1])
            value <- args[x]
            params <- append(params, value)
            names <- append(names, param)
        }
    }
    names(params) <- names
    return(params)
}

parseResponseBody <- function(body) {
  hex <- c(body)
  intValues <- as.integer(hex)
  rawVector <- as.raw(intValues)
  readableOutput <- rawToChar(rawVector)
  jsonObject <- jsonlite::fromJSON(readableOutput)
  return(jsonObject)
}

getOutputs <- function(url, process, output) {
    url <- paste(paste(url, "/processes/", sep = ""), process, sep = "")
    request <- request(url)
    response <- req_perform(request)
    responseBody <- parseResponseBody(response$body)
    outputs <- list()

    sink(paste0(output, "processDescription.json"))
      print(toJSON(responseBody, pretty = TRUE))
    sink()

    transmissionMode <- list("transmissionMode" = "reference")
    #missing: possibility to specify output type, see OTB.BandMath and
    # outputs.out.format.mediaType
    for (x in 1:length(responseBody$outputs)) {
        outputs[[x]] <- transmissionMode
    }

    names(outputs) <- names(responseBody$outputs)
    return(outputs)
}


executeProcess <- function(url, process, requestBodyData) {
    url <- paste(paste(paste(url, "processes/", sep = ""), process, sep = ""), "/execution", sep = "")
    cat("\n url: ", url)
    response <- request(url) %>%
    req_headers(
      "accept" = "/*",
      "Prefer" = "respond-async;return=representation",
      "Content-Type" = "application/json"
    ) %>%
    req_body_json(requestBodyData) %>%
    req_perform()

    cat("\n Process executed")
    cat("\n status: ", response$status_code)
    cat("\n jobID: ", parseResponseBody(response$body)$jobID)

    jobID <- parseResponseBody(response$body)$jobID

    return(jobID)
}

checkJobStatus <- function(server, jobID) {
  response <- request(paste0(server, "jobs/", jobID)) %>%
    req_headers(
        'accept' = 'application/json'
    ) %>%
    req_perform()
  jobStatus <- parseResponseBody(response$body)$status
  cat("\n status: ", jobStatus)
  return(jobStatus)
}

getStatusCode <- function(server, jobID) {
  url <- paste0(server, "jobs/", jobID)
  response <- request(url) %>%
      req_headers(
        'accept' = 'application/json'
      ) %>%
      req_perform()
  return(response$status_code)
}

getResult <- function (server, jobID) {
  response <- request(paste0(server, "jobs/", jobID, "/results")) %>%
    req_headers(
      'accept' = 'application/json'
    ) %>%
    req_perform()
  return(response)
}

retrieveResults <- function(server, jobID, outputData) {
    status_code <- getStatusCode(server, jobID)
    if(status_code == 200){
        status <- "running"
        cat(status)
        while(status == "running"){
            jobStatus <- checkJobStatus(server, jobID)
            if (jobStatus == "successful") {
                status <- jobStatus
                result <- getResult(server, jobID)
                if (result$status_code == 200) {
                  resultBody <- parseResponseBody(result$body)
                  sink(paste0(outputData, "_result.txt"))
                    print(resultBody)
                  sink()
                }
            }
        Sys.sleep(3)
        }
        cat("\n done \n")
    } else if (status_code1 == 400) {
    print("A query parameter has an invalid value.")
  } else if (status_code1 == 404) {
    print("The requested URI was not found.")
  } else if (status_code1 == 500) {
    print("The requested URI was not found.")
  } else {
    print(paste("HTTP", status_code1, "Error:", resp1$status_message))
  }
}

is_url <- function(x) {
  grepl("^https?://", x)
}

inputs <- getParameters()

inputParameters <- inputs[3:length(inputs)]

outputs <- getOutputs(inputs$server, inputs$process, inputParameters$outputData)

for (key in names(inputParameters)) {
  if (is_url(inputParameters[[key]])) {
    inputParameters[[key]] <- list("href" = inputParameters[[key]])
  }
}

jsonData <- list(
  "inputs" = inputParameters,
  "outputs" = outputs
)

jobID <- executeProcess(inputs$server, inputs$process, jsonData)

retrieveResults(inputs$server, jobID, inputParameters$outputData)
