source("R/concentration.R")
stopifnot(hhi(c(75,25),c("A","B"))==6250,
          hhi(c(50,50),c("A","A"))==10000,
          abs(hhi(rep(1,4),LETTERS[1:4])-2500)<1e-10)
# Cross-language CSV booleans must be parsed explicitly, not used as row names.
x<-c("True","False","TRUE","FALSE")
stopifnot(identical(tolower(x)=="true",c(TRUE,FALSE,TRUE,FALSE)))
cat("R concentration regression checks passed.\n")
