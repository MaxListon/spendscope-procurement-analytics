# Reproducible category-level sensitivity analysis of recorded award values.
args <- commandArgs(trailingOnly=TRUE)
if(length(args)!=2) stop("Expected reports and dashboard output directories")
reports <- args[1]; web <- args[2]
suppressPackageStartupMessages(library(ggplot2))
suppressPackageStartupMessages(library(jsonlite))
if(!requireNamespace("svglite",quietly=TRUE)) stop("Install svglite for SVG output")
d <- read.csv(file.path(reports,"statistical_input.csv"), stringsAsFactors=FALSE)
stopifnot(nrow(d)>0,all(is.finite(d$amount)),all(d$amount>0),!anyDuplicated(d$award_key))
script_path <- sub("^--file=", "", grep("^--file=", commandArgs(), value=TRUE)[1])
source(file.path(dirname(script_path),"concentration.R"))
buyer_results <- concentration_analysis(reports)
RNGkind("Mersenne-Twister","Inversion","Rejection");set.seed(20261112)
# Buyer/process dependence and reporting selection mean these are descriptive sensitivity intervals,
# not population confidence guarantees. Independently resample awards within category/year.
groups <- split(d, interaction(d$category,d$year, drop=TRUE,lex.order=TRUE))
result <- do.call(rbind,lapply(groups,function(g){
 x<-g$amount; B<-500L
 med<-replicate(B,median(sample(x,length(x),replace=TRUE)))
 interval<-quantile(med,c(.025,.975),names=FALSE,type=7)
 cap<-unname(quantile(x,.99,type=7))
 data.frame(category=g$category[1],year=g$year[1],awards=length(x),median=median(x),
            median_low=interval[1],median_high=interval[2],total=sum(x),
            largest_share=max(x)/sum(x), capped_total=sum(pmin(x,cap)),
            excluded_largest_total=sum(x)-max(x),p99=cap)
}))
stopifnot(all(result$median_low<=result$median),all(result$median_high>=result$median),
          all(result$capped_total<=result$total),sum(result$awards)==nrow(d))
write.csv(result,file.path(reports,"category_sensitivity.csv"),row.names=FALSE)
packages<-data.frame(package=c("R","ggplot2","jsonlite"),version=c(as.character(getRversion()),as.character(packageVersion("ggplot2")),as.character(packageVersion("jsonlite"))))
write.csv(packages,file.path(reports,"r_environment.csv"),row.names=FALSE)
p<-ggplot(result,aes(x=factor(year),y=median/1000,group=category,color=category))+
 geom_line(linewidth=.9)+geom_point(size=2.5)+
 geom_errorbar(aes(ymin=median_low/1000,ymax=median_high/1000),width=.10)+
 scale_color_manual(values=c("#087f8c","#d38a22","#6b5b95","#cc5a55"))+
 labs(title="Typical award size varies by category",subtitle="Median recorded award · 500 within-group bootstrap resamples",
      x=NULL,y="Award value (£ thousands)",color="Category",
      caption="Selected Contracts Finder snapshots • Descriptive intervals; reporting coverage is incomplete")+
 theme_minimal(base_size=12)+theme(legend.position="bottom",plot.title=element_text(face="bold"),panel.grid.minor=element_blank())
ggsave(file.path(web,"category-analysis.svg"),p,device=svglite::svglite,width=10,height=5.5,bg="#ffffff")
if(!file.exists(file.path(web,"category-analysis.svg"))) stop("Chart output missing")
output<-list(seed=20261112,replicates=500,unit="award",interval="2.5th–97.5th percentile bootstrap median",
             limitations="Independent awards assumed; shared buyer/process dependence and missing reporting not modeled. No causal or population inference.",
             categories=result,buyers=buyer_results)
write_json(output,file.path(reports,"r_analysis.json"),pretty=TRUE,auto_unbox=TRUE,digits=15)
writeLines(capture.output(sessionInfo()),file.path(reports,"R-session.txt"))
# Standalone research note is generated directly from executed results.
escape_html <- function(x) {
 x<-gsub("&","&amp;",x,fixed=TRUE);x<-gsub("<","&lt;",x,fixed=TRUE);x<-gsub(">","&gt;",x,fixed=TRUE);x
}
buyer_rows<-paste0("<tr><td>",escape_html(buyer_results$buyer_name),"</td><td>",round(buyer_results$hhi),"</td><td>",round(buyer_results$hhi_without_largest),"</td><td>",round(buyer_results$hhi_capped),"</td><td>",round(buyer_results$registered_value_share*100,1),"%</td></tr>",collapse="")
rows<-paste0("<tr><td>",escape_html(result$category),"</td><td>",result$year,"</td><td>",format(round(result$median),big.mark=","),
 "</td><td>",round(result$largest_share*100,1),"%</td><td>",round((1-result$capped_total/result$total)*100,1),"%</td></tr>",collapse="")
html<-paste0('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SpendScope | R research note</title><style>body{max-width:1000px;margin:60px auto;padding:0 24px;color:#18333c;font:17px/1.7 system-ui}h1{font-size:42px}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:12px;border-bottom:1px solid #ddd;text-align:left}img{width:100%}.note{background:#eef5f5;padding:20px}</style><a href="index.html">← Dashboard</a><h1>How stable are award-value comparisons?</h1><p>Executed R analysis of active, positive GBP awards dated 2022–2024 in the selected process snapshots.</p><img src="category-analysis.svg" alt="Median award sizes and bootstrap intervals by category and year"><h2>Tail sensitivity</h2><p>Capping each award at its category-year 99th percentile is a hypothetical sensitivity calculation. It is not a correction to the source or evidence of savings.</p><div style="overflow:auto"><table><tr><th>Category</th><th>Year</th><th>Median £</th><th>Largest award / total</th><th>Value reduction under cap</th></tr>',rows,'</table></div><h2>Buyer concentration sensitivity</h2><p>Top 30 supported buyers by attributable value. Removing the largest award or capping awards at the buyer-specific 99th percentile changes the analytical scenario. Registered evidence is the share of attributable value linked to a registration identifier.</p><div style="overflow:auto"><table><tr><th>Buyer</th><th>HHI</th><th>Without largest</th><th>Capped HHI</th><th>Registered evidence</th></tr>',buyer_rows,'</table></div><p>Buyer bootstrap results use 300 resamples and seed 20261113; download <a href="reports/buyer_sensitivity.csv">the full results</a> for percentile endpoints.</p><h2>Method and limits</h2><p>500 resamples of whole awards within each category-year; fixed seed 20261112. Percentile intervals describe median sensitivity under independent resampling. Repeated buyers and related procurement processes may create dependence. These intervals do not account for selection, missing records, inflation or publication changes.</p><p class="note">Award values may represent framework ceilings or multi-year commitments. They are not payments, annual spending, or realized supplier revenue. Changes between years are descriptive associations.</p><p>Source: UK Contracts Finder, compiled by Open Contracting Partnership. Contains public sector information licensed under the Open Government Licence v3.0.</p></html>')
writeLines(html,file.path(web,"research.html"))
