# R script to generate Venn Diagrams

suppressWarnings(library("VennDiagram"))
suppressWarnings(library("gridExtra"))

draw_pairwise_venn <- function(venn_file){
	# Warning! If the first file you specify has less than the second file, R will flip them for some reason! make sure the bigger file is first!
	# Reference two-set diagram
	venn.plot <- draw.pairwise.venn(
		area1 = venn_file[1,2],
		area2 = venn_file[2,2],
		cross.area = venn_file[3,2],
		category = c(toString(venn_file[1,1]), toString(venn_file[2,1])),
		fill = c("orange", "red"),
		lty = "dashed",
		cex = 1.5,
		cat.cex = 1.5,
		cat.col = c("orange", "red"),
		ind = FALSE,
		scaled = FALSE
		);
	return(venn.plot)
}

draw_triple_venn <- function(venn_file){
	# Reference three-set diagram
	venn.plot <- draw.triple.venn(
		area1 = venn_file[1,2],
		area2 = venn_file[2,2],
		area3 = venn_file[3,2],
		n12 = venn_file[4,2],
		n13 = venn_file[5,2],
		n23 = venn_file[6,2],
		n123 = venn_file[7,2],
		category = c(toString(venn_file[1,1]), toString(venn_file[2,1]), toString(venn_file[3,1])),
		fill = c("orange", "red", "blue"),
		lty = "dashed",
		cex = 2,
		cat.cex = 2,
		cat.col = c("orange", "red", "blue"),
		ind = FALSE,
		scaled = FALSE
		);
	return(venn.plot)
}

draw_quad_venn <- function(venn_file){
	# Reference four-set diagram
	venn.plot <- draw.quad.venn(
		area1 = venn_file[1,2],
		area2 = venn_file[2,2],
		area3 = venn_file[3,2],
		area4 = venn_file[4,2],
		n12 = venn_file[5,2],
		n13 = venn_file[6,2],
		n14 = venn_file[7,2],
		n23 = venn_file[8,2],
		n24 = venn_file[9,2],
		n34 = venn_file[10,2],
		n123 = venn_file[11,2],
		n124 = venn_file[12,2],
		n134 = venn_file[13,2],
		n234 = venn_file[14,2],
		n1234 = venn_file[15,2],
		category = c(toString(venn_file[1,1]), toString(venn_file[2,1]), toString(venn_file[3,1]), toString(venn_file[4,1])),
		fill = c("orange", "red", "green", "blue"),
		lty = "dashed",
		cex = 2,
		cat.cex = 2,
		cat.col = c("orange", "red", "green", "blue"),
		ind = FALSE,
		scaled = FALSE
		);
	return(venn.plot)
}

# here are some R tips I like to keep handy
# if (){
#} else {
#}
#     venn_file <- read.table(file_name, sep="\t", header=FALSE, row.names=NULL)
# grid.newpage()
# grid.arrange(gTree(children=venn), main=paste(venns[i], "#s of Variants Comparison"))
# ------ Code Starts Here -------
args<-commandArgs(TRUE)
output <- args[1]
title <- args[2]
subtitle <- args[3]

text_file <- paste(output, ".txt", sep='')
venn_file <- read.table(text_file, sep="\t", header=FALSE, row.names=NULL)

if (nrow(venn_file) == 3){
	venn.plot <- draw_pairwise_venn(venn_file);
} else if (nrow(venn_file) == 7){
	venn.plot <- draw_triple_venn(venn_file);
} else if (nrow(venn_file) == 15){
	venn.plot <- draw_quad_venn(venn_file);
}	

# Writing to file
pdf(paste(output,".pdf", sep=''));
if (subtitle != "None"){
	grid.arrange(gTree(children=venn.plot), main=textGrob(title, gp=gpar(cex=3), just="top"), sub=textGrob(subtitle, gp=gpar(cex=1), vjust=-.5))
} else {
	grid.arrange(gTree(children=venn.plot), main=textGrob(title, gp=gpar(cex=3), just="top"))
}
dev.off();
