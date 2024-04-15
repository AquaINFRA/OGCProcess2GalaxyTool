args <- commandArgs(trailingOnly = TRUE)

params <- list()

for (x in 1:length(args)) {
    if(x %% 2 == 0) {
        param <- gsub("--", "", args[x-1])
        value <- args[x]
        params$param <- value
        assign(param, value)
        cat(paste("\n", param), value)

    }
}
