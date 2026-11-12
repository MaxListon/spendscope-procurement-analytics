# Award-level concentration sensitivity for supported buyers, independently cross-checked against SQL.
hhi <- function(amount, supplier) {
  totals <- tapply(amount,supplier,sum)
  sum((totals/sum(totals))^2)*10000
}
concentration_analysis <- function(reports) {
  a <- read.csv(file.path(reports,"attributed_input.csv"),stringsAsFactors=FALSE)
  sql <- read.csv(file.path(reports,"buyer_concentration.csv"),stringsAsFactors=FALSE)
  sql$supported <- tolower(as.character(sql$supported)) == "true"
  chosen <- head(sql[sql$supported,],30)
  RNGkind("Mersenne-Twister","Inversion","Rejection"); set.seed(20261113)
  result <- do.call(rbind,lapply(seq_len(nrow(chosen)),function(i){
    buyer<-chosen[i,];g<-a[a$buyer_key==buyer$buyer_key,];x<-g$amount;s<-g$supplier_key
    point<-hhi(x,s)
    if(!isTRUE(all.equal(point,buyer$hhi,tolerance=1e-8)))stop(sprintf("R/SQL HHI disagreement for %s: R=%s SQL=%s awards=%s",buyer$buyer_key,point,buyer$hhi,length(x)))
    # 300 award-level resamples; descriptive sensitivity, not a population inference.
    draws<-replicate(300,{j<-sample.int(length(x),length(x),replace=TRUE);hhi(x[j],s[j])})
    interval<-quantile(draws,c(.025,.975),names=FALSE)
    largest<-which.max(x); cap<-unname(quantile(x,.99))
    data.frame(buyer_key=buyer$buyer_key,buyer_name=buyer$buyer_name,awards=length(x),hhi=point,
      hhi_low=interval[1],hhi_high=interval[2],hhi_without_largest=hhi(x[-largest],s[-largest]),
      hhi_capped=hhi(pmin(x,cap),s),largest_award_share=max(x)/sum(x),
      registered_value_share=sum(x[g$identity_basis=='registered'])/sum(x),value_coverage=buyer$value_coverage)
  }))
  if(is.null(result))stop("No supported buyers for sensitivity analysis")
  stopifnot(all(is.finite(result$hhi)), all(result$hhi>0),all(result$hhi<=10000.00001))
  write.csv(result,file.path(reports,"buyer_sensitivity.csv"),row.names=FALSE)
  result
}
