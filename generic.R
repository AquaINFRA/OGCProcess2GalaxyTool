library("httr")
library("httr2")
library("jsonlite")
library("getopt")

cat("start generic wrapper service \n")

getParameters <- function(){
    con <- file("inputs.json", "r")
    lines <- readLines(con)
    close(con)

    json_string <- paste(lines, collapse = "\n")
    json_data <- fromJSON(json_string)
    formatted_json_string <- toJSON(json_data$conditional_process, pretty = TRUE, auto_unbox = TRUE)
    return(formatted_json_string)
}

parseResponseBody <- function(body) {
  hex <- c(body)
  intValues <- as.integer(hex)
  rawVector <- as.raw(intValues)
  readableOutput <- rawToChar(rawVector)
  jsonObject <- jsonlite::fromJSON(readableOutput)
  return(jsonObject)
}

getOutputs <- function(inputs, output, server) {
    url <- paste(paste(server, "/processes/", sep = ""), inputs$select_process, sep = "")
    request <- request(url)
    response <- req_perform(request)
    responseBody <- parseResponseBody(response$body)
    outputs <- list()

    for (x in 1:length(responseBody$outputs)) {
        outputformatName <- paste(names(responseBody$outputs[x]), "_outformat", sep="")
        output_item <- list()

        for (p in names(inputs)) {
            if(p == outputformatName){
                format <- list("mediaType" = inputs[[outputformatName]])
                output_item$format <- format
            }
        }
        output_item$transmissionMode <- "reference"
        outputs[[x]] <- output_item
    }

    names(outputs) <- names(responseBody$outputs)
    return(outputs)
}

executeProcess <- function(url, process, requestBodyData) {
    headers <- c(
      'Content-Type' = 'application/json',
      'Accept' = 'application/json',
      'Cookie' = 'auth_tkt=d0de6b097d97e29afbff7cf76d0d80abc14775e35802fe0d7d725fb70b1e140a7647627d76548f90f459740568c44377e3aada77801cde806b59a94b7005d0446660526823!userid_type:int'
    )
    #cat("reqBody coming \n")
    #print(requestBodyData)
    body <- toString(requestBodyData$inputs)
    print(fromJSON(requestBodyData$inputs))

    #print(body)
    res <- VERB("POST", url = "https://hirondelle.crim.ca/weaver/processes/download-band-sentinel2-product-safe/execution", body = body, add_headers(headers))

    #cat(content(res, 'text'))
    parsed_response <- fromJSON(content(res, 'text'))
    #print(parsed_response$jobID)
    
    cat("\n Process executed")
    #print(res)
    #cat("\n status: ", response$status_code)
    #cat("\n jobID: ", parseResponseBody(response$body)$jobID, "\n")

    #jobID <- parseResponseBody(response$body)$jobID

    return(parsed_response$jobID)
}

checkJobStatus <- function(server, jobID) {
  response <- request(paste0(server, "jobs/", jobID)) %>%
    req_headers(
        'accept' = 'application/json'
    ) %>%
    req_perform()
  jobStatus <- parseResponseBody(response$body)$status
  jobProgress <- parseResponseBody(response$body)$progress
  cat(paste0("\n status: ", jobStatus, ", progress: ", jobProgress))
  return(jobStatus)
}

getStatusCode <- function(server, jobID) {
  url <- paste0(server, "jobs/", jobID)
  headers = c(
    'Cookie' = 'auth_tkt=d0de6b097d97e29afbff7cf76d0d80abc14775e35802fe0d7d725fb70b1e140a7647627d76548f90f459740568c44377e3aada77801cde806b59a94b7005d0446660526823!userid_type:int'
  )

  res <- VERB("GET", url = "https://hirondelle.crim.ca/weaver/processes/download-band-sentinel2-product-safe/jobs/dfc7b790-d9e4-48a8-9cfe-aacb2d0799e6", add_headers(headers))
  cat(res$status_code)
  parsed_response <- fromJSON(content(res, 'text'))
  #print(parsed_response)
  #der status code ist in der res aber nicht in der parsed response
  return(parsed_response$status)
}

