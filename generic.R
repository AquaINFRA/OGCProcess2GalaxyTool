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

getOutputs <- function(url, process) {
    url <- paste(paste(url, "/processes/", sep = ""), process, sep = "")
    request <- request(url)
    response <- req_perform(request)
    responseBody <- parseResponseBody(response$body)
    responseBody$outputs

    outputs <- list()

    transmissionMode <- list("transmissionMode" = "reference")

    for (x in 1:length(responseBody$outputs)) {
        outputs = append(outputs, transmissionMode)
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

retrieveResults <- function(server, jobID) {
    #get results
}

inputs <- getParameters()
outputs <- getOutputs(inputs$server, inputs$process)

jsonData <- list(
  "inputs" = inputs[2:length(inputs)],
  "outputs" = outputs
)

jobID <- executeProcess(inputs$server, inputs$process, jsonData)

#retrieveResults(inputs$server, jobID)