getResult <- function (server, jobID) {
  headers = c(
    'Cookie' = 'auth_tkt=d0de6b097d97e29afbff7cf76d0d80abc14775e35802fe0d7d725fb70b1e140a7647627d76548f90f459740568c44377e3aada77801cde806b59a94b7005d0446660526823!userid_type:int'
  )

  res <- VERB("GET", url = "https://hirondelle.crim.ca/weaver/processes/download-band-sentinel2-product-safe/jobs/dfc7b790-d9e4-48a8-9cfe-aacb2d0799e6/results", add_headers(headers))

  parsed_response <- fromJSON(content(res, 'text'))
  #print(parsed_response)
  return(parsed_response)
}

retrieveResults <- function(server, jobID, outputData) {
    status <- getStatusCode(server, jobID)
    cat("tstauscode start")
    cat(status)
    status <- "running"
    #cat(status)
    while(status == "running"){
        jobStatus <- getStatusCode(server, jobID)
        cat("jobstatus start")
        cat(jobStatus)
        cat("jobstatus end")
        if (jobStatus == "succeeded") {
            status <- jobStatus
            result <- getResult(server, jobID)
            #if (result$status_code == 200) {
            resultBody <- result
            urls <- unname(unlist(lapply(resultBody, function(x) x$href)))
            urls_with_newline <- paste(urls, collapse = "\n")
            con <- file(outputData, "w")
            writeLines(urls_with_newline, con = con)
            close(con)
            #}
        } else if (jobStatus == "failed") {
          status <- jobStatus
        }
    Sys.sleep(3)
    }
    cat("\n done \n")
}

is_url <- function(x) {
  grepl("^https?://", x)
}

server <- "https://hirondelle.crim.ca/weaver/" #ogc-tb-16
#server <- "https://ospd.geolabs.fr:8300/ogc-api/" #aqua-infra

print("--> Retrieve parameters")
inputParameters <- getParameters()
print("--> Parameters retrieved")

args <- commandArgs(trailingOnly = TRUE)
outputLocation <- args[2]

print("--> Retrieve outputs")
#outputs <- getOutputs(inputParameters, outputLocation, server)
print("--> Outputs retrieved")

print("--> Parse inputs")
convertedKeys <- c()
for (key in names(inputParameters)) {
  #print(inputParameters[[key]])
  if (is.character(inputParameters[[key]]) && (endsWith(inputParameters[[key]], ".dat") || endsWith(inputParameters[[key]], ".txt"))) { 
    con <- file(inputParameters[[key]], "r")
    url_list <- list()
    while (length(line <- readLines(con, n = 1)) > 0) {
      if (is_url(line)) {
        url_list <- c(url_list, list(list(href = trimws(line))))
      }
    }
    close(con)
    inputParameters[[key]] <- url_list
    convertedKeys <- append(convertedKeys, key)
  }
  else if (grepl("_Array_", key)) {
    keyParts <- strsplit(key, split = "_")[[1]]
    type <- keyParts[length(keyParts)]
    values <- inputParameters[[key]]
    value_list <- strsplit(values, split = ",")

    convertedValues <- c()

    for (value in value_list) {
      if(type == "integer") {
        value <- as.integer(value)
      } else if (type == "numeric") {
        value <- as.numeric(balue)
      } else if (type == "character") {
        value <- as.character(value)
      }
    convertedValues <- append(convertedValues, value)

    convertedKey <- ""
    for (part in keyParts) {
      if(part == "Array") {
        break
      }
      convertedKey <- paste(convertedKey, paste(part, "_", sep=""), sep="")
    }
    convertedKey <- substr(convertedKey, 1, nchar(convertedKey)-1)
    #print(paste("--> converted key:", convertedKey))
}

    inputParameters[[key]] <- convertedValues
    convertedKeys <- append(convertedKeys, convertedKey)
  } else {
    convertedKeys <- append(convertedKeys, key)
  }
}
print(convertedKeys)
names(inputParameters) <- convertedKeys
print("--> Inputs parsed")

print("--> Prepare process execution")
jsonData <- list(
  "inputs" = getParameters()
#  "outputs" = outputs
)

#print(jsonData$inputs$inputs)

print("--> Execute process")
jobID <- executeProcess(server, inputParameters$select_process, jsonData)
print("--> Process executed")

print("--> Retrieve results")
retrieveResults(server, jobID, outputLocation)
print("--> Results retrieved")